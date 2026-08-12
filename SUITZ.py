import pygame
import sys
import random
from collections import namedtuple
import time

pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CHIP_RADIUS = 20
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
CARD_WIDTH = 120
CARD_HEIGHT = 162
DICE_SIZE = 40

# Match the chip colors used in Chance O' Chill
CHIP_COLORS = [
    (255, 51, 255),    # Neon pink for £10
    (57, 255, 20),     # Neon green for £20
    (0, 255, 255),     # Neon blue for £50
    (255, 255, 0),     # Neon yellow for £100
    (255, 127, 0)      # Neon orange for £200
]

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED_COLOR = (255, 0, 0)
DARK_BLUE = (0, 255, 255)  # Card deck/back color
GREEN_COLOR = (0, 128, 0)  # Winning bets color
GOLD_COLOR = (184, 134, 11)  # Betting space amounts

# Initialize Screen (deferred when embedded in Casino Sfeer menu)
screen = None
clock = None


def _init_display(caption="Sui'tz"):
    global screen, clock
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(caption)
    if clock is None:
        clock = pygame.time.Clock()
    return screen

# Game State Variables
betting_chips = []
history = []
round_count = 0
# When showing_history is True the credits screen is shown.
showing_history = False  
history_data = None
placed_bets = set()
showing_wallet_info = False  # remains for wallet label clicks

# Card and Dice Variables
Card = namedtuple('Card', ['rank', 'suit'])
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
JOKERS = [Card('Joker', 'Red'), Card('Joker', 'Black')]
current_cards = []
dice_value = random.randint(1, 7)
animation_start_time = 0
is_rolling = False
is_dealing = False

# Wallet and Chip Values
wallet_balance = 1000
CHIP_VALUES = [10, 20, 50, 100, 200]

# Additional State Variables
active_chip = None
results_display_start_time = 0
RESULTS_DISPLAY_DELAY = 3000  # 3 seconds
cards_revealed = False
results_displayed = False

