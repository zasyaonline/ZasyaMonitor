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

def list_maps(api_address, auth_token):
    # List maps payload
    list_payload = {
        "jsonrpc": "2.0",
        "method": "map.get",
        "params": {
            "output": ["name", "sysmapid"]
        },
        "id": 1,
        "auth": auth_token
    }

    # Send list maps request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Available Maps:")
            for index, map_item in enumerate(result['result'], start=1):
                print(f"{index}. {map_item['name']} (ID: {map_item['sysmapid']})")
            return
    print("Failed to fetch maps.")

def delete_map_by_id(api_address, auth_token, map_ids):
    # Delete map payload
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "map.delete",
        "params": map_ids,
        "id": 1,
        "auth": auth_token
    }

    # Send delete map request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=delete_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Map(s) deleted successfully.")
            return
    print("Failed to delete map(s).")

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
        list_maps(api_address, auth_token)  # List available maps
        # Prompt user to delete map(s)
        map_serial_numbers = input("Enter the serial number(s) of the map(s) to delete (comma-separated), or 'm' to return to the main menu: ").split(",")
        if 'm' in map_serial_numbers:
            print()
            print()
            return # returns to main script
            print()
            print()

        map_ids_to_delete = []
        for serial_number in map_serial_numbers:
            try:
                serial_number = int(serial_number)
                # Fetch map list again and get the map ID based on serial number
                list_payload = {
                    "jsonrpc": "2.0",
                    "method": "map.get",
                    "params": {
                        "output": ["sysmapid"],
                    },
                    "id": 1,
                    "auth": auth_token
                }
                response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result and len(result['result']) >= serial_number:
                        map_ids_to_delete.append(result['result'][serial_number - 1]['sysmapid'])
                    else:
                        print(f"Invalid serial number: {serial_number}")
                else:
                    print(f"Failed to fetch map with serial number: {serial_number}")
            except ValueError:
                print(f"Invalid serial number: {serial_number}")

        if map_ids_to_delete:
            delete_map_by_id(api_address, auth_token, map_ids_to_delete)
        else:
            print("No valid map serial numbers provided.")

if __name__ == "__main__":
    main()

