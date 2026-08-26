import pygame
import sys
import random
from typing import List, Optional

# Initialize Pygame
pygame.init()

# Custom events for card animations
REVEAL_EVENT = pygame.USEREVENT + 1
REPLACE_DEALER_CARD_EVENT = pygame.USEREVENT + 2
REPLACE_PLAYER_CARD_EVENT = pygame.USEREVENT + 3

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CARD_WIDTH, CARD_HEIGHT = 70, 100
FPS = 30
CARD_SPACING = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GREY = (128, 128, 128)  # Added grey color for push/tie highlighting

# Chip Constants
CHIP_RADIUS = 20
CHIP_VALUES = [10, 20, 50, 100, 200]
CHIP_COLORS = [(255, 51, 255), (57, 255, 20), (0, 255, 255), (255, 255, 0), (255, 127, 0)]
WALLET_AMOUNT = 1000

# Set up the display (deferred when embedded in Casino Sfeer menu)
screen = None


def _init_display(caption="Foust"):
    global screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(caption)
    return screen

class Card:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'Joker']

    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        # Assign color based on suit, or randomly for Jokers
        if rank == 'Joker':
            self.color = RED if random.choice([True, False]) else BLACK
        else:
            self.color = RED if suit in ['♥', '♦'] else BLACK

    def flip(self):
        self.face_up = not self.face_up

    def __str__(self):
        return f"{self.rank}{self.suit}"

class Deck:
    def __init__(self, num_decks=3):
        self.cards = []
        for _ in range(num_decks):
            for suit in Card.SUITS:
                for rank in Card.RANKS[:-1]:
                    self.cards.append(Card(suit, rank))
            self.cards.append(Card('', 'Joker'))
            self.cards.append(Card('', 'Joker'))
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        if self.cards:
            return self.cards.pop()
        return None

    def cards_remaining(self) -> int:
        return len(self.cards)

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

class BettingCircle:
    def __init__(self, x: int, y: int, radius: int, label: str):
        self.x = x
        self.y = y
        self.radius = radius
        self.label = label
        self.current_bet = 0
        self.current_chip = None
        self.bet_history = []
        self.flash_color = None
        self.flashing = False
        self.flash_duration = 500  # Duration in milliseconds
        self.is_push = False  # New flag to indicate a tie/push state

    def draw(self):
        # Draw the circle with thicker border
        if self.is_push:
            border_color = GREY  # Use grey for push/tie state
        else:
            border_color = self.flash_color if self.flashing else BLACK
        
        pygame.draw.circle(screen, border_color, (self.x, self.y), self.radius, 4)  # Thicker border

        # Draw the label ('P' or 'B') inside the circle, larger and in red
        label_font = pygame.font.Font(None, 36)  # Larger font size
        label_text = label_font.render(self.label, True, RED)  # Use self.label
        label_rect = label_text.get_rect(center=(self.x, self.y))  # Centered inside the circle
        screen.blit(label_text, label_rect)

        # Display current bet if any, positioned below the circle
        if self.current_bet > 0:
            bet_font = pygame.font.Font(None, 24)
            bet_text = bet_font.render(f"£{self.current_bet}", True, ORANGE)
            # Position to the right of the circle
            bet_rect = bet_text.get_rect(midleft=(self.x + self.radius + 10, self.y))
            screen.blit(bet_text, bet_rect)

        # Display current chip if any (chip remains inside the circle)
        if self.current_chip:
            pygame.draw.circle(screen, self.current_chip.color, (self.x, self.y), CHIP_RADIUS)
            pygame.draw.circle(screen, BLACK, (self.x, self.y), CHIP_RADIUS, 2)
            chip_font = pygame.font.Font(None, 20)
            chip_text = chip_font.render(f"£{self.current_chip.value}", True, BLACK)
            chip_rect = chip_text.get_rect(center=(self.x, self.y))
            screen.blit(chip_text, chip_rect)

    def place_bet(self, amount):
        self.current_bet += amount
        self.bet_history.append(amount)
        self.is_push = False  # Reset push state when placing a new bet

    def clear_bets(self):
        self.current_bet = 0
        self.bet_history.clear()
        self.current_chip = None
        self.is_push = False  # Reset push state when clearing bets

    def clear_bets_and_return(self):
        total = sum(self.bet_history)
        self.clear_bets()
        return total

    def reset_result_state(self):
        self.flashing = False
        self.flash_color = None
        self.is_push = False

    def is_clicked(self, mouse_pos):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2).collidepoint(mouse_pos)