class Button:
    def __init__(self, x, y, width, height, text, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.text_surface = self.font.render(text, True, RED_COLOR)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        self.color = WHITE

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 3)
        screen.blit(self.text_surface, self.text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class CardRenderer:
    def __init__(self, card_width, card_height):
        self.card_width = card_width
        self.card_height = card_height
        self.suit_symbols = {'♠': '♠', '♥': '♥', '♦': '♦', '♣': '♣'}
        self.suit_colors = {'♠': (0, 0, 0), '♥': (255, 0, 0), '♦': (255, 0, 0), '♣': (0, 0, 0)}
        self.setup_fonts()

    def setup_fonts(self):
        try:
            self.rank_font = pygame.font.SysFont('dejavusans', 24, bold=True)
            self.suit_font = pygame.font.SysFont('dejavusans', 20, bold=True)
        except:
            self.rank_font = pygame.font.Font(None, 24)
            self.suit_font = pygame.font.Font(None, 20)

    def render_card(self, surface, card, x, y):
        pygame.draw.rect(surface, WHITE, (x, y, self.card_width, self.card_height))
        pygame.draw.rect(surface, BLACK, (x, y, self.card_width, self.card_height), 2)
        if card:
            if card.rank == "Joker":
                suit_color = RED_COLOR if card.suit.lower() == "red" else BLACK
                rank_text = self.rank_font.render("Joker", True, suit_color)
                suit_text = self.suit_font.render("", True, suit_color)
            else:
                suit_color = self.suit_colors.get(card.suit, BLACK)
                rank_text = self.rank_font.render(card.rank, True, suit_color)
                suit_text = self.suit_font.render(self.suit_symbols.get(card.suit, ''), True, suit_color)
            padding = 5
            rank_rect_top = rank_text.get_rect(topleft=(x + padding, y + padding))
            suit_rect_top = suit_text.get_rect(topleft=(x + padding, y + rank_rect_top.height + 2))
            rank_rect_bottom = rank_text.get_rect(bottomright=(x + self.card_width - padding, y + self.card_height - padding))
            suit_rect_bottom = suit_text.get_rect(bottomright=(x + self.card_width - padding, y + self.card_height - rank_rect_bottom.height - 2))
            surface.blit(rank_text, rank_rect_top)
            surface.blit(suit_text, suit_rect_top)
            rotated_rank = pygame.transform.rotate(rank_text, 180)
            rotated_suit = pygame.transform.rotate(suit_text, 180)
            surface.blit(rotated_rank, rank_rect_bottom)
            surface.blit(rotated_suit, suit_rect_bottom)

    def render_card_back(self, surface, x, y, _back_color):
        pygame.draw.rect(surface, WHITE, (x, y, self.card_width, self.card_height))
        inner_x = x + 3
        inner_y = y + 3
        inner_width = self.card_width - 6
        inner_height = self.card_height - 6
        stripe_height = inner_height // 2
        pygame.draw.rect(surface, BLACK, (inner_x, inner_y, inner_width, stripe_height))
        pygame.draw.rect(surface, RED_COLOR, (inner_x, inner_y + stripe_height, inner_width, inner_height - stripe_height))
        pygame.draw.rect(surface, BLACK, (x, y, self.card_width, self.card_height), 2)

    def render_deck(self, surface, x, y, deck_size, back_color):
        if deck_size > 0:
            self.render_card_back(surface, x, y, back_color)

class CardAnimation:
    def __init__(self, card_width, card_height):
        self.card_width = card_width
        self.card_height = card_height
        self.animation_duration = 1000  # ms for slower reveal
        self.animations = []
        self.card_renderer = CardRenderer(card_width, card_height)

    class SingleCardAnimation:
        def __init__(self, start_time, card, x, y):
            self.start_time = start_time
            self.card = card
            self.x = x
            self.y = y
            self.completed = False
            self.revealed = False
            self.flip_progress = 0

    def start_card_reveal(self, cards, start_positions):
        current_time = pygame.time.get_ticks()
        self.animations = []
        for i, (card, pos) in enumerate(zip(cards, start_positions)):
            start_time = current_time + (i * 200)
            self.animations.append(self.SingleCardAnimation(start_time, card, pos[0], pos[1]))

    def draw_animated_cards(self, screen, current_time, card_back_color):
        for anim in self.animations:
            if anim.completed:
                self.card_renderer.render_card(screen, anim.card, anim.x, anim.y)
                continue
            elapsed = current_time - anim.start_time
            if elapsed < 0:
                self.card_renderer.render_card_back(screen, anim.x, anim.y, card_back_color)
                continue
            if elapsed >= self.animation_duration:
                anim.completed = True
                anim.revealed = True
                self.card_renderer.render_card(screen, anim.card, anim.x, anim.y)
                continue
            anim.flip_progress = min(1, elapsed / self.animation_duration)
            self._draw_flipped_card(screen, anim, card_back_color)

    def _draw_flipped_card(self, screen, anim, card_back_color):
        flip_progress = anim.flip_progress
        width_scale = abs(2 * flip_progress - 1)
        current_width = int(self.card_width * width_scale)
        x_offset = (self.card_width - current_width) // 2
        temp_surface = pygame.Surface((self.card_width, self.card_height), pygame.SRCALPHA)
        if flip_progress < 0.5:
            self.card_renderer.render_card_back(temp_surface, 0, 0, card_back_color)
        else:
            self.card_renderer.render_card(temp_surface, anim.card, 0, 0)
        scaled_surface = pygame.transform.scale(temp_surface, (current_width, self.card_height))
        screen.blit(scaled_surface, (anim.x + x_offset, anim.y))

    def is_animation_complete(self):
        return all(anim.completed for anim in self.animations)

class DiceAnimation:
    def __init__(self, dice_size):
        self.dice_size = dice_size
        self.animation_duration = 3000  # ms
        self.frames_per_roll = 20
        self.roll_interval = 50
        self.current_value = 1
        self.final_value = 1
        self.start_time = 0
        self.is_rolling = False
        self.last_roll_time = 0

    def start_roll(self, final_value):
        self.start_time = pygame.time.get_ticks()
        self.final_value = final_value
        self.is_rolling = True
        self.last_roll_time = self.start_time

    def update(self, current_time):
        if not self.is_rolling:
            return self.final_value
        elapsed = current_time - self.start_time
        if elapsed >= self.animation_duration:
            self.is_rolling = False
            self.current_value = self.final_value
        else:
            progress = elapsed / self.animation_duration
            if current_time - self.last_roll_time >= self.roll_interval:
                if progress < 0.8:
                    self.current_value = random.randint(1, 7)
                else:
                    if random.random() > (progress - 0.8) * 5:
                        self.current_value = random.randint(1, 7)
                    else:
                        self.current_value = self.final_value
                self.last_roll_time = current_time
        return self.current_value

    def draw(self, screen, x, y, value):
        if self.is_rolling:
            wobble = random.randint(-2, 2)
            x += wobble
            y += wobble
        pygame.draw.rect(screen, WHITE, (x, y, self.dice_size, self.dice_size))
        pygame.draw.rect(screen, BLACK, (x, y, self.dice_size, self.dice_size), 2)
        dot_positions = {
            1: [(self.dice_size//2, self.dice_size//2)],
            2: [(self.dice_size//4, self.dice_size//4), (3*self.dice_size//4, 3*self.dice_size//4)],
            3: [(self.dice_size//4, self.dice_size//4), (self.dice_size//2, self.dice_size//2), (3*self.dice_size//4, 3*self.dice_size//4)],
            4: [(self.dice_size//4, self.dice_size//4), (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//4, 3*self.dice_size//4), (3*self.dice_size//4, 3*self.dice_size//4)],
            5: [(self.dice_size//4, self.dice_size//4), (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//2, self.dice_size//2), (self.dice_size//4, 3*self.dice_size//4),
                (3*self.dice_size//4, 3*self.dice_size//4)],
            6: [(self.dice_size//4, self.dice_size//4), (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//4, self.dice_size//2), (3*self.dice_size//4, self.dice_size//2),
                (self.dice_size//4, 3*self.dice_size//4), (3*self.dice_size//4, 3*self.dice_size//4)],
            7: [(self.dice_size//4, self.dice_size//4), (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//2, self.dice_size//2), (self.dice_size//4, 3*self.dice_size//4),
                (3*self.dice_size//4, 3*self.dice_size//4)]
        }
        for dot in dot_positions.get(value, []):
            dot_x, dot_y = dot
            pygame.draw.circle(screen, BLACK, (x + dot_x, y + dot_y), 3)

class ResultsDisplay:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.display_duration = 3000
        self.start_time = 0
        self.results = []
        self.showing_results = False
        self.flash_state = False
        self.last_flash_time = 0
        self.flash_interval = 500

    def show_results(self, cards, dice_value, bets):
        self.results.clear()
        if dice_value in [1, 2, 3, 4]:
            winning_card_index = dice_value - 1
            commission = 1.0
        elif dice_value in [5, 6]:
            winning_card_index = 1 if dice_value == 5 else 3
            commission = 0.5
        elif dice_value == 7:
            winning_card_index = 3
            commission = 1.0
        else:
            winning_card_index = None
            commission = 0.0

        if winning_card_index is not None:
            winning_card = cards[winning_card_index]
            for suit in SUITS:
                if suit in bets:
                    if winning_card.suit == suit:
                        base_win = bets[suit] * 3
                        win_amount = int((base_win + bets[suit]) * commission)
                        self.results.append((suit, bets[suit], win_amount, "Win!"))
                    else:
                        self.results.append((suit, bets[suit], 0, "Loss"))
            if 'J' in bets:
                if winning_card.rank == "Joker":
                    base_win = bets['J'] * 50
                    win_amount = int((base_win + bets['J']) * commission)
                    self.results.append(('J', bets['J'], win_amount, "Win!"))
                else:
                    self.results.append(('J', bets['J'], 0, "Loss"))
        else:
            for suit in SUITS + ['J']:
                if suit in bets:
                    self.results.append((suit, bets[suit], 0, "Loss"))
        self.showing_results = True
        self.start_time = pygame.time.get_ticks()
        self.last_flash_time = self.start_time

    def draw(self, screen, bet_circles):
        if not self.showing_results:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_flash_time > self.flash_interval:
            self.flash_state = not self.flash_state
            self.last_flash_time = current_time
        if not self.flash_state:
            return
        for bet_type, amount, winnings, _ in self.results:
            color = GREEN_COLOR if winnings > 0 else RED_COLOR
            pygame.draw.circle(screen, color, bet_circles[bet_type].center, bet_circles[bet_type].width // 2, 5)

    def stop_flashing(self):
        self.showing_results = False

class UI:
    def __init__(self):
        self.chip_font = pygame.font.Font(None, 16)
        self.button_font = pygame.font.Font(None, 24)
        self.wallet_font = pygame.font.Font(None, 30)
        button_x = 150
        base_y = SCREEN_HEIGHT // 2 + 30
        spacing = 50
        self.bet_button = Button(button_x, base_y - spacing, BUTTON_WIDTH, BUTTON_HEIGHT, "Bet")
        self.undo_button = Button(button_x, base_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Undo")
        self.history_button = Button(button_x, base_y + spacing, BUTTON_WIDTH, BUTTON_HEIGHT, "History")
        self.return_button = Button(button_x, base_y + spacing * 2, BUTTON_WIDTH, BUTTON_HEIGHT, "Return")
        self.card_renderer = CardRenderer(CARD_WIDTH, CARD_HEIGHT)
        self.card_animator = CardAnimation(CARD_WIDTH, CARD_HEIGHT)
        self.dice_animator = DiceAnimation(DICE_SIZE)
        self.results_display = ResultsDisplay()

    def draw_wallet(self, screen):
        wallet_text = self.wallet_font.render(f"Wallet: £{wallet_balance}", True, BLACK)
        self.wallet_rect = wallet_text.get_rect(topleft=(20, 500))
        screen.blit(wallet_text, self.wallet_rect)

    def draw_chips(self, screen):
        global active_chip
        for i, color in enumerate(CHIP_COLORS):
            chip_center = (30 + i * 60, 560)
            if active_chip and active_chip[0] == color:
                pygame.draw.circle(screen, (255, 255, 0), chip_center, CHIP_RADIUS + 3)
            pygame.draw.circle(screen, color, chip_center, CHIP_RADIUS)
            pygame.draw.circle(screen, BLACK, chip_center, CHIP_RADIUS, 3)
            chip_text = self.chip_font.render(f"£{CHIP_VALUES[i]}", True, BLACK)
            text_rect = chip_text.get_rect(center=chip_center)
            screen.blit(chip_text, text_rect)

    def draw_buttons(self, screen):
        self.bet_button.draw(screen)
        self.undo_button.draw(screen)
        self.history_button.draw(screen)
        if showing_history or showing_wallet_info:
            self.return_button.draw(screen)

    def draw_ui_elements(self, screen):
        self.draw_wallet(screen)
        self.draw_chips(screen)
        self.draw_buttons(screen)

    def draw_card_slots(self, screen):
        total_width = 4 * (CARD_WIDTH + 20)
        start_x = (SCREEN_WIDTH - total_width) // 2 + 8
        for i in range(4):
            x = start_x + i * (CARD_WIDTH + 20)
            y = 20
            pygame.draw.rect(screen, WHITE, (x, y, CARD_WIDTH, CARD_HEIGHT))
            pygame.draw.rect(screen, BLACK, (x, y, CARD_WIDTH, CARD_HEIGHT), 2)

    def draw_cards(self, screen):
        if current_cards:
            self.card_animator.draw_animated_cards(screen, pygame.time.get_ticks(), DARK_BLUE)

    def draw_static_cards(self, screen):
        if current_cards and cards_revealed:
            total_width = 4 * (CARD_WIDTH + 20)
            start_x = (SCREEN_WIDTH - total_width) // 2 + 8
            card_positions = [(start_x + i * (CARD_WIDTH + 20), 20) for i in range(4)]
            for card, pos in zip(current_cards, card_positions):
                self.card_renderer.render_card(screen, card, pos[0], pos[1])

    def draw_dice(self, screen):
        dice_start_x = (SCREEN_WIDTH - DICE_SIZE) // 2
        y = 520
        current_value = self.dice_animator.update(pygame.time.get_ticks())
        self.dice_animator.draw(screen, dice_start_x, y, current_value)

    def draw_deck(self, screen, deck):
        x = SCREEN_WIDTH - CARD_WIDTH - 20
        y = SCREEN_HEIGHT - CARD_HEIGHT - 20
        self.card_renderer.render_deck(screen, x, y, len(deck), DARK_BLUE)

# Instantiate UI
ui = UI()

def draw_board(screen):
    board_circles = {}
    circle_radius = 40
    padding = 10
    board_width = (2 * circle_radius + padding) * 2
    board_height = (3 * circle_radius + padding * 2)
    start_x = (SCREEN_WIDTH - board_width) // 2 + 46
    start_y = (SCREEN_HEIGHT - board_height) // 2 + 20
    positions = [
        ("♠", (start_x, start_y)),
        ("♥", (start_x + circle_radius * 2 + padding, start_y)),
        ("♦", (start_x, start_y + circle_radius * 2 + padding)),
        ("♣", (start_x + circle_radius * 2 + padding, start_y + circle_radius * 2 + padding)),
        ("J", (start_x + circle_radius + padding // 2, start_y + (circle_radius * 4 + padding * 2)))
    ]
    try:
        font = pygame.font.SysFont('dejavusans', 36, bold=True)
    except:
        font = pygame.font.Font(None, 36)
    suit_colors = {'♠': BLACK, '♥': RED_COLOR, '♦': RED_COLOR, '♣': BLACK, 'J': BLACK}
    for label, pos in positions:
        pygame.draw.circle(screen, WHITE, pos, circle_radius)
        pygame.draw.circle(screen, BLACK, pos, circle_radius, 5)
        if label == "J":
            j_font = pygame.font.SysFont('dejavusans', 36, bold=False)
            text = j_font.render(label, True, suit_colors[label])
        else:
            text = font.render(label, True, suit_colors[label])
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)
        total_bet = sum(chip[1] for chip, _, lbl in betting_chips if lbl == label)
        if total_bet > 0:
            bet_font = pygame.font.Font(None, 24)
            currency_text = bet_font.render("£", True, BLACK)
            amount_text = bet_font.render(f"{total_bet}", True, RED_COLOR)
            total_width = currency_text.get_width() + amount_text.get_width()
            if label in ["♦", "♠"]:
                currency_x = pos[0] - circle_radius - 5 - total_width
                amount_x = currency_x + currency_text.get_width()
                y_coord = pos[1] - currency_text.get_height() // 2
            elif label == "J":
                currency_x = pos[0] - total_width // 2
                amount_x = currency_x + currency_text.get_width()
                y_coord = pos[1] + circle_radius + 5
            else:
                currency_x = pos[0] + circle_radius + 5
                amount_x = currency_x + currency_text.get_width()
                y_coord = pos[1] - currency_text.get_height() // 2
            screen.blit(currency_text, (currency_x, y_coord))
            screen.blit(amount_text, (amount_x, y_coord))
        board_circles[label] = pygame.Rect(pos[0] - circle_radius, pos[1] - circle_radius, circle_radius * 2, circle_radius * 2)
    return board_circles

def draw_betting_chips(screen):
    for chip, center, _ in betting_chips:
        pygame.draw.circle(screen, chip[0], center, CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
        chip_text = pygame.font.Font(None, 16).render(f"£{chip[1]}", True, BLACK)
        text_rect = chip_text.get_rect(center=center)
        screen.blit(chip_text, text_rect)

def roll_dice():
    global dice_value, is_rolling, animation_start_time
    dice_value = random.randint(1, 7)
    is_rolling = True
    animation_start_time = time.time()
    ui.dice_animator.start_roll(dice_value)

def deal_cards():
    global current_cards, is_dealing, cards_revealed
    deck = create_deck()
    current_cards = random.sample(deck, 4)
    is_dealing = True
    cards_revealed = False
    total_width = 4 * (CARD_WIDTH + 20)
    start_x = (SCREEN_WIDTH - total_width) // 2 + 8
    card_positions = [(start_x + i * (CARD_WIDTH + 20), 20) for i in range(4)]
    ui.card_animator.start_card_reveal(current_cards, card_positions)

def handle_animations():
    global is_rolling, is_dealing, results_displayed, results_display_start_time, cards_revealed, history
    current_time = time.time()
    if is_rolling and current_time - animation_start_time > 3.0:
        is_rolling = False
        if dice_value in [1, 2, 3, 4, 5, 6, 7]:
            deal_cards()
        else:
            results_displayed = True
            results_display_start_time = pygame.time.get_ticks()
            cards_revealed = False
            bets = {label: sum(chip[1] for chip, _, lbl in betting_chips if lbl == label) for label in placed_bets}
            ui.results_display.show_results(current_cards, dice_value, bets)
    if is_dealing and ui.card_animator.is_animation_complete():
        is_dealing = False
        results_displayed = True
        results_display_start_time = pygame.time.get_ticks()
        cards_revealed = True
        bets = {label: sum(chip[1] for chip, _, lbl in betting_chips if lbl == label) for label in placed_bets}
        ui.results_display.show_results(current_cards, dice_value, bets)
        history.append((current_cards.copy(), dice_value))

def handle_mouse_click(pos, bet_circles):
    global active_chip, betting_chips, wallet_balance, placed_bets, results_displayed, round_count, showing_history, is_rolling, cards_revealed, history_data, showing_wallet_info
    try:
        # Clicking the wallet label triggers display of credits info
        if showing_wallet_info:
            showing_wallet_info = False
            return
        if ui.bet_button.is_clicked(pos):
            if active_chip and placed_bets and not results_displayed:
                showing_history = False
                showing_wallet_info = False
                roll_dice()
            elif results_displayed:
                showing_history = False
                showing_wallet_info = False
                reset_round()
            ui.results_display.stop_flashing()
        elif ui.undo_button.is_clicked(pos) and betting_chips and not results_displayed:
            last_chip = betting_chips.pop()
            wallet_balance += last_chip[0][1]
            placed_bets.remove(last_chip[2])
        # Modify history button: clicking it now toggles credits display.
        elif ui.history_button.is_clicked(pos):
            showing_history = not showing_history
            showing_wallet_info = False
            ui.results_display.stop_flashing()
        elif ui.return_button.is_clicked(pos) and (showing_history or showing_wallet_info):
            showing_history = False
            showing_wallet_info = False
        elif ui.wallet_rect.collidepoint(pos):
            showing_wallet_info = True
            showing_history = False
        else:
            for i, color in enumerate(CHIP_COLORS):
                chip_center = (30 + i * 60, 560)
                chip_rect = pygame.Rect(chip_center[0] - CHIP_RADIUS, chip_center[1] - CHIP_RADIUS, CHIP_RADIUS * 2, CHIP_RADIUS * 2)
                if chip_rect.collidepoint(pos):
                    active_chip = (color, CHIP_VALUES[i])
                    return
            for label, rect in bet_circles.items():
                if rect.collidepoint(pos) and active_chip and not results_displayed:
                    if wallet_balance >= active_chip[1]:
                        wallet_balance -= active_chip[1]
                        betting_chips.append((active_chip, rect.center, label))
                        placed_bets.add(label)
    except Exception as e:
        print(f"Error in handle_mouse_click: {e}")

def create_deck():
    deck = [Card(rank, suit) for suit in SUITS for rank in RANKS]
    deck.extend(JOKERS)
    full_deck = deck * 3
    random.shuffle(full_deck)
    return full_deck

def calculate_winnings(cards, dice_value, bets):
    winnings = 0
    if dice_value in [1, 2, 3, 4]:
        winning_card_index = dice_value - 1
        commission = 1.0
    elif dice_value in [5, 6]:
        winning_card_index = 1 if dice_value == 5 else 3
        commission = 0.5
    elif dice_value == 7:
        winning_card_index = 3
        commission = 1.0
    else:
        return 0
    winning_card = cards[winning_card_index]
    for suit in SUITS:
        if suit in bets:
            if winning_card.suit == suit:
                base_win = bets[suit] * 3
                winnings += int((base_win + bets[suit]) * commission)
    if 'J' in bets:
        if winning_card.rank == "Joker":
            base_win = bets['J'] * 50
            winnings += int((base_win + bets['J']) * commission)
    return winnings

def reset_round():
    global results_displayed, betting_chips, placed_bets, round_count, current_cards, cards_revealed, wallet_balance
    if current_cards and dice_value:
        bets = {}
        for chip, _, label in betting_chips:
            bets[label] = bets.get(label, 0) + chip[1]
        winnings = calculate_winnings(current_cards, dice_value, bets)
        wallet_balance += winnings
    results_displayed = False
    betting_chips.clear()
    placed_bets.clear()
    current_cards.clear()
    cards_revealed = False
    round_count += 1

# Display credits as required when wallet label or history button is toggled.
def display_credits(screen):
    credits_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    credits_surface.fill(WHITE)
    screen.blit(credits_surface, (0, 0))
    # Using Times New Roman with larger text for most lines
    font_title = pygame.font.SysFont('timesnewroman', 32, bold=True)
    credits_title = font_title.render("CREDITS", True, BLACK)
    credits_title_rect = credits_title.get_rect(center=(SCREEN_WIDTH // 2, 100))
    screen.blit(credits_title, credits_title_rect)
    font_normal = pygame.font.SysFont('timesnewroman', 28, bold=False)
    font_small = pygame.font.SysFont('timesnewroman', 20, bold=False)
    info_lines = [
        "Dealer:",
        "Wesley Nyanhongo",
        "",
        "Kind regards,",
        "Game founder:",
        "Wesley Nyanhongo",
        "",
        "Copyright © 2025 Wesley Tashinga Nyanhongo. All rights reserved"
    ]
    for i, line in enumerate(info_lines):
        if "Copyright" in line:
            line_surface = font_small.render(line, True, BLACK)
        else:
            line_surface = font_normal.render(line, True, BLACK)
        line_rect = line_surface.get_rect(center=(SCREEN_WIDTH // 2, 150 + i * 45))
        screen.blit(line_surface, line_rect)

def main(surface=None, embedded=False, wallet=None):
    global betting_chips, round_count, placed_bets, history, showing_history, showing_wallet_info
    global screen, clock, wallet_balance

    from embedded_utils import check_embedded_exit, draw_back_button

    if surface is not None:
        screen = surface
    elif screen is None:
        _init_display()

    if clock is None:
        clock = pygame.time.Clock()

    if wallet is not None:
        wallet_balance = wallet.balance

    running = True
    back_rect = None
    bet_circles = draw_board(screen)
    deck = create_deck()
    try:
        while running:
            screen.fill(WHITE)
            if showing_wallet_info:
                display_credits(screen)
            elif showing_history:
                display_credits(screen)
            else:
                draw_board(screen)
                ui.draw_ui_elements(screen)
                ui.draw_card_slots(screen)
                ui.draw_dice(screen)
                ui.draw_deck(screen, deck)
                if current_cards and not cards_revealed:
                    ui.draw_cards(screen)
                elif current_cards and cards_revealed:
                    ui.draw_static_cards(screen)
                draw_betting_chips(screen)

            if embedded:
                back_rect = None

            handle_animations()
            for event in pygame.event.get():
                exit_action = check_embedded_exit(event, embedded, back_rect)
                if exit_action == "quit":
                    return "quit"
                if exit_action == "menu":
                    return "menu"
                if event.type == pygame.QUIT:
                    if embedded:
                        return "quit"
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if embedded and back_rect and back_rect.collidepoint(event.pos):
                        continue
                    handle_mouse_click(event.pos, bet_circles)
            if not (showing_wallet_info or showing_history):
                ui.results_display.draw(screen, bet_circles)
            pygame.display.flip()
            clock.tick(60)
    finally:
        if wallet is not None:
            wallet.balance = wallet_balance

    if not embedded:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    from embedded_utils import run_game_standalone
    run_game_standalone(sys.modules[__name__], "Sui'tz")