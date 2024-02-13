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

def list_hosts(api_address, auth_token):
    # List hosts payload
    list_payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "hostid"]
        },
        "id": 1,
        "auth": auth_token
    }

    # Send list hosts request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Available Hosts:")
            for index, host in enumerate(result['result'], start=1):
                print(f"{index}. {host['host']} (ID: {host['hostid']})")
            return
    print("Failed to fetch hosts.")

def delete_host_by_id(api_address, auth_token, host_ids):
    # Delete host payload
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "host.delete",
        "params": host_ids,
        "id": 1,
        "auth": auth_token
    }

    # Send delete host request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=delete_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Host(s) deleted successfully.")
            return
    print("Failed to delete host(s).")

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
        list_hosts(api_address, auth_token)  # List available hosts
        # Prompt user to delete host(s)
        host_serial_numbers = input("Enter the serial number(s) of the host(s) to delete (comma-separated), or 'm' to return to the main menu: ").split(",")

        if 'm' in host_serial_numbers:
            print()
            print()
            return # return to main script
            print()

        host_ids_to_delete = []
        for serial_number in host_serial_numbers:
            try:
                serial_number = int(serial_number)
                # Fetch host list again and get the host ID based on serial number
                list_payload = {
                    "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": ["hostid"],
                    },
                    "id": 1,
                    "auth": auth_token
                }
                response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result and len(result['result']) >= serial_number:
                        host_ids_to_delete.append(result['result'][serial_number - 1]['hostid'])
                    else:
                        print(f"Invalid serial number: {serial_number}")
                else:
                    print(f"Failed to fetch host with serial number: {serial_number}")
            except ValueError:
                print(f"Invalid serial number: {serial_number}")

        if host_ids_to_delete:
            delete_host_by_id(api_address, auth_token, host_ids_to_delete)
        else:
            print("No valid host serial numbers provided.")

if __name__ == "__main__":
    main()

