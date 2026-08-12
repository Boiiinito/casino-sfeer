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
FPS = 30
CARD_SPACING = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 140, 0)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
NEON_PINK = (255, 51, 255)
NEON_GREEN = (57, 255, 20)
NEON_BLUE = (0, 255, 255)
NEON_YELLOW = (255, 255, 0)
NEON_ORANGE = (255, 127, 0)

# Chip Constants
CHIP_RADIUS = 20
CHIP_VALUES = [10, 20, 50, 100, 200]
CHIP_COLORS = [NEON_PINK, NEON_GREEN, NEON_BLUE, NEON_YELLOW, NEON_ORANGE]
WALLET_AMOUNT = 1000

# Triangle Constants
TRIANGLE_SIZE = 80
TRIANGLE_BORDER = 4

# Dice Constants
DICE_SIZE = 40
DICE_SPACING = 10

# Set up the display (deferred when embedded in Casino Sfeer menu)
screen = None


def _init_display(caption="Chanceo'chill"):
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
        # Red suits get a red color; black suits get a black color
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
                for rank in Card.RANKS[:-1]:  # Omit 'Joker' from normal ranks
                    self.cards.append(Card(suit, rank))
            # Two Jokers per deck
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
        # Used for collision detection with the mouse
        self.rect = pygame.Rect(x - CHIP_RADIUS, y - CHIP_RADIUS, CHIP_RADIUS * 2, CHIP_RADIUS * 2)

    def draw(self, is_active=False):
        """
        Draws a circular chip. If is_active=True, highlight the border with RED.
        """
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        border_color = RED if is_active else BLACK
        pygame.draw.circle(screen, border_color, (self.x, self.y), self.radius, 3)

        font = pygame.font.Font(None, 20)
        text_surf = font.render(f"£{self.value}", True, BLACK)
        text_rect = text_surf.get_rect(center=(self.x, self.y))
        screen.blit(text_surf, text_rect)

