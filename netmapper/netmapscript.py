#!/usr/bin/env python
from pyzabbix import ZabbixAPI, ZabbixAPIException
from netmapfunc import *
import os
import base64
import random

min_coordinate = 300 
max_coordinate = 800
zabbixuser = 'Admin'
zabbixpassword = 'ZABBIX_ADMIN_PASS'

trigger1 = 'Generic SNMP: High ICMP ping response time'
trigger2 = 'Generic SNMP: High ICMP ping loss'
trigger3 = 'Generic SNMP: Unavailable by ICMP ping'
trigger1color = 'FF6F00'
trigger2color = 'FF6F00'
trigger3color = 'DD0000'
custom_icon_path = 'icon/cctv_(64).png'

zapi = ZabbixAPI("http://192.168.1.2")
zapi.login(zabbixuser, zabbixpassword)
print('Enter the hostgroup for which you want to make a map, format, exact syntax needed')
my_hostgroup = input('')

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
