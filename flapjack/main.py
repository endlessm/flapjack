# Copyright 2017 Endless Mobile, Inc.

import argparse
import sys

from . import __version__, commands


def main():
    DESCRIPTION = ('Developer workflow for building a flatpak runtime while ' +
                   'developing one or more of the components in it.')
    EPILOG = ('Subcommands are:\n' + commands.get_help_text() +
              '\nFor more information run flapjack <command> --help\n')

    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__.__version__))
    parser.add_argument('command', help='Subcommand to run')
    parser.add_argument('options', nargs=argparse.REMAINDER,
                        help='Options for subcommand')
    args = parser.parse_args()

    try:
        command = commands.get_command(args.command)
    except KeyError:
        print('Unknown command "{}"'.format(args.command))
        parser.print_help()
        sys.exit(1)

    sys.exit(command.run(args.options))
