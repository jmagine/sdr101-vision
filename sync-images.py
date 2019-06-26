#!/usr/bin/env python3
"""
uses `rsync` to pull images from the pi at ~/ForwardVision/images
"""
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Pulls images from the pi")
    parser.add_argument(
        "source",
        help="The host or ip of the pi to " "pull images from",
        default="forward",
    )
    parser.add_argument("-t", "--tunnel", help="SSH tunnel through this ip")
    parser.add_argument(
        "-tu", "--tunnel-user", help="SSH tunnel through this " "username", default="pi"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = "{0}@{1}:{2}".format("pi", args.source, "/home/pi/ForwardVision/images/")
    # source = '{0}@{1}:{2}'.format('pi', args.source,
    #                               '/home/pi/images/')

    dest = os.path.abspath(os.path.join(os.path.dirname(__file__), "images/"))

    if args.tunnel:
        # -A passes auth through tunnel
        if args.tunnel.count("@") == 1:
            rsh = '"ssh -A {} ssh "'.format(args.tunnel)
        elif args.tunnel.count("@") == 0:
            rsh = '"ssh -A {}@{} ssh "'.format(args.tunnel_user, args.tunnel)
        else:
            raise ValueError()
    else:
        rsh = "ssh"

    # recurive, compressed, verbose
    cli_args = "-rzvv"

    cmd = [
        "rsync",
        cli_args,
        "-e",
        rsh,
        '--exclude="__pycache__"',
        '--filter="dir-merge, - ~/ForwardVision/.gitignore"',
        "--remove-source-files",
        "--ignore-existing",
        source,
        dest,
    ]
    command = " ".join(cmd)
    print(command)
    if not args.dry_run:
        ret = os.system(command)
        sys.exit(ret)


if __name__ == "__main__":
    main()
