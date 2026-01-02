import pytest
from rplugin.python3.airlatex.buffers.controllers.text import Text


class TestText:

    def test_initialization(self):
        text = Text()
        assert text.previous == []
        assert text.lines is not None

    def test_content_hash_empty(self):
        text = Text()
        hash_value = text.content_hash
        assert isinstance(hash_value, str)
        assert len(hash_value) == 40

    def test_content_hash_with_content(self):
        text = Text()
        buffer = ["line1", "line2", "line3"]
        text.write(buffer, buffer[:])
        hash_value = text.content_hash
        assert isinstance(hash_value, str)
        assert len(hash_value) == 40

    def test_content_hash_consistency(self):
        text = Text()
        buffer = ["line1", "line2"]
        text.write(buffer, buffer[:])
        hash1 = text.content_hash
        hash2 = text.content_hash
        assert hash1 == hash2

    def test_content_hash_changes_with_content(self):
        text = Text()
        buffer = ["line1"]
        text.write(buffer, buffer[:])
        hash1 = text.content_hash

        buffer = ["line2"]
        text.write(buffer, buffer[:])
        hash2 = text.content_hash

        assert hash1 != hash2

    def test_query(self):
        text = Text()
        buffer = ["hello world", "foo bar"]
        text.write(buffer, buffer[:])

        start_line, start_col, end_line, end_col = text.query(0, 5)
        assert start_line >= 0
        assert start_col >= 0
        assert end_line >= 0
        assert end_col >= 0

    def test_query_across_lines(self):
        text = Text()
        buffer = ["hello", "world"]
        text.write(buffer, buffer[:])

        # query() returns 0-based line numbers
        start_line, start_col, end_line, end_col = text.query(0, 12)
        assert start_line == 0
        assert end_line == 2

    def test_update_buffer(self):
        text = Text()
        buffer = ["line1", "line2"]
        text.updateBuffer(buffer)
        assert text.previous == ["line1", "line2"]

    def test_write_empty_buffer(self):
        text = Text()
        buffer = []
        text.write(buffer, [])
        assert buffer == []
        assert text.previous == []

    def test_write_single_line(self):
        text = Text()
        buffer = []
        lines = ["hello world"]
        text.write(buffer, lines)
        assert buffer == ["hello world"]
        assert text.previous == ["hello world"]

    def test_write_multiple_lines(self):
        text = Text()
        buffer = []
        lines = ["line1", "line2", "line3"]
        text.write(buffer, lines)
        assert buffer == ["line1", "line2", "line3"]
        assert text.previous == ["line1", "line2", "line3"]

    def test_write_replaces_existing_buffer(self):
        text = Text()
        buffer = ["old1", "old2"]
        lines = ["new1", "new2", "new3"]
        text.write(buffer, lines)
        assert buffer == ["new1", "new2", "new3"]
        assert "old1" not in buffer

    def test_build_ops_empty_previous(self):
        text = Text()
        buffer = ["line1"]
        ops = text.buildOps(buffer)
        assert ops == []

    def test_build_ops_no_changes(self):
        text = Text()
        buffer = ["line1", "line2"]
        text.write(buffer, buffer[:])
        ops = text.buildOps(buffer)
        assert ops == []

    def test_build_ops_single_line_modification(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        buffer[0] = "hello there"
        ops = text.buildOps(buffer)

        assert len(ops) > 0
        assert any('i' in op for op in ops) or any('d' in op for op in ops)

    def test_build_ops_line_insertion(self):
        text = Text()
        buffer = ["line1", "line2"]
        text.write(buffer, buffer[:])

        buffer.insert(1, "inserted")
        ops = text.buildOps(buffer)

        assert len(ops) > 0
        assert any('i' in op for op in ops)

    def test_build_ops_line_deletion(self):
        text = Text()
        buffer = ["line1", "line2", "line3"]
        text.write(buffer, buffer[:])

        del buffer[1]
        ops = text.buildOps(buffer)

        assert len(ops) > 0
        assert any('d' in op for op in ops)

    def test_build_ops_line_replacement(self):
        text = Text()
        buffer = ["line1", "line2"]
        text.write(buffer, buffer[:])

        buffer[0] = "replaced"
        ops = text.buildOps(buffer)

        assert len(ops) > 0

    def test_build_ops_append_line(self):
        text = Text()
        buffer = ["line1"]
        text.write(buffer, buffer[:])

        buffer.append("line2")
        ops = text.buildOps(buffer)

        assert len(ops) > 0
        assert any('i' in op for op in ops)

    def test_build_ops_multiple_changes(self):
        text = Text()
        buffer = ["line1", "line2", "line3"]
        text.write(buffer, buffer[:])

        buffer[0] = "modified1"
        buffer[2] = "modified3"
        ops = text.buildOps(buffer)

        assert len(ops) > 0

    def test_apply_op_insert_single_char(self):
        text = Text()
        buffer = ["hello"]
        text.write(buffer, buffer[:])

        op = {"p": 5, "i": " world"}
        text.applyOp(buffer, op)

        assert buffer[0] == "hello world"

    def test_apply_op_insert_newline(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        op = {"p": 5, "i": "\n"}
        text.applyOp(buffer, op)

        assert len(buffer) == 2
        assert buffer[0] == "hello"
        assert buffer[1] == " world"

    def test_apply_op_insert_multiple_lines(self):
        text = Text()
        buffer = ["line1"]
        text.write(buffer, buffer[:])

        op = {"p": 5, "i": "\nline2\nline3"}
        text.applyOp(buffer, op)

        assert len(buffer) == 3

    def test_apply_op_delete_single_char(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        op = {"p": 5, "d": " "}
        text.applyOp(buffer, op)

        assert buffer[0] == "helloworld"

    def test_apply_op_delete_multiple_chars(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        op = {"p": 0, "d": "hello "}
        text.applyOp(buffer, op)

        assert buffer[0] == "world"

    def test_apply_op_delete_with_newline(self):
        text = Text()
        buffer = ["hello", "world"]
        text.write(buffer, buffer[:])

        op = {"p": 5, "d": "\n"}
        text.applyOp(buffer, op)

        assert len(buffer) == 1
        assert buffer[0] == "helloworld"

    def test_apply_op_delete_multiple_lines(self):
        text = Text()
        buffer = ["line1", "line2", "line3"]
        text.write(buffer, buffer[:])

        op = {"p": 5, "d": "\nline2"}
        text.applyOp(buffer, op)

        assert len(buffer) == 2

    def test_apply_op_combined_delete_and_insert(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        op = {"p": 6, "d": "world", "i": "there"}
        text.applyOp(buffer, op)

        assert buffer[0] == "hello there"

    def test_insert_at_beginning(self):
        text = Text()
        buffer = ["world"]
        text.write(buffer, buffer[:])

        text._insert(buffer, 0, "hello ")

        assert buffer[0] == "hello world"

    def test_insert_at_end(self):
        text = Text()
        buffer = ["hello"]
        text.write(buffer, buffer[:])

        text._insert(buffer, 5, " world")

        assert buffer[0] == "hello world"

    def test_insert_in_middle(self):
        text = Text()
        buffer = ["helloworld"]
        text.write(buffer, buffer[:])

        text._insert(buffer, 5, " ")

        assert buffer[0] == "hello world"

    def test_insert_newline_creates_new_line(self):
        text = Text()
        buffer = ["helloworld"]
        text.write(buffer, buffer[:])

        text._insert(buffer, 5, "\n")

        assert len(buffer) == 2
        assert buffer[0] == "hello"
        assert buffer[1] == "world"

    def test_insert_multiple_lines(self):
        text = Text()
        buffer = ["line1"]
        text.write(buffer, buffer[:])

        text._insert(buffer, 5, "\nline2\nline3")

        assert len(buffer) == 3
        assert buffer[1] == "line2"
        assert buffer[2] == "line3"

    def test_remove_single_char(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        text._remove(buffer, 5, " ")

        assert buffer[0] == "helloworld"

    def test_remove_multiple_chars(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        text._remove(buffer, 0, "hello ")

        assert buffer[0] == "world"

    def test_remove_from_end(self):
        text = Text()
        buffer = ["hello world"]
        text.write(buffer, buffer[:])

        text._remove(buffer, 6, "world")

        assert buffer[0] == "hello "

    def test_remove_newline(self):
        text = Text()
        buffer = ["hello", "world"]
        text.write(buffer, buffer[:])

        text._remove(buffer, 5, "\n")

        assert len(buffer) == 1
        assert buffer[0] == "helloworld"

    def test_remove_multiple_lines(self):
        text = Text()
        buffer = ["line1", "line2", "line3"]
        text.write(buffer, buffer[:])

        text._remove(buffer, 5, "\nline2\n")

        assert len(buffer) == 2


class TestTextOperations:

    def test_write_then_buildOps_consistency(self):
        text = Text()
        buffer = []
        lines = ["line1", "line2"]
        text.write(buffer, lines)

        buffer[0] = "modified"
        ops = text.buildOps(buffer)

        assert text.previous == ["modified", "line2"]

    def test_buildOps_then_applyOp_roundtrip(self):
        text1 = Text()
        buffer1 = ["hello", "world"]
        text1.write(buffer1, buffer1[:])

        buffer1[0] = "goodbye"
        ops = text1.buildOps(buffer1)

        text2 = Text()
        buffer2 = ["hello", "world"]
        text2.write(buffer2, buffer2[:])

        for op in reversed(ops):
            text2.applyOp(buffer2, op)

        assert buffer1 == buffer2

    def test_multiple_operations_sequence(self):
        text = Text()
        buffer = []
        text.write(buffer, ["line1"])

        buffer.append("line2")
        ops1 = text.buildOps(buffer)
        assert len(ops1) > 0

        buffer[0] = "modified"
        ops2 = text.buildOps(buffer)
        assert len(ops2) > 0

        del buffer[1]
        ops3 = text.buildOps(buffer)
        assert len(ops3) > 0

    def test_empty_to_content(self):
        text = Text()
        buffer = []
        text.write(buffer, [])

        buffer.append("new line")
        text.previous = []
        ops = text.buildOps(buffer)

        assert ops == []

    def test_content_to_empty(self):
        text = Text()
        buffer = ["line1", "line2"]
        text.write(buffer, buffer[:])

        del buffer[:]
        ops = text.buildOps(buffer)

        assert len(ops) > 0
        assert all('d' in op for op in ops)

    def test_large_buffer_operations(self):
        text = Text()
        lines = [f"line{i}" for i in range(100)]
        buffer = lines[:]
        text.write(buffer, lines)

        buffer[50] = "modified"
        ops = text.buildOps(buffer)

        assert len(ops) > 0

    def test_special_characters(self):
        text = Text()
        buffer = ["hello\tworld"]
        text.write(buffer, buffer[:])

        buffer[0] = "hello  world"
        ops = text.buildOps(buffer)

        assert len(ops) > 0

    def test_unicode_characters(self):
        text = Text()
        buffer = ["hello 世界"]
        text.write(buffer, buffer[:])

        buffer[0] = "hello 🌍"
        ops = text.buildOps(buffer)

        assert len(ops) > 0
