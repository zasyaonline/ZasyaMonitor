import subprocess
import getpass
import json
import requests

def authenticate_user(api_address, zabbix_user, zabbix_password):
    while True:
        
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
        main()
       

def list_actions(api_address, auth_token):
    # List actions payload
    list_payload = {
        "jsonrpc": "2.0",
        "method": "action.get",
        "params": {
            "output": ["name", "actionid"]
        },
        "id": 1,
        "auth": auth_token
    }

    # Send list actions request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Available Actions:")
            for index, action in enumerate(result['result'], start=1):
                print(f"{index}. {action['name']} (ID: {action['actionid']})")
            return
    print("Failed to fetch actions.")

def delete_action_by_id(api_address, auth_token, action_ids):
    # Delete action payload
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "action.delete",
        "params": action_ids,
        "id": 1,
        "auth": auth_token
    }

    # Send delete action request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=delete_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Action rule(s) deleted successfully.")
            return
    print("Failed to delete action rule(s).")

# Main function
def main():
    api_address = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.strip().split()[0]

    print('Enter Zasya Username:')
    zabbix_user = input('')
    print('Enter Zasya Password:')
    zabbix_password = getpass.getpass('')

    auth_token = authenticate_user(api_address, zabbix_user, zabbix_password)
    
    
    if auth_token:
        print("Authentication successful.")
        list_actions(api_address, auth_token)  # List available actions
        # Prompt user to delete action(s)
        action_serial_numbers = input("Enter the serial number(s) of the action rule(s) to delete (comma-separated), or 'm' to return to the main menu: ").split(",")

        if 'm' in action_serial_numbers:
            print()
            print()
            return # return to main script
            print()
        action_ids_to_delete = []
        for serial_number in action_serial_numbers:
            try:
                serial_number = int(serial_number)
                # Fetch action list again and get the action ID based on serial number
                list_payload = {
                    "jsonrpc": "2.0",
                    "method": "action.get",
                    "params": {
                        "output": ["actionid"],
                    },
                    "id": 1,
                    "auth": auth_token
                }
                response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result and len(result['result']) >= serial_number:
                        action_ids_to_delete.append(result['result'][serial_number - 1]['actionid'])
                    else:
                        print(f"Invalid serial number: {serial_number}")
                else:
                    print(f"Failed to fetch action with serial number: {serial_number}")
            except ValueError:
                print(f"Invalid serial number: {serial_number}")

        if action_ids_to_delete:
            delete_action_by_id(api_address, auth_token, action_ids_to_delete)
        else:
            print("No valid action serial numbers provided.")

if __name__ == "__main__":
    main()

