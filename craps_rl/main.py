from craps_rl.env.craps_env import CrapsEnv
import numpy as np # For accessing bankroll if it's a numpy array

def run_craps_example():
    """Runs a basic example of interacting with the CrapsEnv."""
    print("Starting Craps Environment Example...\n")
    # Use a float for initial_bankroll as CrapsEnv now expects it
    env = CrapsEnv(initial_bankroll=100.0)

    num_episodes = 3
    max_steps_per_episode = 50 # Increased for a bit more interaction

    for episode in range(num_episodes):
        print(f"\n--- Episode {episode + 1} ---")
        # Vary seed per episode for potentially different outcomes if game was fully seeded
        obs, info = env.reset(seed=42 + episode)

        # Access bankroll correctly from the observation dictionary space
        # CrapsEnv stores bankroll as a float, but observation space wraps it in a Box (np.ndarray)
        initial_bankroll_obs = obs['bankroll'][0] if isinstance(obs['bankroll'], np.ndarray) else obs['bankroll']
        print(f"Initial Observation Keys: {list(obs.keys())}") # To confirm keys
        print(f"Initial Bankroll from Obs: {initial_bankroll_obs:.2f}")
        print(f"Initial Point: {obs['point']}, Is Come-Out: {obs['is_come_out_roll']}")

        terminated = False
        truncated = False # CrapsEnv doesn't use truncation based on step limit internally
        total_reward_episode = 0.0
        steps = 0

        while not terminated and not truncated and steps < max_steps_per_episode:
            action = env.action_space.sample() # Take a random action

            print(f"\nStep {steps + 1}:")
            # Decoding the action for printing can be helpful
            action_type_str = "Roll Dice"
            bet_type_placed_str = "N/A"
            bet_amount_str = "N/A"

            if action["action_type"] != 0: # It's a bet action
                bet_type_action_idx = action["action_type"]
                # Find the BetType enum member corresponding to the action_idx
                # This relies on _action_idx_to_bet_type existing in env, which it does.
                bet_type_enum = env._action_idx_to_bet_type.get(bet_type_action_idx)
                if bet_type_enum:
                    action_type_str = f"Bet: {bet_type_enum.name}"
                    bet_type_placed_str = bet_type_enum.name
                else:
                    action_type_str = f"Bet: Unknown type {bet_type_action_idx}" # Should not happen

                bet_amount_idx = action["bet_amount_level"]
                actual_bet_amount = env.bet_amount_options[bet_amount_idx]
                bet_amount_str = f"${actual_bet_amount:.2f}"
                print(f"  Action: {action_type_str}, Amount Level Idx: {bet_amount_idx} ({bet_amount_str})")
            else:
                print(f"  Action: {action_type_str}")

            obs, reward, terminated, truncated, info = env.step(action)

            total_reward_episode += reward
            steps += 1

            current_bankroll_obs = obs['bankroll'][0] if isinstance(obs['bankroll'], np.ndarray) else obs['bankroll']
            print(f"  New Bankroll: {current_bankroll_obs:.2f} (Reward this step: {reward:.2f})")
            print(f"  New Point: {obs['point']}, Is Come-Out: {obs['is_come_out_roll']}")
            print(f"  Last Roll Sum: {obs['last_roll_sum']}")
            # print(f"  Full Observation: {obs}") # Can be very verbose
            if info.get('error'):
                print(f"  Info/Error: {info.get('error')}")
            if info.get('bet_successful') is False:
                 print(f"  Bet Attempted: {info.get('bet_type_attempted')} for ${info.get('bet_amount_attempted')}, Status: REJECTED")
            elif info.get('bet_successful') is True:
                 print(f"  Bet Placed: {info.get('bet_type_placed')} for ${info.get('bet_amount_placed')}")


            if terminated or truncated:
                print(f"\nEpisode finished after {steps} steps.")
                if info.get('status') == "Bankrupted":
                    print("Reason: Bankrupted!")
                break

        if not (terminated or truncated):
            print(f"\nEpisode reached max steps ({steps}).")

        final_bankroll_obs = obs['bankroll'][0] if isinstance(obs['bankroll'], np.ndarray) else obs['bankroll']
        print(f"End of Episode {episode + 1}:")
        print(f"  Final Bankroll: {final_bankroll_obs:.2f}")
        print(f"  Total Reward for Episode: {total_reward_episode:.2f}")

    env.close()
    print("\nCraps Environment Example Finished.")

if __name__ == "__main__":
    run_craps_example()
