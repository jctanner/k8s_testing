#!/usr/bin/env python

import argparse
import copy
import os
import glob
import json
import subprocess
import sys


def get_machines_states():
    pid = subprocess.run('vagrant status 2>/dev/null | fgrep "(libvirt)"', shell=True, stdout=subprocess.PIPE)
    stdout = pid.stdout.decode('utf-8')
    lines = [x.strip() for x in stdout.split('\n') if x.strip()]
    mmap = {}
    for line in lines:
        line = line.replace('(libvirt)', '').strip()
        parts = line.split(None, 1)
        mmap[parts[0]] = parts[1]
    return mmap

def get_machines():

    cachefile = 'inventory.cache.json'
    if os.path.exists(cachefile):
        with open(cachefile, 'r') as f:
            machines = json.loads(f.read())
        return machines

    pid = subprocess.run('vagrant ssh-config 2>/dev/null', shell=True, stdout=subprocess.PIPE)
    if pid.returncode == 0:
        lines = pid.stdout.decode('utf-8').split('\n')
    else:
        # try by machine ...
        lines = []
        states = get_machines_states()
        for mname,mstate in states.items():
            if mstate != 'running':
                continue
            mpid = subprocess.run(f'vagrant ssh-config {mname} 2>/dev/null', shell=True, stdout=subprocess.PIPE)
            lines.extend(mpid.stdout.decode('utf-8').split('\n'))

    machines = {}
    this_host = None
    for idx,x in enumerate(lines):
        if not x.strip():
            continue
        if x.startswith('Host'):
            this_host = x.split()[-1]
            if this_host not in machines:
                machines[this_host] = {}
            continue

        words = x.split()
        machines[this_host][words[0]] = words[1]

    with open(cachefile, 'w') as f:
        f.write(json.dumps(machines, indent=2, sort_keys=True))

    return machines


def make_list(machines):
    groups = {}
    hosts = sorted(list(machines.keys()))
    for host in hosts:
        group_name = ''.join([x for x in host if not x.isdigit()])
        group_name += '_hosts'
        if group_name not in groups:
            groups[group_name] = {'hosts': []}
        groups[group_name]['hosts'].append(host)
    return groups


def machines_to_inventory(machines):
    groups = {}
    hosts = sorted(list(machines.keys()))
    for host in hosts:
        group_name = ''.join([x for x in host if not x.isdigit()])
        group_name += '_hosts'
        if group_name not in groups:
            groups[group_name] = {'hosts': []}
        groups[group_name]['hosts'].append(host)

    inv = {
        '_meta': {
            'hostvars': {}
        },
        'all': {
            'children': []
        },
        'ungrouped': {
            'children': []
        }
    }

    for groupn, groupd in groups.items():
        inv[groupn] = copy.deepcopy(groupd)
        inv['all']['children'].append(groupn)

    for machine,mdict in machines.items():
        inv['_meta']['hostvars'][machine] = {
            'ssh_key_policy': 'accept',
            'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
            'ansible_ssh_host': mdict['HostName'],
            'ansible_ssh_port': int(mdict['Port']),
            'ansible_ssh_user': mdict['User'],
            'ansible_user': mdict['User'],
            'ansible_ssh_private_key_file': mdict['IdentityFile'],
        }
        # inv['all']['children'].append(machine)

    # import epdb; epdb.st()
    return inv


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host')
    args = parser.parse_args()

    machines = get_machines()

    if args.list:
        # print(json.dumps(make_list(machines), indent=2))
        print(json.dumps(machines_to_inventory(machines), indent=2))
        return

    #if args.host:
    #    print(json.dumps(machines[args.host], indent=2))
    #    return

    with open('/tmp/log.txt', 'a') as f:
        f.write(str(sys.argv) + '\n')

    print(json.dumps(machines_to_inventory(machines), indent=2))


if __name__ ==  "__main__":
    main()
