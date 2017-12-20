# Copyright 2017 Endless Mobile, Inc.

import os
import sys

here = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(here, '..'))


from flapjack import commands  # noqa


BASH_COMPLETION_TEMPLATE = os.path.join(here, "bash-completion.in")
BASH_COMPLETION_FILE = os.path.join(here, '..', 'build',
                                    "flapjack.bash-completion")


def get_command_vars():
    all_commands = commands.get_all_commands()
    return {
        'SUBCOMMANDS': ' '.join(all_commands['all']),
        'SUBCOMMANDS_MODULE_MATCH': '|'.join(all_commands['requiring module']),
        'SUBCOMMANDS_APPS_MATCH': '|'.join(all_commands['requiring app']),
        'SUBCOMMANDS_OTHER_MATCH': '|'.join(all_commands['no params']),
    }


def fill_template(template_vars):
    with open(BASH_COMPLETION_TEMPLATE) as template:
        script_text = template.read()
        for var_name, value in template_vars.items():
            script_text = script_text.replace('%%' + var_name + '%%', value, 1)
        return script_text


def write_script(script_text):
    dirname = os.path.dirname(BASH_COMPLETION_FILE)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    with open(BASH_COMPLETION_FILE, 'w') as script_file:
        script_file.write(script_text)


template_vars = get_command_vars()
script_text = fill_template(template_vars)
write_script(script_text)
