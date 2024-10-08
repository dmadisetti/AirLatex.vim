"""task.py
Async in vim is an interesting this. Since we are constantly polling the
ShareLatex/ OverLeaf servers, of course we want to have an async thread (or
threads). But you interact with vim, we have to provide a callback to
nvim.async_call (which puts us back on the thread to make vim changes). Having 2
forms of async is not good, and asyncio kinda sucks, so this tries to normalize
all of that.
"""
import inspect
from asyncio import create_task, Queue
import functools
import inspect
import traceback


# For ambiguous number of parameters / response
def _call(fn, result, args=None):
  result = _args(result, args)
  if result is None:
    return fn()
  elif isinstance(result, tuple):
    return fn(*result)
  return fn(result)


# For respnse values, and provided args
def _args(result, args):
  if args is not None and args != ():
    return args
  if result == True:
    return ()
  return result


async def _untangle(callback):
  while (inspect.iscoroutine(callback) or
         inspect.iscoroutinefunction(callback)):
    if not inspect.iscoroutine(callback):
      callback = callback()
    callback = await callback
  return callback


class _VimDecorator:

  def __init__(self, fn, *args):
    self.fn = fn
    self.args = args

  def __call__(self, *args, **kwargs):
    return self.fn(*args, **kwargs)

  def _build_async_call(self, channel):
    raise Exception()


class AsyncDecorator(_VimDecorator):
  nvim = None

  def __init__(self, fn, *args):
    self.fn = fn
    self.args = args
    # self.registered = {}

  def _build_async_call(self, channel):

    async def callback(*args):

      def hook():
        create_task(channel.put(_call(self, args, self.args)))

      self.nvim.async_call(hook)

    return callback

  def __get__(self, instance, cls):
    """Required to support class instances"""
    # Some type of static or meta call is goint on.
    # NOTE: Use objects with derived classes as singletons
    # Weird things will happen otherwise!
    if not instance:
      return cls.__bases__[0].__get__(None, None, cls)
    return AsyncDecorator(functools.partial(self.fn, instance), *self.args)


class _ChainHelper(_VimDecorator):
  """One 'then' feeding into another, requires use to cross channels"""

  def __init__(self, fn, channel, *args):
    self.fn = fn
    self.source = channel
    self.args = args

  def _build_async_call(self, sink):

    async def callback():
      args = await self.source.get()

      def hook():
        create_task(sink.put(_call(self, args, self.args)))

      AsyncDecorator.nvim.async_call(hook)

    return callback


class Task():

  def __init__(self, fn, *args, vim=False):
    self.channel = Queue()
    self.is_vim = isinstance(fn, _VimDecorator)
    if not self.is_vim and vim:
      fn = AsyncDecorator(fn, *args)
      self.is_vim = True
    if self.is_vim:
      fn = fn._build_async_call(self.channel)
    if not inspect.iscoroutine(fn):
      fn = fn(*args)
    # self.task = create_task(fn)
    self.task = create_task(self._logWrapper(fn))

  def _logWrapper(self, awaitable):
    trace = traceback.format_stack()

    async def wrap():
      try:
        return await awaitable
      except Exception as e:
        raise Exception(str(e) + "|" + "".join(trace)[:-1]) from e

    return wrap()

  @staticmethod
  def Fn(*args, vim=False):

    def decorator(fn):
      return Task(fn, *args, vim=vim)

    return decorator

  def fn(self, *args, vim=False):

    def decorator(fn):
      return self.then(fn, *args, vim=vim)

    return decorator

  def _build_enqueue(self, *args):

    def enqueue(future):
      result = future.result()
      task = self.channel.put(_args(result, args))
      # create_task(task)
      create_task(self._logWrapper(task))
      # create_task(task)

    return enqueue

  def _build_callback(self, fn):

    async def callback():
      result = await self._logWrapper(self.channel.get())
      return await _call(fn, result)

    return callback

  def cancel(self):
    return self.task.cancel()

  def then(self, fn, *args, vim=False):
    # Need to specially handle income vim cases to make sure async is invoked.
    # the double async makes things tricker
    if isinstance(fn, AsyncDecorator) or vim:
      callback = _ChainHelper(fn, self.channel, *args)
    else:
      callback = self._build_callback(fn)

    # We are already populating the channels for the vim case.
    # So only need to handle the default case.
    if not self.is_vim:
      self.task.add_done_callback(self._build_enqueue(*args))

    return Task(callback)

  @property
  def next(self):
    # Syntaxic sugar for resolving a returned future.
    async def wait(callback):
      response = await self._logWrapper(_untangle(callback))
      return response

    return self.then(wait)
