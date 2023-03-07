#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule

import datetime
import json
import os
import subprocess


class PackageUpdater:

    cachefile = '/root/.updater.json'

    def __init__(self, check_mode=False):
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

    def run(self):

        timestamp = None

        if os.path.exists(self.cachefile):
            with open(self.cachefile, 'r') as f:
                meta = json.loads(f.read())
            timestamp = datetime.datetime.fromisoformat(meta['timestamp'])

        if timestamp and (datetime.datetime.now() - timestamp).days < 1:
            self.changed = False
            self.message = 'updated less than a day ago'
            return

        pid = subprocess.run(
            'apt -y update',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        if pid.returncode != 0:
            self.failed = True
        self.message = pid.stdout.decode('utf-8')

        pid = subprocess.run(
            'apt list --upgradeable',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        update_check = pid.stdout.decode('utf-8')

        if '[upgradeable from:' in update_check:
            self.changed = True

        if self.check_mode:
            self.msg += update_check
            return

        pid = subprocess.run(
            'apt -y upgrade',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self.message += pid.stdout.decode('utf-8')
        self.changed = True

        with open(self.cachefile, 'w') as f:
            f.write(json.dumps({'timestamp': datetime.datetime.now().isoformat()}))


def run_module():
    module_args = dict()

    result = dict(
        changed=False,
        message="foo bar"
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    PU = PackageUpdater(check_mode=module.check_mode)
    if PU.failed:
        module.fail_json(**PU.result)
    module.exit_json(**PU.result)


def main():
    run_module()


if __name__ == '__main__':
    main()


