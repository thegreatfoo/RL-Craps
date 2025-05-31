import random
from enum import Enum

class BetType(Enum):
    PASS_LINE = "PASS_LINE"
    DONT_PASS = "DONT_PASS"
    PASS_ODDS = "PASS_ODDS"
    DONT_PASS_ODDS = "DONT_PASS_ODDS"
    # COME = "COME" # Stretch goal
    # DONT_COME = "DONT_COME" # Stretch goal

class CrapsGame:
    def __init__(self):
        self.point = None
        self.is_come_out_roll = True
        # self.active_bets stores dicts: {'type': BetType, 'amount': int, 'point_for_odds': int | None}
        self.active_bets = []
        # self.payouts was mentioned but task asks roll_dice to return total_winnings directly.
        # So, self.payouts might not be needed in the class state if it's just a per-roll calculation.

    def place_bet(self, bet_type: BetType, amount: int, player_bankroll: int) -> tuple[bool, int]:
        if not isinstance(bet_type, BetType):
            # print("Invalid bet type object.")
            return False, 0
        if amount <= 0:
            # print("Bet amount must be positive.")
            return False, 0
        if amount > player_bankroll:
            # print("Insufficient bankroll.")
            return False, 0

        valid_bet = False
        if self.is_come_out_roll:
            if bet_type in [BetType.PASS_LINE, BetType.DONT_PASS]:
                valid_bet = True
        else: # Point is established
            if bet_type == BetType.PASS_ODDS:
                # Check for existing Pass Line bet on the current point
                if any(b['type'] == BetType.PASS_LINE and b.get('point_for_odds') == self.point for b in self.active_bets):
                    valid_bet = True
            elif bet_type == BetType.DONT_PASS_ODDS:
                # Check for existing Don't Pass bet on the current point
                if any(b['type'] == BetType.DONT_PASS and b.get('point_for_odds') == self.point for b in self.active_bets):
                    valid_bet = True
            # Cannot place new PASS_LINE or DONT_PASS when point is established.

        if not valid_bet:
            # print(f"Invalid bet type {bet_type.name} for current game state (Come-out: {self.is_come_out_roll}, Point: {self.point}).")
            return False, 0

        new_bet = {'type': bet_type, 'amount': amount}
        # If odds bet, it's inherently tied to the current point.
        # If Pass/Don't Pass, point_for_odds will be set when a point is established.
        if bet_type in [BetType.PASS_ODDS, BetType.DONT_PASS_ODDS]:
            new_bet['point_for_odds'] = self.point

        self.active_bets.append(new_bet)
        return True, amount

    def _get_true_odds_payout(self, bet_amount: int, point: int, is_pass_odds: bool) -> int:
        if point in [4, 10]:
            odds = 2/1 if is_pass_odds else 1/2
        elif point in [5, 9]:
            odds = 3/2 if is_pass_odds else 2/3
        elif point in [6, 8]:
            odds = 6/5 if is_pass_odds else 5/6
        else:
            return 0 # Should not happen for valid odds points
        return int(bet_amount * odds)

    def _resolve_bets(self, roll_sum: int, outcome: str, current_point_for_roll: int | None, was_come_out_roll: bool) -> int:
        total_winnings = 0
        resolved_bet_indices = []

        for i, bet in enumerate(self.active_bets):
            bet_type = bet['type']
            amount = bet['amount']
            bet_wins = 0
            bet_resolved_this_roll = False

            if bet_type == BetType.PASS_LINE:
                if was_come_out_roll:
                    if outcome == "natural":
                        bet_wins = amount
                        bet_resolved_this_roll = True
                    elif outcome == "craps":
                        bet_wins = -amount
                        bet_resolved_this_roll = True
                    elif outcome == "point_established":
                        # Bet continues, associate the established point with this bet
                        bet['point_for_odds'] = current_point_for_roll # current_point_for_roll is the new point
                else: # Point was established before this roll
                    if outcome == "point_hit" and current_point_for_roll == bet.get('point_for_odds'):
                        bet_wins = amount
                        bet_resolved_this_roll = True
                    elif outcome == "seven_out":
                        bet_wins = -amount
                        bet_resolved_this_roll = True

            elif bet_type == BetType.DONT_PASS:
                if was_come_out_roll:
                    if outcome == "natural":
                        bet_wins = -amount
                        bet_resolved_this_roll = True
                    elif outcome == "craps":
                        if roll_sum in [2, 3]:
                            bet_wins = amount
                        elif roll_sum == 12: # Push
                            bet_wins = 0
                        bet_resolved_this_roll = True
                    elif outcome == "point_established":
                        bet['point_for_odds'] = current_point_for_roll # current_point_for_roll is the new point
                else: # Point was established
                    if outcome == "point_hit" and current_point_for_roll == bet.get('point_for_odds'):
                        bet_wins = -amount
                        bet_resolved_this_roll = True
                    elif outcome == "seven_out":
                        bet_wins = amount
                        bet_resolved_this_roll = True

            elif bet_type == BetType.PASS_ODDS:
                # Odds bets are only active if a point was established and matches their 'point_for_odds'
                if not was_come_out_roll and bet.get('point_for_odds') == current_point_for_roll:
                    if outcome == "point_hit":
                        bet_wins = self._get_true_odds_payout(amount, current_point_for_roll, True)
                        bet_resolved_this_roll = True
                    elif outcome == "seven_out":
                        bet_wins = -amount
                        bet_resolved_this_roll = True

            elif bet_type == BetType.DONT_PASS_ODDS:
                if not was_come_out_roll and bet.get('point_for_odds') == current_point_for_roll:
                    if outcome == "seven_out":
                        bet_wins = self._get_true_odds_payout(amount, current_point_for_roll, False)
                        bet_resolved_this_roll = True
                    elif outcome == "point_hit":
                        bet_wins = -amount
                        bet_resolved_this_roll = True

            if bet_resolved_this_roll:
                total_winnings += bet_wins
                resolved_bet_indices.append(i)

        for index in sorted(resolved_bet_indices, reverse=True):
            del self.active_bets[index]

        return total_winnings

    def roll_dice(self) -> tuple[int, int, int, str | None, int]:
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        roll_sum = die1 + die2

        outcome_str = None
        was_come_out_roll_for_this_turn = self.is_come_out_roll
        point_for_this_turn = self.point

        if was_come_out_roll_for_this_turn:
            if roll_sum in [7, 11]:
                outcome_str = "natural"
            elif roll_sum in [2, 3, 12]:
                outcome_str = "craps"
            else:
                outcome_str = "point_established"
                self.point = roll_sum # Point is set now
                self.is_come_out_roll = False
        else: # Point was established
            if roll_sum == self.point:
                outcome_str = "point_hit"
                self.is_come_out_roll = True
                self.point = None
            elif roll_sum == 7:
                outcome_str = "seven_out"
                self.is_come_out_roll = True
                self.point = None
            else:
                outcome_str = "neutral"

        # Resolve bets using the game state *as it was at the start of this roll*
        # For outcome "point_established", the point passed to _resolve_bets should be the new point.
        # For other outcomes, it's the existing point.
        point_for_resolution = self.point if outcome_str == "point_established" else point_for_this_turn

        winnings = self._resolve_bets(roll_sum, outcome_str, point_for_resolution, was_come_out_roll_for_this_turn)

        return die1, die2, roll_sum, outcome_str, winnings

    def get_active_bets(self):
        return list(self.active_bets) # Return a copy

    def clear_bets(self):
        self.active_bets = []

    def reset_game(self):
        self.point = None
        self.is_come_out_roll = True
        self.clear_bets()

