#!/bin/bash

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
        *)
            echo "Invalid choice. Please enter a number from 1 to 7."
            ;;
    esac
done

