#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule

import datetime
import json
import os
import shutil
import subprocess



class HostsEntry:

    types = {
        'c': 'comment',
        'b': 'blank line',
        '6': 'ipv6 entry',
        '4': 'ipv4 entry'
    }

    def __init__(self, raw):
        self.raw = raw
        self.atype = None
        self.addr = None
        self.names = []
        self.process()

    def __repr__(self):
        if self.atype == 'c':
            return f'<comment: {self.raw}>'
        if self.atype == 'b':
            return f'<blank>'
        if self.atype == '6':
            return f'<ipv6: {self.addr} {self.names}>'
        if self.atype == '4':
            return f'<ipv4: {self.addr} {self.names}>'
        return '<unknown>'

    def __str__(self):
        return self.raw

    def process(self):
        if not self.raw.strip():
            self.atype = 'b'
            return
        if self.raw.startswith('#'):
            self.atype = 'c'
            return

        parts = self.raw.split()
        parts = [x.strip() for x in parts if x.strip()]
        self.addr = parts[0]
        self.names = parts[1:]
        if '::' in self.addr:
            self.atype = '6'
        else:
            self.atype = '4'

    def to_string(self):
        if self.atype == 'c':
            return self.raw.rstrip()
        if self.atype == 'b':
            return ''
        return self.addr + ' ' + ' '.join(self.names)


class HostNames:

    fn = '/etc/hosts'

    def __init__(self, check_mode=False, hostvars=None, domain=None):
        self.hostvars = hostvars
        self.domain = domain

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

    def parse_line(self, line):
        return HostsEntry(line)

    def parse_file(self):
        with open(self.fn, 'r') as f:
            fdata = f.read()
        flines = fdata.split('\n')
        parsed = []
        for fline in flines:
            parsed.append(self.parse_line(fline))
        return parsed

    def parse_hostvars(self):
        newhosts = []
        for mname,mdata in self.hostvars.items():
            ipaddress = mdata['ansible_ssh_host']
            if '.' in mname:
                mname = mname.split('.')[0]
            nh = HostsEntry(f'{ipaddress} {mname}.{self.domain} {mname}')
            newhosts.append(nh)
        return newhosts

    def write_hosts(self, hosts):
        tfn = self.fn + '.new'
        with open(tfn, 'w') as f:
            for hn in hosts:
                f.write(hn.to_string() + '\n')
        shutil.copy(tfn, self.fn)

    def run(self):
        current_hosts = self.parse_file()
        self.message += str(current_hosts)

        newhosts = self.parse_hostvars()
        self.message += str(newhosts)

        missing = []
        for nh in newhosts:
            found = None
            for ch in current_hosts:
                if ch.atype in ['b', 'c']:
                    continue
                if ch.atype == nh.atype and ch.addr == nh.addr:
                    found = ch
                    break
            if not found:
                missing.append(nh)

        if missing:
            self.changed = True

        if self.check_mode or not missing:
            return

        self.write_hosts(current_hosts + missing)


def run_module():
    module_args = dict(
        hostvars=dict(type='dict', required=True),
        domain=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        message="foo bar"
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    MP = HostNames(
        check_mode=module.check_mode,
        hostvars=module.params['hostvars'],
        domain=module.params['domain']
    )
    if MP.failed:
        module.fail_json(**MP.result)
    module.exit_json(**MP.result)


def main():
    run_module()


if __name__ == '__main__':
    main()


