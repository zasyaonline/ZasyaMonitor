from pyzabbix import ZabbixAPI, ZabbixAPIException
from netmapfunc import *
import json
import subprocess
import requests
import os
import base64
import random
import time
import getpass
import ipaddress
from multiprocessing import Pool, cpu_count

def get_sysmapid_from_file():
    with open("map.txt", "r") as file:
        sysmapid = file.read().strip()
    return sysmapid

def authenticate_user(api_address, zabbix_user, zabbix_password):
    # Replace with your Zabbix server information
    zabbix_url = f'http://{api_address}/api_jsonrpc.php'

    # Attempt to authenticate user
    zabbix_api_url = f"http://{api_address}"
    zapi = ZabbixAPI(zabbix_api_url)
    try:
        zapi.login(zabbix_user, zabbix_password)
        return zapi  # Return Zabbix API object upon successful authentication
    except Exception as e:
        print()
        print("Authentication failed, Please Try Again")
        print()
        return None  # Return None if authentication fails


# Running the command to get the IP address using hostname -I
result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
if result.returncode == 0:
    api_address = result.stdout.strip().split()[0]
print('Enter Zasya Username:')
zabbix_user = input('')
print('Enter Zasya Password:')
zabbix_password = getpass.getpass('')

# Loop until authentication is successful
while True:
    zapi = authenticate_user(api_address, zabbix_user, zabbix_password)
    if zapi:
        break
    else:
        result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
        if result.returncode == 0:
            api_address = result.stdout.strip().split()[0]
        print('Enter Zasya Username:')
        zabbix_user = input('')
        print('Enter Zasya Password:')
        zabbix_password = getpass.getpass('')

zabbix_url = f'http://{api_address}/api_jsonrpc.php'

min_coordinate = 300
max_coordinate = 800

trigger1 = 'Generic SNMP: High ICMP ping response time'
trigger2 = 'Generic SNMP: High ICMP ping loss'
trigger3 = 'Generic SNMP: Unavailable by ICMP ping'
trigger1color = 'FF6F00'
trigger2color = 'FF6F00'
trigger3color = 'DD0000'
custom_icon_path = 'icon/cctv_(64).png'


