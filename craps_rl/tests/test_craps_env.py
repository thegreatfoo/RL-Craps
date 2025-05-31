import unittest
import gymnasium as gym
import numpy as np
from craps_rl.env.craps_env import CrapsEnv
from craps_rl.env.craps_game import BetType, CrapsGame # For BetType and potentially direct game inspection

# Helper to get the integer index for a BetType in the CrapsEnv's action scheme
def get_bet_type_action_idx(env: CrapsEnv, bet_type_enum: BetType) -> int:
    for idx, bt_enum in env._action_idx_to_bet_type.items():
        if bt_enum == bet_type_enum:
            return idx
    raise ValueError(f"BetType {bet_type_enum} not found in env action mapping.")

class TestEnvInitialization(unittest.TestCase):
    def setUp(self):
        self.env = CrapsEnv(initial_bankroll=100)

    def test_initialization_values(self):
        self.assertIsInstance(self.env.action_space, gym.spaces.Dict)
        self.assertIsInstance(self.env.observation_space, gym.spaces.Dict)
        self.assertEqual(self.env.player_bankroll, 100.0)
        self.assertEqual(self.env.initial_bankroll, 100.0)

        initial_obs, _ = self.env.reset()
        self.assertTrue(initial_obs['is_come_out_roll'] == 1) # is_come_out_roll is 1 (True)
        self.assertEqual(initial_obs['point'], 0) # No point established
        self.assertEqual(initial_obs['last_roll_sum'], 0)


class TestResetMethod(unittest.TestCase):
    def setUp(self):
        self.env = CrapsEnv(initial_bankroll=200)

    def test_reset_returns_valid_observation_and_info(self):
        obs, info = self.env.reset()
        self.assertTrue(self.env.observation_space.contains(obs))
        self.assertIsInstance(info, dict)

    def test_reset_resets_state(self):
        # Modify state then reset
        self.env.player_bankroll = 50
        self.env.game.point = 6 # Manually set point in underlying game for testing reset
        self.env.game.is_come_out_roll = False
        # Place a bet to ensure it's cleared
        pass_line_action_idx = get_bet_type_action_idx(self.env, BetType.PASS_LINE)
        bet_amount_idx = 0 # Smallest bet
        self.env.step({"action_type": pass_line_action_idx, "bet_amount_level": bet_amount_idx})

        obs, _ = self.env.reset()

        self.assertEqual(self.env.player_bankroll, 200.0)
        self.assertTrue(obs['is_come_out_roll'] == 1)
        self.assertEqual(obs['point'], 0)
        self.assertEqual(len(self.env.game.get_active_bets()), 0, "Active bets should be cleared on reset")
        for key in obs: # Check if bet amounts are reset in observation
            if "amount" in key and isinstance(obs[key], np.ndarray):
                self.assertEqual(obs[key][0], 0.0)


    def test_reset_with_seed(self):
        # This primarily tests API conformance. True reproducibility of game rolls
        # would require the underlying CrapsGame to also use the seeded RNG.
        obs1, _ = self.env.reset(seed=42)
        # If game logic were fully deterministic with seed, further actions would yield same results.
        # For now, just check that reset with seed works and returns valid obs.
        self.assertTrue(self.env.observation_space.contains(obs1))

        obs2, _ = self.env.reset(seed=42)
        # Check if initial observations are the same.
        # Note: CrapsGame uses global random, so these won't be identical unless CrapsGame is also seeded.
        # This test is limited for now. The key is that super().reset(seed=seed) is called.
        # self.assertEqual(obs1["last_roll_sum"], obs2["last_roll_sum"]) # This might not hold
        self.assertTrue(self.env.observation_space.contains(obs2))


