# Craps RL Environment

## Overview

A reinforcement learning environment for the game of Craps, built using the Gymnasium API. This environment allows AI agents to learn and test various Craps betting strategies by interacting with a simulated game.

## Features

*   Implements standard Craps game rules.
*   Supports multiple bet types:
    *   Pass Line
    *   Don't Pass
    *   Pass Odds
    *   Don't Pass Odds
*   Detailed observation space providing comprehensive game state information (point, come-out roll status, bankroll, active bets, last roll).
*   Nuanced action space allowing agents to decide whether to roll or place different types of bets with varying amounts.
*   Configurable initial bankroll for the agent.
*   Includes unit tests for ensuring the reliability of the environment's mechanics.
*   Provides an example script (`craps_rl/main.py`) for a quick start on how to use the environment.

## Project Structure

```
craps-rl/
├── craps_rl/
│   ├── env/
│   │   ├── __init__.py
│   │   ├── craps_env.py    # Main Gymnasium environment class (CrapsEnv)
│   │   └── craps_game.py   # Core Craps game logic, bet types, and resolution (CrapsGame)
│   ├── ga/                 # (Placeholder for Genetic Algorithm components)
│   │   ├── __init__.py
│   │   └── genetic_algorithm.py # Example GA structure (if provided by other tasks)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_craps_env.py # Unit tests for CrapsEnv
│   │   └── test_craps_game.py# Unit tests for CrapsGame (if provided by other tasks)
│   ├── __init__.py
│   └── main.py             # Example script demonstrating environment usage
├── main                    # Standalone GA script (separate from craps_rl package)
├── README.md               # This file
└── ... (other project files like a LICENSE if added)
```

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd craps-rl
    ```
2.  **Install required Python packages**:
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install gymnasium numpy
    ```

## Usage

### Basic Example

Here's a minimal example of how to interact with the `CrapsEnv`:

```python
from craps_rl.env.craps_env import CrapsEnv
import numpy as np # For accessing bankroll if it's a numpy array in obs

# Initialize the environment
env = CrapsEnv(initial_bankroll=100.0)

# Reset the environment for a new episode
observation, info = env.reset(seed=42) # Use a seed for reproducibility
print(f"Initial Observation: {observation}")
# Bankroll is a Box space, access its value with [0]
print(f"Initial Bankroll: {observation['bankroll'][0]:.2f}")

# Game loop (example for one step with a random action)
action = env.action_space.sample() # Get a random action from the action space
print(f"Taking action: {action}")

observation, reward, terminated, truncated, info = env.step(action)

print(f"New Observation: {observation}")
print(f"Reward: {reward:.2f}")
print(f"Bankroll: {observation['bankroll'][0]:.2f}")
print(f"Terminated: {terminated}, Truncated: {truncated}")
if info.get('error'):
    print(f"Info/Error: {info['error']}")

env.close()
```

For a more detailed runnable example, see `craps_rl/main.py`. You can run it from the root directory of the project using:
```bash
python -m craps_rl.main
```

## Action Space

The action space is a `gymnasium.spaces.Dict` with the following components:

*   **`action_type`** (`spaces.Discrete`): An integer determining the type of action.
    *   `0`: Roll Dice
    *   `1`: Place Pass Line Bet
    *   `2`: Place Don't Pass Bet
    *   `3`: Place Pass Odds Bet
    *   `4`: Place Don't Pass Odds Bet
    *(The environment internally maps these integer indices to `BetType` enum members defined in `craps_game.py`)*
*   **`bet_amount_level`** (`spaces.Discrete`): An integer index corresponding to predefined bet amounts (e.g., `[1, 5, 10, 20, 50, 100]`). This component is ignored if `action_type` is "Roll Dice".

The environment uses the `action_type` to select the bet (or roll) and `bet_amount_level` to determine the wager amount from its predefined `bet_amount_options` array.

## Observation Space

The observation space is also a `gymnasium.spaces.Dict`, providing the agent with the following information about the game state:

*   **`point`** (`spaces.Discrete(11)`): The currently established point. `0` means no point is established. Otherwise, it will be `4, 5, 6, 8, 9,` or `10`.
*   **`is_come_out_roll`** (`spaces.Discrete(2)`): `1` if the next roll is a come-out roll, `0` otherwise.
*   **`bankroll`** (`spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32)`): The agent's current bankroll.
*   **`last_roll_sum`** (`spaces.Discrete(13)`): The sum of the dice from the most recent roll. `0` if no roll has occurred in the current game episode, otherwise `2` through `12`.
*   **`pass_line_amount`** (`spaces.Box(shape=(1,), ...)`): Current amount wagered on the Pass Line. `0` if no active Pass Line bet.
*   **`dont_pass_amount`** (`spaces.Box(shape=(1,), ...)`): Current amount wagered on the Don't Pass Line. `0` if no active Don't Pass bet.
*   **`pass_odds_amount`** (`spaces.Box(shape=(1,), ...)`): Current amount wagered on Pass Odds. `0` if no active Pass Odds bet.
*   **`pass_odds_point`** (`spaces.Discrete(11)`): The point number (4-10) to which the current Pass Odds bet is tied. `0` if no active Pass Odds bet.
*   **`dont_pass_odds_amount`** (`spaces.Box(shape=(1,), ...)`): Current amount wagered on Don't Pass Odds. `0` if no active Don't Pass Odds bet.
*   **`dont_pass_odds_point`** (`spaces.Discrete(11)`): The point number (4-10) to which the current Don't Pass Odds bet is tied. `0` if no active Don't Pass Odds bet.

*(All `spaces.Box` amounts are `dtype=np.float32` and have `low=0, high=np.inf`)*

## Reward System

The environment's reward system is designed to directly reflect game outcomes:

*   **Rolling Dice**: When the agent chooses to roll the dice, the reward returned is the **net total winnings** from all active bets that were resolved on that roll. This can be positive (if bets won more than they lost), negative (if bets lost more than they won), or zero (if no bets were active or winnings equaled losses).
*   **Placing a Valid Bet**: If the agent places a bet that is valid according to game rules and bankroll, the reward is `0`. The cost of the bet is immediately deducted from the agent's bankroll at the time of placement.
*   **Attempting an Invalid Bet**: If the agent attempts to place an invalid bet (e.g., betting Pass Line when a point is already established, betting odds without a corresponding line bet, betting Pass Odds on the come-out roll, or attempting to bet more than the available bankroll at a chosen level), a small negative reward (currently `-1.0`) is given. This penalizes the agent for taking an invalid action, and the bankroll remains unchanged by this attempt.

## Testing

Unit tests are provided to ensure the environment functions correctly. They are located in the `craps_rl/tests/` directory.

To run the tests, navigate to the root directory of the project and execute:
```bash
python -m unittest discover craps_rl/tests -v
```
(The `-v` flag enables verbose output.)

## License

This project is licensed under the MIT License. (Note: A LICENSE file would typically accompany this statement if one is formally included in the repository.)
