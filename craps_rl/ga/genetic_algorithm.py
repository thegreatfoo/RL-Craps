import random
# from ..env.craps_env import CrapsEnv # To be used when fitness function is fully implemented

# --- Strategy Representation Definition ---
# A strategy is represented as a dictionary:
# {
#     "pass_line_bet_unit": float,  # Base amount to bet on the Pass Line (e.g., in dollars).
#                                   # For simplicity, this is a fixed amount per game/session.
#     "max_odds_multiplier": int    # Maximum odds multiplier to take on a Pass Line bet
#                                   # after a point is established.
#                                   # E.g., 0 (no odds), 1 (1x odds), 2 (2x odds), etc.
#                                   # The actual odds taken might be limited by the point (e.g., 3-4-5x odds).
# }
#
# Simplifications for this initial version:
# - The strategy always bets the "pass_line_bet_unit" on the Pass Line if it's a come-out roll.
# - If a point is established, the strategy always attempts to take odds up to
#   "max_odds_multiplier" times the pass_line_bet_unit, respecting table limits
#   (which will be part of the environment's handling of bets).
# - More complex conditions (e.g., varying bet size by bankroll percentage,
#   not betting on certain points, other bet types like Come bets, Don't Pass)
#   will be introduced in later iterations.

def create_random_strategy(min_bet_unit: float = 5.0, max_bet_unit: float = 50.0, max_allowable_odds: int = 3) -> dict:
    """
    Generates a random strategy dictionary.

    Args:
        min_bet_unit (float): Minimum base unit for the Pass Line bet.
        max_bet_unit (float): Maximum base unit for the Pass Line bet.
        max_allowable_odds (int): The highest possible odds multiplier the strategy can choose.
                                  Actual odds taken might be lower based on table rules for specific points.

    Returns:
        dict: A randomly generated strategy.
    """
    pass_line_bet_unit = round(random.uniform(min_bet_unit, max_bet_unit), 2) # Rounded to 2 decimal places
    max_odds_multiplier = random.randint(0, max_allowable_odds)

    return {
        "pass_line_bet_unit": pass_line_bet_unit,
        "max_odds_multiplier": max_odds_multiplier
    }

def initialize_population(population_size: int,
                          min_bet_unit: float = 5.0,
                          max_bet_unit: float = 50.0,
                          max_allowable_odds: int = 3) -> list[dict]:
    """
    Creates an initial population of random strategies.

    Args:
        population_size (int): The number of strategies in the population.
        min_bet_unit (float): Minimum base unit for Pass Line bets in strategies.
        max_bet_unit (float): Maximum base unit for Pass Line bets in strategies.
        max_allowable_odds (int): Maximum odds multiplier for strategies.

    Returns:
        list[dict]: A list of strategy dictionaries.
    """
    population = []
    for _ in range(population_size):
        population.append(create_random_strategy(min_bet_unit, max_bet_unit, max_allowable_odds))
    return population

