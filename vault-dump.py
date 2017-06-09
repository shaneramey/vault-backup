#! /usr/bin/env python
# dumps a HashiCorp Vault to write statements
# requires an already-authenticated session

import subprocess
import os
import pwd
import hvac
import datetime

def print_header():
    user = pwd.getpwuid(os.getuid()).pw_name
    date = "{} UTC".format(datetime.datetime.utcnow())
    vault_address = os.environ['VAULT_ADDR']

    print '#'
    print '# vault-dump.py backup'
    print "# dump made by {}".format(user)
    print "# backup date: {}".format(date)
    print "# VAULT_ADDR env variable: {}".format(vault_address)
    print '#'

# looks at an argument for a value and prints the key
#  if a value exists
def recurse_for_values(path_prefix, candidate_key):
    candidate_values = candidate_key['data']['keys']
    for candidate_value in candidate_values:
        next_index = path_prefix + candidate_value
        next_value = client.list(next_index)
        if isinstance(next_value, dict):
            recurse_for_values(next_index, next_value)
        else:
            stripped_prefix=path_prefix[:-1]
            final_dict = client.read(next_index)['data']
            print "vault write {} \\".format(next_index)

            sorted_final_keys = sorted(final_dict.keys())
            for final_key in sorted_final_keys[:-1]:
                final_value = final_dict[final_key]
                print "  {0}=\'{1}\' \\".format(final_key, final_value)
            last_final_key = sorted_final_keys[-1]
            last_final_value = final_dict[last_final_key]
            print "  {0}=\'{1}\'".format(last_final_key, last_final_value)

env_token = subprocess.check_output(
    "vault read -field id auth/token/lookup-self",
    shell=True)
client = hvac.Client(token=env_token)
assert client.is_authenticated()

print_header()
top_vault_prefix = '/secret/'
top_level_keys = client.list(top_vault_prefix)
recurse_for_values(top_vault_prefix, top_level_keys)
