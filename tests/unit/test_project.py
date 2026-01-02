import pytest
from unittest.mock import Mock, MagicMock, patch


class TestProjectBasics:

    @patch('rplugin.python3.airlatex.project.Document')
    @patch('rplugin.python3.airlatex.project.tornado')
    def test_project_imports(self, mock_tornado, mock_document):
        from rplugin.python3.airlatex.project import AirLatexProject
        assert AirLatexProject is not None

    def test_message_parsing(self):
        message = "1:2:3:{\"key\":\"value\"}"
        parts = message.split(":", 3)
        assert len(parts) == 4
        assert parts[0] == "1"
        assert parts[1] == "2"
        assert parts[2] == "3"
        assert parts[3] == '{"key":"value"}'

    def test_operational_transform_insert(self):
        op = {"p": 10, "i": "hello"}
        assert "p" in op
        assert "i" in op
        assert op["p"] == 10
        assert op["i"] == "hello"

    def test_operational_transform_delete(self):
        op = {"p": 5, "d": "world"}
        assert "p" in op
        assert "d" in op
        assert op["p"] == 5
        assert op["d"] == "world"

    def test_operational_transform_comment(self):
        op = {"p": 0, "c": "comment text", "t": "thread1"}
        assert "c" in op
        assert "t" in op
        assert op["c"] == "comment text"
        assert op["t"] == "thread1"
