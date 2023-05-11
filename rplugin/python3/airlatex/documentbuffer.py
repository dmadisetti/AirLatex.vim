import pynvim
from difflib import SequenceMatcher
from threading import RLock
from hashlib import sha1
import asyncio
from asyncio import create_task, Lock
from logging import getLogger

from intervaltree import Interval, IntervalTree

if "allBuffers" not in globals():
  allBuffers = {}


class DocumentBuffer:
  allBuffers = allBuffers

  def __init__(self, path, nvim):
    self.log = getLogger("AirLatex")
    self.path = path
    self.nvim = nvim
    self.project_handler = path[0]["handler"]
    self.document = path[-1]
    self.initDocumentBuffer()
    self.buffer_mutex = RLock()
    self.saved_buffer = None
    self.threads = {}
    self.highlight = self.nvim.api.create_namespace('AirLatexCommentGroup')
    self.highlight2 = self.nvim.api.create_namespace(
        'AirLatexDoubleCommentGroup')
    self.pending_selection = self.nvim.api.create_namespace(
        'PendingCommentGroup')
    self.comment_selection = IntervalTree()
    self.buffer_event = asyncio.Event()
    self.thread_intervals = IntervalTree()
    self.cursors = {}

  @staticmethod
  def getName(path):
    return "/".join([p["name"] for p in path])

  @staticmethod
  def getExt(document):
    return document["name"].split(".")[-1]

  @property
  def content_hash(self):
    # compute sha1-hash of current buffer
    buffer_cpy = self.buffer[:]
    current_len = 0
    for row in buffer_cpy:
      current_len += len(row) + 1
    current_len -= 1
    tohash = ("blob " + str(current_len) + "\x00")
    for b in buffer_cpy[:-1]:
      tohash += b + "\n"
    tohash += buffer_cpy[-1]
    sha = sha1()
    sha.update(tohash.encode())
    return sha.hexdigest()

  @property
  def name(self):
    return DocumentBuffer.getName(self.path)

  @property
  def ext(self):
    return DocumentBuffer.getExt(self.document)

  def initDocumentBuffer(self):
    self.log.debug_gui("initDocumentBuffer")

    # Creating new Buffer
    self.nvim.command('wincmd w')
    self.nvim.command('enew')
    self.nvim.command('file ' + self.name)
    self.buffer = self.nvim.current.buffer
    DocumentBuffer.allBuffers[self.buffer] = self

    # Buffer Settings
    self.nvim.command("syntax on")
    self.nvim.command('setlocal noswapfile')
    self.nvim.command('setlocal buftype=nofile')
    self.nvim.command("set filetype=" + self.ext)

    # ??? Returning normal function to these buttons
    # self.nvim.command("nmap <silent> <up> <up>")
    # self.nvim.command("nmap <silent> <down> <down>")
    # self.nvim.command("nmap <silent> <enter> <enter>")
    # self.nvim.command("set updatetime=500")
    # self.nvim.command("autocmd CursorMoved,CursorMovedI * :call AirLatex_update_pos()")
    # self.nvim.command("autocmd CursorHold,CursorHoldI * :call AirLatex_update_pos()")
    self.nvim.command("cmap <buffer> w call AirLatex_Compile()<CR>")
    self.nvim.command("au CursorMoved <buffer> call AirLatex_WriteBuffer()")
    self.nvim.command("au CursorMovedI <buffer> call AirLatex_WriteBuffer()")
    self.nvim.command("au CursorMoved <buffer> call AirLatex_ShowComments()")
    self.nvim.command("command! -buffer -nargs=0 W call AirLatex_WriteBuffer()")

    self.nvim.command("vnoremap gv :<C-u>call AirLatex_CommentSelection()<CR>")

    # Comment formatting
    self.nvim.command(f"hi PendingCommentGroup ctermbg=190")
    self.nvim.command(f"hi AirLatexCommentGroup ctermbg=58")
    self.nvim.command(f"hi AirLatexDoubleCommentGroup ctermbg=94")
    self.nvim.command(f"hi CursorGroup ctermbg=18")

  def write(self, lines):

    def writeLines(buffer, lines):
      buffer[0] = lines[0]
      for l in lines[1:]:
        buffer.append(l)
      self.saved_buffer = buffer[:]
      self.buffer_event.set()

    self.nvim.async_call(writeLines, self.buffer, lines)

  def compile(self):
    create_task(self.project_handler.compile())

  def highlightRange(
      self, highlight, group, start_line, start_col, end_line, end_col):
    if start_line == end_line:
      self.buffer.api.add_highlight(
          highlight, group, start_line, start_col, end_col)
    else:
      self.buffer.api.add_highlight(highlight, group, start_line, start_col, -1)
      for line_num in range(start_line + 1, end_line):  # In-between lines
        self.buffer.api.add_highlight(highlight, group, line_num, 0, -1)
      self.buffer.api.add_highlight(highlight, group, end_line, 0, end_col)

  def markComment(self, *lineinfo):
    if self.comment_selection.is_empty():
      self.comment_selection = IntervalTree()
      start_line, start_col, end_line, end_col = lineinfo
      self.comment_selection.add(
          Interval(
              self.getPosition(start_line, start_col),
              self.getPosition(end_line, end_col)))

      self.highlightRange(
          self.pending_selection, "PendingCommentGroup", *lineinfo)

  def getCommentPosition(self, next: bool = False, prev: bool = False):
    if next == prev:
      return (-1, -1), 0

    cursor = self.nvim.current.window.cursor
    cursor_offset = self.getPosition(cursor[0] - 1, cursor[1])

    if next:
      positions = self.thread_intervals[
          cursor_offset + 1:] - self.thread_intervals[cursor_offset]
      offset = len(self.thread_intervals[:]) - len(positions) + 1
      if not positions:
        positions = self.thread_intervals[:
                                          cursor_offset] - self.thread_intervals[
                                              cursor_offset]
        offset = 1
      if not positions:
        return (-1, -1), 0
      pos = min(positions).begin
    elif prev:
      positions = self.thread_intervals[:cursor_offset] - self.thread_intervals[
          cursor_offset]
      offset = len(positions)
      if not positions:
        positions = self.thread_intervals[
            cursor_offset + 1:] - self.thread_intervals[cursor_offset]
        offset = 1
      if not positions:
        return (-1, -1), 0
      pos = max(positions).begin

    _, start_line, start_col, *_ = self.getLineInfo(pos, pos + 1)
    return (start_line + 1, start_col), offset

  def publishComment(self, thread, count, content):

    def callback():
      self.log.debug(f"Calling {content, thread, count}")
      create_task(
          self.project_handler.sendOps(
              self.document,
              self.content_hash,
              ops=[{
                  "c": content,
                  "p": count,
                  "t": thread
              }]))

    self.nvim.async_call(callback)

  def highlightComment(self, comments, thread):
    thread_id = thread["id"]
    comments = comments.get(thread_id, {})
    resolved = comments.get("resolved", False)
    if resolved or not comments:
      return
    messages = comments["messages"]

    start = thread["op"]["p"]
    end = start + len(thread["op"]["c"])

    char_count, start_line, start_col, end_line, end_col = self.getLineInfo(
        start, end)
    # Apply the highlight
    self.log.debug(f"highlight {start_line} {start_col} {end_line} {end_col}")

    if start == end:
      start -= 1
      end += 1
      start_col = max(start_col - 1, 0)
      end_col = min(
          end_col + 1, char_count + self.cummulativePosition()[end_line] - 1)
      self.log.debug(f"same so {start_line} {start_col} {end_line} {end_col}")

    self.highlightRange(
        self.highlight, 'AirLatexCommentGroup', start_line, start_col, end_line,
        end_col)
    self.thread_intervals[start:end] = thread_id

  async def highlightComments(self, comments, threads=None):
    # Clear any existing highlights
    self.log.debug(f"highlight {self.highlight}")

    def highlight_callback():
      self.buffer.api.clear_namespace(self.highlight, 0, -1)
      self.buffer.api.clear_namespace(self.highlight2, 0, -1)
      self.thread_intervals.clear()
      if threads:
        self.threads = {thread["id"]: thread for thread in threads}
      for thread in self.threads.values():
        self.highlightComment(comments, thread)
      # Apply double highlights. Note we could extend this to the nth case, but
      # 2 seems fine
      overlapping_ranges = set()
      for interval in self.thread_intervals:
        overlaps = self.thread_intervals[interval.begin:interval.end]
        for overlap in overlaps:
          if overlap == interval:
            continue
          overlapping_range = Interval(
              max(interval.begin, overlap.begin),
              min(interval.end, overlap.end))
          overlapping_ranges.add(overlapping_range)
      for overlap in overlapping_ranges:
        _, *lineinfo = self.getLineInfo(overlap.begin, overlap.end)
        self.highlightRange(
            self.highlight2, 'AirLatexDoubleCommentGroup', *lineinfo)

      self.log.debug("done")

    await self.buffer_event.wait()
    self.nvim.async_call(highlight_callback)

  def clearRemoteCursor(self, remote_id):
    if remote_id in self.cursors:
      highlight = self.cursors[remote_id]
      self.buffer.api.clear_namespace(highlight, 0, -1)

  def updateRemoteCursor(self, cursor):
    self.log.debug(f"updateRemoteCursor {cursor}")
    # Don't draw the current cursor
    # Client id if remote, id if local
    if not cursor.get("id") or cursor.get(
        "id") == self.project_handler.session_id:
      return

    def handle_cursor(cursor):
      if cursor["id"] not in self.cursors:
        highlight = self.nvim.api.create_namespace(cursor["id"])
        self.cursors[cursor["id"]] = highlight
      else:
        highlight = self.cursors[cursor["id"]]
        self.buffer.api.clear_namespace(highlight, 0, -1)
      self.log.debug(
          f"highlighting {cursor} 'CursorGroup', {(cursor['row'], cursor['column'], cursor['column'])}"
      )
      if len(self.buffer[cursor["row"]]) == cursor["column"]:
        self.buffer.api.add_highlight(
            highlight, 'CursorGroup', cursor["row"],
            max(cursor["column"] - 1, 0), cursor["column"])
      else:
        self.buffer.api.add_highlight(
            highlight, 'CursorGroup', cursor["row"], cursor["column"],
            cursor["column"] + 1)

    self.nvim.async_call(handle_cursor, cursor)

  def showComments(self, comment_buffer):
    if comment_buffer.drafting:
      return
    if comment_buffer.creation:
      return
    self.buffer.api.clear_namespace(self.pending_selection, 0, -1)
    self.comment_selection = IntervalTree()
    cursor = self.nvim.current.window.cursor
    self.log.debug(f"cursor {cursor}")
    cursor_offset = self.getPosition(cursor[0] - 1, cursor[1])
    threads = self.thread_intervals[cursor_offset]
    if not threads:
      comment_buffer.buffer[:] = []
      return
    self.log.debug(f"found threads {threads}")
    comment_buffer.render(self.project_handler, threads)
    # comment_buffer.render(self.project_handler, threads)
    # messages = self.project_handler.comments[threads.pop().data]["messages"]
    # self.log.debug(f"messages {messages}")

  def cummulativePosition(self):
    # TODO: make a cached linked list that updates with changes
    pos = [0]
    for row in self.buffer[:]:
      pos.append(pos[-1] + len(row) + 1)
    return pos

  def getPosition(self, row, col):
    return self.cummulativePosition()[row] + col

  def getLineInfo(self, start, end):
    char_count, start_line, start_col, end_line, end_col = 0, -1, 0, 0, 0
    for i, line in enumerate(self.buffer[:]):
      line_length = len(line) + 1  # +1 for the newline character
      if char_count + line_length > start and start_line == -1:
        start_line, start_col = i, start - char_count
      if char_count + line_length >= end:
        end_line, end_col = i, end - char_count
        break
      char_count += line_length
    return char_count, start_line, start_col, end_line, end_col

  def writeBuffer(self):
    self.log.debug("writeBuffer: calculating changes to send")

    # update CursorPosition
    create_task(
        self.project_handler.updateCursor(
            self.document, self.nvim.current.window.cursor))

    # skip if not yet initialized
    if self.saved_buffer is None:
      self.log.debug("writeBuffer: -> buffer not yet initialized")
      return

    # nothing to do
    if len(self.saved_buffer) == len(self.buffer):
      skip = True
      for ol, nl in zip(self.saved_buffer, self.buffer):
        if hash(ol) != hash(nl):
          skip = False
          break
      if skip:
        self.log.debug("writeBuffer: -> done (hashtest says nothing to do)")
        return

    # cummulative position of line
    pos = self.cummulativePosition()

    # first calculate diff row-wise
    ops = []
    S = SequenceMatcher(
        None, self.saved_buffer, self.buffer, autojunk=False).get_opcodes()
    for op in S:
      if op[0] == "equal":
        continue

      # inserting a whole row
      elif op[0] == "insert":
        s = "\n".join(self.buffer[op[3]:op[4]])
        if op[1] >= len(self.saved_buffer):
          p = pos[-1] - 1
          s = "\n" + s
        else:
          p = pos[op[1]]
          s = s + "\n"
        ops.append({"p": p, "i": s})

      # deleting a whole row
      elif op[0] == "delete":
        s = "\n".join(self.saved_buffer[op[1]:op[2]])
        if op[1] == len(self.buffer):
          p = pos[-(op[2] - op[1]) - 1] - 1
          s = "\n" + s
        else:
          p = pos[op[1]]
          s = s + "\n"
        ops.append({"p": p, "d": s})

      # for replace, check in more detail what has changed
      elif op[0] == "replace":
        old = "\n".join(self.saved_buffer[op[1]:op[2]])
        new = "\n".join(self.buffer[op[3]:op[4]])
        S2 = SequenceMatcher(None, old, new, autojunk=False).get_opcodes()
        for op2 in S2:
          # relative to document end
          linestart = pos[op[1]]

          if op2[0] == "equal":
            continue

          elif op2[0] == "replace":
            ops.append({"p": linestart + op2[1], "i": new[op2[3]:op2[4]]})
            ops.append({"p": linestart + op2[1], "d": old[op2[1]:op2[2]]})

          elif op2[0] == "insert":
            ops.append({"p": linestart + op2[1], "i": new[op2[3]:op2[4]]})

          elif op2[0] == "delete":
            ops.append({"p": linestart + op2[1], "d": old[op2[1]:op2[2]]})

    # nothing to do
    if len(ops) == 0:
      self.log.debug(
          "writeBuffer: -> done (sequencematcher says nothing to do)")
      return

    # reverse, as last op should be applied first
    ops.reverse()

    # update saved buffer & send command
    self.saved_buffer = self.buffer[:]
    self.log.debug(" -> sending ops")

    track = self.nvim.eval("g:AirLatexTrackChanges") == 1
    create_task(
        self.project_handler.sendOps(
            self.document, self.content_hash, ops, track))

  def applyUpdate(self, packet, comments):
    self.log.debug("apply server updates to buffer")

    # adapt version
    if "v" in packet:
      v = packet["v"]
      if v >= self.document["version"]:
        self.document["version"] = v + 1

    # do nothing if no op included
    if not 'op' in packet:
      return
    ops = packet['op']
    self.log.debug("got ops:" + str(ops))

    # async execution
    def applyOps(self, ops):
      self.buffer_mutex.acquire()
      try:
        for op in ops:
          self.log.debug(f"the op {op} and {'c' in op}")

          # delete char and lines
          if 'd' in op:
            p = op['p']
            s = op['d']
            self._remove(self.saved_buffer, p, s)
            self._remove(self.buffer, p, s)

          # add characters and newlines
          if 'i' in op:
            p = op['p']
            s = op['i']
            self._insert(self.saved_buffer, p, s)
            self._insert(self.buffer, p, s)

          # add comment
          if 'c' in op:
            self.log.debug(f"So wtf")
            thread = {"id": op['t'], "metadata": packet["meta"], "op": op}
            self.threads[op['t']] = thread
            create_task(self.highlightComments(comments))
      except Exception as e:
        self.log.debug(f"{op} failed: {e}")
      finally:
        self.buffer_mutex.release()

    self.nvim.async_call(applyOps, self, ops)

  # inster string at given position
  def _insert(self, buffer, start, string):
    p_linestart = 0

    # find start line
    for line_i, line in enumerate(self.buffer):

      # start is not yet there
      if start >= p_linestart + len(line) + 1:
        p_linestart += len(line) + 1
      else:
        break

    # convert format to array-style
    string = string.split("\n")

    # append end of current line to last line of new line
    string[-1] += line[(start - p_linestart):]

    # include string at start position
    buffer[line_i] = line[:(start - p_linestart)] + string[0]

    # append rest to next line
    if len(string) > 1:
      buffer[line_i + 1:line_i + 1] = string[1:]

  # remove len chars from pos
  def _remove(self, buffer, start, string):
    p_linestart = 0

    # find start line
    for line_i, line in enumerate(buffer):

      # start is not yet there
      if start >= p_linestart + len(line) + 1:
        p_linestart += len(line) + 1
      else:
        break

    # convert format to array-style
    string = string.split("\n")
    new_string = ""

    # remove first line from found position
    new_string = line[:(start - p_linestart)]

    # add rest of last line to new string
    if len(string) == 1:
      new_string += buffer[line_i + len(string) - 1][(start - p_linestart) +
                                                     len(string[-1]):]
    else:
      new_string += buffer[line_i + len(string) - 1][len(string[-1]):]

    # overwrite buffer
    buffer[line_i:line_i + len(string)] = [new_string]
