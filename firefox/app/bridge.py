#!/usr/bin/env python

import os
import socket
import sys
import json
import struct
from contextlib import closing
import errno

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


def bind_socket(sock, socket_path):
  try:
    sock.bind(socket_path)
  except OSError as e:
    # If the socket already exists, remove it and try again
    if e.errno == errno.EADDRINUSE:
        os.remove(socket_path)
        bind_socket(sock, socket_path)  # Recursive call
    else:
        raise e


# receivedMessage = getMessage()
# if receivedMessage == "pair":

# We don't need a pair. Just send if if we get it, otherwise we can get out of
# sync.
while True:
  try:
    socket_path = f"/run/user/{os.getuid()}/airlatex_socket"

    with closing(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)) as sock:
      bind_socket(sock, socket_path)  # Call the helper function
      # Queue of just size 1
      sock.listen(1)
      conn, addr = sock.accept()
      while True:
        data = conn.recv(1024).decode('utf-8')
        # If the received scroll value is empty or some termination signal,
        # break out of the loop
        if not data or data == 'TERMINATION_SIGNAL':
          break
        # Send the scroll value back to the client
        sendMessage(encodeMessage(data))
      conn.close()
  except Exception as e:
    sendMessage(encodeMessage(f"{e}"))
sendMessage(encodeMessage("closed"))
