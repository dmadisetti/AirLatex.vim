import pytest
from rplugin.python3.airlatex.lib.range import FenwickTree, NaiveAccumulator


class TestFenwickTree:

    def test_initialization_empty(self):
        ft = FenwickTree(size=512)
        assert ft.size == 512
        assert len(ft.tree) == 513
        assert len(ft.array) == 512
        assert ft.last_index == -1

    def test_initialization_with_array(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        assert ft.last_index == 3
        assert ft.array[:4] == [10, 20, 30, 40]

    def test_get_cumulative_value_empty(self):
        ft = FenwickTree()
        assert ft.get_cumulative_value(0) == 0
        assert ft.get_cumulative_value(1) == 0

    def test_get_cumulative_value_with_data(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        assert ft.get_cumulative_value(1) == 10
        assert ft.get_cumulative_value(2) == 30
        assert ft.get_cumulative_value(3) == 60
        assert ft.get_cumulative_value(4) == 100

    def test_append_single_value(self):
        ft = FenwickTree()
        ft.append(10)
        assert ft.last_index == 0
        assert ft.array[0] == 10
        assert ft.get_cumulative_value(1) == 10

    def test_append_multiple_values(self):
        ft = FenwickTree()
        ft.append(10)
        ft.append(20)
        ft.append(30)
        assert ft.last_index == 2
        assert ft.array[:3] == [10, 20, 30]
        assert ft.get_cumulative_value(1) == 10
        assert ft.get_cumulative_value(2) == 30
        assert ft.get_cumulative_value(3) == 60

    def test_update_value(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        ft.update(2, 5)
        assert ft.get_cumulative_value(2) == 35
        assert ft.get_cumulative_value(4) == 105

    def test_getitem(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        assert ft[0] == 10
        assert ft[1] == 30
        assert ft[2] == 60
        assert ft[3] == 100
        assert ft[-1] == 100

    def test_setitem(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        ft[1] = 25
        assert ft.array[1] == 25
        assert ft[1] == 35
        assert ft[3] == 105

    def test_setitem_negative_index(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        ft[-1] = 50
        assert ft.array[3] == 50
        assert ft[-1] == 110

    def test_remove_middle_element(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        ft.remove(1)
        assert ft.last_index == 2
        assert ft.array[:3] == [10, 30, 40]
        assert ft[0] == 10
        assert ft[1] == 40
        assert ft[2] == 80

    def test_remove_last_element(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        ft.remove(3)
        assert ft.last_index == 2
        assert ft[2] == 60

    def test_remove_negative_index(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        ft.remove(-1)
        assert ft.last_index == 2
        assert ft[2] == 60

    def test_delitem(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        del ft[1]
        assert ft.last_index == 2
        assert ft.array[:3] == [10, 30, 40]

    def test_insert_at_beginning(self):
        ft = FenwickTree()
        ft.initialize([20, 30, 40])
        ft.insert(0, 10)
        assert ft.last_index == 3
        assert ft.array[:4] == [10, 20, 30, 40]
        assert ft[0] == 10
        assert ft[1] == 30
        assert ft[2] == 60
        assert ft[3] == 100

    def test_insert_in_middle(self):
        ft = FenwickTree()
        ft.initialize([10, 30, 40])
        ft.insert(1, 20)
        assert ft.last_index == 3
        assert ft.array[:4] == [10, 20, 30, 40]
        assert ft[1] == 30
        assert ft[2] == 60

    def test_insert_negative_index(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30])
        ft.insert(-1, 25)
        assert ft.last_index == 3

    def test_search_exact_match(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        row, col = ft.search(10)
        assert row == 1
        assert col == 0

    def test_search_within_range(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        row, col = ft.search(15)
        assert row == 1
        assert col == 5

    def test_search_accumulates(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        row, col = ft.search(35)
        assert row == 2
        assert col == 5

    def test_search_beyond_range(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        row, col = ft.search(150)
        assert row == -1
        assert col is None

    def test_position(self):
        ft = FenwickTree()
        ft.initialize([10, 20, 30, 40])
        assert ft.position(0, 5) == 15
        assert ft.position(1, 5) == 35
        assert ft.position(2, 5) == 65

    def test_resize_on_large_insert(self):
        ft = FenwickTree(size=4)
        ft.initialize([10, 20])
        original_size = ft.size
        ft.insert(10, 30)
        assert ft.size > original_size

    def test_resize_on_append(self):
        ft = FenwickTree(size=4)
        for i in range(10):
            ft.append(i)
        assert ft.size >= 10
        assert ft.last_index == 9

    def test_large_dataset(self):
        ft = FenwickTree()
        values = list(range(1, 101))
        ft.initialize(values)
        expected_sum = sum(values)
        assert ft[99] == expected_sum

    def test_multiple_operations_sequence(self):
        ft = FenwickTree()
        ft.append(10)
        ft.append(20)
        ft.insert(1, 15)
        assert ft.array[:3] == [10, 15, 20]
        del ft[1]
        assert ft.array[:2] == [10, 20]
        ft[0] = 5
        assert ft[0] == 5
        assert ft[1] == 25


class TestNaiveAccumulator:

    def test_initialization_empty(self):
        na = NaiveAccumulator()
        assert na.array == [0]
        assert na.last_index == 0

    def test_initialization_with_base(self):
        na = NaiveAccumulator([10, 20, 30])
        assert na.last_index == 3
        assert na.arr == [10, 20, 30, 0]

    def test_insert(self):
        na = NaiveAccumulator()
        na.insert(0, 10)
        na.insert(1, 20)
        assert na.array[:3] == [10, 20, 0]
        assert na.last_index == 2

    def test_get_cumulative_value(self):
        na = NaiveAccumulator([10, 20, 30])
        # Array is [10, 20, 30, 0], so cumulative sums are:
        assert na.get_cumulative_value(0) == 0    # sum([])
        assert na.get_cumulative_value(1) == 10   # sum([10])
        assert na.get_cumulative_value(2) == 30   # sum([10, 20])
        assert na.get_cumulative_value(3) == 60   # sum([10, 20, 30])
        assert na.get_cumulative_value(4) == 60   # sum([10, 20, 30, 0])

    def test_get_cumulative_value_negative_index(self):
        na = NaiveAccumulator([10, 20, 30])
        result = na.get_cumulative_value(-1)
        assert result >= 0

    def test_remove(self):
        na = NaiveAccumulator([10, 20, 30])
        na.remove(2)
        assert na.last_index == 2
        assert 20 in na.arr

    def test_remove_negative_index(self):
        na = NaiveAccumulator([10, 20, 30])
        na.remove(-1)
        assert na.last_index == 2

    def test_search(self):
        na = NaiveAccumulator([10, 20, 30])
        # Array is [10, 20, 30, 0], searching position 5 is in first element
        row, col = na.search(5)
        assert row == 0
        assert col == 5

    def test_search_accumulates(self):
        na = NaiveAccumulator([10, 20, 30])
        # Position 15 is past first element (10), so in second element at offset 5
        row, col = na.search(15)
        assert row == 1
        assert col == 5

    def test_search_beyond_range(self):
        na = NaiveAccumulator([10, 20, 30])
        row, col = na.search(100)
        assert row == na.last_index
        assert col == 0

    def test_position(self):
        na = NaiveAccumulator([10, 20, 30])
        # position(row, col) = get_cumulative_value(row) + col
        assert na.position(1, 5) == 15  # cumulative(1)=10, +5 = 15
        assert na.position(2, 5) == 35  # cumulative(2)=30, +5 = 35

    def test_update_existing(self):
        na = NaiveAccumulator([10, 20, 30])
        # update() adds to existing value (ADD behavior)
        na.update(1, 5)
        assert na.array[1] == 25  # 20 + 5 = 25

    def test_update_append(self):
        na = NaiveAccumulator([10, 20, 30])
        original_last = na.last_index
        na.update(original_last + 1, 40)
        assert na.last_index == original_last + 1
        assert na.array[original_last + 1] == 40

    def test_getitem(self):
        na = NaiveAccumulator([10, 20, 30])
        # __getitem__ returns cumulative values
        assert na[0] == 0   # sum([])
        assert na[1] == 10  # sum([10])
        assert na[2] == 30  # sum([10, 20])

    def test_setitem_existing(self):
        na = NaiveAccumulator([10, 20, 30])
        na[1] = 15
        assert na.array[1] == 15

    def test_setitem_append(self):
        na = NaiveAccumulator([10, 20, 30])
        original_last = na.last_index
        na[original_last + 1] = 40
        assert na.last_index == original_last + 1
        assert na.array[original_last + 1] == 40

    def test_delitem(self):
        na = NaiveAccumulator([10, 20, 30])
        del na[2]
        assert na.last_index == 2

    def test_arr_property(self):
        na = NaiveAccumulator([10, 20, 30])
        arr = na.arr
        assert len(arr) == na.last_index + 1
        assert 10 in arr
        assert 20 in arr
        assert 30 in arr


class TestFenwickTreeVsNaiveAccumulator:

    def test_same_cumulative_values(self):
        data = [10, 20, 30, 40, 50]
        ft = FenwickTree()
        ft.initialize(data)
        na = NaiveAccumulator(data)

        for i in range(len(data)):
            assert ft[i] == na[i + 1], f"Mismatch at index {i}"

    def test_same_search_results(self):
        data = [10, 20, 30, 40, 50]
        ft = FenwickTree()
        ft.initialize(data)
        na = NaiveAccumulator(data)

        for value in [5, 15, 35, 75, 125]:
            ft_row, ft_col = ft.search(value)
            na_row, na_col = na.search(value)
            if ft_row != -1:
                assert ft_row == na_row, f"Row mismatch for value {value}"
                assert ft_col == na_col, f"Col mismatch for value {value}"

    def test_same_position_results(self):
        data = [10, 20, 30, 40, 50]
        ft = FenwickTree()
        ft.initialize(data)
        na = NaiveAccumulator(data)

        for row in range(len(data)):
            for col in [0, 5, 10]:
                ft_pos = ft.position(row, col)
                na_pos = na.position(row + 1, col)
                assert ft_pos == na_pos, f"Position mismatch at row {row}, col {col}"
