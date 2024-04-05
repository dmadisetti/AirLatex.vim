import os
import stat
import errno
import fuse
import requests
import threading
import json
from fuse import Fuse
import sys
import neovim
import base64

if not hasattr(fuse, '__version__'):
    raise RuntimeError(
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."
    )

fuse.fuse_python_api = (0, 2)


class Stat(fuse.Stat):

    def __init__(self, mode, size=0):
        self.st_mode = mode
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 2 if stat.S_ISDIR(mode) else 1
        self.st_uid = os.getuid()
        self.st_gid = os.getgid()
        self.st_size = size
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


class OverleafBuildFS(Fuse):

    def __init__(self, root, *args, **kwargs):
        super(OverleafBuildFS, self).__init__(*args, **kwargs)
        self.root = root
        self.projects = {}
        self.build_id = None
        socket_path = f"{root}/socket"
        self.nvim = neovim.attach('socket', path=socket_path)
        self.update_thread = threading.Thread(target=self.event_listener)
        self.update_thread.start()

    def event_listener(self):
        self.nvim.subscribe('compile_output')
        self.nvim.subscribe('umount')

        def noop(*args, **kwargs):
            pass

        def handle_notification(event, encoding):
            if event == 'umount':
                self.nvim.stop_loop()
                return
            json_dump = base64.b64decode(encoding[0]).decode("ascii")
            response = json.loads(json_dump)
            project_files = {}
            for file in response['outputFiles']:
                # Initially, don't download the file; just store its URL
                project_files[file['path']] = {
                    'url': response['url'] + file['url'],
                    'content': None
                }
            self.projects[response['project']] = project_files
            self.header = response['headers']
            self.nvim.command("call rpcnotify(0, \"remount\", "
                              f"\"{response['mount_name']}\","
                              f"\"{response['project']}\")")

        def callback():
            self.nvim.command("call AirLatex_Compile(1)")

        self.nvim.run_loop(noop, handle_notification, setup_cb=callback)

    def getattr(self, path):
        parts = path.lstrip('/').split('/')
        if path == '/':
            return Stat(stat.S_IFDIR | 0o755)
        elif len(parts) == 1:  # Project directories
            if parts[0] in self.projects:
                return Stat(stat.S_IFDIR | 0o755)
            else:
                return -errno.ENOENT
        elif len(parts) == 2:  # Files within projects
            project, filename = parts
            if filename in self.projects.get(project, ()):
                file_info = self.projects[project][filename]
                size = len(file_info['content']
                           ) if file_info['content'] is not None else 1024000
                return Stat(stat.S_IFREG | 0o444, size=size)
            else:
                return -errno.ENOENT
        else:
            return -errno.ENOENT

    def readdir(self, path, offset):
        parts = path.lstrip('/').split('/')
        if path == '/':
            yield fuse.Direntry('.')
            yield fuse.Direntry('..')
            for project in self.projects:
                yield fuse.Direntry(project)
        elif len(parts) == 1 and parts[0] in self.projects:
            yield fuse.Direntry('.')
            yield fuse.Direntry('..')
            for filename in self.projects[parts[0]]:
                yield fuse.Direntry(filename)

    def read(self, path, size, offset):
        parts = path.lstrip('/').split('/')
        if len(parts) != 2:
            return -errno.ENOENT  # Not a file path

        project, filename = parts
        if project not in self.projects or filename not in self.projects[
                project]:
            return -errno.ENOENT  # File does not exist

        file_info = self.projects[project][filename]
        if file_info['content'] is None:
            # File content is not cached, fetch it
            try:
                response = requests.get(file_info['url'], headers=self.header)
                response.raise_for_status(
                )  # Ensure we got a successful response
                file_info['content'] = response.content
            except requests.RequestException:
                return -errno.EIO  # I/O error

        # Calculate the portion of the file to return based on size and offset
        file_content = file_info['content'][offset:offset + size]
        return file_content


def main(mountpoint):
    usage = "Neovim compile_output FUSE example" + Fuse.fusage

    root = os.path.dirname(os.path.abspath(mountpoint))
    server = OverleafBuildFS(root, version="%prog " + fuse.__version__,
                             usage=usage)
    server.parse(errex=1)
    print(server.__dict__)
    server.main()
    # Doesn't like me touching the server object, so just connect
    # again.
    socket_path = f"{root}/socket"
    neovim.attach('socket',
                  path=socket_path).command("call rpcnotify(0, \"umount\")")
    server.update_thread.join()


if __name__ == '__main__':
    main(sys.argv[-1])
