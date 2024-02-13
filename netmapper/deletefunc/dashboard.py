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

def list_dashboards(api_address, auth_token):
    # List dashboards payload
    list_payload = {
        "jsonrpc": "2.0",
        "method": "dashboard.get",
        "params": {
            "output": ["name", "dashboardid"]
        },
        "id": 1,
        "auth": auth_token
    }

    # Send list dashboards request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Available Dashboards:")
            for index, dashboard in enumerate(result['result'], start=1):
                print(f"{index}. {dashboard['name']} (ID: {dashboard['dashboardid']})")
            return
    print("Failed to fetch dashboards.")

def delete_dashboard_by_id(api_address, auth_token, dashboard_ids):
    # Delete dashboard payload
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "dashboard.delete",
        "params": dashboard_ids,
        "id": 1,
        "auth": auth_token
    }

    # Send delete dashboard request
    response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=delete_payload)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            print("Dashboard(s) deleted successfully.")
            return
    print("Failed to delete dashboard(s).")

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
        list_dashboards(api_address, auth_token)  # List available dashboards
        # Prompt user to delete dashboard(s)
        dashboard_serial_numbers = input("Enter the serial number(s) of the dashboard(s) to delete (comma-separated), or 'm' to return to the main menu: ").split(",")

        if 'm' in dashboard_serial_numbers:
            print()
            print()
            return # return to main script
            print()

        dashboard_ids_to_delete = []
        for serial_number in dashboard_serial_numbers:
            try:
                serial_number = int(serial_number)
                # Fetch dashboard list again and get the dashboard ID based on serial number
                list_payload = {
                    "jsonrpc": "2.0",
                    "method": "dashboard.get",
                    "params": {
                        "output": ["dashboardid"],
                    },
                    "id": 1,
                    "auth": auth_token
                }
                response = requests.post(f"http://{api_address}/api_jsonrpc.php", json=list_payload)
                if response.status_code == 200:
                    result = response.json()
                    if 'result' in result and len(result['result']) >= serial_number:
                        dashboard_ids_to_delete.append(result['result'][serial_number - 1]['dashboardid'])
                    else:
                        print(f"Invalid serial number: {serial_number}")
                else:
                    print(f"Failed to fetch dashboard with serial number: {serial_number}")
            except ValueError:
                print(f"Invalid serial number: {serial_number}")

        if dashboard_ids_to_delete:
            delete_dashboard_by_id(api_address, auth_token, dashboard_ids_to_delete)
        else:
            print("No valid dashboard serial numbers provided.")

if __name__ == "__main__":
    main()

