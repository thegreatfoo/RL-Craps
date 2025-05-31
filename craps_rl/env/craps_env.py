import gymnasium as gym
from gymnasium import spaces
import numpy as np
from .craps_game import CrapsGame, BetType # Assuming BetType is in craps_game.py

class CrapsEnv(gym.Env):
    metadata = {'render_modes': ['human'], 'render_fps': 1}

    def __init__(self, initial_bankroll=1000, render_mode=None):
        super().__init__()

        self.game = CrapsGame()
        self.initial_bankroll = float(initial_bankroll) # Ensure float
        self.player_bankroll = float(initial_bankroll)  # Ensure float

        self.render_mode = render_mode

        # Define action categories based on BetType enum + Roll
        # Action: 0=Roll, 1=BetType1, 2=BetType2, ...
        self._action_idx_to_bet_type = {i+1: bet_type for i, bet_type in enumerate(BetType)}
        self._bet_type_to_action_idx = {v: k for k, v in self._action_idx_to_bet_type.items()}

        # Define a set of bet amounts/levels
        self.bet_amount_options = np.array([1, 5, 10, 20, 50, 100], dtype=np.float32)

        self.action_space = self._define_action_space()
        self.observation_space = self._define_observation_space()

        # Track last roll for observation
        self.last_roll_sum = 0
        self.last_dice = (0,0) # Tuple (die1, die2)

    def _define_action_space(self):
        num_bet_types = len(BetType)
        num_bet_amount_options = len(self.bet_amount_options)

        return spaces.Dict({
            "action_type": spaces.Discrete(num_bet_types + 1), # 0 for roll, 1 to N for bet types
            "bet_amount_level": spaces.Discrete(num_bet_amount_options) # Index for self.bet_amount_options
        })

    def _define_observation_space(self):
        return spaces.Dict({
            "point": spaces.Discrete(11), # 0 for no point, values 4,5,6,8,9,10 for established points
            "is_come_out_roll": spaces.Discrete(2), # 0 or 1
            "bankroll": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "last_roll_sum": spaces.Discrete(13), # 0 for initial state, 2-12 for roll sums
            "pass_line_amount": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "dont_pass_amount": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "pass_odds_amount": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "pass_odds_point": spaces.Discrete(11), # Point for the odds bet (0 if none)
            "dont_pass_odds_amount": spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32),
            "dont_pass_odds_point": spaces.Discrete(11), # Point for the odds bet (0 if none)
        })

    def _get_observation(self):
        obs = {
            "point": self.game.point if self.game.point is not None else 0,
            "is_come_out_roll": 1 if self.game.is_come_out_roll else 0,
            "bankroll": np.array([self.player_bankroll], dtype=np.float32),
            "last_roll_sum": self.last_roll_sum,
            "pass_line_amount": np.array([0.0], dtype=np.float32),
            "dont_pass_amount": np.array([0.0], dtype=np.float32),
            "pass_odds_amount": np.array([0.0], dtype=np.float32),
            "pass_odds_point": 0, # 0 if no pass odds bet or point not applicable
            "dont_pass_odds_amount": np.array([0.0], dtype=np.float32),
            "dont_pass_odds_point": 0, # 0 if no don't pass odds bet or point not applicable
        }

        active_game_bets = self.game.get_active_bets() # Expects list of dicts
        for bet in active_game_bets:
            bet_type = bet['type']
            amount = float(bet['amount']) # Ensure float for np.array

            if bet_type == BetType.PASS_LINE:
                obs["pass_line_amount"] = np.array([amount], dtype=np.float32)
            elif bet_type == BetType.DONT_PASS:
                obs["dont_pass_amount"] = np.array([amount], dtype=np.float32)
            elif bet_type == BetType.PASS_ODDS:
                obs["pass_odds_amount"] = np.array([amount], dtype=np.float32)
                # Ensure point_for_odds is an int and defaults to 0 if not present or None
                obs["pass_odds_point"] = int(bet.get('point_for_odds', 0) or 0)
            elif bet_type == BetType.DONT_PASS_ODDS:
                obs["dont_pass_odds_amount"] = np.array([amount], dtype=np.float32)
                obs["dont_pass_odds_point"] = int(bet.get('point_for_odds', 0) or 0)
        return obs

    def reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[dict, dict]:
        super().reset(seed=seed)

        self.game.reset_game()
        self.player_bankroll = self.initial_bankroll # Reset to float
        self.last_roll_sum = 0
        self.last_dice = (0,0)

        if self.render_mode == "human":
            self.render()
        return self._get_observation(), {} # Return obs and info dict

    def step(self, action) -> tuple[dict, float, bool, bool, dict]:
        action_type_idx = action["action_type"]
        bet_amount_level_idx = action["bet_amount_level"]

        reward = 0.0 # Default reward
        terminated = False
        truncated = False # Not used for episode truncation by step limit
        info = {}

        # 1. Process Action (Bet or Roll)
        if action_type_idx == 0: # Roll dice action
            die1, die2, roll_sum, outcome_str, winnings = self.game.roll_dice()

            # 2. Update internal state based on action
            self.last_roll_sum = roll_sum
            self.last_dice = (die1, die2)

            # 3. Update bankroll
            self.player_bankroll += float(winnings)

            # 4. Calculate reward
            reward = float(winnings)
            info = {'dice': self.last_dice, 'roll_sum': self.last_roll_sum, 'outcome': outcome_str, 'winnings': winnings}

        else: # Place a bet action
            bet_type_to_place = self._action_idx_to_bet_type.get(action_type_idx)

            if bet_type_to_place is None: # Should ideally not be hit with a valid policy
                reward = -10.0 # Severe penalty for invalid action index
                info = {"error": f"Invalid action_type_idx {action_type_idx} mapped to no BetType."}
                # Observation is returned below, no game state change here.
            else:
                bet_amount_to_place = self.bet_amount_options[bet_amount_level_idx]

                # Attempt to place the bet in the game logic
                bet_placed_successfully, actual_bet_amount_placed = self.game.place_bet(
                    bet_type_to_place, bet_amount_to_place, self.player_bankroll
                )

                if bet_placed_successfully:
                    self.player_bankroll -= float(actual_bet_amount_placed)
                    # Reward for placing a valid bet is 0. Main reward comes from roll outcomes.
                    info = {
                        'bet_type_placed': bet_type_to_place.name,
                        'bet_amount_placed': actual_bet_amount_placed,
                        'bet_successful': True
                    }
                else:
                    # Penalty for attempting an invalid bet (e.g., wrong timing, insufficient funds)
                    reward = -1.0
                    info = {
                        'bet_type_attempted': bet_type_to_place.name,
                        'bet_amount_attempted': bet_amount_to_place,
                        'bet_successful': False,
                        'error': 'Bet rejected by game logic (e.g., timing, funds, existing bets)'
                    }

        # 5. Check for termination condition (bankruptcy)
        if self.player_bankroll <= 0:
            terminated = True
            # Optional: additional penalty for going bankrupt can be added to `reward` here
            # e.g., reward -= self.initial_bankroll
            info['status'] = "Bankrupted"

        # 6. Get the new observation
        observation = self._get_observation()

        if self.render_mode == "human":
            self.render()

        return observation, reward, terminated, truncated, info

    def render(self):
        if self.render_mode == 'human':
            print(f"\nBankroll: ${self.player_bankroll:.2f}")
            print(f"Is Come-Out: {self.game.is_come_out_roll}, Point: {self.game.point if self.game.point else 'None'}")
            if self.last_roll_sum > 0:
                print(f"Last Roll: {self.last_dice} = {self.last_roll_sum}")

            active_bets_str = []
            for bet_info in self.game.get_active_bets(): # bet_info is a dict
                s = f"  - {bet_info['type'].name}: ${bet_info['amount']}"
                if 'point_for_odds' in bet_info and bet_info['point_for_odds']:
                    s += f" (Point: {bet_info['point_for_odds']})"
                active_bets_str.append(s)

            if active_bets_str:
                print("Active Bets:")
                for s_bet in active_bets_str:
                    print(s_bet)
            else:
                print("No active bets.")
            print("-" * 30)

    def close(self):
        pass

