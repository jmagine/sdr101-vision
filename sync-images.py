#!/usr/bin/env python3
"""
Copies images from pi to host
"""

import os
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_host')
    parser.add_argument('source_dir')
    args = parser.parse_args()


    source = '{}@{}:~/{}'.format('pi', args.source_host, args.source_dir)
    dest = os.path.join('~', args.source_dir)

    cmd = ['rsync', '-rzvv', '-e', 'ssh', source, dest]
    print(cmd)
    subprocess.Popen(cmd, shell=True)

if __name__ == '__main__':
    main()
