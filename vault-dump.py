#! /usr/bin/env python3
#
# Dumps a HashiCorp Vault database to write statements.
# Useful for backing up in-memory vault data
# and later restoring from the generated script.
#
# Requires: an already-authenticated session
#
# Reads env vars:
# - VAULT_ADDR  which points to desired Hashicorp Vault instance, default http://localhost:8200
# - TOP_VAULT_PREFIX to specify path to dump, for partial backups, default /secret/
#
# Use custom encoding:
#   PYTHONIOENCODING=utf-8 python vault-dump.py
#
# Copyright (c) 2017 Shane Ramey <shane.ramey@gmail.com>
# Licensed under the Apache License, Version 2.0
from __future__ import print_function
import sys
import subprocess
import os
import pwd
import hvac
import datetime

def print_header():
    user = pwd.getpwuid(os.getuid()).pw_name
    date = "{} UTC".format(datetime.datetime.utcnow())
    vault_address = os.environ.get('VAULT_ADDR')
    top_vault_prefix = os.environ.get('TOP_VAULT_PREFIX','/secret/')

    print ('#')
    print ('# vault-dump.py backup')
    print ("# dump made by {}".format(user))
    print ("# backup date: {}".format(date))
    print ("# VAULT_ADDR env variable: {}".format(vault_address))
    print ("# TOP_VAULT_PREFIX env variable: {}".format(top_vault_prefix))
    print ('# STDIN encoding: {}'.format(sys.stdin.encoding))
    print ('# STDOUT encoding: {}'.format(sys.stdout.encoding))
    print ('#')
    print ('# WARNING: not guaranteed to be consistent!')
    print ('#')

# looks at an argument for a value and prints the key
#  if a value exists
def recurse_for_values(path_prefix, candidate_key):
    if 'keys' in candidate_key:
        candidate_values = candidate_key['keys']
    else:
        candidate_values = candidate_key['data']['keys']
    for candidate_value in candidate_values:
        next_index = path_prefix + candidate_value
        if candidate_value.endswith('/'):
            next_value = client.list(next_index)
            recurse_for_values(next_index, next_value)
        else:
            final_data = client.read(next_index) or {}
            if 'rules' in final_data:
                print ("\necho -ne {} | vault policy write {} -".format(repr(final_data['rules']), candidate_value), end='')
            elif 'data' in final_data:
                final_dict = final_data['data']
                print ("\nvault write {}".format(next_index), end='')

                sorted_final_keys = sorted(final_dict.keys())
                for final_key in sorted_final_keys:
                    final_value = final_dict[final_key]
                    print (" {0}='{1}'".format(final_key, final_value), end='')
            else:
                print("*** WARNING: no data for {}".format(next_index))


env_vars = os.environ.copy()
hvac_token = subprocess.check_output(
    "vault read -field id auth/token/lookup-self",
    shell=True,
    env=env_vars)

hvac_url = os.environ.get('VAULT_ADDR','http://localhost:8200')
hvac_client = {
    'url': hvac_url,
    'token': hvac_token,
}
client = hvac.Client(**hvac_client)
if os.environ.get('VAULT_SKIP_VERIFY'):
    import requests
    rs = requests.Session()
    client.session = rs
    rs.verify = False
    import warnings
    warnings.filterwarnings("ignore")
assert client.is_authenticated()

top_vault_prefix = os.environ.get('TOP_VAULT_PREFIX','/secret/')

print_header()
top_level_keys = client.list(top_vault_prefix)
recurse_for_values(top_vault_prefix, top_level_keys)
print()
