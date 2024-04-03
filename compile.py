import os
import sys

import neovim
import logging


def noop(*args):
    pass


def main(rest, file_path):
    logging.basicConfig(filename='app.log', filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')
    logging.warning('This will get logged to a file')
    logging.warning(str(rest))
    logging.warning(file_path)

    base = f"/run/user/{os.getuid()}/airlatex"
    socket_path = f"{base}/socket"

    nvim = neovim.attach('socket', path=socket_path)
    logging.info('Neovim attached')
    # Listen for fuse mount event
    nvim.subscribe('remount')

    def handle_notification(event, *args):
        # Create a symlink for lsp
        active_path = f'{base}/active'
        build_path = f'{base}/builds/{file_path}'
        if os.path.lexists(active_path):
            os.remove(active_path)
        logging.info('Removed existing active path')
        os.symlink(build_path, active_path)
        logging.info('Created symlink for lsp')

        with open(f'{base}/builds/{file_path}/output.stderr', 'r') as f:
            sys.stderr.write(f.read())
        with open(f'{base}/builds/{file_path}/output.stdout', 'r') as f:
            sys.stdout.write(f.read())

        nvim.stop_loop()
        logging.info('Stopped Neovim loop')

    def callback():
        nvim.command("call AirLatex_Compile(1)")
        logging.info('Called AirLatex_Compile')

    nvim.run_loop(noop, handle_notification, setup_cb=callback)
    logging.info('Started Neovim loop')


if __name__ == "__main__":
    main(sys.argv, sys.argv[-1].lstrip('/').split('/')[0])
