import subprocess
import getpass
import json
import requests

def authenticate_user(api_address, zabbix_user, zabbix_password):
    # Authentication payload
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
    # Send authentication request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=auth_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            auth_token = result['result']
            return auth_token
    print("Authentication failed. Please try again.")

def list_hostgroups(api_address, auth_token):
    # List host groups payload
    list_payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": ["name", "groupid"]
        },
        "id": 1,
        "auth": auth_token
    }

    # Send list host groups request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Available Host Groups:")
            for index, hostgroup in enumerate(result['result'], start=1):
                print(f"{index}. {hostgroup['name']} (ID: {hostgroup['groupid']})")
            return
    print("Failed to fetch host groups.")

def delete_hostgroup_by_id(api_address, auth_token, hostgroup_ids):
    # Delete host group payload
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.delete",
        "params": hostgroup_ids,
        "id": 1,
        "auth": auth_token
    }

    # Send delete host group request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=delete_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Host group(s) deleted successfully.")
            return
    print("Failed to delete host group(s).")

# Main function
def main():
    api_address = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.strip().split()[0]

    print('Enter Zabbix Username:')
    zabbix_user = input('')
    print('Enter Zabbix Password:')
    zabbix_password = getpass.getpass('')

    auth_token = authenticate_user(api_address, zabbix_user, zabbix_password)
    
    if auth_token:
        print("Authentication successful.")
        list_hostgroups(api_address, auth_token)  # List available host groups
        # Prompt user to delete host group(s)
        hostgroup_serial_numbers = input("Enter the serial number(s) of the hostgroup(s) to delete (comma-separated), or 'm' to return to the main menu: ").split(",")

        if 'm' in hostgroup_serial_numbers:
            print()
            print()
            return # return to main script
            print()

        hostgroup_ids_to_delete = []
        for serial_number in hostgroup_serial_numbers:
            try:
                serial_number = int(serial_number)
                # Fetch host group list again and get the host group ID based on serial number
                list_payload = {
                    "jsonrpc": "2.0",
                    "method": "hostgroup.get",
                    "params": {
                        "output": ["groupid"],
                    },
                    "id": 1,
                    "auth": auth_token
                }
                response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result and len(result['result']) >= serial_number:
                        hostgroup_ids_to_delete.append(result['result'][serial_number - 1]['groupid'])
                    else:
                        print(f"Invalid serial number: {serial_number}")
                else:
                    print(f"Failed to fetch host group with serial number: {serial_number}")
            except ValueError:
                print(f"Invalid serial number: {serial_number}")

        if hostgroup_ids_to_delete:
            delete_hostgroup_by_id(api_address, auth_token, hostgroup_ids_to_delete)
        else:
            print("No valid host group serial numbers provided.")

if __name__ == "__main__":
    main()

