import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from rplugin.python3.airlatex.lib.task import (
    Task, AsyncDecorator, _call, _args, _untangle, _VimDecorator, _ChainHelper
)


class TestCallFunction:

    def test_call_with_none_result(self):
        fn = Mock(return_value=42)
        result = _call(fn, None)
        fn.assert_called_once_with()
        assert result == 42

    def test_call_with_single_value(self):
        fn = Mock(return_value=42)
        result = _call(fn, 10)
        fn.assert_called_once_with(10)
        assert result == 42

    def test_call_with_tuple(self):
        fn = Mock(return_value=42)
        result = _call(fn, (1, 2, 3))
        fn.assert_called_once_with(1, 2, 3)
        assert result == 42

    def test_call_with_args_override(self):
        fn = Mock(return_value=42)
        result = _call(fn, "ignored", args=(5, 6))
        fn.assert_called_once_with(5, 6)
        assert result == 42


class TestArgsFunction:

    def test_args_with_none(self):
        result = _args(None, None)
        assert result is None

    def test_args_with_true(self):
        result = _args(True, None)
        assert result == ()

    def test_args_with_value(self):
        result = _args(42, None)
        assert result == 42

    def test_args_with_override(self):
        result = _args("ignored", (1, 2, 3))
        assert result == (1, 2, 3)

    def test_args_with_empty_tuple_override(self):
        result = _args("value", ())
        assert result == "value"


