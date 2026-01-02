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
      index = self.last_index + index + 1

    # Use simple array remove to ensure correctness, then rebuild tree
    # TODO: Implement proper Fenwick tree remove for better performance
    temp_array = self.array[:self.last_index + 1]
    del temp_array[index]

    # Rebuild the tree with new array
    self.initialize(temp_array)

  def insert(self, index, value):
    if index < 0:
      index = self.last_index + index + 1
    if index > self.last_index:
      return self.append(value)

    # Check if we need to resize
    if self.last_index + 1 >= self.size - 1:
      self.resize(self.size * 2)

    # Shift elements to the right and update tree
    # We need to shift from the end backwards to avoid overwriting
    for i in range(self.last_index, index - 1, -1):
      # Move element from i to i+1
      old_val = self.array[i]
      new_pos = i + 1

      # Update array
      self.array[new_pos] = old_val

      # Update tree: remove old_val from position i, add it to position i+1
      if i <= self.last_index:
        # Remove from old position
        self.update(i + 1, -old_val)
        # Add to new position
        self.update(new_pos + 1, old_val)

    # Insert the new value at the specified index
    self.array[index] = value
    self.update(index + 1, value)

    # Increment last_index
    self.last_index += 1

  def resize(self, new_size):
    new_tree = FenwickTree(new_size)
    new_tree.initialize(self.array)
    self.size = new_size
    self.tree = new_tree.tree
    self.array = new_tree.array

  def position(self, row, col):
    return self[row] + col

  def search(self, v):
    # Binary search using Fenwick tree for O(log n) performance
    # Handle edge cases
    if self.last_index < 0:
      return 0, 0

    total = self.get_cumulative_value(self.last_index + 1)
    if v > total:
      return self.last_index, 0

    # Binary search to find the index where cumulative sum >= v
    left, right = 0, self.last_index

    while left < right:
      mid = (left + right) // 2
      cumulative = self.get_cumulative_value(mid + 1)

      if cumulative < v:
        left = mid + 1
      else:
        right = mid

    # left is now the index where cumulative sum >= v
    prev_cumulative = self.get_cumulative_value(left) if left > 0 else 0
    return left, v - prev_cumulative

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