class FoustGame:
    def __init__(self):
        self.deck = Deck(3)
        self.dealer_hand: List[Card] = []
        self.player_hand: List[Card] = []
        self.game_state = "WAITING"
        self.wallet = WALLET_AMOUNT

        self.chips = self.create_chips()

        # Updated positioning:
        # Vertically aligned betting circles with the same x-coordinate
        # and a sufficient gap between them to prevent overlapping
        self.dealer_betting_circle = BettingCircle(150, 290, 50, 'D') # Label 'D' for Dealer
        self.player_betting_circle = BettingCircle(150, 400, 50, 'C') # Label 'C' for Customer

        self.active_chip = None

        self.show_previous_round = False
        self.show_credits = False
        self.round_history = []

        # Animation state variables
        self.reveal_phase = None  # Can be "player", "dealer", "replacing", "player_replacing", or None
        self.player_reveal_index = 0
        self.dealer_reveal_index = 0
        self.dealer_replaced = False
        self.player_replaced_card_index = None
        self.player_replacement_time = 0
        self.player_card_rects = []  # Store rectangles for player cards for click detection
        
        # Card replacement tracking variables
        self.dealer_card_to_replace = None
        self.player_card_to_replace = None

        self.deal_initial_cards()
        
    def end_round_immediately(self):
        """
        Ends the round immediately when a Joker is revealed.
        Stops any active timers and determines the winner.
        """
        print("Joker drawn! Ending round immediately.")
        # Stop any active timers
        pygame.time.set_timer(REVEAL_EVENT, 0)
        pygame.time.set_timer(REPLACE_DEALER_CARD_EVENT, 0)
        pygame.time.set_timer(REPLACE_PLAYER_CARD_EVENT, 0)
        
        # Reveal all cards
        for card in self.player_hand:
            card.face_up = True
        for card in self.dealer_hand:
            card.face_up = True
            
        # Determine the winner and set game state to ROUND_OVER
        self.determine_winner()

    def create_chips(self):
        chips_list = []
        start_y = 255
        for i, val in enumerate(CHIP_VALUES):
            chip_x = 50
            chip_y = start_y + i * (CHIP_RADIUS * 2 + 5)
            chips_list.append(Chip(val, chip_x, chip_y, CHIP_COLORS[i]))
        return chips_list

    def betting_allowed(self) -> bool:
        """
        Returns True if bets can be edited:
        - Game state must be WAITING AND no reveal/replacement animations are running.
        """
        return self.game_state == "WAITING" and self.reveal_phase is None

    def handle_chip_click(self, mouse_pos):
        # Allow selecting a chip only if betting is allowed.
        if not self.betting_allowed():
            return False
        for chip in self.chips:
            if chip.rect.collidepoint(mouse_pos):
                self.active_chip = chip  # Allow selecting a chip once
                return True
        return False

    def handle_betting_space_click(self, mouse_pos):
        # Editing bets is allowed only when betting is allowed.
        if not self.betting_allowed():
            return False
            
        handled = False
        # Check player's betting circle
        if self.player_betting_circle.is_clicked(mouse_pos):
            if self.active_chip:
                if self.wallet < self.active_chip.value:
                    print("Insufficient funds to place this bet on Player!")
                    return False

                self.player_betting_circle.place_bet(self.active_chip.value)
                self.player_betting_circle.current_chip = self.active_chip
                self.wallet -= self.active_chip.value
                # Deselect chip after placing bet
                # self.active_chip = None # Optional: deselect chip after bet
                handled = True
            else:
                # If no active chip, clicking the circle shows previous round
                self.show_previous_round = True
                
        # Check dealer's betting circle
        if self.dealer_betting_circle.is_clicked(mouse_pos):
            if self.active_chip:
                if self.wallet < self.active_chip.value:
                    print("Insufficient funds to place this bet on Dealer!")
                    return False

                self.dealer_betting_circle.place_bet(self.active_chip.value)
                self.dealer_betting_circle.current_chip = self.active_chip
                self.wallet -= self.active_chip.value
                handled = True
            else:
                # If no active chip, clicking the circle shows previous round
                self.show_previous_round = True

        return handled

    def handle_wallet_click(self, mouse_pos):
        wallet_rect = pygame.Rect(40, 156, 100, 40)
        if wallet_rect.collidepoint(mouse_pos):
            self.show_credits = True

    def reset_game(self):
        if self.deck.cards_remaining() <= 24:
            self.deck = Deck(3)

        self.dealer_hand.clear()
        self.player_hand.clear()

        self.player_betting_circle.reset_result_state()
        self.dealer_betting_circle.reset_result_state()
        self.player_betting_circle.clear_bets()
        self.dealer_betting_circle.clear_bets()

        self.show_previous_round = False
        self.show_credits = False

        # Reset animation state
        self.reveal_phase = None
        self.player_reveal_index = 0
        self.dealer_reveal_index = 0
        self.dealer_replaced = False
        self.player_replaced_card_index = None
        self.player_replacement_time = 0
        
        # Reset card replacement tracking
        self.dealer_card_to_replace = None
        self.player_card_to_replace = None

        # Stop any active timers
        pygame.time.set_timer(REVEAL_EVENT, 0)
        pygame.time.set_timer(REPLACE_DEALER_CARD_EVENT, 0)
        pygame.time.set_timer(REPLACE_PLAYER_CARD_EVENT, 0)

        # Set game state to WAITING to allow betting
        self.game_state = "WAITING"

        self.deal_initial_cards()

    def deal_initial_cards(self):
        self.dealer_hand.clear()
        self.player_hand.clear()
        self.game_state = "WAITING"

        for _ in range(4):
            c = self.deck.draw()
            if c:
                c.face_up = False
                self.player_hand.append(c)
        for _ in range(4):
            c = self.deck.draw()
            if c:
                c.face_up = False
                self.dealer_hand.append(c)

    def get_card_value(self, card: Card) -> int:
        if card.rank == 'A':
            return 1
        elif card.rank in ['J', 'Q', 'K']:
            return 2 if card.rank == 'J' else (3 if card.rank == 'Q' else 4)
        elif card.rank == 'Joker':
            return 5
        else:  # Number cards 2-10
            try:
                return int(card.rank) // 2  # Half the face value, rounded down
            except ValueError:
                return 0

    def calculate_hand_value(self, hand: List[Card]) -> int:
        return sum(self.get_card_value(c) for c in hand)

    def determine_winner(self):
        # If round is already over, skip re-processing
        if self.game_state == "ROUND_OVER":
            return

        self.player_betting_circle.reset_result_state()
        self.dealer_betting_circle.reset_result_state()

        # Disable the reveal timer to prevent further events
        pygame.time.set_timer(REVEAL_EVENT, 0)
        pygame.time.set_timer(REPLACE_DEALER_CARD_EVENT, 0)
        pygame.time.set_timer(REPLACE_PLAYER_CARD_EVENT, 0)
    
        # Helper functions
        def count_color(hand, color, include_joker=True):
            if include_joker:
                return sum(1 for card in hand if card.color == color)
            else:
                return sum(1 for card in hand if card.color == color and card.rank != 'Joker')

        def has_joker(hand):
            return any(card.rank == 'Joker' for card in hand)

        def get_joker_color(hand):
            for card in hand:
                if card.rank == 'Joker':
                    return card.color
            return None

        def has_multiple_jokers_of_different_colors(hand):
            joker_colors = [card.color for card in hand if card.rank == 'Joker']
            return len(joker_colors) > 1 and len(set(joker_colors)) > 1

        # Check for multiple Jokers of different colors first.
        if has_multiple_jokers_of_different_colors(self.player_hand) or has_multiple_jokers_of_different_colors(self.dealer_hand):
            result_str = "All Bets Lost"
            if self.player_betting_circle.current_bet > 0:
                self.player_betting_circle.flashing = True
                self.player_betting_circle.flash_color = RED
            if self.dealer_betting_circle.current_bet > 0:
                self.dealer_betting_circle.flashing = True
                self.dealer_betting_circle.flash_color = RED
            # Record history and set game state to over.
            self.round_history.append({
                "player_hand": [c for c in self.player_hand],
                "dealer_hand": [c for c in self.dealer_hand],
                "result": result_str,
                "player_red_count": count_color(self.player_hand, RED),
                "player_black_count": count_color(self.player_hand, BLACK),
                "dealer_red_count": count_color(self.dealer_hand, RED),
                "dealer_black_count": count_color(self.dealer_hand, BLACK)
            })
            self.game_state = "ROUND_OVER"
            return

        # Count colors for both hands.
        player_red_count = count_color(self.player_hand, RED)
        player_black_count = count_color(self.player_hand, BLACK)
        dealer_red_count = count_color(self.dealer_hand, RED)
        dealer_black_count = count_color(self.dealer_hand, BLACK)

        # Flags for Joker presence.
        player_has_joker = has_joker(self.player_hand)
        dealer_has_joker = has_joker(self.dealer_hand)

        player_wins = False
        dealer_wins = False
        is_tie = False

        # NEW JOKER RULE: If someone has a joker, they win automatically,
        # unless counting the joker's color still leaves their hand's colors tied (e.g. 2 red/2 black),
        # in which case it's a push.
        # If both have jokers, it's a tie
        if player_has_joker and dealer_has_joker:
            is_tie = True
        elif player_has_joker:
            if player_red_count == player_black_count:
                is_tie = True
            else:
                player_wins = True
        elif dealer_has_joker:
            if dealer_red_count == dealer_black_count:
                is_tie = True
            else:
                dealer_wins = True
        else:
            # If no Jokers present, use the original win conditions
            
            # Full color (4 of a kind) check.
            player_has_full_color = (player_red_count == 4 or player_black_count == 4)
            dealer_has_full_color = (dealer_red_count == 4 or dealer_black_count == 4)
            
            # Full-color decision takes precedence.
            if player_has_full_color and not dealer_has_full_color:
                player_wins = True
            elif dealer_has_full_color and not player_has_full_color:
                dealer_wins = True
            elif player_has_full_color and dealer_has_full_color:
                # Both player and dealer have 4 cards of one color. This is now considered a tie (push).
                is_tie = True
            else:
                # Compute effective counts - use the majority color for each hand
                player_majority_color = RED if player_red_count > player_black_count else BLACK
                dealer_majority_color = RED if dealer_red_count > dealer_black_count else BLACK
            
                # Get the count of the majority color for each hand
                player_majority_count = player_red_count if player_majority_color == RED else player_black_count
                dealer_majority_count = dealer_red_count if dealer_majority_color == RED else dealer_black_count
            
                # If there's a tie in colors (2 red, 2 black), use the higher value color (RED)
                if player_red_count == player_black_count:
                    player_majority_color = RED
                    player_majority_count = player_red_count
                
                if dealer_red_count == dealer_black_count:
                    dealer_majority_color = RED
                    dealer_majority_count = dealer_red_count
            
                # Compare the majority counts
                if player_majority_count > dealer_majority_count:
                    player_wins = True
                elif dealer_majority_count > player_majority_count:
                    dealer_wins = True
                else:
                    # If majority counts are equal, it's a tie (push)
                    is_tie = True


        # Payout logic and circle flashing for each case.
        player_bet = self.player_betting_circle.current_bet
        dealer_bet = self.dealer_betting_circle.current_bet

        if is_tie:
            result_str = "Tie (Push)"
            # Push means the original wager is returned to the player without any payout.
            if player_bet > 0:
                self.wallet += player_bet
                self.player_betting_circle.clear_bets()
            if dealer_bet > 0:
                self.wallet += dealer_bet
                self.dealer_betting_circle.clear_bets()
            self.player_betting_circle.flashing = True
            self.player_betting_circle.flash_color = GREY
            self.dealer_betting_circle.flashing = True
            self.dealer_betting_circle.flash_color = GREY
        elif player_wins:
            result_str = "Player Wins"
            # Only the Customer ('C') bet wins; the dealer bet loses.
            if player_bet > 0:
                self.wallet += player_bet * 2  # Payout for customer bet: original bet + winnings
                self.player_betting_circle.flashing = True
                self.player_betting_circle.flash_color = GREEN
            if dealer_bet > 0:
                self.dealer_betting_circle.flashing = True
                self.dealer_betting_circle.flash_color = RED
        else:
            result_str = "Dealer Wins"
            # Only the Dealer ('D') bet wins; the customer bet loses.
            if dealer_bet > 0:
                self.wallet += dealer_bet * 2  # Payout for dealer bet: original bet + winnings
                self.dealer_betting_circle.flashing = True
                self.dealer_betting_circle.flash_color = GREEN
            if player_bet > 0:
                self.player_betting_circle.flashing = True
                self.player_betting_circle.flash_color = RED

        # Record round history.
        self.round_history.append({
            "player_hand": [c for c in self.player_hand],
            "dealer_hand": [c for c in self.dealer_hand],
            "result": result_str,
            "player_red_count": player_red_count,
            "player_black_count": player_black_count,
            "dealer_red_count": dealer_red_count,
            "dealer_black_count": dealer_black_count
        })

        self.game_state = "ROUND_OVER"

    def start_reveal_sequence(self):
        # Begin the non-blocking card reveal sequence
        self.reveal_phase = "player"
        self.player_reveal_index = 0
        self.dealer_reveal_index = 0
        self.dealer_replaced = False
        self.player_card_rects = []  # Reset card rectangles
        # Set timer to trigger REVEAL_EVENT every 500ms
        pygame.time.set_timer(REVEAL_EVENT, 500)
        
    def process_reveal_event(self):
        if self.reveal_phase == "player":
            # Flip player's cards in the order: left, top, right, bottom
            flip_order = [0, 1, 3, 2]
            if self.player_reveal_index < len(flip_order):
                index = flip_order[self.player_reveal_index]
                self.player_hand[index].face_up = True
                self.player_reveal_index += 1
            else:
                # After finishing player reveal, switch to dealer reveal phase
                self.reveal_phase = "dealer"
        elif self.reveal_phase == "dealer":
            if self.dealer_reveal_index < len(self.dealer_hand):
                self.dealer_hand[self.dealer_reveal_index].face_up = True
                self.dealer_reveal_index += 1
            else:
                # All dealer cards have been revealed.
                # If any Joker is present, immediately end round.
                all_visible_cards = self.player_hand + self.dealer_hand
                if any(card.rank == 'Joker' for card in all_visible_cards):
                    self.end_round_immediately()
                    return
                
                # Instead of checking for a full-color condition on the player's hand now,
                # always proceed to the dealer replacement phase.
                self.reveal_phase = "replacing"
                self.dealer_replaced = False  # Reset dealer replacement flag
                pygame.time.set_timer(REVEAL_EVENT, 1400)  # Set timer for first replacement check
        elif self.reveal_phase == "replacing":
            # This handles continuous replacement until a condition is met
            self.process_replace_event()

    def draw_round_history(self):
        font = pygame.font.Font(None, 24)
        start_y = 100
        for i, info in enumerate(self.round_history[-5:]):
            text = (
                f"Round {i+1}: "
                f"Player R:{info['player_red_count']}/B:{info['player_black_count']} - "
                f"Dealer R:{info['dealer_red_count']}/B:{info['dealer_black_count']} - "
                f"{info['result']}"
            )
            surf = font.render(text, True, BLACK)
            screen.blit(surf, (50, start_y + i * 30))

    def has_all_same_color(self, hand, color):
        """Check if all cards in a hand are the same color"""
        return all(card.color == color for card in hand)
    
    def process_replace_event(self):
        # If round is already over, do nothing.
        if self.game_state == "ROUND_OVER":
            return

        # Replacement phase logic.
        if self.reveal_phase == "replacing":
            if not self.dealer_replaced:
                # Dealer's turn: replace one card.
                self.flip_and_replace_dealer_card()
                self.dealer_replaced = True
                # Wait for the dealer replacement event to complete before further processing.
                return
            else:
                # After dealer's replacement, check immediate win conditions.
                dealer_red_count = sum(1 for card in self.dealer_hand if card.color == RED)
                dealer_black_count = sum(1 for card in self.dealer_hand if card.color == BLACK)
                if dealer_red_count == 4 or dealer_black_count == 4:
                    self.determine_winner()
                    return
                # If dealer did not win, now allow the player to replace a card.
                self.reveal_phase = "player_replacing"
                card_index_to_replace = self.get_player_card_to_replace()
                self.flip_and_replace_player_card(card_index_to_replace)
                return

        elif self.reveal_phase == "player_replacing":
            # After the player's replacement, win conditions will be checked in the REPLACE_PLAYER_CARD_EVENT handler.
            # No further actions needed here - the cycle will continue in the REPLACE_PLAYER_CARD_EVENT handler.
            return

    def get_player_card_to_replace(self) -> int:
        """Determines the index of the player card to replace based on minority color."""
        # Defensive check: ensure player_hand is not empty
        if not self.player_hand:
            print("Error: Player hand is empty when trying to replace a card.")
            return 0
            
        red_count = sum(1 for card in self.player_hand if card.color == RED)
        black_count = sum(1 for card in self.player_hand if card.color == BLACK)
        joker_count = sum(1 for card in self.player_hand if card.rank == 'Joker')
        
        print(f"Card counts - Red: {red_count}, Black: {black_count}, Jokers: {joker_count}")
        
        target_color = None

        if black_count < red_count:
            target_color = BLACK
            print(f"Targeting BLACK card for replacement (minority color)")
        elif red_count < black_count:
            target_color = RED
            print(f"Targeting RED card for replacement (minority color)")
        else: # Tied count (e.g., 2 red, 2 black)
            target_color = BLACK # Default tie-breaker: replace first black
            print(f"Tied color count. Defaulting to replace BLACK card")

        # First try to find a non-Joker card of the target color
        for i, card in enumerate(self.player_hand):
            if card.color == target_color and card.rank != 'Joker':
                print(f"Replacing card at index {i}: {card.rank}{card.suit}")
                return i
                
        # If no non-Joker card of target color, try any card of target color
        for i, card in enumerate(self.player_hand):
            if card.color == target_color:
                print(f"Replacing card at index {i}: {card.rank}{card.suit}")
                return i
        
        # Fallback if no card of the target color is found
        print("Warning: Could not find player card of minority color to replace.")
        
        # Try to avoid replacing Jokers if possible
        for i, card in enumerate(self.player_hand):
            if card.rank != 'Joker':
                print(f"Fallback: Replacing non-Joker card at index {i}")
                return i
                
        # Last resort: replace first card
        print("Last resort: Replacing card at index 0")
        return 0

    def flip_and_replace_dealer_card(self):
        # Calculate current color counts in dealer's hand.
        red_count = sum(1 for card in self.dealer_hand if card.color == RED)
        black_count = sum(1 for card in self.dealer_hand if card.color == BLACK)
        
        # Determine target color: choose the color that is less frequent.
        if red_count < black_count:
            target_color = RED
        elif black_count < red_count:
            target_color = BLACK
        else:
            target_color = None  # Counts are equal.
        
        # Identify the card index to replace.
        target_index = None
        if target_color is not None:
            # Try to find the first card of the target (minority) color.
            for i, card in enumerate(self.dealer_hand):
                if card.color == target_color:
                    target_index = i
                    break
            # Fallback: if no card of the target color is found, use last card.
            if target_index is None:
                target_index = len(self.dealer_hand) - 1
        else:
            # If both colors are equally represented, replace the last card dealt.
            target_index = len(self.dealer_hand) - 1

        # Ensure the deck is not exhausted.
        if self.deck.cards_remaining() == 0:
            print("Deck is exhausted. Reshuffling...")
            self.deck = Deck(3)
            
        # Prepare the selected card for replacement.
        self.dealer_hand[target_index].face_up = False
        
        # Set a timer event for delayed replacement.
        pygame.time.set_timer(REPLACE_DEALER_CARD_EVENT, 1000, 1)  # One-time event after 1000ms
        
        # Store the index of the card to be replaced.
        self.dealer_card_to_replace = target_index
        
        print(f"Dealer replacing card at index {target_index}: {self.dealer_hand[target_index].rank}{self.dealer_hand[target_index].suit}")
        
    def flip_and_replace_player_card(self, card_index):
        # Replace the player's card at the specified index
        if 0 <= card_index < len(self.player_hand):
            # Check if deck is exhausted
            if self.deck.cards_remaining() == 0:
                print("Deck is exhausted. Reshuffling...")
                self.deck = Deck(3)
                
            # Get the card being replaced for logging
            card_to_replace = self.player_hand[card_index]
            print(f"Player replacing card at index {card_index}: {card_to_replace.rank}{card_to_replace.suit}")
                
            # Flip card back first
            self.player_hand[card_index].face_up = False
            
            # Create a custom event for delayed replacement
            REPLACE_PLAYER_CARD_EVENT = pygame.USEREVENT + 3
            pygame.time.set_timer(REPLACE_PLAYER_CARD_EVENT, 1000, 1)  # One-time event after 1000ms (1 second)
            
            # Store the card index to replace in a class variable
            self.player_card_to_replace = card_index
        else:
            print(f"Invalid card index: {card_index}. Valid range: 0-{len(self.player_hand)-1}")

    def draw(self):
        self.player_betting_circle.draw()
        self.dealer_betting_circle.draw()

        # Draw ALL chips from the stack
        for chip in self.chips:
            chip.draw(is_active=(chip == self.active_chip))
                
    def check_auto_win_conditions(self):
        # If round is already over, skip checking
        if self.game_state == "ROUND_OVER":
            return
            
        # Check for Joker in dealer's hand first
        if any(card.rank == 'Joker' for card in self.dealer_hand):
            self.end_round_immediately()
            return

        # Note: We no longer check for player's 4-of-a-kind here
        # This check will happen after the replacement phase
        
        # Continue with the replacement cycle
        pygame.time.set_timer(REVEAL_EVENT, 1400)
        
    def update_animations(self):
        # Handle card replacement animation
        if self.player_replaced_card_index is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.player_replacement_time > 500:
                self.player_replaced_card_index = None

    def undo_all_bets(self):
        # Only allow undoing bets if betting is allowed
        if not self.betting_allowed():
            return 0
        # Implement the logic to undo all bets and return the total amount
        return self.player_betting_circle.clear_bets_and_return() + self.dealer_betting_circle.clear_bets_and_return()

