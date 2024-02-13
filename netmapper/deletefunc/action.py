import subprocess
import getpass
import json
import requests

def authenticate_user(api_address, zabbix_user, zabbix_password):
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
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=auth_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            auth_token = result['result']
            return auth_token
    print("Authentication failed. Please try again.")
        

def list_discovery_rules(api_address, auth_token):
    list_payload = {
        "jsonrpc": "2.0",
        "method": "drule.get",
        "params": {
            "output": ["name", "druleid"]
        },
        "id": 1,
        "auth": auth_token
    }
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Available Discovery Rules:")
            for index, drule in enumerate(result['result'], start=1):
                print(f"{index}. {drule['name']} (ID: {drule['druleid']})")
            return
    print("Failed to fetch discovery rules.")

def delete_discovery_rule_by_id(api_address, auth_token, drule_ids):
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "drule.delete",
        "params": drule_ids,
        "id": 1,
        "auth": auth_token
    }
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=delete_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Discovery rule(s) deleted successfully.")
            return
    print("Failed to delete discovery rule(s).")

def main():
    
    api_address = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.strip().split()[0]
    print('Enter Zabbix Username:')
    zabbix_user = input('')
    print('Enter Zabbix Password:')
    zabbix_password = getpass.getpass('')
    auth_token = authenticate_user(api_address, zabbix_user, zabbix_password)
     
    
    if auth_token:
        print("Authentication successful.")
        list_discovery_rules(api_address, auth_token)
        rule_serial_numbers = input("Enter the serial number(s) of the discovey rule(s) to delete (comma-separated), or 'm' to return to the main menu: ").split(",")

        if 'm' in rule_serial_numbers:
            print()
            print()
            return # return to main script
            print()

        rule_ids_to_delete = []
        for serial_number in rule_serial_numbers:
            try:
                serial_number = int(serial_number)
                list_payload = {
                    "jsonrpc": "2.0",
                    "method": "drule.get",
                    "params": {
                        "output": ["druleid"],
                    },
                    "id": 1,
                    "auth": auth_token
                }
                response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result and len(result['result']) >= serial_number:
                        rule_ids_to_delete.append(result['result'][serial_number - 1]['druleid'])
                    else:
                        print(f"Invalid serial number: {serial_number}")
                else:
                    print(f"Failed to fetch discovery rule with serial number: {serial_number}")
            except ValueError:
                print(f"Invalid serial number: {serial_number}")

        if rule_ids_to_delete:
            delete_discovery_rule_by_id(api_address, auth_token, rule_ids_to_delete)
        else:
            print("No valid rule serial numbers provided.")

if __name__ == "__main__":
    main()

