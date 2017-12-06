#!/usr/bin/env python

from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: cisco_imc_bios
short_description: Configures bios settings on a Cisco IMC server
version_added: "0"
description:
    - Configures bios settings on a Cisco IMC server
    - Does not change settings if they are already correct
Input Params:
    bios_settings:
        description: List of {distinguished name, flag, value} to be set 
        required: True

requirements: ['imcsdk']
author: "Sarah Burgess (sarah@trademe.co.nz)"
'''

EXAMPLES = '''
- name: set bios values
  cisco_imc_bios:
    bios_settings:
      - dn: 'sys/rack-unit-1/bios/bios-settings/Processor-C3-Report'
        flag: vp_processor_c3_report
        value: disabled
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


def bios_setup(server, module):
    from imcsdk.imchandle import ImcHandle

    results = {}
    err = False

    try:
        ansible = module.params
        bios_settings=ansible['bios_settings']

        for setting in bios_settings:
            dn = setting['dn']
            flag = setting['flag']
            value = setting['value']

            managed_object = server.query_dn(dn)
            current_value = getattr(managed_object, flag)
            results["msg"] = str(current_value)

            # Set only if not already the correct value
            if current_value != value:
                setattr(managed_object, flag, value)
                server.set_mo(managed_object)
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
            bios_settings=dict(required=True, type='list'),

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
    results, err = bios_setup(server, module)
    conn.logout()
    if err:
        module.fail_json(**results)
    module.exit_json(**results)


if __name__ == '__main__':
    main()