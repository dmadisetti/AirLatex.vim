import os
import sys

import neovim


def noop(*args):
    pass


def main(rest, expected_path):
    base = f"/run/user/{os.getuid()}/airlatex"
    socket_path = f"{base}/socket"

    nvim = neovim.attach('socket', path=socket_path)
    # Listen for fuse mount event
    nvim.subscribe('remount')

    def handle_notification(event, args):
        buffer_path, document_id = args
        if buffer_path != expected_path:
            nvim.err_write(f"Buffer path {buffer_path} does not"
                           f"match expected path {expected_path}\n")

        # Create a symlink for lsp + vimtex
        active_path = f'{base}/active'
        build_path = f'{base}/builds/{document_id}'
        if os.path.lexists(active_path):
            os.remove(active_path)
        os.symlink(build_path, active_path)

        with open(f'{base}/builds/{document_id}/output.stderr', 'r') as f:
            sys.stderr.write(f.read())
        with open(f'{base}/builds/{document_id}/output.stdout', 'r') as f:
            sys.stdout.write(f.read())

        nvim.stop_loop()

    def callback():
        nvim.command("call AirLatex_Compile(1)")

    nvim.run_loop(noop, handle_notification, setup_cb=callback)


if __name__ == "__main__":
    main(sys.argv, sys.argv[-1])
