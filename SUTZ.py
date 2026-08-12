import pygame
import sys
import random
import math
from typing import List, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CARD_WIDTH, CARD_HEIGHT = 70, 100
DICE_SIZE = 60  # Size for the dice
FPS = 30
CARD_SPACING = 10

# Colors
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
RED         = (255, 0, 0)
GOLD        = (255, 215, 0)
GRAY        = (128, 128, 128)
ORANGE      = (255, 140, 0)
GREEN       = (0, 255, 0)
BLUE        = (0, 0, 255)
PURPLE      = (128, 0, 128)
CYAN        = (0, 255, 255)
NEON_PINK   = (255, 51, 255)
NEON_GREEN  = (57, 255, 20)
NEON_BLUE   = (0, 255, 255)
NEON_YELLOW = (255, 255, 0)
NEON_ORANGE = (255, 127, 0)
LIGHT_GRAY  = (220, 220, 220)

# Chip Constants
CHIP_RADIUS = 20
CHIP_VALUES = [10, 20, 50, 100, 200]
CHIP_COLORS = [NEON_PINK, NEON_GREEN, NEON_BLUE, NEON_YELLOW, NEON_ORANGE]
WALLET_AMOUNT = 1000

# Triangle Constants
TRIANGLE_SIZE = 80
TRIANGLE_BORDER = 4

# Set up the display (deferred when embedded in Casino Sfeer menu)
screen = None


def _init_display(caption="Su'tz"):
    global screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(caption)
    return screen

