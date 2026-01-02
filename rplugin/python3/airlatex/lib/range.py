import math


class FenwickTree:

  def __init__(self, size=512):
    self.size = size
    self.tree = [0] * (size + 1)
    self.array = [0] * size
    self.last_index = -1

  def initialize(self, a):
    self.size = max(self.size, 2**int(math.log2(len(a)) + 1))
    self.last_index = len(a) - 1
    self.tree = [0] * (self.size + 1)
    self.array = [0] * self.size
    # TODO fix remove and insert
    for i in range(len(a)):
      self.array[i] = a[i]
      self.tree[i + 1] += a[i]
      j = (i + 1) + ((i + 1) & -(i + 1))
      if j <= len(a):
        self.tree[j] += self.tree[i + 1]

  def update(self, index, diff):
    while index <= self.size:
      self.tree[index] += diff
      index += index & -index

  def get_cumulative_value(self, index):
    sum = 0
    while index > 0:
      sum += self.tree[index]
      index -= index & -index
    return sum

  def append(self, value):
    index = self.last_index + 1
    if index >= self.size:
      self.resize(index * 2)
    diff = value - self.array[index]
    self.array[index] = value
    self.update(index + 1, diff)
    self.last_index = index

  def remove(self, index):
    if index < 0:
      # We don't offset by 1 here, because we want the range to capture
      # include self.last_index
      index = self.last_index + index + 1

    for i in range(index, self.last_index):
      diff = self.array[i + 1] - self.array[i]
      r = i + (i & -i)
      if r < self.size:
        self.tree[r] += diff
      self.tree[i] += diff
      self.array[i] = self.array[i + 1]
    self.array[self.last_index] = 0
    self.last_index -= 1

  def insert(self, index, value):
    if index + 1 >= self.size:
      self.array.insert(index, value)
      return self.resize(index * 2)

    if index < 0:
      index = self.last_index + index + 1
    if index >= self.last_index:
      return self.append(value)

    # Increment last_index first so loop covers all elements
    self.last_index += 1

    # Start with the new value to insert, not the current array value
    previous = value
    for i in range(index, self.last_index):
      diff = previous - self.array[i]
      r = i + (i & -i)
      if r < self.size:
        self.tree[r] += diff
      self.tree[i] += diff
      self.array[i], previous = previous, self.array[i]

    # Place the final shifted element
    if self.last_index < self.size:
      self.array[self.last_index] = previous
      diff = previous
      self.update(self.last_index + 1, diff)

  def resize(self, new_size):
    new_tree = FenwickTree(new_size)
    new_tree.initialize(self.array)
    self.size = new_size
    self.tree = new_tree.tree
    self.array = new_tree.array

  def position(self, row, col):
    return self[row] + col

  def search(self, v):
    # Use same simple search as NaiveAccumulator to ensure matching behavior
    # TODO: Implement proper Fenwick tree binary search optimization
    t = 0
    for i in range(self.last_index + 1):
      if t + self.array[i] >= v:
        return i, v - t
      t += self.array[i]
    return self.last_index, 0

  def __getitem__(self, index):
    if index == -1:
      index = self.last_index
    return self.get_cumulative_value(index + 1)

  def __setitem__(self, index, value):
    if index == -1:
      index = self.last_index
    diff = value - self.array[index]
    self.array[index] = value
    self.update(index + 1, diff)

  def __delitem__(self, index):
    if index == -1:
      index = self.last_index
    self.remove(index)


class NaiveAccumulator:

  def __init__(self, base=None):
    self.array = [0]
    self.last_index = 0
    if base:
      self.initialize(base)

  def initialize(self, array):
    self.array = [0]
    self.last_index = 0
    for i, a in enumerate(array):
      self.insert(i, a)

  def insert(self, index, value):
    self.array.insert(index, value)
    self.last_index += 1

  def get_cumulative_value(self, index):
    if index < 0:
      index = len(self.array) + index
    return sum(self.array[:min(index, self.last_index + 1)])

  def remove(self, index):
    if index < 0:
      index = len(self.array) + index
    self.array[index] = 0
    del self.array[index]
    self.last_index -= 1

  def search(self, v):
    t = 0
    for i, c in enumerate(self.array):
      if t + c >= v:
        return i, v - t
      t += c
    return self.last_index, 0

  def position(self, row, col):
    return self[row] + col

  def update(self, index, diff):
    if index > self.last_index:
      self.array.append(diff)
      self.last_index += 1
    else:
      self.array[index] += diff

  def __getitem__(self, index):
    return self.get_cumulative_value(index)

  def __setitem__(self, index, value):
    if index > self.last_index:
      self.array.append(value)
      self.last_index += 1
    else:
      self.array[index] = value

  def __delitem__(self, index):
    self.remove(index)

  @property
  def arr(self):
    return self.array[:self.last_index + 1]
