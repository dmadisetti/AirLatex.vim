#!/nix/store/qfq0id8z2zsag00230ps8zlmb18s18aa-python3-3.10.13-env/bin/python3.10

import os
import sys
import json

import neovim


def noop(*args):
    pass


def main(file_path):
    socket_path = f"/run/user/{os.getuid()}/airlatex/socket"

    nvim = neovim.attach('socket', path=socket_path)
    # Listen for fuse mount event
    nvim.subscribe('remount')

    def handle_notification(event, *args):
        with open(f'mount/{file_path}/output.stderr', 'r') as f:
            sys.stderr.write(f.read())
        with open(f'mount/{file_path}/output.stdout', 'r') as f:
            sys.stdout.write(f.read())
        nvim.stop_loop()

    callback = lambda: nvim.command("call AirLatex_Compile(1)")
    nvim.run_loop(noop, handle_notification, setup_cb=callback)


if __name__ == "__main__":
    main(sys.argv[1].lstrip('/').split('/')[0])