def draw_card(x: int, y: int, card: Optional[Card] = None):
    tl = (x, y)
    tr = (x + CARD_WIDTH, y)
    bl = (x, y + CARD_HEIGHT)
    br = (x + CARD_WIDTH, y + CARD_HEIGHT)

    if card and card.face_up:
        pygame.draw.rect(screen, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
    else:
        # Draw the card back with black, red, and white stripes
        pygame.draw.rect(screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT))
        
        # Draw red, black, and white stripes
        stripe_height = CARD_HEIGHT // 15
        colors = [RED, BLACK, WHITE]
        for i in range(0, CARD_HEIGHT, stripe_height * 3):
            for j, color in enumerate(colors):
                pygame.draw.rect(screen, color, (x, y + i + j * stripe_height, CARD_WIDTH, stripe_height))

    pygame.draw.line(screen, BLACK, tl, tr, 2)
    pygame.draw.line(screen, BLACK, tr, br, 2)
    pygame.draw.line(screen, BLACK, bl, br, 2)
    pygame.draw.line(screen, BLACK, tl, bl, 2)

    if card and card.face_up:
        font = pygame.font.Font(pygame.font.match_font("arial"), 20)
        suit_surface_top = font.render(card.suit, True, card.color)
        top_rect = suit_surface_top.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 4))
        screen.blit(suit_surface_top, top_rect)

        rank_surface = font.render(card.rank, True, card.color)
        rank_rect = rank_surface.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
        screen.blit(rank_surface, rank_rect)

        suit_surface_bottom = font.render(card.suit, True, card.color)
        bot_rect = suit_surface_bottom.get_rect(
            center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT * 3 // 4)
        )
        screen.blit(suit_surface_bottom, bot_rect)