class TestStepMethodAndBetting(unittest.TestCase):
    def setUp(self):
        self.env = CrapsEnv(initial_bankroll=100)
        self.initial_bankroll = 100.0

    def _get_roll_action(self):
        return {"action_type": 0, "bet_amount_level": 0} # bet_amount_level is ignored

    def _get_bet_action(self, bet_type: BetType, bet_level_idx: int = 0):
        action_idx = get_bet_type_action_idx(self.env, bet_type)
        return {"action_type": action_idx, "bet_amount_level": bet_level_idx}

    def test_roll_action(self):
        obs, reward, terminated, truncated, info = self.env.step(self._get_roll_action())
        self.assertTrue(self.env.observation_space.contains(obs))
        self.assertIsInstance(reward, float)
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIsInstance(info, dict)
        self.assertIn('roll_sum', info)
        self.assertIn('outcome', info)
        # Bankroll change depends on outcome (if any bets were placed prior, which is not the case here)
        # If no bets, winnings should be 0 from roll_dice.
        self.assertEqual(reward, 0.0)
        self.assertEqual(self.env.player_bankroll, self.initial_bankroll + reward)


    def test_place_valid_pass_line_bet(self):
        self.env.reset()
        bet_amount = self.env.bet_amount_options[0] # e.g. $1
        action = self._get_bet_action(BetType.PASS_LINE, 0)

        obs, reward, _, _, info = self.env.step(action)

        self.assertEqual(reward, 0.0) # No immediate reward/penalty for valid bet
        self.assertEqual(self.env.player_bankroll, self.initial_bankroll - bet_amount)
        self.assertTrue(self.env.observation_space.contains(obs))
        self.assertEqual(obs['pass_line_amount'][0], bet_amount)
        self.assertIn('bet_successful', info)
        self.assertTrue(info['bet_successful'])

    def test_place_invalid_pass_line_bet_on_point(self):
        self.env.reset()
        # Establish a point: Requires a roll that results in a point.
        # This is tricky without mocking. We'll assume a sequence.
        # 1. Place Pass Line
        self.env.step(self._get_bet_action(BetType.PASS_LINE, 0))
        # 2. Roll until point is established or max attempts
        point_established = False
        for _ in range(10): # Try a few rolls to establish a point
            obs, _, _, _, _ = self.env.step(self._get_roll_action())
            if not obs['is_come_out_roll']: # Point is established
                point_established = True
                break

        self.assertTrue(point_established, "Test setup failed: Could not establish a point.")

        # Now try to place another Pass Line bet (should be invalid)
        initial_bankroll_before_invalid_bet = self.env.player_bankroll
        obs, reward, _, _, info = self.env.step(self._get_bet_action(BetType.PASS_LINE, 0))

        self.assertEqual(reward, -1.0) # Penalty for invalid bet
        self.assertEqual(self.env.player_bankroll, initial_bankroll_before_invalid_bet) # Bankroll unchanged
        self.assertIn('bet_successful', info)
        self.assertFalse(info['bet_successful'])

    def test_place_valid_pass_odds_bet(self):
        self.env.reset()
        pass_line_bet_amount = self.env.bet_amount_options[0]
        pass_odds_bet_amount = self.env.bet_amount_options[1]

        # 1. Place Pass Line
        self.env.step(self._get_bet_action(BetType.PASS_LINE, 0))
        bankroll_after_pass_line = self.env.player_bankroll

        # 2. Roll to establish point
        point_established = False
        current_obs = None
        for _ in range(20): # Increased attempts for randomness
            current_obs, _, _, _, _ = self.env.step(self._get_roll_action())
            if not current_obs['is_come_out_roll']:
                point_established = True
                break
        self.assertTrue(point_established, "Failed to establish a point to test odds.")

        # 3. Place Pass Odds
        action = self._get_bet_action(BetType.PASS_ODDS, 1)
        obs, reward, _, _, info = self.env.step(action)

        self.assertEqual(reward, 0.0)
        self.assertEqual(self.env.player_bankroll, bankroll_after_pass_line - pass_odds_bet_amount)
        self.assertTrue(self.env.observation_space.contains(obs))
        self.assertEqual(obs['pass_odds_amount'][0], pass_odds_bet_amount)
        self.assertEqual(obs['pass_odds_point'], current_obs['point']) # Odds bet is on current point
        self.assertTrue(info['bet_successful'])

    def test_place_invalid_pass_odds_no_point(self):
        self.env.reset() # On come-out roll, no point
        action = self._get_bet_action(BetType.PASS_ODDS, 0)
        obs, reward, _, _, info = self.env.step(action)

        self.assertEqual(reward, -1.0)
        self.assertEqual(self.env.player_bankroll, self.initial_bankroll)
        self.assertFalse(info['bet_successful'])

    def test_place_invalid_pass_odds_no_line_bet(self):
        self.env.reset()
        # Establish point without a line bet (not typical, but for testing odds validity)
        # This requires direct game manipulation or specific roll sequence.
        # For simplicity, assume a point is established, but we haven't placed pass line.
        # Let's roll until point established without any prior bet.
        point_established = False
        for _ in range(10):
            obs, _, _, _, _ = self.env.step(self._get_roll_action())
            if not obs['is_come_out_roll']:
                point_established = True
                break
        self.assertTrue(point_established, "Test setup: Could not establish point.")

        # Now try to place odds - should be invalid as no pass line bet
        action = self._get_bet_action(BetType.PASS_ODDS, 0)
        obs, reward, _, _, info = self.env.step(action)

        self.assertEqual(reward, -1.0)
        self.assertEqual(self.env.player_bankroll, self.initial_bankroll) # Bankroll unchanged
        self.assertFalse(info['bet_successful'])


    def test_termination_on_bankrupt(self):
        self.env = CrapsEnv(initial_bankroll=5) # Low bankroll
        self.env.reset()

        # Try to place a bet larger than bankroll (game logic should prevent, env might penalize)
        # Or, a sequence of losing bets.
        # Let's make a large bet that is allowed by bet_amount_options but > bankroll
        # Find a bet_amount_idx for an amount > 5. Assume 10 is idx 2.
        bet_amount_idx_for_10 = -1
        for i, amount in enumerate(self.env.bet_amount_options):
            if amount == 10:
                bet_amount_idx_for_10 = i
                break
        self.assertNotEqual(bet_amount_idx_for_10, -1, "Bet amount $10 not found for test.")

        action = self._get_bet_action(BetType.PASS_LINE, bet_amount_idx_for_10) # Bet $10
        obs, reward, terminated, _, info = self.env.step(action)

        # The CrapsGame.place_bet should reject this if amount > player_bankroll.
        # So, this tests the "invalid bet attempt" path.
        self.assertEqual(reward, -1.0)
        self.assertFalse(terminated) # Not terminated by just attempting invalid bet
        self.assertEqual(self.env.player_bankroll, 5)

        # To test termination, we need a sequence of actual losses.
        # This is hard without controlling dice.
        # Alternative: set bankroll very low, make a small valid bet, and hope for a loss.
        # For now, this aspect is hard to test reliably without mocking or game state control.
        # We can directly test the termination condition logic:
        self.env.player_bankroll = 0
        obs, reward, terminated, _, info = self.env.step(self._get_roll_action()) # Any action
        self.assertTrue(terminated)

        self.env.player_bankroll = -10
        obs, reward, terminated, _, info = self.env.step(self._get_roll_action()) # Any action
        self.assertTrue(terminated)


