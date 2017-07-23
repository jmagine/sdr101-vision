#!/usr/bin/env python3
"""
uses `rsync` to push code to the python module to the pi
pi should have used `sudo pip3 install -e .`

"""

import os
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Pushes the contents "
                                     "of ForwardVision/forward_vision "
                                     "to the pi")
    # parser.add_argument('source', required=True)
    parser.add_argument('remote', help="The host or ip of the pi to "
                        "push to")
    args = parser.parse_args()


    source = os.path.join(os.path.dirname(__file__), 'forward_vision')
    dest_dir = os.path.join('ForwardVision', 'forward_vision')
    dest = '{}@{}:~/{}'.format('pi', args.remote, 'ForwardVision')

    cmd = ['rsync', '-rzvv', '-e', 'ssh',
           '--exclude="__pycache__"',
           '--filter="dir-merge, - ~/ForwardVision/.gitignore"',
           source, dest]
    command = ' '.join(cmd)
    ret = os.system(command )
    if ret:
        pass
        # Fail

if __name__ == '__main__':
    main()
