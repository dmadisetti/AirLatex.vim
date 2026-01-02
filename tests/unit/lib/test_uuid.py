import pytest
import time
import re
from unittest.mock import patch
from rplugin.python3.airlatex.lib.uuid import generateId, generateCommentId, generateTimeStamp


class TestGenerateId:

    def test_generates_string(self):
        id = generateId()
        assert isinstance(id, str)

    def test_generates_correct_length(self):
        id = generateId()
        assert len(id) == 18

    def test_generates_hex_string(self):
        id = generateId()
        assert re.match(r'^[0-9a-f]{18}$', id)

    def test_generates_unique_ids(self):
        ids = set()
        for _ in range(100):
            id = generateId()
            ids.add(id)
        assert len(ids) == 100

    def test_timestamp_component(self):
        with patch('time.time', return_value=1234567890):
            id = generateId()
            timestamp_part = id[:8]
            expected_timestamp = format(1234567890, 'x').zfill(8)
            assert timestamp_part == expected_timestamp

    def test_structure_with_fixed_random(self):
        with patch('random.randint', side_effect=[12345, 67890]):
            with patch('time.time', return_value=1234567890):
                id = generateId()
                assert len(id) == 18
                assert id[:8] == format(1234567890, 'x').zfill(8)

    def test_padding_small_values(self):
        with patch('random.randint', side_effect=[1, 1]):
            with patch('time.time', return_value=1):
                id = generateId()
                assert len(id) == 18
                assert id == '000000010000010001'

    def test_multiple_calls_different_results(self):
        id1 = generateId()
        time.sleep(0.001)
        id2 = generateId()
        assert id1 != id2


class TestGenerateCommentId:

    def test_generates_string(self):
        id = generateCommentId(1)
        assert isinstance(id, str)

    def test_generates_correct_length(self):
        id = generateCommentId(1)
        assert len(id) == 24

    def test_generates_hex_string(self):
        id = generateCommentId(1)
        assert re.match(r'^[0-9a-f]{24}$', id)

    def test_includes_increment_at_end(self):
        id = generateCommentId(255)
        increment_part = id[-6:]
        assert increment_part == format(255, 'x').zfill(6)

    def test_increment_zero(self):
        id = generateCommentId(0)
        assert id[-6:] == '000000'

    def test_increment_padding(self):
        id = generateCommentId(1)
        assert id[-6:] == '000001'

    def test_large_increment(self):
        id = generateCommentId(16777215)
        increment_part = id[-6:]
        assert increment_part == format(16777215, 'x').zfill(6)

    def test_first_18_chars_match_generateId(self):
        with patch('random.randint', side_effect=[12345, 67890]):
            with patch('time.time', return_value=1234567890):
                base_id = generateId()

        with patch('random.randint', side_effect=[12345, 67890]):
            with patch('time.time', return_value=1234567890):
                comment_id = generateCommentId(100)

        assert comment_id[:18] == base_id

    def test_different_increments_different_ids(self):
        with patch('random.randint', side_effect=[1, 1, 1, 1]):
            with patch('time.time', return_value=1):
                id1 = generateCommentId(1)
                id2 = generateCommentId(2)
                assert id1 != id2
                assert id1[:-6] == id2[:-6]
                assert id1[-6:] != id2[-6:]

    def test_generates_unique_ids_with_different_increments(self):
        ids = set()
        for i in range(100):
            id = generateCommentId(i)
            ids.add(id)
        assert len(ids) == 100


class TestGenerateTimeStamp:

    def test_generates_string(self):
        ts = generateTimeStamp()
        assert isinstance(ts, str)

    def test_generates_13_digit_string(self):
        ts = generateTimeStamp()
        assert len(ts) == 13

    def test_generates_numeric_string(self):
        ts = generateTimeStamp()
        assert ts.isdigit()

    def test_timestamp_increases(self):
        ts1 = generateTimeStamp()
        time.sleep(0.001)
        ts2 = generateTimeStamp()
        assert int(ts2) >= int(ts1)

    def test_fixed_time(self):
        with patch('time.time', return_value=1234567890.123456):
            ts = generateTimeStamp()
            expected = str(int(1234567890.123456 * 1e13))[:13]
            assert ts == expected

    def test_small_time_value(self):
        with patch('time.time', return_value=1.0):
            ts = generateTimeStamp()
            assert len(ts) == 13
            assert ts.isdigit()

    def test_large_time_value(self):
        with patch('time.time', return_value=9999999999.999999):
            ts = generateTimeStamp()
            assert len(ts) == 13
            assert ts.isdigit()

    def test_multiple_calls_different_or_equal(self):
        ts1 = generateTimeStamp()
        ts2 = generateTimeStamp()
        assert int(ts2) >= int(ts1)


class TestIDGenerationIntegration:

    def test_all_functions_return_different_formats(self):
        id1 = generateId()
        id2 = generateCommentId(1)
        ts = generateTimeStamp()

        assert len(id1) == 18
        assert len(id2) == 24
        assert len(ts) == 13

        assert id1 != id2[:18]

    def test_concurrent_generation(self):
        ids = []
        comment_ids = []
        timestamps = []

        for i in range(50):
            ids.append(generateId())
            comment_ids.append(generateCommentId(i))
            timestamps.append(generateTimeStamp())

        assert len(set(ids)) == 50
        assert len(set(comment_ids)) == 50
        assert len(set(timestamps)) >= 1