def calculate_fitness(strategy: dict, env: 'CrapsEnv', num_games: int = 100, num_rolls_per_game: int = 50) -> float:
    """
    Calculates the fitness of a given strategy by simulating games in the Craps environment.

    Args:
        strategy (dict): The strategy to evaluate.
        env ('CrapsEnv'): The Craps environment instance to use for simulation.
                          Note: The environment must be capable of interpreting the strategy
                          to place bets. This function assumes `env.step` or a related
                          mechanism handles bet placement based on the strategy.
        num_games (int): The number of full games to simulate.
        num_rolls_per_game (int): The maximum number of rolls for each game if it doesn't
                                  terminate due to bankroll depletion.

    Returns:
        float: The calculated fitness score (e.g., average profit per game or final bankroll).

    Placeholder Note:
    The actual implementation of this function requires `CrapsEnv` to be extended
    to handle actions related to placing bets according to the `strategy` dictionary.
    Currently, `env.step()` only knows about "roll_dice".
    The logic below is a high-level placeholder for how it might work.
    """
    total_net_gain = 0.0
    # initial_bankroll_for_eval = env.initial_bankroll # Assuming env resets bankroll correctly

    for _ in range(num_games):
        # Ensure environment is reset for each game, including bankroll
        # The passed 'env' might be a single instance reused, so reset is crucial.
        # Or, a fresh env copy could be made for each call if state between calls is an issue.
        current_obs, info = env.reset()
        # env.bankroll should be at initial_bankroll after reset.
        bankroll_at_game_start = env.bankroll

        for _ in range(num_rolls_per_game):
            # --- Decision Making (Conceptual - to be implemented in Env) ---
            # 1. Determine bets based on `strategy` and `current_obs`.
            #    Example: If `current_obs['is_come_out_roll']` is True,
            #             place Pass Line bet of `strategy['pass_line_bet_unit']`.
            #             If a point is established, place odds up to `strategy['max_odds_multiplier']`.
            #
            # 2. Communicate these bets to the environment.
            #    This might involve a new `env.place_bets(bet_actions)` method before `env.step("roll_dice")`,
            #    or `env.step()` could take a more complex action object that includes bets.
            #
            # For now, we assume the environment somehow uses the strategy internally
            # when "roll_dice" is called, or bets are placed implicitly.
            # This is the MAJOR part that needs future implementation in CrapsEnv.

            # --- Action ---
            # The only physical action the agent/player takes is to roll the dice.
            # Bets are considered placed *before* the roll.
            action_to_take = "roll_dice"

            # Pass the strategy to step, or have env store current strategy
            # For now, assuming env.step is not yet strategy-aware
            current_obs, reward, terminated, truncated, info = env.step(action_to_take)

            # `reward` in this placeholder env.step is 0.
            # Actual reward would be calculated in env.step based on resolved bets.

            if terminated or truncated:
                break

        # Calculate profit/loss for this game
        game_net_gain = env.bankroll - bankroll_at_game_start
        total_net_gain += game_net_gain

    average_net_gain_per_game = total_net_gain / num_games
    return average_net_gain_per_game


# --- Evolutionary Operator Placeholders ---

def selection(population: list[dict], fitnesses: list[float], num_parents: int) -> list[dict]:
    """
    Selects the best strategies from the population to serve as parents.
    (Placeholder - more sophisticated selection methods like tournament or roulette wheel can be used)
    """
    # Simple Elitism: Sort by fitness and pick the top num_parents
    sorted_population = [strat for _, strat in sorted(zip(fitnesses, population), key=lambda x: x[0], reverse=True)]
    return sorted_population[:num_parents]

def crossover(parent1: dict, parent2: dict) -> dict:
    """
    Combines two parent strategies to create an offspring strategy.
    (Placeholder - various crossover techniques exist)
    """
    offspring = {}
    # Example: Average bet unit, randomly pick odds multiplier
    offspring["pass_line_bet_unit"] = round((parent1["pass_line_bet_unit"] + parent2["pass_line_bet_unit"]) / 2, 2)
    offspring["max_odds_multiplier"] = random.choice([parent1["max_odds_multiplier"], parent2["max_odds_multiplier"]])
    return offspring

def mutate(strategy: dict,
           mutation_rate: float,
           min_bet_unit: float = 5.0,
           max_bet_unit: float = 50.0,
           max_allowable_odds: int = 3,
           mutation_strength_bet: float = 0.1,
           mutation_strength_odds: int = 1) -> dict:
    """
    Randomly alters parts of a strategy.
    (Placeholder - more nuanced mutation operators can be designed)
    """
    mutated_strategy = strategy.copy()

    # Mutate pass_line_bet_unit
    if random.random() < mutation_rate:
        change = random.uniform(-max_bet_unit * mutation_strength_bet, max_bet_unit * mutation_strength_bet)
        mutated_strategy["pass_line_bet_unit"] = round(max(min_bet_unit, min(max_bet_unit, mutated_strategy["pass_line_bet_unit"] + change)),2)

    # Mutate max_odds_multiplier
    if random.random() < mutation_rate:
        change = random.choice([-mutation_strength_odds, mutation_strength_odds])
        mutated_strategy["max_odds_multiplier"] = max(0, min(max_allowable_odds, mutated_strategy["max_odds_multiplier"] + change))

    return mutated_strategy