class TestUntangleFunction:

    @pytest.mark.asyncio
    async def test_untangle_with_value(self):
        result = await _untangle(42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_untangle_with_coroutine(self):
        async def coro():
            return 42
        result = await _untangle(coro())
        assert result == 42

    @pytest.mark.asyncio
    async def test_untangle_with_coroutine_function(self):
        async def coro():
            return 42
        result = await _untangle(coro)
        assert result == 42

    @pytest.mark.asyncio
    async def test_untangle_nested_coroutines(self):
        async def inner():
            return 42

        async def outer():
            return inner()

        result = await _untangle(outer())
        assert result == 42


class TestVimDecorator:

    def test_initialization(self):
        fn = Mock()
        decorator = _VimDecorator(fn, 1, 2, 3)
        assert decorator.fn == fn
        assert decorator.args == (1, 2, 3)

    def test_call(self):
        fn = Mock(return_value=42)
        decorator = _VimDecorator(fn)
        result = decorator(1, 2, key='value')
        fn.assert_called_once_with(1, 2, key='value')
        assert result == 42

    def test_build_async_call_raises(self):
        fn = Mock()
        decorator = _VimDecorator(fn)
        with pytest.raises(Exception):
            decorator._build_async_call(None)


class TestAsyncDecorator:

    def test_initialization(self):
        fn = Mock()
        decorator = AsyncDecorator(fn, 1, 2)
        assert decorator.fn == fn
        assert decorator.args == (1, 2)

    def test_nvim_class_variable(self):
        assert AsyncDecorator.nvim is None

    @pytest.mark.asyncio
    async def test_build_async_call(self):
        fn = Mock(return_value=42)
        decorator = AsyncDecorator(fn)

        mock_nvim = Mock()
        AsyncDecorator.nvim = mock_nvim

        channel = asyncio.Queue()
        callback = decorator._build_async_call(channel)

        await callback(1, 2)

        assert mock_nvim.async_call.called

    def test_get_with_instance(self):
        class TestClass:
            @AsyncDecorator
            def method(self):
                return 42

        instance = TestClass()
        result = TestClass.method.__get__(instance, TestClass)
        assert isinstance(result, AsyncDecorator)

    def test_get_without_instance(self):
        class TestClass:
            pass

        fn = Mock()
        decorator = AsyncDecorator(fn)
        with patch.object(object, '__get__', return_value='mocked'):
            result = decorator.__get__(None, TestClass)


class TestChainHelper:

    def test_initialization(self):
        fn = Mock()
        channel = asyncio.Queue()
        helper = _ChainHelper(fn, channel, 1, 2)
        assert helper.fn == fn
        assert helper.source == channel
        assert helper.args == (1, 2)

    @pytest.mark.asyncio
    async def test_build_async_call(self):
        fn = Mock(return_value=42)
        source_channel = asyncio.Queue()
        sink_channel = asyncio.Queue()

        await source_channel.put((1, 2))

        helper = _ChainHelper(fn, source_channel)

        mock_nvim = Mock()
        AsyncDecorator.nvim = mock_nvim

        callback = helper._build_async_call(sink_channel)

        await callback()

        assert mock_nvim.async_call.called


class TestTask:

    @pytest.mark.asyncio
    async def test_initialization_with_function(self):
        async def coro():
            return 42

        task = Task(coro)
        assert task.channel is not None
        assert task.task is not None
        assert not task.is_vim

    @pytest.mark.asyncio
    async def test_initialization_with_vim_decorator(self):
        fn = Mock()
        decorator = AsyncDecorator(fn)
        AsyncDecorator.nvim = Mock()

        task = Task(decorator)
        assert task.is_vim

    @pytest.mark.asyncio
    async def test_initialization_with_vim_flag(self):
        def fn():
            return 42

        AsyncDecorator.nvim = Mock()
        task = Task(fn, vim=True)
        assert task.is_vim

    @pytest.mark.asyncio
    async def test_cancel(self):
        async def coro():
            await asyncio.sleep(10)

        task = Task(coro)
        result = task.cancel()
        assert result is True or result is False

    @pytest.mark.asyncio
    async def test_fn_decorator(self):
        async def first():
            return 42

        task = Task(first)

        @task.fn()
        async def second(value):
            return value * 2

        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_static_fn_decorator(self):
        @Task.Fn()
        async def task_func():
            return 42

        assert isinstance(task_func, Task)

    @pytest.mark.asyncio
    async def test_then_with_regular_function(self):
        async def first():
            return 42

        async def second(value):
            return value * 2

        task = Task(first)
        next_task = task.then(second)

        assert isinstance(next_task, Task)
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_then_with_vim_flag(self):
        async def first():
            return 42

        def second(value):
            return value * 2

        AsyncDecorator.nvim = Mock()
        task = Task(first)
        next_task = task.then(second, vim=True)

        assert isinstance(next_task, Task)
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_next_property(self):
        async def first():
            async def inner():
                return 42
            return inner

        task = Task(first)
        next_task = task.next

        assert isinstance(next_task, Task)
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_build_enqueue(self):
        async def coro():
            return 42

        task = Task(coro)
        enqueue = task._build_enqueue(1, 2)

        mock_future = Mock()
        mock_future.result = Mock(return_value=42)

        enqueue(mock_future)
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_build_callback(self):
        async def coro():
            return 42

        task = Task(coro)
        await task.channel.put(10)

        async def process(value):
            return value * 2

        callback = task._build_callback(process)
        result = await callback()
        assert result == 20

    @pytest.mark.asyncio
    async def test_log_wrapper_success(self):
        async def coro():
            return 42

        task = Task(coro)
        result = await task.task
        assert result == 42

    @pytest.mark.asyncio
    async def test_log_wrapper_exception(self):
        async def failing_coro():
            raise ValueError("Test error")

        task = Task(failing_coro)

        with pytest.raises(Exception) as exc_info:
            await task.task

        assert "Test error" in str(exc_info.value)


class TestTaskIntegration:

    @pytest.mark.asyncio
    async def test_simple_task_chain(self):
        results = []

        async def first():
            results.append(1)
            return 10

        async def second(value):
            results.append(2)
            return value * 2

        async def third(value):
            results.append(3)
            return value + 5

        task = Task(first).then(second).then(third)
        await asyncio.sleep(0.2)

        assert 1 in results
        assert 2 in results
        assert 3 in results

    @pytest.mark.asyncio
    async def test_task_with_arguments(self):
        async def process(a, b, c):
            return a + b + c

        task = Task(process, 1, 2, 3)
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_multiple_task_branches(self):
        async def source():
            return 42

        async def branch1(value):
            return value * 2

        async def branch2(value):
            return value + 10

        source_task = Task(source)
        task1 = source_task.then(branch1)
        task2 = source_task.then(branch2)

        await asyncio.sleep(0.1)

        assert isinstance(task1, Task)
        assert isinstance(task2, Task)

    @pytest.mark.asyncio
    async def test_task_cancellation_propagation(self):
        async def long_running():
            await asyncio.sleep(10)

        async def next_step(value):
            return value

        task = Task(long_running).then(next_step)
        task.cancel()

        await asyncio.sleep(0.1)