if __name__ == '__main__':
    env = CrapsEnv(render_mode='human')
    obs, info = env.reset()

    pass_line_action_idx = env._bet_type_to_action_idx[BetType.PASS_LINE]
    bet_amount_idx = 2 # Corresponds to $10 from self.bet_amount_options

    action = {"action_type": pass_line_action_idx, "bet_amount_level": bet_amount_idx}
    print(f"Action: Place PASS_LINE (${env.bet_amount_options[bet_amount_idx]})")
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Reward: {reward:.2f}, Terminated: {terminated}, Truncated: {truncated}, Info: {info}")

    action = {"action_type": 0, "bet_amount_level": 0}
    print(f"\nAction: Roll Dice")
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Reward: {reward:.2f}, Terminated: {terminated}, Truncated: {truncated}, Info: {info}")

    if not env.game.is_come_out_roll and env.game.point is not None and not terminated:
        pass_odds_action_idx = env._bet_type_to_action_idx[BetType.PASS_ODDS]
        odds_bet_amount_idx = 3 # $20
        action = {"action_type": pass_odds_action_idx, "bet_amount_level": odds_bet_amount_idx}
        print(f"\nAction: Place PASS_ODDS (${env.bet_amount_options[odds_bet_amount_idx]}) on Point {env.game.point}")
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Reward: {reward:.2f}, Terminated: {terminated}, Truncated: {truncated}, Info: {info}")

    if not terminated:
        action = {"action_type": 0, "bet_amount_level": 0}
        print(f"\nAction: Roll Dice")
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Reward: {reward:.2f}, Terminated: {terminated}, Truncated: {truncated}, Info: {info}")

    if terminated:
        print("\nGAME OVER!")
    env.close()
