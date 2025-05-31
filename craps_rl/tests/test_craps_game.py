import unittest
from craps_rl.env.craps_game import Dice, CrapsGame # Adjusted import path

# Helper class for testing CrapsGame
class MockDice:
    def __init__(self, rolls_to_return: list[tuple[int, int, int]]):
        self.rolls_to_return = rolls_to_return
        self.roll_count = 0

    def roll(self) -> tuple[int, int, int]:
        if not self.rolls_to_return:
            raise IndexError("MockDice has no more rolls to return.")
        roll_data = self.rolls_to_return.pop(0)
        self.roll_count += 1
        # Ensure the sum is provided correctly or calculate it if only d1, d2 are given
        if len(roll_data) == 2: # d1, d2
            return roll_data[0], roll_data[1], roll_data[0] + roll_data[1]
        return roll_data # d1, d2, sum

class TestDice(unittest.TestCase):
    def test_roll_dice(self):
        dice = Dice()
        for _ in range(100):  # Roll 100 times
            d1, d2, total = dice.roll()
            self.assertTrue(1 <= d1 <= 6, f"Die 1 out of range: {d1}")
            self.assertTrue(1 <= d2 <= 6, f"Die 2 out of range: {d2}")
            self.assertEqual(d1 + d2, total, f"Sum incorrect: {d1}+{d2}!={total}")

class TestCrapsGame(unittest.TestCase):
    def setUp(self):
        """This method is called before each test."""
        self.game = CrapsGame()

    def test_initial_state(self):
        self.assertIsNone(self.game.point, "Initial point should be None")
        self.assertTrue(self.game.is_come_out_roll, "Should be come-out roll initially")
        self.assertIsNone(self.game.last_roll_detail, "Initial last_roll_detail should be None")
        self.assertIsNone(self.game.roll_outcome, "Initial roll_outcome should be None")

    def test_come_out_roll_natural_7(self):
        self.game.is_come_out_roll = True
        self.game.dice = MockDice([(3, 4, 7)])
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice()
        self.assertEqual(outcome, "natural")
        self.assertTrue(self.game.is_come_out_roll, "Should still be come-out roll after natural")
        self.assertIsNone(self.game.point, "Point should be None after natural")

    def test_come_out_roll_natural_11(self):
        self.game.is_come_out_roll = True
        self.game.dice = MockDice([(5, 6, 11)])
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice()
        self.assertEqual(outcome, "natural")
        self.assertTrue(self.game.is_come_out_roll)
        self.assertIsNone(self.game.point)

    def test_come_out_roll_craps_2(self):
        self.game.is_come_out_roll = True
        self.game.dice = MockDice([(1, 1, 2)])
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice()
        self.assertEqual(outcome, "craps")
        self.assertTrue(self.game.is_come_out_roll)
        self.assertIsNone(self.game.point)

    def test_come_out_roll_craps_3(self):
        self.game.is_come_out_roll = True
        self.game.dice = MockDice([(1, 2, 3)])
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice()
        self.assertEqual(outcome, "craps")
        self.assertTrue(self.game.is_come_out_roll)
        self.assertIsNone(self.game.point)

    def test_come_out_roll_craps_12(self):
        self.game.is_come_out_roll = True
        self.game.dice = MockDice([(6, 6, 12)])
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice()
        self.assertEqual(outcome, "craps")
        self.assertTrue(self.game.is_come_out_roll)
        self.assertIsNone(self.game.point)

    def test_come_out_roll_point_established(self):
        self.game.is_come_out_roll = True
        point_value = 4
        self.game.dice = MockDice([(1, 3, point_value)])
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice()
        self.assertEqual(outcome, "point_established")
        self.assertEqual(self.game.point, point_value)
        self.assertFalse(self.game.is_come_out_roll)

    def test_point_roll_hit_point(self):
        # Establish point
        self.game.is_come_out_roll = True
        point_to_establish = 6
        self.game.dice = MockDice([(3, 3, point_to_establish), (2, 4, point_to_establish)])
        self.game.roll_dice() # Establish point

        self.assertEqual(self.game.point, point_to_establish)
        self.assertFalse(self.game.is_come_out_roll)

        # Roll the point
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice() # Hit point
        self.assertEqual(outcome, "point_hit")
        self.assertTrue(self.game.is_come_out_roll)
        self.assertIsNone(self.game.point)

    def test_point_roll_seven_out(self):
        # Establish point
        self.game.is_come_out_roll = True
        point_to_establish = 8
        self.game.dice = MockDice([(4, 4, point_to_establish), (3, 4, 7)])
        self.game.roll_dice() # Establish point

        self.assertEqual(self.game.point, point_to_establish)
        self.assertFalse(self.game.is_come_out_roll)

        # Roll seven_out
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice() # Seven out
        self.assertEqual(outcome, "seven_out")
        self.assertTrue(self.game.is_come_out_roll)
        self.assertIsNone(self.game.point)

    def test_point_roll_continue(self):
        # Establish point
        self.game.is_come_out_roll = True
        point_to_establish = 9
        roll_to_continue = 5
        self.game.dice = MockDice([(4, 5, point_to_establish), (2, 3, roll_to_continue)])
        self.game.roll_dice() # Establish point

        self.assertEqual(self.game.point, point_to_establish)
        self.assertFalse(self.game.is_come_out_roll)

        # Roll something else
        _d1, _d2, _roll_sum, outcome = self.game.roll_dice() # Continue point
        self.assertEqual(outcome, "point_continued")
        self.assertFalse(self.game.is_come_out_roll)
        self.assertEqual(self.game.point, point_to_establish)

if __name__ == '__main__':
    unittest.main()