def ping_ip(ip, snmp_community, port):
    # Perform SNMP walk for each community string
    snmpwalk_command = ['snmpwalk', '-c', snmp_community, '-v', '2c', '-t', '2', str(ip), 'iso.3.6.1.2.1.1.1.0']
    try:
        result = subprocess.run(snmpwalk_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        if result.returncode == 0:
            return str(ip)
    except subprocess.TimeoutExpired:
        pass
    return None

def scan_cidr(cidr, snmp_community, port):
    ip_list = []
    network = ipaddress.ip_network(cidr)
    hosts_list = list(network.hosts())
    num_workers = min(cpu_count(), len(hosts_list))  # Use number of CPU cores by default
    with Pool(processes=num_workers) as p:
        ip_list = p.starmap(ping_ip, [(ip, snmp_community, port) for ip in hosts_list])
    return [ip for ip in ip_list if ip is not None]

def sort_ip_addresses(ip_addresses):
    sorted_ips = sorted(ip_addresses, key=lambda ip: tuple(map(int, ip.split('.'))))
    return sorted_ips

def save_to_file(reachable_ips, filename):
    sorted_ips = sort_ip_addresses(reachable_ips)

    with open(filename, 'a') as file:
        if sorted_ips:
            concatenated_line = ','.join(sorted_ips)
            concatenated_line = concatenated_line.rstrip(',')  
            file.write(concatenated_line)        

def read_from_file(filename):
    with open(filename, 'r') as file:
        ips = file.readlines()
        return [ip.rstrip('\n') for ip in ips]


def get_all_action_ids():
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}',
        }

        data = {
            'jsonrpc': '2.0',
            'method': 'action.get',
            'params': {'output': ['actionid']},
            'id': 1,
        }

        response = requests.post(zabbix_url, json=data, headers=headers)
        response.raise_for_status()

        actions = response.json()

        if 'result' in actions:
            # Extract action IDs
            action_ids = [action["actionid"] for action in actions['result']]
            return action_ids
        else:
            print(f"Failed to get action IDs. Response: {actions}")
            return []

    except requests.RequestException as e:
        print(f"Error making API request: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print(f"Response content: {response.text}")
        return []

def update_action_status(action_id, new_status):
    try:
        # Update action status using curl
        curl_command = [
            'curl',
            '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {auth_token}',
            '-d', f'{{"jsonrpc": "2.0", "method": "action.update", "params": {{"actionid": "{action_id}", "status": "{new_status}"}}, "id": 1}}',
            zabbix_url
        ]

        subprocess.check_output(curl_command)
        print(f"Updated status for action ID {action_id} to {new_status}")

    except subprocess.CalledProcessError as e:
        print(f"Error executing curl command: {e}")

def update_all_action_statuses(new_status):
    # Get all action IDs
    action_ids = get_all_action_ids()

    # Update status for each action
    for action_id in action_ids:
        update_action_status(action_id, new_status)

    print(f"All actions have been updated to status {new_status}")

def discovery_rule_exists(zapi, rule_name):
    # Function to check if a discovery rule with the given name already exists
    rules = zapi.drule.get(filter={"name": rule_name})
    return bool(rules)

def discovery_action_exists(zapi, action_name):
    # Function to check if a discovery action with the given name already exists
    actions = zapi.action.get(filter={"name": action_name})
    return bool(actions)

def get_hostgroup_id(zapi, group_name):
    # Function to get the host group ID by name
    hostgroup_id = None
    groups = zapi.hostgroup.get(filter={"name": group_name})
    if groups:
        hostgroup_id = groups[0]['groupid']
    return hostgroup_id

def create_hostgroup(zapi, group_name):
    # Function to create a host group
    result = zapi.hostgroup.create(name=group_name)
    return result['groupids'][0]

def create_or_get_hostgroup(zapi, group_name):
    # Function to create or get the host group by name
    hostgroup_id = get_hostgroup_id(zapi, group_name)
    if not hostgroup_id:
        hostgroup_id = create_hostgroup(zapi, group_name)
        print(f"Host group '{group_name}' created with ID: {hostgroup_id}")
        print()
    else:
        print(f"Host group '{group_name}' already exists with ID: {hostgroup_id}")
    return hostgroup_id

def make_api_request(url, data, headers):
    response = requests.post(url, json=data, headers=headers)
    return response.json()


def get_existing_iprange(existing_rule_id):
    get_rule_data = {
        "jsonrpc": "2.0",
        "method": "drule.get",
        "params": {
            "output": ["iprange"],
            "filter": {
                "druleid": existing_rule_id
            }
        },
        "auth": auth_token,
        "id": 1
    }

    response = make_api_request(zabbix_url, get_rule_data, headers={"Content-Type": "application/json"})

    # Check if the request was successful
    if "result" in response and response["result"]:
        existing_iprange = response["result"][0].get("iprange", "")
        return existing_iprange
    else:
        print("Failed to fetch existing IP range.")
        return None


def get_existing_delay(existing_rule_id):
    get_rule_data = {
        "jsonrpc": "2.0",
        "method": "drule.get",
        "params": {
            "output": ["delay"],
            "filter": {
                "druleid": existing_rule_id
            }
        },
        "auth": auth_token,
        "id": 1
    }

    response = make_api_request(zabbix_url, get_rule_data, headers={"Content-Type": "application/json"})

    # Check if the request was successful
    if "result" in response and response["result"]:
        existing_delay = response["result"][0].get("delay", "")
        return existing_delay
    else:
        print("Failed to fetch existing delay.")
        return None



def format_update_payload(existing_rule_id, new_values):
    return {
        "jsonrpc": "2.0",
        "method": "drule.update",
        "params": {
            "druleid": existing_rule_id,
            **new_values
            # ... (other parameters to update)
        },
        "id": 1,
        "auth": auth_token
    }

def create_dashboard(user, password, zabbix_url):

    # Define the JSON-RPC request payload for creating the dashboard widget with the auth token
    dashboard_payload = {
        "jsonrpc": "2.0",
        "method": "dashboard.create",
        "params": {
            "name": "IP Camera",
            "display_period": 30,
            "auto_start": 1,
            "pages": [
                {
                    "widgets": [
                        {
                            "type": "map",
                            "name": "Map",
                            "x": 0,
                            "y": 0,
                            "width": 18,
                            "height": 5,
                            "view_mode": 0,
                            "fields": [
                                {
                                    "type": 8,
                                    "name": "sysmapid",
                                    "value": map_id
                                }
                            ]
                        }
                    ]
                }
            ],
            "userGroups": [
                {
                    "usrgrpid": 7,
                    "permission": 2
                }
            ],
            "users": [
                {
                    "userid": 1,
                    "permission": 3
                }
            ]
        },
        "auth": auth_token,
        "id": 1,
    }

    # Convert the payload to JSON format
    dashboard_payload_json = json.dumps(dashboard_payload)

    # Make the API request to create the dashboard widget
    dashboard_response = requests.post(zabbix_url, headers={"Content-Type": "application/json"}, data=dashboard_payload_json)

    # Check if the request was successful
    if dashboard_response.status_code == 200:
        dashboard_response_data = dashboard_response.json()
        if "error" in dashboard_response_data:
            return {"success": False, "error_message": dashboard_response_data["error"]["message"]}
        else:
            return {"success": True}
    else:
        return {"success": False, "error_message": f"Failed to create dashboard. Status code: {dashboard_response.status_code}"}


try:
    # Authentication
    auth_payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": zabbix_user,
            "password": zabbix_password
        },
        "id": 1,
        "auth": None
    }

    auth_response = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(auth_payload), zabbix_url])
    auth_result = json.loads(auth_response.decode())

    if 'result' in auth_result:
        auth_token = auth_result['result']
        print(f"Authentication successful. Auth token: {auth_token}")
        print()
        # Create hostgroup 
        #print('Enter the name for your hostgroup')
        hostgroup_name = 'IP Camera'
        hostgroup_id = create_or_get_hostgroup(zapi, hostgroup_name)
        
        current_discovery_rule_name = 'cctv'
        
        if not discovery_rule_exists(zapi, current_discovery_rule_name):
            # Prompting user for SNMP community and port
            snmp_community = input("Enter SNMP community: ")
            port = input("Enter port number: ")

            
            existing_lines = []
            with open("configure-checks.txt", "r") as file:
                existing_lines = file.readlines()

            community_exists = False

            for i, line in enumerate(existing_lines):
                if snmp_community in line:
                    existing_lines[i] = "{} {}\n".format(snmp_community, port)
                    community_exists = True
                    break

            if not community_exists:
                # Lines to be added to the configure-checks.txt file
                lines_to_add = [
                    "iso.3.6.1.2.1.1.1.0 {} {}\n".format(snmp_community, port),
                ]
                
                existing_lines.extend(lines_to_add)

                # Writing lines to configure-checks.txt file
                with open("configure-checks.txt", "w") as file:
                    for line in existing_lines:
                        file.write(line)
            else:
                print("Community string already exists in configure-checks.txt")
            
            cidr  = input("Enter the CIDR range to scan (e.g., 192.168.1.0/24): ")
            with open('configure-checks.txt', 'r') as f:
                for line in f:
                    if line.startswith('iso.3.6.1.2.1.1.1.0'):
                        snmp_community, port = line.split()[1:3]
                        reachable_ips = scan_cidr(cidr, snmp_community, port)
                        filename = 'reachable_ips.txt'
                        save_to_file(reachable_ips, filename)
            r_iprange = read_from_file("reachable_ips.txt")
            
            for ip in r_iprange:
                current_iprange = ip


            print('Enter interval check for discovery to run, for eg 1m or 5s or 1h:')
            current_delay = input('')
            
            json_code = {
                "jsonrpc": "2.0",
                "method": "drule.create",
                "params": {
                    "name": current_discovery_rule_name,
                    "iprange": current_iprange,
                    "delay": current_delay,
                    "dchecks": []
                },
                "id": 1,
                "auth": auth_token
            }

            # Read values from the text file
            with open('configure-checks.txt', 'r') as file:
                for line in file:
                    values = line.strip().split(' ')
                    # Check if there are at least three elements in values
                    if len(values) >= 3:
                        key = values[0]

                        # Add the new dcheck
                        dcheck = {
                            "type": 11,  # Constant value
                            "key_": key,
                            "snmp_community": values[1],
                            "ports": values[2],
                            "uniq": "0"  # Constant value
                        }
                        json_code["params"]["dchecks"].append(dcheck)

            # Set the new status (1 for disable)
            new_status = "1"

            # Update status for all actions
            update_all_action_statuses(new_status)
            
            # Create the discovery rule
            response = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(json_code), zabbix_url])
            drule_result = json.loads(response.decode())
            drule_id = drule_result['result']['druleids'][0]
            print()
            print(f"Discovery rule created with ID: {drule_id}")

        else:      

            # Discovery rule already exists, update it with new values
            existing_rule = zapi.drule.get(filter={"name": current_discovery_rule_name})
            print('Enter additonal network range you want to discover, you can use commas to seperate IP address or IP ranges, for eg 192.168.0.1,192.168.1.8 or 192.168.1.0-254,192.168.2.0-254:')
            updated_iprange = input('')

            print('Enter updated interval check for discovery to run, for eg 1m or 5s or 1h:')
            updated_delay = input('')
            

            if existing_rule:
                
                existing_rule_id = existing_rule[0]['druleid']
                # Fetch existing IP range
                current_iprange = get_existing_iprange(existing_rule_id)
                current_delay = get_existing_delay(existing_rule_id)
                if updated_iprange:

                    new_values = {
                        "iprange": f"{current_iprange},{updated_iprange}", # Update with your new IP range
                        "delay": updated_delay,
                        "dchecks": []

                        # ... (other parameters to update)
                    }
                elif updated_delay:
                    new_values = {
                        "iprange": f"{current_iprange}", # Update with your new IP range
                        "delay": updated_delay,
                        "dchecks": []

                        # ... (other parameters to update)
                    }

                else:
                    new_values = {
                        "iprange": f"{current_iprange}", # Update with your new IP range
                        "delay": current_delay,
                        "dchecks": []

                        # ... (other parameters to update)
                    }

                # Read values from the text file
                with open('configure-checks.txt', 'r') as file:
                    for line in file:
                        values = line.strip().split(' ')
                        # Check if there are at least three elements in values
                        if len(values) >= 3:
                            key = values[0]
                            
                            # Add the new dcheck
                            dcheck = {
                                "type": 11,  # Constant value
                                "key_": key,
                                "snmp_community": values[1],
                                "ports": values[2],
                                "uniq": "0"  # Constant value
                            }
                            new_values["dchecks"].append(dcheck)

                
                # Format the JSON payload for the update
                update_payload = format_update_payload(existing_rule_id, new_values)
                # Update the discovery rule
                response_update = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(update_payload), zabbix_url])
                drule_update_result = json.loads(response_update.decode())
                print()
                print(f"Discovery rule updated for ID: {existing_rule_id} with new values.")
            else:
                print(f"Error: Discovery rule ID: '{exisiting_rule_id}' not found.")


        # Discovery Action Rule for cctv automap devices
        discovery_action_name = "cctv"
 
        if not discovery_action_exists(zapi, discovery_action_name):
            json_action = {
                "jsonrpc": "2.0",
                "method": "action.create",
                "params": {
                    "name": discovery_action_name,
                    "eventsource": 1,
                    "filter": {
                        "evaltype": 0,
                        "conditions": [

                            {
                                "conditiontype": 10,
                                "operator": 0,
                                "value": 2
                            },

                            {
                                "conditiontype": 8,
                                "operator": 0,
                                "value": 11
                            }
                        ]
                    },
                    "operations": [
                        {
                            "operationtype": 6,
                            "optemplate": [
                                {
                                    "templateid": "10563"
                                }
                            ]
                        },

                        {
                            "operationtype": 4,
                            "opgroup": [
                                {
                                    "groupid": hostgroup_id
                                }
                            ]
                        }
                    ]
                },
                "id": 1,
                "auth": auth_token
            }

          # Create the discovery action
            response_action = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(json_action), zabbix_url])
            action_result = json.loads(response_action.decode())
            print("Action result:", action_result)
            action_id = action_result['result']['actionids'][0]
            print()
            print(f"Discovery action created with ID: {action_id}")
        else:
            print(f"Discovery action '{discovery_action_name}' already exists.")


        # Discovery Action Rule for all cctv devices
        discovery_action_name1 = "cctv devices"
        
        if not discovery_action_exists(zapi, discovery_action_name1):
            json_action = {
                "jsonrpc": "2.0",
                "method": "action.create",
                "params": {
                    "name": discovery_action_name1,
                    "eventsource": 1,
                    "filter": {
                        "evaltype": 0,
                        "conditions": [
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "PvTel"
                            },
                            
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Mobotix"
                            },
                    
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Honeywell"
                            },
                    
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Hikivision"
                            },
                    
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Hanwa"
                            },
                   
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Flir"
                            },
                    
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Dahua"
                            },
                            
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "CP Plus"
                            },
                            
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Bosch"
                            },
                            
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Axis"
                            }
                        ]
                    },
                    "operations": [
                        {
                            "operationtype": 6,
                            "optemplate": [
                                {
                                    "templateid": "10563"
                                }
                            ]
                        },

                        {
                            "operationtype": 4,
                            "opgroup": [
                                {
                                    "groupid": hostgroup_id
                                }
                            ]
                        }
                    ]
                },
                "id": 1,
                "auth": auth_token
            }

            
            # Create the discovery action
            response_action = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(json_action), zabbix_url])
            action_result = json.loads(response_action.decode())
            print("Action result:", action_result)
            action_id = action_result['result']['actionids'][0]
            print()
            print(f"Discovery action created with ID: {action_id}")
        else:
            print(f"Discovery action '{discovery_action_name1}' already exists.")
        
        # Discovery Action Rule for Hikivision
        discovery_action_name2 = "Hikivision"
        
        if not discovery_action_exists(zapi, discovery_action_name2):
            json_action = {
                "jsonrpc": "2.0",
                "method": "action.create",
                "params": {
                    "name": discovery_action_name2,
                    "eventsource": 1,
                    "filter": {
                        "evaltype": 0,
                        "conditions": [
                            
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Hikivision"
                            },

                            {
                                "conditiontype": 8,
                                "operator": 0,
                                "value": 11
                            }
                        ]
                    },
                    "operations": [
                        {
                            "operationtype": 6,
                            "optemplate": [
                                {
                                    "templateid": "10380"
                                }
                            ]
                        },

                        {
                            "operationtype": 4,
                            "opgroup": [
                                {
                                    "groupid": hostgroup_id
                                }
                            ]
                        }
                    ]
                },
                "id": 1,
                "auth": auth_token
            }

            
            # Create the discovery action
            response_action = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(json_action), zabbix_url])
            action_result = json.loads(response_action.decode())
            print("Action result:", action_result)
            action_id = action_result['result']['actionids'][0]
            print()
            print(f"Discovery action created with ID: {action_id}")
        else:
            print(f"Discovery action '{discovery_action_name2}' already exists.")
        
        # Discovery Action Rule for Axis
        discovery_action_name3 = "Axis"
        
        if not discovery_action_exists(zapi, discovery_action_name3):
            json_action = {
                "jsonrpc": "2.0",
                "method": "action.create",
                "params": {
                    "name": discovery_action_name3,
                    "eventsource": 1,
                    "filter": {
                        "evaltype": 0,
                        "conditions": [
                            
                            {
                                "conditiontype": 12,
                                "operator": 2,
                                "value": "Axis"
                            },

                            {
                                "conditiontype": 8,
                                "operator": 0,
                                "value": 11
                            }
                        ]
                    },
                    "operations": [
                        {
                            "operationtype": 6,
                            "optemplate": [
                                {
                                    "templateid": "10602"
                                }
                            ]
                        },

                        {
                            "operationtype": 4,
                            "opgroup": [
                                {
                                    "groupid": hostgroup_id
                                }
                            ]
                        }
                    ]
                },
                "id": 1,
                "auth": auth_token
            }

            
            # Create the discovery action
            response_action = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(json_action), zabbix_url])
            action_result = json.loads(response_action.decode())
            print("Action result:", action_result)
            action_id = action_result['result']['actionids'][0]
            print()
            print(f"Discovery action created with ID: {action_id}")
        else:
            print(f"Discovery action '{discovery_action_name3}' already exists.")

        
        
    else:
        print("Authentication failed.")

