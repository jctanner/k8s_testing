#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule

import datetime
import json
import os
import subprocess


class ModProber:

    fn = '/etc/modules-load.d/k8s.conf'

    def __init__(self, check_mode=False, module_name=None):
        self.module_name = module_name
        self.check_mode = check_mode
        self.changed = False
        self.message = ''
        self.failed = False

        self.run()

    @property
    def result(self):
        return {
            'changed': self.changed,
            'message': self.message,
            'msg': self.message
        }

    def list_probed(self):
        pid = subprocess.run(
            "lsmod | awk '{print $1}' | fgrep -v Module",
            shell=True,
            stdout=subprocess.PIPE
        )
        modules = pid.stdout.decode('utf-8').split('\n')
        modules = [x.strip() for x in modules if x.strip()]
        return modules

    def list_configured(self):
        if not os.path.exists(self.fn):
            return []
        with open(self.fn, 'r') as f:
            raw = f.read()
        modules = [x.strip() for x in raw.split('\n') if x.strip()]
        return modules

    def set_onboot_config(self, module_name):
        current_modules = self.list_configured()
        if module_name in current_modules:
            return

        current_modules.append(module_name)
        current_modules = sorted(current_modules)
        with open(self.fn, 'w') as f:
            for cm in current_modules:
                f.write(f'{cm}\n')

    def run(self):
        current_modules = self.list_probed()
        current_configured_modules = self.list_configured()
        if self.module_name in current_modules and self.module_name in current_configured_modules:
            self.changed = False
            return
        self.changed = True

        pid = subprocess.run(
            f'modprobe {self.module_name}',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.message = pid.stdout.decode('utf-8')
        if pid.returncode != 0:
            self.failed = True

        self.set_onboot_config(self.module_name)


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present')
    )

    result = dict(
        changed=False,
        message="foo bar"
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    MP = ModProber(check_mode=module.check_mode, module_name=module.params['name'])
    if MP.failed:
        module.fail_json(**MP.result)
    module.exit_json(**MP.result)


def main():
    run_module()


if __name__ == '__main__':
    main()


