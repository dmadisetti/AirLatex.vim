from intervaltree import Interval, IntervalTree

from logging import getLogger

class Range():

  def __init__(self):
    self.threads = IntervalTree()

  def create(self, text, comments, thread):
    "abstract"

  def applyOp(self, op, packet):
    "abstract"

  def clear(self):
    self.threads.clear()

  def get(self, text, start_line, start_col, end_line, end_col):
    start = text.lines.position(start_line, start_col)
    end = text.lines.position(end_line, end_col)
    return [r.data for r in self.threads[start:end]]

  def getNextPosition(self, offset):
    positions = self.threads[offset + 1:] - self.threads[offset]
    count = len(self.threads[:]) - len(positions) + 1
    if not positions:
      positions = self.threads[:offset] - self.threads[offset]
      count = 1
    if not positions:
      return (-1, -1), 0
    return min(positions).begin, count

  def getPrevPosition(self, offset):
    positions = self.threads[:offset] - self.threads[offset]
    count = len(positions)
    if not positions:
      positions = self.threads[offset + 1:] - self.threads[offset]
      count = 1
    if not positions:
      return (-1, -1), 0
    return max(positions).begin, count

  def _remove(self, start, end):
    overlap = set({})
    delta = end - start
    for interval in self.threads[start:end + 1]:
      self.threads.remove(interval)
      begin = interval.begin + min(start - interval.begin, 0)
      # end = (interval.end -
      #        min(end, interval.end) +
      #        max(start, interval.begin) +
      #        min(start - interval.begin, 0))
      if end >= interval.end:
        stop = start
      else:
        stop = interval.end - delta
      if begin >= stop:
        stop = begin + 1
      interval = Interval(begin, stop, interval.data)
      overlap.add(interval)
    for interval in self.threads[end + 1:]:
      self.threads.remove(interval)
      self.threads.add(Interval(interval.begin - delta,
                                interval.end - delta,
                                interval.data))
    for o in overlap:
      self.threads.add(o)

  def _insert(self, start, end):
    overlap = set({})
    delta = end - start
    for interval in self.threads[start]:
        self.threads.remove(interval)
        end = interval.end + delta
        interval = Interval(interval.begin, end, interval.data)
        overlap.add(interval)
    for interval in self.threads[start + 1:]:
        self.threads.remove(interval)
        self.threads.add(Interval(interval.begin + delta, interval.end + delta, interval.data))

    for o in overlap:
      self.threads.add(o)


class Threads(Range):

  def __init__(self):
    self.threads = IntervalTree()
    self.data = {}
    self.selection = IntervalTree()
    self.active = True

  def create(self, text, comments, thread):
    if not comments:
      return False, ()
    thread_id = thread.get("id")
    comments = comments.get(thread_id, {})
    resolved = comments.get("resolved", False)
    if resolved or not comments:
      return False, ()

    start = thread["op"]["p"]
    end = start + len(thread["op"]["c"])
    start_line, start_col, end_line, end_col = text.query(start, end)

    if start == end:
      start -= 1
      end += 1
      start_col = max(start_col - 1, 0)
      end_col = min(
          end_col + 1, text.lines[end_line] - text.lines[end_line - 1] - 1)
    self.threads[start:end] = thread_id
    return True, (start_line, start_col, end_line, end_col)

  def applyOp(self, op, packet):

    # delete char and lines
    if 'd' in op:
      p = op['p']
      s = op['d']
      self._remove(p, p + len(s))

    # add characters and newlines
    if 'i' in op:
      p = op['p']
      s = op['i']
      self._insert(p, p + len(s))

    # add comment
    if 'c' in op:
      thread = {"id": op['t'], "metadata": packet["meta"], "op": op}
      self.data[op['t']] = thread

  # Should check
  def activate(self, text, cursor):
    cursor_offset = text.lines.position(cursor[0] - 1, cursor[1])
    threads = self.threads[cursor_offset]
    self.active = bool(threads)
    return threads

  # Mark comment
  def select(self, text, start_line, start_col, end_line, end_col):
    self.selection = IntervalTree()
    self.selection.add(
        Interval(
            text.lines.position(start_line, start_col),
            text.lines.position(end_line, end_col)))

  @property
  def doubled(self):
    overlapping_ranges = set()
    for interval in self.threads:
      overlaps = self.threads[interval.begin:interval.end]
      for overlap in overlaps:
        if overlap == interval:
          continue
        overlapping_range = Interval(
            max(interval.begin, overlap.begin), min(interval.end, overlap.end))
        # Redundant adds don't matter since set
        overlapping_ranges.add(overlapping_range)
    return overlapping_ranges

class Changes(Range):

  def __init__(self):
    self.selection = IntervalTree()
    self.threads = IntervalTree()
    self.data = {}
    self.lookup = {}
    self.active = True

  def create(self, text, changes):
    if not changes:
      return False, ()

    change_id = changes.get("id")
    start = changes["op"]["p"]
    # Implicilty handle deletions. If deletion, 'i' will not be set
    delta = len(changes["op"].get("i",""))
    insertion = delta == 0
    end = start + delta
    start_line, start_col, end_line, end_col = text.query(start, end)

    if start == end:
      start -= 1
      end += 1
      start_col = max(start_col - 1, 0)
      end_col = min(
          end_col + 1, text.lines[end_line] - text.lines[end_line - 1] - 1)
    self.threads[start:end] = (insertion, change_id)
    self.lookup[change_id] = Interval(start, end, (insertion, change_id))
    self.threads.add(self.lookup[change_id])
    return True, insertion, (start_line, start_col, end_line, end_col)

  def applyOp(self, op, packet):

    start = end = 0
    insertion = False

    # delete char and lines
    if 'd' in op:
      start = op['p']
      end = start + 1
      self._remove(start, start + len(op['d']))

    # add characters and newlines
    if 'i' in op:
      start = op['p']
      end = start + len(op['i'])
      self._insert(start, start + end)
      insertion = True

    tc = packet.get("meta", {}).get("tc")
    if not tc or end == 0:
      return

    # tc rejections are marked as undos
    if op.get('u'):
      if tc in self.lookup:
        self.threads.remove(interval)
        del self.lookup[tc]
      return

    self.lookup[tc] = Interval(start, end, (insertion, tc))
    self.threads.add(self.lookup[tc])