except subprocess.CalledProcessError as e:
    print(f"Error executing curl command: {e}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON response: {e}")
except ZabbixAPIException as e:
    print(f"Zabbix API Exception: {e}")

print()

print('############## Restarting Zasya Services ##################')
# Restart server and wait for 2 min 

service_name = "zabbix-server"
restart_command = ["systemctl", "restart", service_name]

try:
    subprocess.run(restart_command, check=True)
    print("Zasya Service restarted succesfully !")
except subprocess.CalledProcessError as e:
    print(f"Error restarting Zasya Services: {e}")


print("############### Starting Network Auto Map Configurator ##############")

time.sleep(300)

print()

print()
# Netmap Discovery Code Starts from here----------------------

print('Enter the hostgroup for which you want to make a map, format, exact syntax needed')
my_hostgroup = input('')

print()

my_hostgroup_obj = get_hostgroup_id(zapi, my_hostgroup)
hosts = get_hosts_from_hostgroup(zapi, my_hostgroup)
host_element_id_mapping = []

for index, host in enumerate(hosts):
    hostid = host['hostid']
    elementid = index + 2
    host_element_id_mapping.append((hostid, elementid))

# Check if the map already exists
existing_maps = zapi.map.get(filter={"name": my_hostgroup})
if existing_maps:
    existing_map = existing_maps[0]
    map_id = existing_map['sysmapid']
    print(f"Map '{my_hostgroup}' already exists. Updating...")
