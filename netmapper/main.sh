#!/bin/bash

# Banner
display_banner () {
	echo "#########################################################################
#									#
#			Zasya Configurator		                #
#									#
#########################################################################"
}

main_menu() {
    clear
    display_banner
    echo "Select an option:"
    echo "1. Use Autodiscovery and Network Mapper"
    echo "2. Delete Autodiscovery and Network Mapper"
    echo "3. Exit"
}

submenu_option1() {
    echo "You selected: Use Autodiscovery and Network Mapper"
    # Run the first Python script
    echo "##################### Running AutoDiscovery Script ##################"
    sudo python3 autodiscover.py
    echo ""
    echo "Auto Discovery Completed"

    echo "Network Map Created. Please arrange the map to your suitable topology and perform any other manual changes to your liking !!"

}

submenu_option2() {
    echo "You selected: Delete Autodiscovery and Network Mapper"

# Banner
display_banner () {
	echo "#########################################################################
#									#
#			Zasya Configuration Remover		        #
#									#
#########################################################################"
}

display_banner
echo ""
while true; do
    echo "Main Menu:"
    echo "1. Delete Auto Discover Action Rules"
    echo "2. Delete Auto Discovery Rules"
    echo "3. Delete Hostgroups"
    echo "4. Delete Hosts"
    echo "5. Delete Maps"
    echo "6. Delete Dashboards"
    echo "7. Quit"
    echo "8. Return to Zabbix Configurator Menu"

    read -p "Enter your choice (1-7): " choice

    case $choice in
        1)
            python3 deletefunc/discovery.py
            ;;
        2)
            python3 deletefunc/action.py
            ;;
        3)
            python3 deletefunc/hostgroup.py
            ;;
        4)
            python3 deletefunc/host.py
            ;;
        5)
            python3 deletefunc/map.py
            ;;
        6)
            python3 deletefunc/dashboard.py
            ;;
        7)
            echo "Exiting..."
            exit 0
            ;;

	8)
	    return
	    ;;
        *)
            echo "Invalid choice. Please enter a number from 1 to 7."
            ;;
    esac
done


}

main_menu

while true; do
    read -p "Enter your choice: " choice
    case $choice in
        1)
            submenu_option1
            ;;
        2)
            submenu_option2
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option. Please select again."
            ;;
    esac
    main_menu
done

