from pyzabbix import ZabbixAPI, ZabbixAPIException

def get_host_id(zapi,hostname):
    hostname_lookup = zapi.host.get(filter={"host": hostname})
    if not hostname_lookup:
        return False
    else:
        return hostname_lookup[0]['hostid']

def get_ip_from_host_id(zapi,hostid):
    ip_lookup = zapi.hostinterface.get(filter={"hostid": hostid})
    if not ip_lookup:
        return False
    else:
        return ip_lookup[0]['ip']

def get_host_id_from_ip(zapi,ip):
    ip_lookup = zapi.hostinterface.get(filter={"ip": ip})
    if not ip_lookup:
        return False
    else:
        return hostname_lookup[0]['hostid']

def get_hostgroup_id(zapi,hostgroup_name):
    hostgroup_id_lookup = zapi.hostgroup.get(filter={"name": hostgroup_name})
    hostgroup_id = hostgroup_id_lookup[0]['groupid']
    return hostgroup_id

def get_hosts_from_hostgroup(zapi, hostgroup):
    # Get the hostgroup ID
    hostgroup_id = zapi.hostgroup.get(output="extend", filter={"name": hostgroup})[0]['groupid']

    # Get hosts from the hostgroup
    hosts = zapi.host.get(output=["hostid", "host"], groupids=hostgroup_id)

    return hosts

def get_hostname_from_hostid(zapi,hostid):
    hostname_lookup = zapi.host.get(filter={"hostid": hostid})
    hostname = hostname_lookup[0]['host']
    return hostname

def get_trigger_id(zapi, host, trigger_name):
    host_id = host.get('hostid') if isinstance(host, dict) else host[0]
    
    # Get triggers for the host
    triggers = zapi.trigger.get(output=["triggerid", "description"], hostids=host_id)

    # Find the trigger with the specified name
    for trigger in triggers:
        if trigger['description'] == trigger_name:
            return trigger['triggerid']

    # If the trigger is not found, print available triggers for debugging
    print("Trigger '{}' not found for host '{}'. Available triggers:".format(trigger_name, host_id))
    for trigger in triggers:
        print("Trigger ID: {}, Description: {}".format(trigger['triggerid'], trigger['description']))

    return None

def check_if_member_of_hostgroup(zapi,hostname,hostgroup):
    x = zapi.host.get(filter={"host": hostname},
                      selectGroups=hostgroup)
    hostgroup_id = get_hostgroup_id(zapi,hostgroup)
    return x

def get_system_name_from_host_id(zapi, hostid):
    try:
        # Get system.name item for the host
        item = zapi.item.get(
            hostids=hostid,
            search={'key_': 'system.name'},
            output=['itemid', 'lastvalue']
        )

        if item:
            system_name = item[0]['lastvalue']
            return system_name
        else:
            return None
    except ZabbixAPIException as e:
        print(f"Zabbix API error: {e}")
        return None