def draw_dealer_layout(start_x: int, y: int, cards: List[Card]):
    # Calculate the total width of the cards and spacing
    total_width = 3 * CARD_SPACING + 4 * CARD_WIDTH
    # Calculate the starting x-coordinate to center the cards
    start_x = (SCREEN_WIDTH - total_width) // 2

    slot_positions = []
    for i in range(4):
        sx = start_x + i * (CARD_WIDTH + CARD_SPACING)
        slot_positions.append((sx, y))

    for i, pos in enumerate(slot_positions):
        if i < len(cards):
            draw_card(pos[0], pos[1], cards[i])
        else:
            draw_card(pos[0], pos[1])

def draw_pyramid_layout(start_x: int, y: int, cards: List[Card], game=None):
    # Calculate the total width of the cards and spacing
    total_width = 2 * (CARD_WIDTH + CARD_SPACING) + CARD_WIDTH
    # Calculate the starting x-coordinate to center the cards
    start_x = (SCREEN_WIDTH - total_width) // 2

    # Adjusted positions for the layout: left card, top center card, bottom center card, right card
    positions = [
        (start_x, y - CARD_HEIGHT // 2 + 50),  # Left side card, moved up
        (start_x + CARD_WIDTH + CARD_SPACING, y - CARD_HEIGHT - CARD_SPACING + 50),  # Top center card
        (start_x + CARD_WIDTH + CARD_SPACING, y + 50),  # Bottom center card
        (start_x + 2 * (CARD_WIDTH + CARD_SPACING), y - CARD_HEIGHT // 2 + 50)  # Right side card, moved up
    ]
    
    # Clear previous card rectangles if game is provided
    if game:
        game.player_card_rects = []
    
    for i, pos in enumerate(positions):
        if i < len(cards):
            draw_card(pos[0], pos[1], cards[i])
            # Store card rectangles for click detection if game is provided
            if game and game.reveal_phase == "replacing":
                card_rect = pygame.Rect(pos[0], pos[1], CARD_WIDTH, CARD_HEIGHT)
                if game:
                    game.player_card_rects.append((card_rect, i))
        else:
            draw_card(pos[0], pos[1])

def draw_wallet_and_chips(game: "FoustGame"):
    font = pygame.font.Font(None, 36)
    wallet_text = font.render("Wallet", True, BLACK)
    wallet_value = font.render(f"£{game.wallet}", True, BLACK)

    wallet_y_position = 156
    screen.blit(wallet_text, (40, wallet_y_position))
    screen.blit(wallet_value, (40, wallet_y_position + 40))

    # Draw both betting circles
    game.player_betting_circle.draw()
    game.dealer_betting_circle.draw()
    
    # Draw ALL chips from the stack
    for chip in game.chips:
        chip.draw(is_active=(chip == game.active_chip))

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
        font = title_font if is_title else (copyright_font if i == len(lines) - 1 else regular_font)
        surf = font.render(line, True, BLACK)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, sy + i * 30))
        screen.blit(surf, rect)

