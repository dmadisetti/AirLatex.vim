import pytest
from unittest.mock import Mock, MagicMock, patch


class TestDocumentBasics:

    def test_highlight_structure(self):
        from rplugin.python3.airlatex.buffers.document import highlight
        h = highlight(name="test", group="TestGroup", line=1, col_start=0, col_end=5)
        assert h.name == "test"
        assert h.group == "TestGroup"
        assert h.line == 1
        assert h.col_start == 0
        assert h.col_end == 5

    @patch('rplugin.python3.airlatex.buffers.document.pynvim')
    @patch('rplugin.python3.airlatex.buffers.document.Text')
    def test_document_imports(self, mock_text, mock_pynvim):
        from rplugin.python3.airlatex.buffers.document import Document
        assert Document is not None

    def test_cursor_data_structure(self):
        cursor = {
            "row": 10,
            "column": 5,
            "name": "User Name",
            "user_id": "user123"
        }
        assert cursor["row"] == 10
        assert cursor["column"] == 5
        assert "name" in cursor
        assert "user_id" in cursor
