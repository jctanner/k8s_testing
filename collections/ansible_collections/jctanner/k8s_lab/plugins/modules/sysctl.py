#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule

import datetime
import json
import os
import subprocess


class SysCtl:

    fn = '/etc/sysctl.d/1000-ansible.conf'

    def __init__(self, check_mode=False, setting=None, value=None):
        self.setting = setting
        self.value = value
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

    def get_conf_settings(self):
        if not os.path.exists(self.fn):
            return {}

        with open(self.fn, 'r') as f:
            raw = f.read()

        conf = {}
        lines = raw.split('\n')
        lines = [x.strip() for x in lines if x.strip()]
        for line in lines:
            words = line.split('=')
            words = [x.strip() for x in words if x.strip()]
            if len(words) != 2:
                raise Exception(f'{line} {words}')
            conf[words[0]] = words[1]

        return conf

    def set_conf(self, setting, value):
        current_conf = self.get_conf_settings()
        current_conf[setting] = value
        keys = sorted(list(current_conf.keys()))
        with open(self.fn, 'w') as f:
            for key in keys:
                f.write(f"{key} = {current_conf[key]}\n")

    def run(self):
        current_conf = self.get_conf_settings()

        pid = subprocess.run(
            f'sysctl {self.setting}',
            shell=True,
            stdout=subprocess.PIPE
        )
        current_value = pid.stdout.decode('utf-8').split()[-1].strip()
        if current_value != str(self.value):
            self.changed = True
        if self.setting not in current_conf or current_conf.get(self.setting) != str(self.value):
            self.changed = True
        if self.check_mode or self.changed is False:
            return

        pid = subprocess.run(
            f'sysctl {self.setting}={self.value}',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.message = pid.stdout.decode('utf-8')
        if pid.returncode != 0:
            self.failed = True
            return

        self.set_conf(self.setting, self.value)


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        value=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        message="foo bar"
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    MP = SysCtl(
        check_mode=module.check_mode,
        setting=module.params['name'],
        value=module.params['value']
    )
    if MP.failed:
        module.fail_json(**MP.result)
    module.exit_json(**MP.result)


def main():
    run_module()


if __name__ == '__main__':
    main()


