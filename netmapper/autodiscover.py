from pyzabbix import ZabbixAPI, ZabbixAPIException
import json
import subprocess
import requests

# Replace with your Zabbix server information
zabbix_url = 'http://192.168.1.2/api_jsonrpc.php'
zabbix_user = 'Admin'
zabbix_password = 'ZABBIX_ADMIN_PASS'

zapi = ZabbixAPI("http://192.168.1.2")
zapi.login(zabbix_user, zabbix_password)

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

        # Create hostgroup 
        #print('Enter the name for your hostgroup')
        hostgroup_name = 'IP Camera'
        hostgroup_id = create_or_get_hostgroup(zapi, hostgroup_name)
        
        current_discovery_rule_name = 'cctv'
        
        if not discovery_rule_exists(zapi, current_discovery_rule_name):
            print('Enter network range you want to discover, you can use commas to seperate IP address or IP ranges, for eg 192.168.0.1,192.168.1.8 or 192.168.1.0-254,192.168.2.0-254:')
            current_iprange = input('')
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

                        # Check if the key already exists in the dchecks
                        existing_keys = {dcheck["key_"] for dcheck in json_code["params"]["dchecks"]}

                        if key not in existing_keys:
                            # Add the new dcheck
                            dcheck = {
                                "type": 11,  # Constant value
                                "key_": key,
                                "snmp_community": values[1],
                                "ports": values[2],
                                "uniq": "0"  # Constant value
                            }
                            json_code["params"]["dchecks"].append(dcheck)
                        else:
                            print(f"Error: Insufficient elements in values for line '{line.strip()}'")

            # Create the discovery rule
            response = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(json_code), zabbix_url])
            drule_result = json.loads(response.decode())
            drule_id = drule_result['result']['druleids'][0]
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
                new_values = {
                    "iprange": f"{current_iprange},{updated_iprange}", # Update with your new IP range
                    "delay": updated_delay,
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

                            # Check if the key already exists in the dchecks
                            existing_keys = {dcheck["key_"] for dcheck in new_values["dchecks"]}

                            if key not in existing_keys:
                                # Add the new dcheck
                                dcheck = {
                                    "type": 11,  # Constant value
                                    "key_": key,
                                    "snmp_community": values[1],
                                    "ports": values[2],
                                    "uniq": "0"  # Constant value
                                }
                                new_values["dchecks"].append(dcheck)
                            else:
                                print(f"Error: Insufficient elements in values for line '{line.strip()}'")
                # Format the JSON payload for the update
                update_payload = format_update_payload(existing_rule_id, new_values)
                # Update the discovery rule
                response_update = subprocess.check_output(['curl', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(update_payload), zabbix_url])
                drule_update_result = json.loads(response_update.decode())
                print(f"Discovery rule updated for ID: {existing_rule_id} with new values.")
            else:
                print(f"Error: Discovery rule ID: '{exisiting_rule_id}' not found.")


        # Your adjusted code for creating a discovery action
        discovery_action_name = "cctv devices"
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
            print(f"Discovery action created with ID: {action_id}")
        else:
            print(f"Discovery action '{discovery_action_name}' already exists.")

    else:
        print("Authentication failed.")

except subprocess.CalledProcessError as e:
    print(f"Error executing curl command: {e}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON response: {e}")
except ZabbixAPIException as e:
    print(f"Zabbix API Exception: {e}")