else:
    map_id = None
    print(f"Map '{my_hostgroup}' does not exist. Creating...")

existing_icon_id = None  # Initialize existing_icon_id to None

print()

try:
    # Extract filename from the path
    custom_icon_name = os.path.splitext(os.path.basename(custom_icon_path))[0]

    # Check if the image with the same name already exists
    existing_images = zapi.image.get(filter={'name': custom_icon_name})
    if existing_images:
        existing_icon_id = existing_images[0]['imageid']
        print(f"Custom icon '{custom_icon_name}' already exists with ID: {existing_icon_id}. Skipping the upload.")
    else:
        # Upload Custom Icon
        with open(custom_icon_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        image_result = zapi.image.create(name=custom_icon_name, image=image_data, imagetype=1)

        custom_icon_id = image_result['imageids'][0]

        print(f"Custom icon '{custom_icon_name}' uploaded successfully with ID: {custom_icon_id}")

except ZabbixAPIException as e:
    print(f"Error: {e}")

print()

map_elements = []
cloud_node = {"selementid": "1",
                 "elements": [],
                 "elementtype": "4",
                 "iconid_off": "5",
                 "x": 680,
                 "y": 50,
                 'label': 'Cloud Node',
                 'label_location': '-1'
                 }

map_elements.append(cloud_node)


# Add another node connecting to cloud_node
edge_node = {"selementid": "2",
            "elements": [],
            "elementtype": "4",
            "iconid_off": "131",
            "x": 680,
            "y": 300,
            'label': 'Edge Router',
            'label_location': '-1'
            }

map_elements.append(edge_node)


# Add another node connecting to cloud_node
core_node = {"selementid": "3",
            "elements": [],
            "elementtype": "4",
            "iconid_off": "156",
            "x": 530,
            "y": 450,
            'label': 'Core Switch',
            'label_location': '-1'
            }

map_elements.append(core_node)

links = []

# Create a link from cloud_node to edge_node
cloud_to_edge_link = {}
cloud_to_edge_link['selementid1'] = '1'  # cloud_node
cloud_to_edge_link['selementid2'] = '2'  # edge_node
cloud_to_edge_link['color'] = "00CC00"  # Set your desired color for the link
cloud_to_edge_link['label'] = 'Cloud to Edge Link'
links.append(cloud_to_edge_link)

# Create a link from edge_node to core_node
edge_to_core_link = {}
edge_to_core_link['selementid1'] = '2'  # edge_node
edge_to_core_link['selementid2'] = '3'  # core_node
edge_to_core_link['color'] = "00CC00"  # Set your desired color for the link
edge_to_core_link['label'] = 'Edge to Core Link'
links.append(edge_to_core_link)

network_hosts = {}

for host in host_element_id_mapping:
    map_element = {}
    map_element['selementid'] = host[0]
    map_element['elements'] = []

    element = {}
    element['hostid'] = host[0]
    map_element['elements'].append(element)
    map_element['elementtype'] = "0"
    # Check if existing_icon_id is not None
    if existing_icon_id is not None:
        map_element['iconid_off'] = existing_icon_id
    else:
        map_element['iconid_off'] = custom_icon_id

    map_element['x'] = random.randint(min_coordinate, max_coordinate)
    map_element['y'] = random.randint(min_coordinate, max_coordinate)
    print(f"Randomizing coordinates for new host {host[0]}: X={map_element['x']}, Y={map_element['y']}")

    ip_address = get_ip_from_host_id(zapi, host[0])
    system_name = get_system_name_from_host_id(zapi, host[0])

    map_elements.append(map_element)


    # Create links from new_node to each host in host_element_id_mapping
    link = {}
    link['selementid1'] = '3'
    link['selementid2'] = host[0]
    link['color'] = "00CC00"
    hostname = get_hostname_from_hostid(zapi, host[0])
    label = f"{system_name}\n{ip_address}"
    link['label'] = label

    link['linktriggers'] = []
    linktrigger1 = {}
    linktrigger1['triggerid'] = get_trigger_id(zapi, host, trigger1)
    linktrigger1['drawtype'] = '0'
    linktrigger1['color'] = 'FF6F00'
    link['linktriggers'].append(linktrigger1)

    linktrigger2 = {}
    linktrigger2['triggerid'] = get_trigger_id(zapi, host, trigger2)
    linktrigger2['drawtype'] = '0'
    linktrigger2['color'] = 'FF6F00'
    link['linktriggers'].append(linktrigger2)

    linktrigger3 = {}
    linktrigger3['triggerid'] = get_trigger_id(zapi, host, trigger3)
    linktrigger3['drawtype'] = '0'
    linktrigger3['color'] = 'DD0000'
    link['linktriggers'].append(linktrigger3)

    links.append(link)

print()

# Check if the map already exists and update or create accordingly
if map_id:
    # Map already exists, update it
    zapi.map.update(sysmapid=map_id,
                    name=my_hostgroup,
                    selements=map_elements,
                    links=links)
    print(f"Map '{my_hostgroup}' updated successfully.")
else:
    # Map does not exist, create it
    new_map = zapi.map.create(name=my_hostgroup,
                              width="1920",
                              height="1080",
                              selements=map_elements,
                              links=links)


    print(f"Map '{my_hostgroup}' created successfully.")

    sysmapid = new_map['sysmapids'][0]

    with open("map.txt", "w") as file:
        file.write(str(sysmapid))

print()
print("#################### Creating Dashboard for Map ##############################")
print()

zabbix_url = f'http://{api_address}/api_jsonrpc.php'
user = zabbix_user
password = zabbix_password
map_id = get_sysmapid_from_file()
result = create_dashboard(user, password, zabbix_url)
if result["success"]:
    print("Dashboard created succesfully.")
else:
    print("Error:", result["error_message"])