def draw_previous_round(game: "FoustGame"):
    screen.fill(WHITE)
    if game.round_history:
        rd = game.round_history[-1]
        draw_dealer_layout(SCREEN_WIDTH // 2, 100, rd["dealer_hand"])
        draw_pyramid_layout(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200, rd["player_hand"])  # Adjusted y-coordinate

def draw_buttons(chance_rect, undo_rect):
    font = pygame.font.Font(None, 24)

    pygame.draw.rect(screen, WHITE, chance_rect)
    pygame.draw.rect(screen, BLACK, chance_rect, 2)
    chance_surf = font.render("Play", True, RED)
    chance_surf_rect = chance_surf.get_rect(center=chance_rect.center)
    screen.blit(chance_surf, chance_surf_rect)

    pygame.draw.rect(screen, WHITE, undo_rect)
    pygame.draw.rect(screen, BLACK, undo_rect, 2)
    undo_surf = font.render("Undo", True, RED)
    undo_surf_rect = undo_surf.get_rect(center=undo_rect.center)
    screen.blit(undo_surf, undo_surf_rect)

def main(surface=None, embedded=False, wallet=None):
    global screen

    from embedded_utils import check_embedded_exit, draw_back_button

    if surface is not None:
        screen = surface
    elif screen is None:
        _init_display()

    clock = pygame.time.Clock()
    game = FoustGame()
    if wallet is not None:
        game.wallet = wallet.balance

    # Position buttons: Play above Undo
    chance_rect = pygame.Rect(570, 300, 80, 40)  # Play button
    undo_rect = pygame.Rect(570, 350, 80, 40)    # Undo button

    running = True
    back_rect = None
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
            elif event.type == REVEAL_EVENT:
                game.process_reveal_event()
            elif event.type == REPLACE_DEALER_CARD_EVENT:
                # Handle dealer card replacement after flip animation
                if game.dealer_card_to_replace is not None:
                    i = game.dealer_card_to_replace
                    if 0 <= i < len(game.dealer_hand):  # Validate index
                        new_card = game.deck.draw()
                        if new_card:
                            new_card.face_up = True
                            game.dealer_hand[i] = new_card
                        else:
                            # If deck is exhausted, reshuffle and try again
                            print("Deck is exhausted during dealer replacement. Reshuffling...")
                            game.deck = Deck(3)
                            new_card = game.deck.draw()
                            if new_card:
                                new_card.face_up = True
                                game.dealer_hand[i] = new_card
                        
                        # After dealer replacement, check if dealer has 4 of a kind
                        dealer_red_count = sum(1 for card in game.dealer_hand if card.color == RED)
                        dealer_black_count = sum(1 for card in game.dealer_hand if card.color == BLACK)
                        
                        if dealer_red_count == 4 or dealer_black_count == 4:
                            # Dealer wins with 4 of a kind
                            game.determine_winner()
                        else:
                            # Dealer doesn't have 4 of a kind, proceed to player replacement
                            game.reveal_phase = "player_replacing"
                            card_index_to_replace = game.get_player_card_to_replace()
                            game.flip_and_replace_player_card(card_index_to_replace)
                    else:
                        print(f"Invalid dealer card index: {i}")
                    game.dealer_card_to_replace = None
            elif event.type == REPLACE_PLAYER_CARD_EVENT:
                # Handle player card replacement after flip animation
                if game.player_card_to_replace is not None:
                    card_index = game.player_card_to_replace
                    if 0 <= card_index < len(game.player_hand):  # Validate index
                        new_card = game.deck.draw()
                        if new_card:
                            new_card.face_up = True
                            game.player_hand[card_index] = new_card
                        else:
                            # If deck is exhausted, reshuffle and try again
                            print("Deck is exhausted during player replacement. Reshuffling...")
                            game.deck = Deck(3)
                            new_card = game.deck.draw()
                            if new_card:
                                new_card.face_up = True
                                game.player_hand[card_index] = new_card
                        
                        # Check if any card is a Joker and end the round immediately if so
                        if any(card.rank == 'Joker' for card in game.player_hand):
                            game.end_round_immediately()
                        else:
                            # Count colors in both hands to check for 4 of a kind
                            player_red_count = sum(1 for card in game.player_hand if card.color == RED)
                            player_black_count = sum(1 for card in game.player_hand if card.color == BLACK)
                            dealer_red_count = sum(1 for card in game.dealer_hand if card.color == RED)
                            dealer_black_count = sum(1 for card in game.dealer_hand if card.color == BLACK)
                            
                            # Check if either hand has 4 of a kind
                            if player_red_count == 4 or player_black_count == 4 or dealer_red_count == 4 or dealer_black_count == 4:
                                # Determine the winner if a win condition is met
                                game.determine_winner()
                            else:
                                # No win condition met, continue the replacement cycle
                                print("No win condition met. Continuing alternating replacements...")
                                # Reset the reveal phase to "replacing" and dealer_replaced to False
                                # to start a new dealer-player replacement cycle
                                game.reveal_phase = "replacing"
                                game.dealer_replaced = False
                                # Schedule the next replacement cycle after a brief delay
                                pygame.time.set_timer(REVEAL_EVENT, 1400)
                    else:
                        print(f"Invalid player card index: {card_index}")
                    game.player_card_to_replace = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game.game_state == "WAITING":
                    if game.player_betting_circle.current_bet > 0 or game.dealer_betting_circle.current_bet > 0:
                        game.start_reveal_sequence()
                        game.game_state = "PLAYING"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if embedded and back_rect and back_rect.collidepoint(pos):
                    continue

                if game.show_previous_round:
                    game.show_previous_round = False
                elif game.show_credits:
                    game.show_credits = False
                elif chance_rect.collidepoint(pos):  # Play button
                    if game.game_state == "ROUND_OVER":
                        game.reset_game()  # reset_game already sets state to "WAITING"
                    elif game.game_state == "WAITING":
                        # Only start reveal if there is a bet placed
                        if game.player_betting_circle.current_bet > 0 or game.dealer_betting_circle.current_bet > 0:
                            game.start_reveal_sequence()
                            game.game_state = "PLAYING"
                elif undo_rect.collidepoint(pos):
                    if game.game_state in ["WAITING", "PLAYING"]:
                        # Use new undo method for both circles
                        returned = game.undo_all_bets() 
                        game.wallet += returned
                else:
                    chip_clicked = game.handle_chip_click(pos)
                    if not chip_clicked:
                        game.handle_betting_space_click(pos)
                    game.handle_wallet_click(pos)

        if game.show_previous_round:
            draw_previous_round(game)
        elif game.show_credits:
            draw_credits_screen()
        else:
            # Update animations and flash effect
            game.update_animations()

            draw_dealer_layout(SCREEN_WIDTH // 2, 100, game.dealer_hand)  # Adjusted y-coordinate
            draw_pyramid_layout(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200, game.player_hand, game)  # Adjusted y-coordinate
            draw_wallet_and_chips(game)
            draw_buttons(chance_rect, undo_rect)

        if embedded:
            back_rect = None

        pygame.display.flip()
        clock.tick(FPS)

    if wallet is not None:
        wallet.balance = game.wallet

    if not embedded:
        pygame.quit()

if __name__ == "__main__":
    from embedded_utils import run_game_standalone
    run_game_standalone(sys.modules[__name__], "Foust")