class BettingTriangle:
    """
    A triangle to represent a betting area. We determine orientation by which side is the "apex".
    """
    def __init__(self, x: int, y: int, size: int, label="B", orientation="upright"):
        """
        orientation can be "upright", "downward", or "right".
        - "upright": apex pointing up
        - "downward": apex pointing down
        - "right": apex pointing right
        """
        self.x = x
        self.y = y
        self.size = size
        self.label = label
        # We'll define the bounding rect for a quick "collidepoint" check
        self.rect = pygame.Rect(x - size // 2, y - size // 2, size, size)

        # Define triangle geometry
        if orientation == "upright":
            self.points = [
                (x, y - size // 2),  # apex at top
                (x - size // 2, y + size // 2),
                (x + size // 2, y + size // 2)
            ]
        elif orientation == "downward":
            self.points = [
                (x, y + size // 2),  # apex at bottom
                (x - size // 2, y - size // 2),
                (x + size // 2, y - size // 2)
            ]
        else:  # orientation == "right"
            self.points = [
                (x + size // 2, y),  # apex to the right
                (x - size // 2, y - size // 2),
                (x - size // 2, y + size // 2)
            ]

        self.current_bet = 0
        self.current_chip = None
        self.bet_history = []
        self.flash_color = None
        self.flash_start_time = 0
        self.flashing = False
        self.flash_duration = 500

    def draw(self):
        # Draw polygon border in flashing color or black
        if self.flashing:
            pygame.draw.polygon(screen, self.flash_color, self.points, TRIANGLE_BORDER)
        else:
            pygame.draw.polygon(screen, BLACK, self.points, TRIANGLE_BORDER)

        # Calculate centroid for label and chip
        centroid_x = sum(pt[0] for pt in self.points) / 3
        centroid_y = sum(pt[1] for pt in self.points) / 3

        # Draw the label (moved 1 pixel left from original position)
        font = pygame.font.Font(None, 36)
        label_surf = font.render(self.label, True, ORANGE)
        label_rect = label_surf.get_rect(center=(centroid_x, centroid_y))
        screen.blit(label_surf, label_rect)

        # Draw bet amount to the right of the triangle
        if self.current_bet > 0:
            bet_font = pygame.font.Font(None, 24)
            bet_text = bet_font.render(f"£{self.current_bet}", True, ORANGE)
            # Adjust the position to be on the right side of the triangle
            bet_rect = bet_text.get_rect(midleft=(centroid_x + self.size // 2 + 10, centroid_y))
            screen.blit(bet_text, bet_rect)

        # Draw the chip on top of the label (moved 1 pixel to the right)
        if self.current_chip:
            chip_x = int(centroid_x) + 1  # Move chip 1 pixel to the right
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
        """
        Return the total bet to the player's wallet if the round hasn't started.
        """
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

class Dice:
    """
    Represents a single die with a rolling animation and a drawn face.
    """
    def __init__(self, x: int, y: int, size: int):
        self.x = x
        self.y = y
        self.size = size
        self.value = 1
        self.rolling = False
        self.roll_start_time = 0
        self.roll_duration = 3000
        self.shake_offset = 0
        self.shake_frequency = 10
        self.shake_amplitude = 3

    def roll(self):
        self.rolling = True
        self.roll_start_time = pygame.time.get_ticks()
        self.shake_offset = 0

    def update(self):
        if self.rolling:
            now = pygame.time.get_ticks()
            elapsed = now - self.roll_start_time
            if elapsed >= self.roll_duration:
                self.rolling = False
                self.shake_offset = 0
            else:
                # Random value while rolling
                self.value = random.randint(1, 6)
                # Shake effect
                self.shake_offset = self.shake_amplitude * math.sin((elapsed / 100) * self.shake_frequency)

    def draw(self, highlight=False):
        pygame.draw.rect(
            screen,
            WHITE,
            (
                self.x + self.shake_offset,
                self.y + self.shake_offset,
                self.size,
                self.size
            )
        )
        border_color = ORANGE if highlight else BLACK
        pygame.draw.rect(
            screen,
            border_color,
            (
                self.x + self.shake_offset,
                self.y + self.shake_offset,
                self.size,
                self.size
            ),
            4
        )
        self.draw_dice_face(
            int(self.x + self.shake_offset),
            int(self.y + self.shake_offset),
            self.size,
            self.value
        )

    def draw_dice_face(self, x, y, size, value):
        dot_color = BLACK
        center_x = x + size // 2
        center_y = y + size // 2
        r = 3

        if value == 1:
            pygame.draw.circle(screen, dot_color, (center_x, center_y), r)
        elif value == 2:
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size * 3 // 4), r)
        elif value == 3:
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (center_x, center_y), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size * 3 // 4), r)
        elif value == 4:
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size * 3 // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size * 3 // 4), r)
        elif value == 5:
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (center_x, center_y), r)
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size * 3 // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size * 3 // 4), r)
        elif value == 6:
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size // 2), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size // 2), r)
            pygame.draw.circle(screen, dot_color, (x + size // 4, y + size * 3 // 4), r)
            pygame.draw.circle(screen, dot_color, (x + size * 3 // 4, y + size * 3 // 4), r)

class ChanceoChillGame:
    def __init__(self):
        # Start with a fresh deck
        self.deck = Deck(3)
        self.dealer_hand: List[Card] = []
        self.player_hand: List[Card] = []
        self.game_state = "WAITING"
        self.wallet = WALLET_AMOUNT

        self.chips = self.create_chips()

        self.betting_triangle_13f = BettingTriangle(
            150, 300, TRIANGLE_SIZE, label="13f", orientation="upright"
        )
        self.betting_triangle = BettingTriangle(
            150, 380, TRIANGLE_SIZE, label="B", orientation="downward"
        )

        self.dealing_animation = False
        self.dealing_start_time = 0
        self.cards_to_deal = 4
        self.chance_card_count = 0
        self.chance_side = 0
        self.player_cards_revealed = False

        self.dice1 = Dice(SCREEN_WIDTH - 246 + 6, 250, DICE_SIZE)
        self.dice2 = Dice(
            SCREEN_WIDTH - 246 + DICE_SIZE + DICE_SPACING + 4 + 6,
            250,
            DICE_SIZE
        )
        self.active_dice_index = 1
        self.dice_total = 0
        self.dice_rolling = False
        self.dice_roll_start_time = 0
        self.dice_roll_complete = False

        self.active_chip = None

        self.show_previous_round = False
        self.show_credits = False
        self.round_history = []

        self.deal_initial_cards()

    def create_chips(self):
        chips_list = []
        start_y = 255
        for i, val in enumerate(CHIP_VALUES):
            chip_x = 50
            chip_y = start_y + i * (CHIP_RADIUS * 2 + 5)
            chips_list.append(Chip(val, chip_x, chip_y, CHIP_COLORS[i]))
        return chips_list

    def handle_chip_click(self, mouse_pos):
        for chip in self.chips:
            if chip.rect.collidepoint(mouse_pos):
                if self.active_chip == chip:
                    self.active_chip = None
                else:
                    self.active_chip = chip
                return True
        return False

    def handle_betting_space_click(self, mouse_pos):
        """
        Revised method to ensure no bet is placed if wallet is insufficient.
        """
        if self.active_chip:
            if self.wallet < self.active_chip.value:
                print("Insufficient funds to place this bet!")
                return False

            if self.betting_triangle.is_clicked(mouse_pos):
                if self.game_state == "WAITING":
                    self.betting_triangle.place_bet(self.active_chip.value)
                else:
                    self.betting_triangle.place_chance_bet(self.active_chip.value)
                self.betting_triangle.current_chip = self.active_chip
                self.wallet -= self.active_chip.value
                return True
            elif self.betting_triangle_13f.is_clicked(mouse_pos):
                if self.game_state == "WAITING":
                    self.betting_triangle_13f.place_bet(self.active_chip.value)
                else:
                    self.betting_triangle_13f.place_chance_bet(self.active_chip.value)
                self.betting_triangle_13f.current_chip = self.active_chip
                self.wallet -= self.active_chip.value
                return True

        if self.betting_triangle.is_clicked(mouse_pos):
            self.show_previous_round = True

        return False

    def handle_wallet_click(self, mouse_pos):
        wallet_rect = pygame.Rect(40, 156, 100, 40)
        if wallet_rect.collidepoint(mouse_pos):
            self.show_credits = True

    def start_dice_roll(self):
        self.dice1.roll()
        self.dice2.roll()
        self.dice_rolling = True
        self.dice_roll_start_time = pygame.time.get_ticks()
        self.dice_roll_complete = False

    def update_dice_roll(self):
        if self.dice_rolling:
            now = pygame.time.get_ticks()
            if now - self.dice_roll_start_time >= 3000:
                self.dice_rolling = False
                self.dice_roll_complete = True
                self.dice_total = self.dice1.value + self.dice2.value

                if self.betting_triangle.current_bet > 0:
                    self.reveal_dealer_cards()

                self.determine_winner()
                self.game_state = "ROUND_OVER"
            else:
                self.dice1.update()
                self.dice2.update()

    def reveal_dealer_cards(self):
        for c in self.dealer_hand:
            c.face_up = True

    def reveal_player_cards(self):
        limit = min(len(self.player_hand), 4)
        for i in range(limit):
            self.player_hand[i].face_up = True
        self.player_cards_revealed = True

    def add_chance_cards(self):
        if not self.player_cards_revealed:
            return
        new_cards = []
        to_add = min(2, 8 - len(self.player_hand))
        for _ in range(to_add):
            c = self.deck.draw()
            if c:
                c.face_up = True
                new_cards.append(c)
        if len(self.player_hand) >= 4:
            for new_card in new_cards:
                if self.chance_side == 0:
                    self.player_hand.insert(4 + (self.chance_card_count * 2), new_card)
                    self.chance_side = 1
                else:
                    self.player_hand.insert(4 + (self.chance_card_count * 2) + 1, new_card)
                    self.chance_side = 0
                self.chance_card_count += 1
        else:
            self.player_hand.extend(new_cards)

    def reset_game(self):
        """
        Only shuffle into a new Deck if 24 or fewer cards remain.
        Otherwise, reuse the existing Deck.
        """
        if self.deck.cards_remaining() <= 24:
            self.deck = Deck(3)

        self.dealer_hand.clear()
        self.player_hand.clear()
        self.betting_triangle.stop_flash()
        self.betting_triangle_13f.stop_flash()

        self.betting_triangle.clear_bets()
        self.betting_triangle_13f.clear_bets()

        self.chance_card_count = 0
        self.chance_side = 0
        self.player_cards_revealed = False
        self.dice_total = 0
        self.dice_rolling = False
        self.dice_roll_complete = False
        self.show_previous_round = False
        self.show_credits = False

        self.active_dice_index = 2 if self.active_dice_index == 1 else 1
        self.deal_initial_cards()

    def deal_initial_cards(self):
        self.dealer_hand.clear()
        self.player_hand.clear()
        self.dealing_animation = True
        self.dealing_start_time = pygame.time.get_ticks()

        for _ in range(4):
            c = self.deck.draw()
            if c:
                c.face_up = False
                self.player_hand.append(c)
        for _ in range(6):
            c = self.deck.draw()
            if c:
                c.face_up = False
                self.dealer_hand.append(c)

    def update_dealing_animation(self):
        if self.dealing_animation:
            now = pygame.time.get_ticks()
            if now - self.dealing_start_time > 500:
                self.dealing_animation = False
                self.game_state = "PLAYING"

    def get_card_value(self, card: Card) -> int:
        """
        A=1, J=2, K=3, Q=4, Joker=5, else=0
        """
        if card.rank == 'A':
            return 1
        elif card.rank in ['J', 'Q', 'K']:
            return 2 if card.rank == 'J' else (3 if card.rank == 'K' else 4)
        elif 'Joker' in card.rank:
            return 5
        return 0

    def calculate_hand_value(self, hand: List[Card]) -> int:
        return sum(self.get_card_value(c) for c in hand)

    def determine_winner(self):
        p_val = self.calculate_hand_value(self.player_hand)
        d_val = self.calculate_hand_value(self.dealer_hand)
        p_diff = abs(self.dice_total - p_val)
        d_diff = abs(self.dice_total - d_val)

        if self.betting_triangle.current_bet > 0:
            bet_amount = self.betting_triangle.current_bet
            lost = True
            if p_val > 12 and d_val > 12:
                self.betting_triangle.start_flash(RED)
            elif p_val > 12:
                self.betting_triangle.start_flash(RED)
            elif d_val > 12:
                self.wallet += bet_amount * 2
                self.betting_triangle.start_flash(GREEN)
                lost = False
            elif p_diff < d_diff:
                self.wallet += bet_amount * 2
                self.betting_triangle.start_flash(GREEN)
                lost = False
            elif p_diff > d_diff:
                self.betting_triangle.start_flash(RED)
            else:
                # Tie: push - return the bet to the player's wallet with no profit.
                self.wallet += bet_amount
                self.betting_triangle.start_flash(ORANGE)  # ORANGE indicates a push
                lost = False
                self.betting_triangle.current_bet = 0

            if lost:
                self.betting_triangle.current_bet = 0

        if self.betting_triangle_13f.current_bet > 0:
            bet_amount_13f = self.betting_triangle_13f.current_bet
            lost_13f = True
            active_value = max(self.dice1.value, self.dice2.value)
            if active_value in [1, 3, 5]:
                self.wallet += bet_amount_13f * 2  # 1:1 payout plus original bet
                self.betting_triangle_13f.start_flash(GREEN)
                lost_13f = False
            else:
                self.betting_triangle_13f.start_flash(RED)

            if lost_13f:
                self.betting_triangle_13f.current_bet = 0

        result_str = f"PlayerVal={p_val} DealerVal={d_val} Dice={self.dice_total}"
        self.round_history.append({
            "player_hand": [c for c in self.player_hand],
            "dealer_hand": [c for c in self.dealer_hand],
            "dice_values": (self.dice1.value, self.dice2.value),
            "result": result_str,
            "player_value": p_val,
            "dealer_value": d_val
        })

    def draw_round_history(self):
        font = pygame.font.Font(None, 24)
        start_y = 100
        for i, info in enumerate(self.round_history[-5:]):
            text = (
                f"Round {i+1}: "
                f"Player {info['player_value']} - "
                f"Dealer {info['dealer_value']} - "
                f"Dice {sum(info['dice_values'])} - "
                f"{info['result']}"
            )
            surf = font.render(text, True, BLACK)
            screen.blit(surf, (50, start_y + i * 30))

    def draw(self):
        if self.dice1.value >= self.dice2.value:
            self.dice1.draw(highlight=True)
            self.dice2.draw(highlight=False)
        else:
            self.dice1.draw(highlight=False)
            self.dice2.draw(highlight=True)

        self.betting_triangle.draw()
        self.betting_triangle_13f.draw()

        for chip in self.chips:
            if chip not in (self.betting_triangle.current_chip, self.betting_triangle_13f.current_chip):
                chip.draw(is_active=(chip == self.active_chip))

def draw_card(x: int, y: int, card: Optional[Card] = None):
    """
    Draw the card:
    If face-up, white background with rank/suit.
    If face-down, diagonal split:
    - Top-right corner: ORANGE
    - Bottom-left corner: BLACK
    """
    # Define corners
    tl = (x, y)
    tr = (x + CARD_WIDTH, y)
    bl = (x, y + CARD_HEIGHT)
    br = (x + CARD_WIDTH, y + CARD_HEIGHT)

    if card and card.face_up:
        # Draw the face with a white background
        pygame.draw.rect(screen, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
    else:
        # Draw the card back
        pygame.draw.polygon(screen, BLACK, [bl, tl, br])     # bottom-left triangle in black
        pygame.draw.polygon(screen, ORANGE, [tr, tl, br])    # top-right triangle in orange

    # Draw black/orange border lines
    pygame.draw.line(screen, ORANGE, tl, tr, 2)  # Top line in orange
    pygame.draw.line(screen, ORANGE, tr, br, 2)  # Right line in orange
    pygame.draw.line(screen, BLACK, bl, br, 2)   # Bottom line in black
    pygame.draw.line(screen, BLACK, tl, bl, 2)   # Left line in black

    # If there's a card and it's face-up, render suit/rank
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
    slot_positions = []
    for i in range(6):
        sx = start_x + i * (CARD_WIDTH + CARD_SPACING) - (CARD_WIDTH + CARD_SPACING)
        slot_positions.append((sx, y))

    for i, pos in enumerate(slot_positions):
        if i < len(cards):
            draw_card(pos[0], pos[1], cards[i])
        else:
            draw_card(pos[0], pos[1])

def draw_pyramid_layout(start_x: int, y: int, cards: List[Card]):
    positions = [
        (start_x - CARD_WIDTH // 2, y - CARD_HEIGHT - CARD_SPACING),
        (start_x - CARD_WIDTH - CARD_SPACING // 2, y),
        (start_x + CARD_SPACING // 2, y),
        (start_x - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING),
        (start_x - CARD_WIDTH - CARD_SPACING - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING),
        (start_x + CARD_WIDTH + CARD_SPACING - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING),
        (start_x - (CARD_WIDTH + CARD_SPACING) * 2 - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING),
        (start_x + (CARD_WIDTH + CARD_SPACING) * 2 - CARD_WIDTH // 2, y + CARD_HEIGHT + CARD_SPACING)
    ]
    for i, pos in enumerate(positions):
        if i < len(cards):
            draw_card(pos[0], pos[1], cards[i])
        else:
            draw_card(pos[0], pos[1])

def draw_wallet_and_chips(game: "ChanceoChillGame"):
    font = pygame.font.Font(None, 36)
    wallet_text = font.render("Wallet", True, BLACK)
    wallet_value = font.render(f"£{game.wallet}", True, BLACK)

    wallet_y_position = 156
    screen.blit(wallet_text, (40, wallet_y_position))
    screen.blit(wallet_value, (40, wallet_y_position + 40))

    game.betting_triangle.draw()
    game.betting_triangle_13f.draw()
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
        font = title_font if is_title else (copyright_font if i == len(lines) - 1 else regular_font)
        surf = font.render(line, True, BLACK)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, sy + i * 30))
        screen.blit(surf, rect)

def draw_previous_round(game: "ChanceoChillGame"):
    screen.fill(WHITE)
    if game.round_history:
        rd = game.round_history[-1]
        draw_dealer_layout(SCREEN_WIDTH // 2 - 150, 50, rd["dealer_hand"])
        draw_pyramid_layout(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 250, rd["player_hand"])

        dice1 = Dice(SCREEN_WIDTH - 246 + 6, 250, DICE_SIZE)
        dice2 = Dice(SCREEN_WIDTH - 246 + DICE_SIZE + DICE_SPACING + 4 + 6, 250, DICE_SIZE)
        dice1.value, dice2.value = rd["dice_values"]
        dice1.draw(highlight=False)
        dice2.draw(highlight=False)

def draw_buttons(chance_rect, chill_rect, undo_rect):
    font = pygame.font.Font(None, 24)

    pygame.draw.rect(screen, WHITE, chance_rect)
    pygame.draw.rect(screen, BLACK, chance_rect, 2)
    chance_surf = font.render("Chance", True, RED)
    chance_surf_rect = chance_surf.get_rect(center=chance_rect.center)
    screen.blit(chance_surf, chance_surf_rect)

    pygame.draw.rect(screen, WHITE, chill_rect)
    pygame.draw.rect(screen, BLACK, chill_rect, 2)
    chill_surf = font.render("Chill", True, RED)
    chill_surf_rect = chill_surf.get_rect(center=chill_rect.center)
    screen.blit(chill_surf, chill_surf_rect)

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
    game = ChanceoChillGame()
    if wallet is not None:
        game.wallet = wallet.balance

    chance_rect = pygame.Rect(570, 350, 80, 40)
    chill_rect = pygame.Rect(570, 400, 80, 40)
    undo_rect = pygame.Rect(660, 375, 80, 40)

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
            elif event.type == pygame.KEYDOWN:
                # Press SPACE in WAITING state if there's a bet => start a new round
                if event.key == pygame.K_SPACE and game.game_state == "WAITING":
                    if (game.betting_triangle.current_bet > 0
                        or game.betting_triangle_13f.current_bet > 0):
                        game.reset_game()
                        game.game_state = "PLAYING"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if embedded and back_rect and back_rect.collidepoint(pos):
                    continue

                if game.show_previous_round:
                    # Return to the game if anywhere is clicked on the history screen
                    game.show_previous_round = False
                elif game.show_credits:
                    # Return to the game if anywhere is clicked on the credits screen
                    game.show_credits = False
                elif chill_rect.collidepoint(pos) or chance_rect.collidepoint(pos) or undo_rect.collidepoint(pos):
                    if game.game_state == "ROUND_OVER":
                        game.betting_triangle.clear_bets()
                        game.betting_triangle_13f.clear_bets()
                        game.reset_game()
                        game.game_state = "PLAYING"
                    else:
                        if chill_rect.collidepoint(pos):
                            if (game.player_cards_revealed
                                or (game.betting_triangle_13f.current_bet > 0
                                    and game.betting_triangle.current_bet == 0)):
                                if game.game_state != "WAITING":
                                    game.start_dice_roll()
                        elif chance_rect.collidepoint(pos):
                            if game.betting_triangle.current_bet > 0:
                                if game.game_state == "ROUND_OVER":
                                    game.betting_triangle.clear_bets()
                                    game.betting_triangle_13f.clear_bets()
                                    game.reset_game()
                                    game.game_state = "PLAYING"
                                else:
                                    if (game.betting_triangle.current_bet > 0
                                        or game.betting_triangle_13f.current_bet > 0):
                                        if not game.player_cards_revealed:
                                            game.reveal_player_cards()
                                        else:
                                            game.add_chance_cards()
                        elif undo_rect.collidepoint(pos):
                            if game.game_state in ["WAITING", "PLAYING"] and not game.player_cards_revealed:
                                returned = game.betting_triangle.clear_bets_and_return()
                                returned += game.betting_triangle_13f.clear_bets_and_return()
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
            game.update_dealing_animation()
            game.update_dice_roll()
            draw_dealer_layout(SCREEN_WIDTH // 2 - 150, 50, game.dealer_hand)
            draw_pyramid_layout(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 250, game.player_hand)
            draw_wallet_and_chips(game)
            game.draw()
            draw_buttons(chance_rect, chill_rect, undo_rect)

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
    run_game_standalone(sys.modules[__name__], "Chanceo'chill")
