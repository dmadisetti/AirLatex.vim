#!/nix/store/jra1iipq1x81v593kq2gnf74h7vbf3fs-python3-3.8.16/bin/python

import os
import socket
import sys
import json
import struct
from contextlib import closing

# Python 3.x version
# Read a message from stdin and decode it.
def getMessage():
    rawLength = sys.stdin.buffer.read(4)
    if len(rawLength) == 0:
        sys.exit(0)
    messageLength = struct.unpack('@I', rawLength)[0]
    message = sys.stdin.buffer.read(messageLength).decode('utf-8')
    return json.loads(message)

# Encode a message for transmission,
# given its content.
def encodeMessage(messageContent):
    # https://docs.python.org/3/library/json.html#basic-usage
    # To get the most compact JSON representation, you should specify
    # (',', ':') to eliminate whitespace.
    # We want the most compact representation because the browser rejects
    # messages that exceed 1 MB.
    encodedContent = json.dumps(messageContent, separators=(',', ':')).encode('utf-8')
    encodedLength = struct.pack('@I', len(encodedContent))
    return {'length': encodedLength, 'content': encodedContent}

# Send an encoded message to stdout
def sendMessage(encodedMessage):
    sys.stdout.buffer.write(encodedMessage['length'])
    sys.stdout.buffer.write(encodedMessage['content'])
    sys.stdout.buffer.flush()

def getScrollValue():
    with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as sock:
        sock.bind(f"/run/user/{os.getuid()}/airlatex_socket")
        sock.listen(1)
        conn, addr = sock.accept()
        with closing(conn):
            scroll_value = conn.recv(1024).decode('utf-8')
    return scroll_value

while True:
    receivedMessage = getMessage()
    if receivedMessage == "ping":
        # sendMessage(encodeMessage("Getting there"))
        scrollValue = getScrollValue()
        # sendMessage(encodeMessage("yes!"))
        sendMessage(encodeMessage(scrollValue))
