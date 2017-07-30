#!/usr/bin/env python3
"""
uses `rsync` to push code to the python module to the pi
pi should have used `sudo pip3 install -e .`
"""
import sys
import os
import argparse
import subprocess
import logging


def main():
    parser = argparse.ArgumentParser(description="Pushes the contents "
                                     "of ForwardVision/forward_vision "
                                     "to the pi")
    # parser.add_argument('source', required=True)
    parser.add_argument('destination', help="The host or ip of the pi to "
                        "push to")
    parser.add_argument('-t', '--tunnel', help="SSH tunnel through this ip")
    parser.add_argument('-tu', '--tunnel-user', help="SSH tunnel through this "
                        "username", default='pi')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()


    source = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          'forward_vision'))
    source = os.path.abspath(os.path.dirname(__file__))
    dest_dir = '/home/pi/'
    dest = '{0}@{1}:{2}'.format('pi', args.destination, dest_dir)

    rsh = 'ssh'
    if args.tunnel:
        # -A passes auth through tunnel
        if args.tunnel.count('@') == 1:
            rsh = '"ssh -A {} ssh "'.format(args.tunnel)
        elif args.tunnel.count('@') == 0:
            rsh = '"ssh -A {}@{} ssh "'.format(args.tunnel_user, args.tunnel)
        else:
            raise ValueError(args.tunnel)

    # recurive, compressed, verbose
    cli_args = '-rzvv'

    cmd = ['rsync', cli_args, '-e', rsh,
           '--exclude="__pycache__"', '--exclude="images"', '--exclude=".git/"'
           '--filter="dir-merge"',
           source, dest]
    command = ' '.join(cmd)
    print(command)
    if not args.dry_run:
        ret = os.system(command)
        sys.exit(ret)

if __name__ == '__main__':
    main()