# Example Usage (Illustrative)
if __name__ == '__main__':
    game = CrapsGame()
    bankroll = 1000
    print(f"Initial state: Come-out: {game.is_come_out_roll}, Point: {game.point}, Bankroll: ${bankroll}")

    # Game Loop Example
    for i in range(3): # Play 3 full rounds (come-out to point resolution or vice-versa)
        print(f"\n--- ROUND {i+1} ---")
        game.reset_game() # Ensure clean state for a full round, though roll_dice handles point resets.
                         # For this loop, let's manually reset to ensure it's a new "shooter"
        print(f"Start of Round. CO: {game.is_come_out_roll}, P: {game.point}, Bankroll: ${bankroll}, Active Bets: {game.get_active_bets()}")

        # Come-out bet
        bet_placed, bet_amt = game.place_bet(BetType.PASS_LINE, 10, bankroll)
        if bet_placed:
            bankroll -= bet_amt
            print(f"Placed $10 Pass Line. Bankroll: ${bankroll}, Bets: {game.get_active_bets()}")
        else:
            print("Could not place Pass Line bet.")
            continue

        roll_count_in_round = 0
        while True:
            roll_count_in_round += 1
            print(f"\nRoll {roll_count_in_round} (CO: {game.is_come_out_roll}, P: {game.point})")
            d1, d2, r_sum, outcome, W = game.roll_dice()
            bankroll += W
            print(f"Dice: {d1}+{d2}={r_sum}. Outcome: {outcome}. Winnings for this roll: ${W}. Bankroll: ${bankroll}")
            print(f"Game state after roll: CO: {game.is_come_out_roll}, P: {game.point}, Active Bets: {game.get_active_bets()}")

            if outcome == "point_established":
                print(f"Point is now {game.point}. Placing $10 Pass Odds.")
                bet_placed, bet_amt = game.place_bet(BetType.PASS_ODDS, 10, bankroll) # 1x odds
                if bet_placed:
                    bankroll -= bet_amt
                    print(f"Placed $10 Pass Odds. Bankroll: ${bankroll}, Bets: {game.get_active_bets()}")
                else:
                    print(f"Could not place Pass Odds on point {game.point}. Bets: {game.get_active_bets()}")

            # Check if round ends (back to come-out roll)
            if game.is_come_out_roll and outcome not in ["point_established", "neutral"]:
                # "neutral" shouldn't happen if is_come_out_roll is true post-roll, but defensive check.
                # "point_established" means it *was* a come-out, but now point is set.
                # If outcome is natural, craps, point_hit, seven_out, the round effectively ends or resets state.
                if outcome in ["natural", "craps"]: # Resolved on come-out, next is also come-out
                    print("Come-out roll resolved (Natural/Craps). Next roll is a new come-out.")
                    break
                elif outcome in ["point_hit", "seven_out"]: # Point resolved
                    print("Point resolved (Hit/Seven-Out). Next roll is a new come-out.")
                    break

            if roll_count_in_round > 10: # Safety break for the example loop
                print("Reached max rolls for this round example.")
                break

        print(f"End of ROUND {i+1}. Final bankroll for round: ${bankroll}")

    print(f"\n--- Don't Pass Example ---")
    game.reset_game()
    bankroll = 100 # Reset bankroll for this example
    print(f"Start of Don't Pass. CO: {game.is_come_out_roll}, P: {game.point}, Bankroll: ${bankroll}")
    bet_placed, bet_amt = game.place_bet(BetType.DONT_PASS, 10, bankroll)
    if bet_placed:
        bankroll -= bet_amt
        print(f"Placed $10 Don't Pass. Bankroll: ${bankroll}, Bets: {game.get_active_bets()}")

    # Simulate one roll
    d1, d2, r_sum, outcome, W = game.roll_dice()
    bankroll += W
    print(f"Dice: {d1}+{d2}={r_sum}. Outcome: {outcome}. Winnings: ${W}. Bankroll: ${bankroll}")
    print(f"Game state: CO: {game.is_come_out_roll}, P: {game.point}, Bets: {game.get_active_bets()}")

    if outcome == "point_established":
        print(f"Point is {game.point}. Placing $10 Don't Pass Odds.")
        # For DONT_PASS_ODDS, the point_for_odds in the bet must match game.point
        # The place_bet logic should handle this correctly.
        bet_placed, bet_amt = game.place_bet(BetType.DONT_PASS_ODDS, 10, bankroll)
        if bet_placed:
            bankroll -= bet_amt
            print(f"Placed $10 Don't Pass Odds. Bankroll: ${bankroll}, Bets: {game.get_active_bets()}")
        else:
            print(f"Could not place Don't Pass Odds. Bets: {game.get_active_bets()}")

        # Simulate another roll
        d1, d2, r_sum, outcome, W = game.roll_dice()
        bankroll += W
        print(f"Dice: {d1}+{d2}={r_sum}. Outcome: {outcome}. Winnings: ${W}. Bankroll: ${bankroll}")
        print(f"Game state: CO: {game.is_come_out_roll}, P: {game.point}, Bets: {game.get_active_bets()}")
