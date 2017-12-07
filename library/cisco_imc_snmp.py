#!/usr/bin/env python

from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: cisco_imc_snmp
short_description: Configures snmp settings on a Cisco IMC server
version_added: "0"
description:
    - Configures snmp settings on a Cisco IMC server
Input Params:
    enabled:
        description: Is SNMP enabled?
        required: True
        default: "no"
        choices: ["yes","no"]

    snmp_port:
        description: SNMP Port
        required: False
        default: 161

    community:
        description: Access community string
        required: False
        default: None

    privilege:
        description: SNMP community access
        required: False
        default: "disabled"
        choices: ["disabled","limited", "full"]

    trap_community:
        description: Trap community string
        default: None
        required: False

    sys_contact: 
        description: System contact email
        default: None
        required: False
    
    sys_location: 
        description: System location
        default: None
        required: False

requirements: ['imcsdk']
author: "Sarah Burgess (sarah@trademe.co.nz)"
'''

EXAMPLES = '''
- name: enable snmp
  cisco_imc_snmp:
    enabled: yes
    snmp_port: 161
    community: community
    privilege: disabled
    trap_community: trap_community
    sys_contact: test@test.com
    sys_location: wellington
    ip: "192.168.1.1"
    username: "admin"
    password: "password"
'''


def login(module):
    ansible = module.params
    server = ansible.get('server')
    if server:
        return server

    from imcsdk.imchandle import ImcHandle
    results = {}
    try:
        server = ImcHandle(ip=ansible["ip"],
                           username=ansible["username"],
                           password=ansible["password"],
                           port=ansible["port"],
                           secure=ansible["secure"],
                           proxy=ansible["proxy"])
        server.login()
    except Exception as e:
        results["msg"] = str(e)
        module.fail_json(**results)
    return server


def logout(module, imc_server):
    ansible = module.params
    server = ansible.get('server')
    if server:
        # we used a pre-existing handle from another task.
        # do not logout
        return False

    if imc_server:
        imc_server.logout()
        return True
    return False


def snmp_setup(server, module):
    from imcsdk.imchandle import ImcHandle

    from imcsdk.apis.admin.snmp import is_snmp_enabled
    from imcsdk.apis.admin.snmp import snmp_enable
    from imcsdk.apis.admin.snmp import snmp_disable

    results = {}
    err = False
    results["changed"] = False

    try:
        ansible = module.params

        enabled=ansible['enabled']
        snmp_port=ansible['snmp_port']
        community=ansible['community']
        privilege=ansible['privilege']
        trap_community=ansible['trap_community']
        sys_contact=ansible['sys_contact']
        sys_location=ansible['sys_location']

        if enabled == "yes":
            
            mo = snmp_enable(server, snmp_port=snmp_port,community=community,
                            privilege=privilege,trap_community=trap_community,
                            sys_contact=sys_contact,sys_location=sys_location)
            
            results["changed"] = True

        else:
            snmp_enabled, mo_exists = is_snmp_enabled(server)
            if snmp_enabled:
                snmp_disable(server)
                results["changed"] = True
        
    except Exception as e:
        err = True
        results["msg"] = str(e)
        results["changed"] = False

    return results, err


def main():
    from ansible.module_utils.cisco_imc import ImcConnection
    module = AnsibleModule(
        argument_spec=dict(
            enabled=dict(required=True, type='str', 
                    choices=["yes", "no"]),
            snmp_port=dict(required=False, type='int', default=161 ),
            community=dict(required=False, type='str', default=None),
            privilege=dict(required=False, type='str', default="disabled",
                    choices=["disabled","limited", "full"]),
            trap_community=dict(required=False, type='str', default=None),
            sys_contact=dict(required=False, type='str', default=None),
            sys_location=dict(required=False, type='str', default=None),

            # ImcHandle
            server=dict(required=False, type='dict'),

            # Imc server credentials
            ip=dict(required=False, type='str'),
            username=dict(required=False, default="admin", type='str'),
            password=dict(required=False, type='str', no_log=True),
            port=dict(required=False, default=None),
            secure=dict(required=False, default=None),
            proxy=dict(required=False, default=None)
        ),
        supports_check_mode=False
    )

    conn = ImcConnection(module)
    server = conn.login()
    results, err = snmp_setup(server, module)
    conn.logout()
    if err:
        module.fail_json(**results)
    module.exit_json(**results)


if __name__ == '__main__':
    main()