import unittest
import bot

TESTS_TABLE = "tests"
TESTS_COL_1, TESTS_COL_2, TESTS_COL_3 = range(3)


class TestSum(unittest.TestCase):

    bot.load_db()

    def test_get_cell(self):
        self.assertEqual(bot.get_cell(TESTS_TABLE, 2, TESTS_COL_2), 5420)

    def test_get_col(self):
        expected_data = ['zozo', 'a', 'b', 'c']
        self.assertListEqual(bot.get_col(TESTS_TABLE, TESTS_COL_3)[:4], expected_data)

    def test_get_row(self):
        expected_data = [12, 1231, 'a']
        self.assertListEqual(bot.get_row(TESTS_TABLE, 1), expected_data)

    def test_append_row(self):
        new_data = [321, 1231, "test data"]
        row = bot.append_row(TESTS_TABLE, new_data)
        self.assertListEqual(bot.get_row(TESTS_TABLE, row), new_data)

    def test_update_cell(self):
        new_value = 23
        bot.update_cell(TESTS_TABLE, 5, TESTS_COL_2, new_value)
        self.assertEqual(bot.get_cell(TESTS_TABLE, 5, TESTS_COL_2), new_value)
        bot.update_cell(TESTS_TABLE, 5, TESTS_COL_2, new_value * 2)
        self.assertEqual(bot.get_cell(TESTS_TABLE, 5, TESTS_COL_2), new_value * 2)


if __name__ == '__main__':
    unittest.main()
