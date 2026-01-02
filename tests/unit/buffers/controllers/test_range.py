import pytest
from unittest.mock import Mock, MagicMock
from intervaltree import Interval, IntervalTree
from rplugin.python3.airlatex.buffers.controllers.range import Range, Threads, Changes


class MockText:
    def __init__(self):
        self.lines = Mock()
        self.lines.position = Mock(side_effect=lambda row, col: row * 100 + col)

    def query(self, start, end):
        start_line = start // 100
        start_col = start % 100
        end_line = end // 100
        end_col = end % 100
        return start_line, start_col, end_line, end_col


class ConcreteRange(Range):
    def create(self, text, comments, thread):
        pass

    def applyOp(self, op, packet):
        pass


class TestRange:

    def test_initialization(self):
        range_obj = ConcreteRange()
        assert isinstance(range_obj.range, IntervalTree)

    def test_clear(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(0, 10, "data"))
        assert len(range_obj.range) == 1

        range_obj.clear()
        assert len(range_obj.range) == 0

    def test_get_empty_range(self):
        range_obj = ConcreteRange()
        text = MockText()

        result = range_obj.get(text, 0, 0, 1, 0)
        assert result == []

    def test_get_with_intervals(self):
        range_obj = ConcreteRange()
        text = MockText()

        range_obj.range.add(Interval(0, 50, "data1"))
        range_obj.range.add(Interval(50, 100, "data2"))

        result = range_obj.get(text, 0, 0, 1, 0)
        assert len(result) > 0

    def test_get_next_position_empty(self):
        range_obj = ConcreteRange()
        position, count = range_obj.getNextPosition(0)
        assert position == (-1, -1)
        assert count == 0

    def test_get_next_position_with_intervals(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data1"))
        range_obj.range.add(Interval(30, 40, "data2"))

        position, count = range_obj.getNextPosition(0)
        assert position >= 0
        assert count >= 1

    def test_get_next_position_at_end(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data"))

        position, count = range_obj.getNextPosition(25)
        assert count >= 0

    def test_get_prev_position_empty(self):
        range_obj = ConcreteRange()
        position, count = range_obj.getPrevPosition(100)
        assert position == (-1, -1)
        assert count == 0

    def test_get_prev_position_with_intervals(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data1"))
        range_obj.range.add(Interval(30, 40, "data2"))

        position, count = range_obj.getPrevPosition(50)
        assert position >= 0
        assert count >= 1

    def test_get_prev_position_at_beginning(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data"))

        position, count = range_obj.getPrevPosition(5)
        assert count >= 0

    def test_doubled_no_overlaps(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(0, 10, "data1"))
        range_obj.range.add(Interval(20, 30, "data2"))

        overlaps = range_obj.doubled
        assert len(overlaps) == 0

    def test_doubled_with_overlaps(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(0, 20, "data1"))
        range_obj.range.add(Interval(10, 30, "data2"))

        overlaps = range_obj.doubled
        assert len(overlaps) > 0

    def test_doubled_complete_overlap(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(0, 30, "data1"))
        range_obj.range.add(Interval(10, 20, "data2"))

        overlaps = range_obj.doubled
        assert len(overlaps) > 0

    def test_remove_simple(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 30, "data"))

        range_obj._remove(15, 20)

        assert len(range_obj.range) > 0

    def test_remove_complete(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data"))

        range_obj._remove(0, 30)

        intervals = list(range_obj.range)
        assert len(intervals) > 0

    def test_remove_shifts_later_intervals(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(50, 60, "data"))

        range_obj._remove(10, 20)

        intervals = list(range_obj.range)
        assert len(intervals) == 1
        assert intervals[0].begin == 40
        assert intervals[0].end == 50

    def test_insert_simple(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data"))

        range_obj._insert(15, 25)

        intervals = list(range_obj.range)
        assert len(intervals) > 0

    def test_insert_extends_overlapping_interval(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(10, 20, "data"))

        range_obj._insert(10, 20)

        intervals = list(range_obj.range)
        assert len(intervals) > 0
        assert intervals[0].end == 30

    def test_insert_shifts_later_intervals(self):
        range_obj = ConcreteRange()
        range_obj.range.add(Interval(50, 60, "data"))

        range_obj._insert(10, 20)

        intervals = list(range_obj.range)
        assert len(intervals) == 1
        assert intervals[0].begin == 60
        assert intervals[0].end == 70


class TestThreads:

    def test_initialization(self):
        threads = Threads()
        assert isinstance(threads.range, IntervalTree)
        assert threads.data == {}
        assert isinstance(threads.selection, IntervalTree)
        assert threads.active is True

    def test_create_no_comments(self):
        threads = Threads()
        text = MockText()

        result, coords = threads.create(text, None, {})
        assert result is False
        assert coords == ()

    def test_create_resolved_thread(self):
        threads = Threads()
        text = MockText()
        text.query = Mock(return_value=(0, 0, 0, 5))

        comments = {"thread1": {"resolved": True}}
        thread = {"id": "thread1", "op": {"p": 0, "c": "hello"}}

        result, coords = threads.create(text, comments, thread)
        assert result is False

    def test_create_valid_thread(self):
        threads = Threads()
        text = MockText()
        text.query = Mock(return_value=(0, 0, 0, 5))

        comments = {"thread1": {"resolved": False}}
        thread = {"id": "thread1", "op": {"p": 0, "c": "hello"}}

        result, coords = threads.create(text, comments, thread)
        assert result is True
        assert len(coords) == 4

    def test_create_empty_comment(self):
        threads = Threads()
        text = MockText()
        text.lines.__getitem__ = Mock(return_value=100)

        comments = {"thread1": {"resolved": False}}
        thread = {"id": "thread1", "op": {"p": 10, "c": ""}}

        result, coords = threads.create(text, comments, thread)
        assert result is True

    def test_apply_op_delete(self):
        threads = Threads()
        op = {"p": 10, "d": "hello"}
        packet = {}

        threads.applyOp(op, packet)

    def test_apply_op_insert(self):
        threads = Threads()
        op = {"p": 10, "i": "hello"}
        packet = {}

        threads.applyOp(op, packet)

    def test_apply_op_comment(self):
        threads = Threads()
        op = {"c": "comment text", "t": "thread1", "p": 0}
        packet = {"meta": {"user": "testuser"}}

        threads.applyOp(op, packet)

        assert "thread1" in threads.data
        assert threads.data["thread1"]["id"] == "thread1"

    def test_apply_op_combined(self):
        threads = Threads()
        op = {"p": 10, "i": "hello", "c": "comment", "t": "thread1"}
        packet = {"meta": {}}

        threads.applyOp(op, packet)

        assert "thread1" in threads.data

    def test_activate_with_threads(self):
        threads = Threads()
        text = MockText()
        threads.range.add(Interval(50, 100, "thread1"))

        cursor = (0, 50)
        result = threads.activate(text, cursor)

        assert threads.active is True
        assert len(result) > 0

    def test_activate_without_threads(self):
        threads = Threads()
        text = MockText()

        cursor = (0, 50)
        result = threads.activate(text, cursor)

        assert threads.active is False
        assert len(result) == 0

    def test_select(self):
        threads = Threads()
        text = MockText()

        threads.select(text, 0, 0, 1, 10)

        assert len(threads.selection) == 1
        interval = list(threads.selection)[0]
        assert interval.begin == 0
        assert interval.end == 110

    def test_select_replaces_previous(self):
        threads = Threads()
        text = MockText()

        threads.select(text, 0, 0, 1, 10)
        assert len(threads.selection) == 1

        threads.select(text, 2, 0, 3, 10)
        assert len(threads.selection) == 1


class TestChanges:

    def test_initialization(self):
        changes = Changes()
        assert isinstance(changes.range, IntervalTree)
        assert isinstance(changes.selection, IntervalTree)
        assert changes.data == {}
        assert changes.lookup == {}
        assert changes.active is True

    def test_create_no_changes(self):
        changes = Changes()
        text = MockText()

        result, coords = changes.create(text, None)
        assert result is False
        assert coords == ()

    def test_create_valid_insertion(self):
        changes = Changes()
        text = MockText()
        text.query = Mock(return_value=(0, 0, 0, 5))

        change = {"id": "change1", "op": {"p": 0, "i": "hello"}}

        result, insertion, coords = changes.create(text, change)
        assert result is True
        assert insertion is False
        assert len(coords) == 4

    def test_create_valid_deletion(self):
        changes = Changes()
        text = MockText()
        text.lines.__getitem__ = Mock(return_value=100)

        change = {"id": "change1", "op": {"p": 10}}

        result, insertion, coords = changes.create(text, change)
        assert result is True
        assert insertion is True

    def test_create_adds_to_lookup(self):
        changes = Changes()
        text = MockText()
        text.query = Mock(return_value=(0, 0, 0, 5))

        change = {"id": "change1", "op": {"p": 0, "i": "hello"}}

        changes.create(text, change)
        assert "change1" in changes.lookup

    def test_apply_op_delete(self):
        changes = Changes()
        op = {"p": 10, "d": "hello"}
        packet = {}

        changes.applyOp(op, packet)

    def test_apply_op_insert(self):
        changes = Changes()
        op = {"p": 10, "i": "hello"}
        packet = {"meta": {"tc": "tc1"}}

        changes.applyOp(op, packet)

        assert "tc1" in changes.lookup

    def test_apply_op_undo(self):
        changes = Changes()
        changes.lookup["tc1"] = Interval(10, 20, (True, "tc1"))
        changes.range.add(changes.lookup["tc1"])

        op = {"p": 10, "i": "hello", "u": True}
        packet = {"meta": {"tc": "tc1"}}

        changes.applyOp(op, packet)

    def test_apply_op_no_tc(self):
        changes = Changes()
        op = {"p": 10, "i": "hello"}
        packet = {"meta": {}}

        changes.applyOp(op, packet)

        assert len(changes.lookup) == 0

    def test_apply_op_insert_updates_lookup(self):
        changes = Changes()
        op = {"p": 10, "i": "world"}
        packet = {"meta": {"tc": "tc2"}}

        changes.applyOp(op, packet)

        assert "tc2" in changes.lookup
        interval = changes.lookup["tc2"]
        assert interval.begin == 10
        assert interval.end == 15

    def test_apply_op_delete_no_tc(self):
        changes = Changes()
        op = {"p": 10, "d": "hello"}
        packet = {}

        changes.applyOp(op, packet)

        assert len(changes.lookup) == 0


class TestRangeIntegration:

    def test_threads_workflow(self):
        threads = Threads()
        text = MockText()
        text.query = Mock(return_value=(0, 0, 0, 5))

        comments = {"thread1": {"resolved": False}}
        thread = {"id": "thread1", "op": {"p": 0, "c": "hello"}}

        created, coords = threads.create(text, comments, thread)
        assert created

        op = {"c": "reply", "t": "thread1", "p": 0}
        packet = {"meta": {"user": "user1"}}
        threads.applyOp(op, packet)

        assert "thread1" in threads.data

    def test_changes_workflow(self):
        changes = Changes()
        text = MockText()
        text.query = Mock(return_value=(0, 0, 0, 5))

        change = {"id": "change1", "op": {"p": 0, "i": "hello"}}
        created, insertion, coords = changes.create(text, change)
        assert created

        op = {"p": 5, "i": " world"}
        packet = {"meta": {"tc": "tc1"}}
        changes.applyOp(op, packet)

        assert "tc1" in changes.lookup

    def test_multiple_operations_on_threads(self):
        threads = Threads()

        op1 = {"p": 0, "i": "hello"}
        threads.applyOp(op1, {})

        op2 = {"p": 5, "i": " world"}
        threads.applyOp(op2, {})

        op3 = {"c": "comment", "t": "thread1", "p": 0}
        threads.applyOp(op3, {"meta": {}})

        assert "thread1" in threads.data

    def test_multiple_operations_on_changes(self):
        changes = Changes()

        op1 = {"p": 0, "i": "hello"}
        packet1 = {"meta": {"tc": "tc1"}}
        changes.applyOp(op1, packet1)

        op2 = {"p": 5, "i": " world"}
        packet2 = {"meta": {"tc": "tc2"}}
        changes.applyOp(op2, packet2)

        assert "tc1" in changes.lookup
        assert "tc2" in changes.lookup