class TestObservationSpaceConsistency(unittest.TestCase):
    def setUp(self):
        self.env = CrapsEnv(initial_bankroll=100)

    def test_observation_consistency(self):
        obs, _ = self.env.reset()
        self.assertTrue(self.env.observation_space.contains(obs))

        # Action 1: Place Pass Line
        pass_line_idx = get_bet_type_action_idx(self.env, BetType.PASS_LINE)
        action = {"action_type": pass_line_idx, "bet_amount_level": 0}
        obs, _, _, _, _ = self.env.step(action)
        self.assertTrue(self.env.observation_space.contains(obs))

        # Action 2: Roll
        action = {"action_type": 0, "bet_amount_level": 0}
        obs, _, _, _, _ = self.env.step(action)
        self.assertTrue(self.env.observation_space.contains(obs))

        # If point established, try to place odds
        if not obs['is_come_out_roll']:
            pass_odds_idx = get_bet_type_action_idx(self.env, BetType.PASS_ODDS)
            action = {"action_type": pass_odds_idx, "bet_amount_level": 0}
            obs, _, _, _, _ = self.env.step(action)
            self.assertTrue(self.env.observation_space.contains(obs))

            action_roll = {"action_type": 0, "bet_amount_level": 0}
            obs, _, _, _, _ = self.env.step(action_roll)
            self.assertTrue(self.env.observation_space.contains(obs))


# More tests for specific win/loss scenarios would require either:
# 1. Mocking CrapsGame.roll_dice() to return specific outcomes.
# 2. Running the environment many times and checking statistics (probabilistic testing).
# 3. Having a way to set dice rolls directly in CrapsGame (if CrapsGame were designed for it).
# For current scope, we test the Env's handling of actions and basic game states.

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False) # For running in environments like notebooks
