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


def _init_display(caption="Fanirafana"):
    global screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(caption)
    return screen

class Dice:
    SUITS = ['♠', '♥', '♦', '♣', '', '']
    NUMBERS = ['1', '2', '3', '4', '5', '6']

    def __init__(self, x, y, dice_type='suit'):
        self.x = x
        self.y = y
        self.size = DICE_SIZE
        self.dice_type = dice_type  # 'suit' or 'number'
        self.value = self.roll_value()
        self.rolling = False
        self.roll_start_time = 0
        self.roll_duration = 1500  # 1.5 seconds roll duration
        self.color = self.get_color()
        # Shake animation properties
        self.shake_magnitude = 5  # maximum offset for shaking
        self.offset_x = 0
        self.offset_y = 0
        # Timing for value change during rolling
        self.last_value_change = 0
        self.value_change_interval = 100  # ms between value changes

    def roll_value(self):
        if self.dice_type == 'suit':
            return random.choice(self.SUITS)
        else:
            return random.choice(self.NUMBERS)

    def get_color(self):
        if self.dice_type == 'suit':
            return RED if self.value in ['♥', '♦'] else BLACK
        else:
            return BLACK

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
            if current_time - self.last_value_change >= self.value_change_interval:
                self.value = self.roll_value()
                self.color = self.get_color()
                self.last_value_change = current_time
            if elapsed >= self.roll_duration:
                self.rolling = False
                self.value = self.roll_value()
                self.color = self.get_color()
                self.offset_x = 0
                self.offset_y = 0

    def draw(self):
        pos_x = self.x + self.offset_x
        pos_y = self.y + self.offset_y
        pygame.draw.rect(screen, WHITE, (pos_x, pos_y, self.size, self.size))
        pygame.draw.rect(screen, BLACK, (pos_x, pos_y, self.size, self.size), 2)
        # Only render text if the dice face is not blank (for suit dice)
        if self.value:
            font = pygame.font.Font(pygame.font.match_font("arial"), 36)
            text_surf = font.render(self.value, True, self.color)
            text_rect = text_surf.get_rect(center=(pos_x + self.size // 2, pos_y + self.size // 2))
            screen.blit(text_surf, text_rect)

class Card:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        self.color = RED if suit in ['♥', '♦'] else BLACK

    def flip(self):
        self.face_up = not self.face_up

    def __str__(self):
        return f"{self.rank}{self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        for _ in range(3):
            for suit in Card.SUITS:
                for rank in Card.RANKS:
                    self.cards.append(Card(suit, rank))
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        if self.cards:
            return self.cards.pop()
        return None

    def cards_remaining(self) -> int:
        return len(self.cards)

    def shuffle_if_needed(self):
        if len(self.cards) <= 72:
            self.cards = []
            for _ in range(3):
                for suit in Card.SUITS:
                    for rank in Card.RANKS:
                        self.cards.append(Card(suit, rank))
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
    def __init__(self, x: int, y: int, size: int, label="F", orientation="upright"):
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

class FanirafanaGame:
    def __init__(self):
        self.deck = Deck()
        # 2 suit dice (ends), 2 number dice (middle)
        dice_positions = [SCREEN_WIDTH // 2 - 150 + i * (DICE_SIZE + 20) for i in range(4)]
        self.dice = [
            Dice(dice_positions[0], 70, 'suit'),
            Dice(dice_positions[1], 70, 'number'),
            Dice(dice_positions[2], 70, 'number'),
            Dice(dice_positions[3], 70, 'suit')
        ]
        self.player_hand: List[Card] = []
        self.game_state = "WAITING"
        self.wallet = WALLET_AMOUNT
        self.chips = self.create_chips()
        self.betting_triangle = BettingTriangle(150, 380, TRIANGLE_SIZE, label="F", orientation="right")
        self.dealing_animation = False
        self.dealing_start_time = 0
        self.cards_to_deal = 8
        self.player_cards_revealed = False
        self.active_chip = None
        self.show_previous_round = False
        self.show_credits = False
        self.round_history = []
        self.player_flip_index = 0
        self.player_flip_order = list(range(8))
        self.last_flip_time = 0
        self.flip_interval = 500
        self.dice_roll_start = None
        self.reroll_timer = None
        self.reroll_delay = 1000
        self.num_rerolls = 0
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
        if self.active_chip:
            if self.wallet < self.active_chip.value:
                print("Insufficient funds!")
                return False
            if self.betting_triangle.is_clicked(mouse_pos):
                self.betting_triangle.place_bet(self.active_chip.value)
                self.betting_triangle.current_chip = self.active_chip
                self.wallet -= self.active_chip.value
                return True
        if self.betting_triangle.is_clicked(mouse_pos):
            self.show_previous_round = True
        return False

    def handle_wallet_click(self, mouse_pos):
        wallet_rect = pygame.Rect(40, 200, 100, 40)
        if wallet_rect.collidepoint(mouse_pos):
            self.show_credits = True

    def roll_all_dice(self):
        for die in self.dice:
            die.roll()
        self.reroll_timer = None

    def reveal_player_cards(self):
        for card in self.player_hand:
            card.face_up = True
        self.player_cards_revealed = True

    def reset_game(self):
        self.deck.shuffle_if_needed()
        self.player_hand.clear()
        self.betting_triangle.stop_flash()
        self.betting_triangle.clear_bets()
        self.player_cards_revealed = False
        self.show_previous_round = False
        self.show_credits = False
        self.game_state = "PLAYING"
        self.player_flip_index = 0
        self.last_flip_time = 0
        self.num_rerolls = 0
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
                self.player_cards_revealed = True
                self.determine_winner()

    def process_rolling_dice(self):
        """Resolves the ROLLING_DICE state: re-rolls once on 11/12 totals or double-blank
        suits, then pushes if the re-roll still lands on one of those outcomes."""
        if not all(not die.rolling for die in self.dice):
            return
        number_dice = [die for die in self.dice if die.dice_type == 'number']
        suit_dice = [die for die in self.dice if die.dice_type == 'suit']
        try:
            total = int(number_dice[0].value) + int(number_dice[1].value)
        except (ValueError, IndexError):
            total = 0
        suit1 = suit_dice[0].value
        suit2 = suit_dice[1].value
        needs_reroll = total in [11, 12] or (suit1 == '' and suit2 == '')

        if needs_reroll and self.num_rerolls < 1:
            # Only one auto re-roll is allowed before resolving as a push.
            current_time = pygame.time.get_ticks()
            if self.reroll_timer is None:
                self.reroll_timer = current_time
            elif current_time - self.reroll_timer >= self.reroll_delay:
                self.num_rerolls += 1
                self.roll_all_dice()
                self.dice_roll_start = pygame.time.get_ticks()
        elif needs_reroll:
            self.game_state = "ROUND_OVER"
            self.determine_winner()
        else:
            self.game_state = "FLIPPING_PLAYER"
            self.player_flip_index = 0
            self.last_flip_time = pygame.time.get_ticks()

    def determine_winner(self):
        # Get dice values
        number_dice = [die for die in self.dice if die.dice_type == 'number']
        suit_dice = [die for die in self.dice if die.dice_type == 'suit']
        try:
            num1 = int(number_dice[0].value)
            num2 = int(number_dice[1].value)
        except (ValueError, IndexError):
            self.round_history.append({'result': 'Invalid dice roll.'})
            self.betting_triangle.start_flash(RED)
            return
        winning_number = num1 + num2
        suit1 = suit_dice[0].value
        suit2 = suit_dice[1].value
        # If number is 11 or 12, the round is a push (no win/loss)
        if winning_number > 10:
            returned = self.betting_triangle.clear_bets_and_return()
            self.wallet += returned
            self.round_history.append({
                'result': f'Push. Dice sum is {winning_number} (11 or 12). Bet returned.',
                'winning_number': winning_number,
                'winning_suits': [suit1, suit2],
                'player_hand': list(self.player_hand)
            })
            return
        # Determine required suits
        if suit1 == '' and suit2 == '':
            # Both suit dice are blank: round is a push, bet returned
            returned = self.betting_triangle.clear_bets_and_return()
            self.wallet += returned
            self.round_history.append({
                'result': 'Push. Both suit dice are blank. Bet returned.',
                'winning_number': winning_number,
                'winning_suits': [suit1, suit2],
                'player_hand': list(self.player_hand)
            })
            return
        elif suit1 == '':
            required_suits = [suit2]
        elif suit2 == '':
            required_suits = [suit1]
        else:
            required_suits = [suit1, suit2]
        # Check player hand
        found = False
        for card in self.player_hand:
            if card.rank == str(winning_number):
                if required_suits is None or card.suit in required_suits:
                    found = True
                    break
        if found:
            self.betting_triangle.start_flash(GREEN)
            # PAYOUT 5:1 plus original bet (total 6x)
            self.wallet += self.betting_triangle.current_bet * 6
            self.round_history.append({
                'result': f'Player wins! Needs {winning_number} ' + (f'of {" or ".join(required_suits)}' if required_suits else ''),
                'winning_number': winning_number,
                'winning_suits': required_suits,
                'player_hand': list(self.player_hand)
            })
        else:
            self.betting_triangle.start_flash(RED)
            self.round_history.append({
                'result': f'Player loses. Needs {winning_number} ' + (f'of {" or ".join(required_suits)}' if required_suits else '') + ' but not found.',
                'winning_number': winning_number,
                'winning_suits': required_suits,
                'player_hand': list(self.player_hand)
            })

    # For demonstration, let's just draw the dice and cards
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
        suit_surface_top = font.render(card.suit, True, card.color)
        top_rect = suit_surface_top.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 4))
        screen.blit(suit_surface_top, top_rect)
        rank_surface = font.render(card.rank, True, card.color)
        rank_rect = rank_surface.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
        screen.blit(rank_surface, rank_rect)
        suit_surface_bottom = font.render(card.suit, True, card.color)
        bot_rect = suit_surface_bottom.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT * 3 // 4))
        screen.blit(suit_surface_bottom, bot_rect)

def draw_fanirafana_layout(start_x: int, y: int, cards: List[Card]):
    # 2 rows: 4 cards on top, 4 on bottom
    row_spacing = CARD_HEIGHT + 30
    col_spacing = CARD_WIDTH + 20
    top_row_y = y - row_spacing // 2
    bottom_row_y = y + row_spacing // 2
    for i in range(8):
        row = 0 if i < 4 else 1
        col = i % 4
        card_x = start_x - (3 * col_spacing // 2) + col * col_spacing
        card_y = top_row_y if row == 0 else bottom_row_y
        if i < len(cards):
            draw_card(card_x, card_y, cards[i])
        else:
            draw_card(card_x, card_y)

def draw_wallet_and_chips(game: "FanirafanaGame"):
    font = pygame.font.Font(None, 36)
    wallet_y_position = 200
    wallet_text = font.render("Wallet", True, BLACK)
    wallet_value = font.render(f"£{game.wallet}", True, BLACK)
    screen.blit(wallet_text, (40, wallet_y_position))
    screen.blit(wallet_value, (40, wallet_y_position + 40))
    game.betting_triangle.draw()
    for chip in game.chips:
        chip.draw()

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
    game = FanirafanaGame()
    if wallet is not None:
        game.wallet = wallet.balance
    # Move buttons further right
    flip_rect = pygame.Rect(659, 324, 80, 40)
    undo_rect = pygame.Rect(659, 374, 80, 40)
    history_rect = pygame.Rect(659, 424, 80, 40)
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
                            # game.determine_winner()  # Add winner logic as needed
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
                                if game.game_state == "PLAYING" and game.betting_triangle.current_bet > 0:
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
                game.process_rolling_dice()
            elif game.game_state == "FLIPPING_PLAYER":
                game.update_flip_animation()

            game.update_dealing_animation()
            # Center cards between the leftmost and rightmost dice
            dice_left = SCREEN_WIDTH // 2 - 150
            dice_right = SCREEN_WIDTH // 2 - 150 + 3 * (DICE_SIZE + 20)
            cards_width = 3 * (CARD_WIDTH + 20)
            cards_center_x = (dice_left + dice_right) // 2 + DICE_SIZE // 2 - 40  # shift slightly left
            draw_fanirafana_layout(cards_center_x, SCREEN_HEIGHT - 250, game.player_hand)
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
    run_game_standalone(sys.modules[__name__], "Fanirafana")