class Dice:
    # Updated to include two blank sides.
    SUITS = ['♠', '♥', '♦', '♣', '', '']
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = DICE_SIZE
        self.value = random.choice(self.SUITS)
        self.rolling = False
        self.roll_start_time = 0
        self.roll_duration = 1500  # 1.5 seconds roll duration
        self.color = RED if self.value in ['♥', '♦'] else BLACK
        # Shake animation properties
        self.shake_magnitude = 5  # maximum offset for shaking
        self.offset_x = 0
        self.offset_y = 0
        # Timing for suit change during rolling
        self.last_suit_change = 0
        self.suit_change_interval = 100  # ms between suit changes

    def roll(self):
        self.rolling = True
        self.roll_start_time = pygame.time.get_ticks()
        self.offset_x = 0
        self.offset_y = 0

    def update(self):
        if self.rolling:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.roll_start_time
            self.offset_x = random.randint(-self.shake_magnitude, self.shake_magnitude)
            self.offset_y = random.randint(-self.shake_magnitude, self.shake_magnitude)
            if current_time - self.last_suit_change >= self.suit_change_interval:
                self.value = random.choice(self.SUITS)
                self.color = RED if self.value in ['♥', '♦'] else BLACK
                self.last_suit_change = current_time
            if elapsed >= self.roll_duration:
                self.rolling = False
                self.value = random.choice(self.SUITS)
                self.color = RED if self.value in ['♥', '♦'] else BLACK
                self.offset_x = 0
                self.offset_y = 0

    def draw(self):
        pos_x = self.x + self.offset_x
        pos_y = self.y + self.offset_y
        pygame.draw.rect(screen, WHITE, (pos_x, pos_y, self.size, self.size))
        pygame.draw.rect(screen, BLACK, (pos_x, pos_y, self.size, self.size), 2)
        # Only render text if the dice face is not blank.
        if self.value:
            font = pygame.font.Font(pygame.font.match_font("arial"), 36)
            text_surf = font.render(self.value, True, self.color)
            text_rect = text_surf.get_rect(center=(pos_x + self.size // 2, pos_y + self.size // 2))
            screen.blit(text_surf, text_rect)

class Card:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'Joker']

    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        # For Jokers, set color based on whether it's the first or second Joker
        # First Joker is RED, second Joker is BLACK
        if rank == 'Joker':
            # This will be determined when the deck is created
            self.color = BLACK
        else:
            self.color = RED if suit in ['♥', '♦'] else BLACK

    def flip(self):
        self.face_up = not self.face_up

    def __str__(self):
        return f"{self.rank}{self.suit}"

class Deck:
    def __init__(self):
        # Build three decks (each with 54 cards: 52 regular + 2 Jokers)
        self.cards = []
        for _ in range(3):  # Updated from 4 decks to 3 decks of cards
            for suit in Card.SUITS:
                for rank in Card.RANKS[:-1]:
                    self.cards.append(Card(suit, rank))
            # Create two Jokers with different colors per deck
            red_joker = Card('', 'Joker')
            red_joker.color = RED
            black_joker = Card('', 'Joker')
            black_joker.color = BLACK
            self.cards.append(red_joker)
            self.cards.append(black_joker)
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        if self.cards:
            return self.cards.pop()
        return None

    def cards_remaining(self) -> int:
        return len(self.cards)
        
    def shuffle_if_needed(self):
        """Shuffle the deck only if the number of cards is low."""
        # For three decks, there are 162 cards total.
        # Using a similar ratio as before, set the threshold to 72 (roughly 44% remaining).
        if len(self.cards) <= 72:
            self.cards = []
            for _ in range(3):  # Updated to rebuild 3 decks
                for suit in Card.SUITS:
                    for rank in Card.RANKS[:-1]:
                        self.cards.append(Card(suit, rank))
                # Create two Jokers with different colors per deck
                red_joker = Card('', 'Joker')
                red_joker.color = RED
                black_joker = Card('', 'Joker')
                black_joker.color = BLACK
                self.cards.append(red_joker)
                self.cards.append(black_joker)
            random.shuffle(self.cards)

class Chip:
    def __init__(self, value: int, x: int, y: int, color: tuple):
        self.value = value
        self.x = x
        self.y = y
        self.radius = CHIP_RADIUS
        self.color = color
        self.rect = pygame.Rect(x - CHIP_RADIUS, y - CHIP_RADIUS, CHIP_RADIUS * 2, CHIP_RADIUS * 2)

    def draw(self, is_active=False):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        border_color = RED if is_active else BLACK
        pygame.draw.circle(screen, border_color, (self.x, self.y), self.radius, 3)
        font = pygame.font.Font(None, 20)
        text_surf = font.render(f"£{self.value}", True, BLACK)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        screen.blit(text_surf, text_rect)

class BettingTriangle:
    """
    A triangle used as a betting button.
    """
    def __init__(self, x: int, y: int, size: int, label="S", orientation="upright"):
        self.x = x
        self.y = y
        self.size = size
        self.label = label
        self.rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        if orientation == "upright":
            self.points = [(x, y - size // 2), (x - size // 2, y + size // 2), (x + size // 2, y + size // 2)]
        elif orientation == "downward":
            self.points = [(x, y + size // 2), (x - size // 2, y - size // 2), (x + size // 2, y - size // 2)]
        else:
            self.points = [(x + size // 2, y), (x - size // 2, y - size // 2), (x - size // 2, y + size // 2)]
        self.current_bet = 0
        self.current_chip = None
        self.bet_history = []
        self.flash_color = None
        self.flash_start_time = 0
        self.flashing = False
        self.flash_duration = 500

    def draw(self):
        if self.flashing:
            pygame.draw.polygon(screen, self.flash_color, self.points, TRIANGLE_BORDER)
        else:
            pygame.draw.polygon(screen, BLACK, self.points, TRIANGLE_BORDER)
        centroid_x = sum(pt[0] for pt in self.points) / 3
        centroid_y = sum(pt[1] for pt in self.points) / 3
        font = pygame.font.Font(None, 36)
        label_surf = font.render(self.label, True, RED)
        label_rect = label_surf.get_rect(center=(centroid_x, centroid_y))
        screen.blit(label_surf, label_rect)
        if self.current_bet > 0:
            bet_font = pygame.font.Font(None, 24)
            bet_text = bet_font.render(f"£{self.current_bet}", True, RED)
            bottom_y = max(pt[1] for pt in self.points)
            bet_rect = bet_text.get_rect(midtop=(centroid_x, bottom_y + 5))
            screen.blit(bet_text, bet_rect)
        if self.current_chip:
            chip_x = int(centroid_x) + 1
            chip_y = int(centroid_y)
            pygame.draw.circle(screen, self.current_chip.color, (chip_x, chip_y), CHIP_RADIUS)
            pygame.draw.circle(screen, BLACK, (chip_x, chip_y), CHIP_RADIUS, 2)
            chip_font = pygame.font.Font(None, 20)
            chip_text = chip_font.render(f"£{self.current_chip.value}", True, BLACK)
            chip_rect = chip_text.get_rect(center=(chip_x, chip_y))
            screen.blit(chip_text, chip_rect)

    def place_bet(self, amount):
        self.current_bet += amount
        self.bet_history.append(amount)

    def place_chance_bet(self, amount):
        self.current_bet += amount
        self.bet_history.append(amount)

    def clear_bets(self):
        self.current_bet = 0
        self.bet_history.clear()
        self.current_chip = None

    def clear_bets_and_return(self):
        total = sum(self.bet_history)
        self.current_bet = 0
        self.bet_history.clear()
        self.current_chip = None
        return total

    def start_flash(self, color):
        self.flash_color = color
        self.flash_start_time = pygame.time.get_ticks()
        self.flashing = True

    def stop_flash(self):
        self.flashing = False

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class SutzGame:
    def __init__(self):
        self.deck = Deck()  # Three 54-card decks (162 cards total).
        self.dice = [Dice(SCREEN_WIDTH // 2 - 150 + i * (DICE_SIZE + 20), 70) for i in range(4)]
        self.player_hand: List[Card] = []
        # Game states: WAITING, PLAYING, ROLLING_DICE, FLIPPING_PLAYER, ROUND_OVER
        self.game_state = "WAITING"
        self.wallet = WALLET_AMOUNT
        self.chips = self.create_chips()
        self.betting_triangle = BettingTriangle(150, 380, TRIANGLE_SIZE, label="S", orientation="right")
        self.dealing_animation = False
        self.dealing_start_time = 0
        self.cards_to_deal = 6
        self.player_cards_revealed = False
        self.active_chip = None
        self.show_previous_round = False
        self.show_credits = False
        self.round_history = []
        self.player_flip_index = 0
        self.player_flip_order = [0, 1, 2, 3, 4, 5]
        self.last_flip_time = 0
        self.flip_interval = 500  # control card flip timing
        self.dice_roll_start = None
        # Variables for handling automatic re-roll when no suit qualifies.
        self.reroll_timer = None
        self.reroll_delay = 1000  # 1 second delay before auto re-roll
        self.num_rerolls = 0   # Track number of auto re-rolls (max 1)
        self.deal_initial_cards()

    def create_chips(self):
        chips_list = []
        start_y = 300
        for i, val in enumerate(CHIP_VALUES):
            chip_x = 50
            chip_y = start_y + i * (CHIP_RADIUS * 2 + 5)
            chips_list.append(Chip(val, chip_x, chip_y, CHIP_COLORS[i]))
        return chips_list

    def handle_chip_click(self, mouse_pos):
        for chip in self.chips:
            if chip.rect.collidepoint(mouse_pos):
                self.active_chip = None if self.active_chip == chip else chip
                return True
        return False

    def handle_betting_space_click(self, mouse_pos):
        if not self.betting_triangle.is_clicked(mouse_pos):
            return False
        if self.active_chip is None:
            return False
        self.betting_triangle.place_bet(self.active_chip.value)
        self.betting_triangle.current_chip = self.active_chip
        self.wallet -= self.active_chip.value
        self.active_chip = None
        return True

    def handle_wallet_click(self, mouse_pos):
        wallet_rect = pygame.Rect(40, 200, 100, 40)
        if wallet_rect.collidepoint(mouse_pos):
            self.show_credits = True

    def roll_all_dice(self):
        for die in self.dice:
            die.roll()
        # Reset reroll timer when starting a new roll
        self.reroll_timer = None

    def resolve_push(self, result_str, details):
        bet_amount = self.betting_triangle.current_bet
        if bet_amount > 0:
            self.wallet += bet_amount
        self.betting_triangle.clear_bets()
        self.betting_triangle.start_flash(GRAY)
        self.round_history.append({
            "player_hand": list(self.player_hand),
            "dice_values": [die.value for die in self.dice],
            "result": result_str,
            "winning_details": details
        })
        self.game_state = "ROUND_OVER"

    def reveal_player_cards(self):
        # This method flips all cards to face up.
        for card in self.player_hand:
            card.face_up = True
        self.player_cards_revealed = True

    def reset_game(self):
        self.deck.shuffle_if_needed()  # Shuffle the deck only if needed
        self.player_hand.clear()
        self.betting_triangle.stop_flash()
        self.betting_triangle.clear_bets()
        self.player_cards_revealed = False
        self.show_previous_round = False
        self.show_credits = False
        self.game_state = "PLAYING"
        self.player_flip_index = 0
        self.last_flip_time = 0
        self.num_rerolls = 0  # Reset the re-roll counter
        self.deal_initial_cards()

    def deal_initial_cards(self):
        self.player_hand.clear()
        self.dealing_animation = True
        self.dealing_start_time = pygame.time.get_ticks()
        for _ in range(self.cards_to_deal):
            c = self.deck.draw()
            if c:
                c.face_up = False
                self.player_hand.append(c)
        self.dealing_animation = False
        self.game_state = "PLAYING"

    def update_dealing_animation(self):
        if self.dealing_animation:
            now = pygame.time.get_ticks()
            if now - self.dealing_start_time > 500:
                self.dealing_animation = False
                self.game_state = "PLAYING"

    def update_flip_animation(self):
        # Only used if the round is not a loss condition.
        current_time = pygame.time.get_ticks()
        if self.game_state == "FLIPPING_PLAYER":
            if self.player_flip_index < len(self.player_flip_order):
                if current_time - self.last_flip_time >= self.flip_interval:
                    idx = self.player_flip_order[self.player_flip_index]
                    if idx < len(self.player_hand):
                        self.player_hand[idx].face_up = True
                    self.player_flip_index += 1
                    self.last_flip_time = current_time
            else:
                self.game_state = "ROUND_OVER"
                self.player_cards_revealed = True  # Mark that all cards have been revealed
                self.determine_winner()

    def update_rolling_dice(self):
        current_time = pygame.time.get_ticks()
        # Check if dice rolling period (1.5 seconds) has elapsed.
        if self.dice_roll_start is not None and current_time - self.dice_roll_start >= 1500:
            # Check if any dice are still rolling
            if any(die.rolling for die in self.dice):
                return
                
            # Count the occurrences of each face (including blank '' values)
            dice_counts = {}
            for die in self.dice:
                dice_counts[die.value] = dice_counts.get(die.value, 0) + 1

            # Immediately declare loss if all 4 dice are blank.
            if dice_counts.get('', 0) == 4:
                self.game_state = "ROUND_OVER"
                self.betting_triangle.start_flash(RED)
                result_str = "Dealer wins. All dice are blank."
                self.round_history.append({
                    "player_hand": list(self.player_hand),
                    "dice_values": [die.value for die in self.dice],
                    "result": result_str,
                    "winning_details": ["All dice blank"]
                })
                return

            # Determine if any non-blank suit appears at least twice.
            qualifies = any(count >= 2 for suit, count in dice_counts.items() if suit != '')
            
            if qualifies:
                # At least one suit appears at least twice: stop auto rerolling and proceed.
                
                # Allow game to proceed if there are exactly 2 blanks and the other 2 dice are of the same suit.
                if dice_counts.get('', 0) == 2:
                    non_blank = {k: v for k, v in dice_counts.items() if k != ''}
                    if len(non_blank) == 1 and list(non_blank.values())[0] == 2:
                        self.game_state = "FLIPPING_PLAYER"
                        self.last_flip_time = current_time
                        return

                # Immediate loss if exactly 2 blanks and the two non-blank dice are of different suits.
                if dice_counts.get('', 0) == 2:
                    non_blank = {k: v for k, v in dice_counts.items() if k != ''}
                    if len(non_blank) == 2:
                        self.game_state = "ROUND_OVER"
                        self.determine_winner()
                        return

                # A tie between two suits is a push instead of a loss.
                if len(dice_counts) == 2 and all(count == 2 for count in dice_counts.values()):
                    self.resolve_push(
                        "Push. The dice landed on two matching suits.",
                        ["Tie condition, bet returned"]
                    )
                    return

                # Otherwise, proceed to flip cards gradually.
                self.game_state = "FLIPPING_PLAYER"
                self.last_flip_time = current_time
                # Clear any existing reroll_timer for a clean state.
                self.reroll_timer = None
                return
            else:
                # Condition not met (no suit appears at least twice).
                if self.num_rerolls < 1:
                    # Attempt auto re-roll if delay has been met.
                    if self.reroll_timer is None:
                        self.reroll_timer = current_time
                    elif current_time - self.reroll_timer >= self.reroll_delay:
                        self.roll_all_dice()
                        self.dice_roll_start = pygame.time.get_ticks()
                        self.reroll_timer = None
                        self.num_rerolls += 1
                        return  # Wait for the re-rolled dice to settle in the next update
                else:
                    # If the second roll still has blank outcomes, treat it as a push.
                    if self.num_rerolls >= 1 and any(die.value == '' for die in self.dice):
                        self.resolve_push(
                            "Push. The second roll ended with blank dice.",
                            ["Blank dice after second roll"]
                        )
                        return

                    non_blank = {k: v for k, v in dice_counts.items() if k != ''}
                    if self.num_rerolls >= 1 and len(non_blank) == 4 and all(count == 1 for count in non_blank.values()):
                        self.resolve_push(
                            "Push. The second roll showed four different suits.",
                            ["Four distinct suits after second roll"]
                        )
                        return

                    # Maximum re-roll reached (only one re-roll allowed) and still no qualifying suit: treat as loss.
                    self.game_state = "ROUND_OVER"
                    self.betting_triangle.start_flash(RED)
                    result_str = "Dealer wins. No suit appeared at least twice after max re-rolls."
                    self.round_history.append({
                        "player_hand": list(self.player_hand),
                        "dice_values": [die.value for die in self.dice],
                        "result": result_str,
                        "winning_details": ["Max auto re-rolls reached without qualifying dice"]
                    })
                    return

    def determine_winner(self):
        # Check if all player cards are revealed
        if not all(card.face_up for card in self.player_hand):
            # If cards are not all revealed, it's a loss
            self.betting_triangle.start_flash(RED)
            result_str = "Dealer wins. Cards did not flip up."
            self.round_history.append({
                "player_hand": list(self.player_hand),
                "dice_values": [die.value for die in self.dice],
                "result": result_str,
                "winning_details": ["Cards did not flip up"]
            })
            return

        bet_amount = self.betting_triangle.current_bet

        # Count Jokers in hand
        jokers = [card for card in self.player_hand if card.rank == "Joker"]
        num_jokers = len(jokers)

        if num_jokers > 1:
            # More than one joker: player loses
            self.betting_triangle.start_flash(RED)
            result_str = "Dealer wins. More than one Joker in hand is an instant loss."
            self.round_history.append({
                "player_hand": list(self.player_hand),
                "dice_values": [die.value for die in self.dice],
                "result": result_str,
                "winning_details": ["Player had more than one Joker"]
            })
            return

        # Analyze the dice for possible win/loss
        dice_counts = {}
        for die in self.dice:
            dice_counts[die.value] = dice_counts.get(die.value, 0) + 1

        # Determine winning suit: only consider non-blank suits that appear at least twice.
        winning_suits = {suit: cnt for suit, cnt in dice_counts.items() if suit != '' and cnt >= 2}
        if not winning_suits:
            self.betting_triangle.start_flash(RED)
            result_str = "Dealer wins. No qualifying dice suit."
            self.round_history.append({
                "player_hand": list(self.player_hand),
                "dice_values": [die.value for die in self.dice],
                "result": result_str,
                "winning_details": ["No suit with 2+ occurrences"]
            })
            return

        # Select the winning suit with the highest count.
        winning_suit = max(winning_suits, key=winning_suits.get)
        winning_count = winning_suits[winning_suit]

        # If one joker: check for color/suit match!
        if num_jokers == 1:
            joker = jokers[0]
            # Determine the needed color based on winning suit
            needed_color = BLACK if winning_suit in ['♠', '♣'] else RED
            color_str = "BLACK" if needed_color == BLACK else "RED"
            
            if joker.color == needed_color:
                # Payout is 1:1 (original bet + winnings equals 2 * bet)
                payout = bet_amount  # 1:1 payout, only winnings
                total_payout = payout + bet_amount  # Return original bet as well

                self.wallet += total_payout
                self.betting_triangle.start_flash(GREEN)
                result_str = f"Player wins with color-matched Joker! Winning suit: {winning_suit} ({color_str}), Total payout: £{total_payout} (1:1 + original bet)"
                self.round_history.append({
                    "player_hand": list(self.player_hand),
                    "dice_values": [die.value for die in self.dice],
                    "result": result_str,
                    "winning_details": [f"Single {color_str} Joker (matches {winning_suit})"]
                })
                return
            else:
                # Joker is wrong color: player loses
                self.betting_triangle.start_flash(RED)
                opp_color = "RED" if needed_color == BLACK else "BLACK"
                result_str = f"Dealer wins. Joker does not match the winning suit color ({winning_suit}: needs {color_str}, got {opp_color})."
                self.round_history.append({
                    "player_hand": list(self.player_hand),
                    "dice_values": [die.value for die in self.dice],
                    "result": result_str,
                    "winning_details": [f"Joker color ({opp_color}) did not match suit color ({color_str})"]
                })
                return

        # If no jokers in hand, proceed with normal rules
        # Now count player's cards of the winning suit
        player_count = sum(1 for card in self.player_hand if card.suit == winning_suit)
        
        # Player loses if they have only one card of the winning suit
        if player_count == 1:
            self.betting_triangle.start_flash(RED)
            result_str = f"Dealer wins. Player has only 1 card of the winning suit {winning_suit}."
            self.round_history.append({
                "player_hand": list(self.player_hand),
                "dice_values": [die.value for die in self.dice],
                "result": result_str,
                "winning_details": [f"Only 1 {winning_suit} card in hand"]
            })
            return

        # Player loses if they have more cards of the winning suit than dice showing that suit
        if player_count > winning_count:
            self.betting_triangle.start_flash(RED)
            result_str = f"Dealer wins. Player has {player_count} cards of {winning_suit}, exceeding the threshold of {winning_count}."
            self.round_history.append({
                "player_hand": list(self.player_hand),
                "dice_values": [die.value for die in self.dice],
                "result": result_str,
                "winning_details": [f"{winning_suit}: dice {winning_count} vs player {player_count}"]
            })
            return
        
        # Player loses if they have no cards of the winning suit
        if player_count == 0:
            self.betting_triangle.start_flash(RED)
            result_str = f"Dealer wins. Player has no cards of the winning suit {winning_suit}."
            self.round_history.append({
                "player_hand": list(self.player_hand),
                "dice_values": [die.value for die in self.dice],
                "result": result_str,
                "winning_details": [f"No {winning_suit} cards in hand"]
            })
            return

        # Calculate payout based on the number of matching cards and dice
        # Updated payout multipliers
        payout_multipliers = {
            2: 4,  # 2 matching cards pays 4x
            3: 6,  # 3 matching cards pays 6x
            4: 8   # 4 matching cards pays 8x
        }
        
        # Calculate final multiplier and payout
        multiplier = payout_multipliers.get(player_count, 0)
        payout = bet_amount * multiplier
        total_payout = payout + bet_amount  # Include original bet
        
        self.wallet += total_payout
        self.betting_triangle.start_flash(GREEN)
        
        match_description = "exact match" if player_count == winning_count else f"{player_count} of {winning_count}"
        result_str = f"Player wins! Winning suit: {winning_suit} ({match_description}). Total payout: £{total_payout} ({multiplier}x + original bet)"
        
        self.round_history.append({
            "player_hand": list(self.player_hand),
            "dice_values": [die.value for die in self.dice],
            "result": result_str,
            "winning_details": [f"{winning_suit}({winning_count}) with {player_count} matching cards"]
        })

    def draw_round_history(self):
        font = pygame.font.Font(None, 24)
        start_y = 100
        for i, info in enumerate(self.round_history[-5:]):
            text = f"Round {i+1}: {info['result']}"
            surf = font.render(text, True, BLACK)
            screen.blit(surf, (50, start_y + i * 30))

    def draw(self):
        self.betting_triangle.draw()
        for chip in self.chips:
            if chip != self.betting_triangle.current_chip:
                chip.draw(is_active=(chip == self.active_chip))
        for die in self.dice:
            die.update()
            die.draw()

def draw_card(x: int, y: int, card: Optional[Card] = None):
    tl = (x, y)
    tr = (x + CARD_WIDTH, y)
    bl = (x, y + CARD_HEIGHT)
    br = (x + CARD_WIDTH, y + CARD_HEIGHT)
    if card and card.face_up:
        pygame.draw.rect(screen, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
    else:
        pygame.draw.polygon(screen, BLACK, [bl, tl, br])
        pygame.draw.polygon(screen, RED, [tr, tl, br])
    pygame.draw.line(screen, RED, tl, tr, 2)
    pygame.draw.line(screen, RED, tr, br, 2)
    pygame.draw.line(screen, BLACK, bl, br, 2)
    pygame.draw.line(screen, BLACK, tl, bl, 2)
    if card and card.face_up:
        font = pygame.font.Font(pygame.font.match_font("arial"), 20)
        if card.rank == "Joker":
            joker_surface = font.render("Joker", True, card.color)
            joker_rect = joker_surface.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
            screen.blit(joker_surface, joker_rect)
        else:
            suit_surface_top = font.render(card.suit, True, card.color)
            top_rect = suit_surface_top.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 4))
            screen.blit(suit_surface_top, top_rect)
            rank_surface = font.render(card.rank, True, card.color)
            rank_rect = rank_surface.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
            screen.blit(rank_surface, rank_rect)
            suit_surface_bottom = font.render(card.suit, True, card.color)
            bot_rect = suit_surface_bottom.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT * 3 // 4))
            screen.blit(suit_surface_bottom, bot_rect)

def draw_pyramid_layout(start_x: int, y: int, cards: List[Card]):
    positions = [
        (start_x - CARD_WIDTH // 2, y - CARD_HEIGHT - CARD_SPACING),
        (start_x - CARD_WIDTH - CARD_SPACING // 2, y),
        (start_x + CARD_SPACING // 2, y),
        (start_x - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING),
        (start_x - CARD_WIDTH - CARD_SPACING - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING),
        (start_x + CARD_WIDTH + CARD_SPACING - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING)
    ]
    for i, pos in enumerate(positions):
        if i < len(cards):
            draw_card(pos[0], pos[1], cards[i])
        else:
            draw_card(pos[0], pos[1])

def draw_wallet_and_chips(game: "SutzGame"):
    font = pygame.font.Font(None, 36)
    wallet_y_position = 200
    wallet_text = font.render("Wallet", True, BLACK)
    wallet_value = font.render(f"£{game.wallet}", True, BLACK)
    screen.blit(wallet_text, (40, wallet_y_position))
    screen.blit(wallet_value, (40, wallet_y_position + 40))
    for chip in game.chips:
        chip.draw()

def draw_credits_screen():
    screen.fill(WHITE)
    title_font = pygame.font.SysFont("timesnewroman", 32, bold=True)
    regular_font = pygame.font.SysFont("timesnewroman", 24)
    copyright_font = pygame.font.SysFont("timesnewroman", 18)
    lines = [
        ("CREDITS", True),
        ("", False),
        ("Dealer:", False),
        ("Wesley Nyanhongo", False),
        ("", False),
        ("Kind regards,", False),
        ("Game founder:", False),
        ("Wesley Nyanhongo", False),
        ("", False),
        ("Copyright © 2025 Wesley Tashinga Nyanhongo. All rights reserved", False)
    ]
    sy = (SCREEN_HEIGHT - len(lines) * 30) // 2
    for i, (line, is_title) in enumerate(lines):
        font_used = title_font if is_title else (copyright_font if i == len(lines) - 1 else regular_font)
        surf = font_used.render(line, True, BLACK)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, sy + i * 30))
        screen.blit(surf, rect)

def draw_previous_round(game: "SutzGame"):
    screen.fill(WHITE)
    if game.round_history:
        rd = game.round_history[-1]
        # Render dice using same styling as Dice.draw
        for i, die_value in enumerate(rd["dice_values"]):
            font = pygame.font.Font(pygame.font.match_font("arial"), 36)
            color = RED if die_value in ['♥', '♦'] else BLACK
            x = SCREEN_WIDTH // 2 - 150 + i * (DICE_SIZE + 20)
            y = 70
            pygame.draw.rect(screen, WHITE, (x, y, DICE_SIZE, DICE_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, DICE_SIZE, DICE_SIZE), 2)
            text_surf = font.render(die_value, True, color)
            text_rect = text_surf.get_rect(center=(x + DICE_SIZE // 2, y + DICE_SIZE // 2))
            screen.blit(text_surf, text_rect)
        draw_pyramid_layout(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 250, rd["player_hand"])

def draw_buttons(flip_rect, undo_rect, history_rect):
    font = pygame.font.Font(None, 24)
    pygame.draw.rect(screen, WHITE, flip_rect)
    pygame.draw.rect(screen, BLACK, flip_rect, 2)
    flip_surf = font.render("Flip", True, RED)
    flip_surf_rect = flip_surf.get_rect(center=flip_rect.center)
    screen.blit(flip_surf, flip_surf_rect)
    pygame.draw.rect(screen, WHITE, undo_rect)
    pygame.draw.rect(screen, BLACK, undo_rect, 2)
    undo_surf = font.render("Undo", True, RED)
    undo_surf_rect = undo_surf.get_rect(center=undo_rect.center)
    screen.blit(undo_surf, undo_surf_rect)
    pygame.draw.rect(screen, WHITE, history_rect)
    pygame.draw.rect(screen, BLACK, history_rect, 2)
    history_surf = font.render("History", True, RED)
    history_surf_rect = history_surf.get_rect(center=history_rect.center)
    screen.blit(history_surf, history_surf_rect)

def main(surface=None, embedded=False, wallet=None):
    global screen

    from embedded_utils import check_embedded_exit, draw_back_button

    if surface is not None:
        screen = surface
    elif screen is None:
        _init_display()

    clock = pygame.time.Clock()
    game = SutzGame()
    if wallet is not None:
        game.wallet = wallet.balance
    # Test adjustment: move buttons up by 20 pixels.
    flip_rect = pygame.Rect(570, 324, 80, 40)      # originally 570,344 (moved up 20)
    undo_rect = pygame.Rect(570, 374, 80, 40)      # originally 570,394 (moved up 20)
    history_rect = pygame.Rect(570, 424, 80, 40)   # originally 570,444 (moved up 20)
    running = True
    back_rect = None
    try:
        while running:
            screen.fill(WHITE)
            for event in pygame.event.get():
                exit_action = check_embedded_exit(event, embedded, back_rect)
                if exit_action == "quit":
                    if wallet is not None:
                        wallet.balance = game.wallet
                    return "quit"
                if exit_action == "menu":
                    if wallet is not None:
                        wallet.balance = game.wallet
                    return "menu"
                if event.type == pygame.QUIT:
                    if embedded:
                        if wallet is not None:
                            wallet.balance = game.wallet
                        return "quit"
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and game.game_state == "WAITING":
                        if game.betting_triangle.current_bet > 0:
                            game.reset_game()
                            game.game_state = "PLAYING"
                            game.determine_winner()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if embedded and back_rect and back_rect.collidepoint(pos):
                        continue
                    if history_rect.collidepoint(pos):
                        game.show_previous_round = not game.show_previous_round
                    elif game.show_previous_round:
                        game.show_previous_round = False
                    elif game.show_credits:
                        game.show_credits = False
                    elif flip_rect.collidepoint(pos) or undo_rect.collidepoint(pos):
                        if game.game_state == "ROUND_OVER":
                            game.betting_triangle.clear_bets()
                            game.reset_game()
                            game.game_state = "PLAYING"
                        else:
                            if flip_rect.collidepoint(pos):
                                # Start rolling without requiring a bet (triangle bet space removed)
                                if game.game_state == "PLAYING":
                                    game.game_state = "ROLLING_DICE"
                                    game.dice_roll_start = pygame.time.get_ticks()
                                    game.roll_all_dice()
                            elif undo_rect.collidepoint(pos):
                                if game.game_state in ["WAITING", "PLAYING"] and not game.player_cards_revealed:
                                    returned = game.betting_triangle.clear_bets_and_return()
                                    game.wallet += returned
                    else:
                        chip_clicked = game.handle_chip_click(pos)
                        if not chip_clicked:
                            game.handle_betting_space_click(pos)
                        game.handle_wallet_click(pos)

            if game.game_state == "ROLLING_DICE":
                game.update_rolling_dice()
            elif game.game_state == "FLIPPING_PLAYER":
                game.update_flip_animation()

            if game.show_previous_round:
                draw_previous_round(game)
            elif game.show_credits:
                draw_credits_screen()
            else:
                game.update_dealing_animation()
                draw_pyramid_layout(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 250, game.player_hand)
                draw_wallet_and_chips(game)
                game.draw()
                draw_buttons(flip_rect, undo_rect, history_rect)

            if embedded:
                back_rect = None

            pygame.display.flip()
            clock.tick(FPS)
    finally:
        if wallet is not None:
            wallet.balance = game.wallet

    if not embedded:
        pygame.quit()

if __name__ == "__main__":
    from embedded_utils import run_game_standalone
    run_game_standalone(sys.modules[__name__], "Su'tz")
