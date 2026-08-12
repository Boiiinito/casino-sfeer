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
DARK_BLUE = (0, 0, 139)   # Dark blue for card back
GREEN_COLOR = (0, 128, 0) # Green for winning bets
GOLD_COLOR = (184, 134, 11) # Darker gold for betting space amounts

# Initialize Screen (deferred when embedded in Casino Sfeer menu)
screen = None
clock = None


def _init_display(caption="Di'el"):
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
showing_history = False
history_data = None
placed_bets = set()
showing_wallet_info = False  # New state variable for wallet info screen

# Card and Dice Variables
Card = namedtuple('Card', ['rank', 'suit'])
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10']
current_cards = []
dice_values = [1, 1]
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
results_displayed = False  # Initialize results_displayed

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
        self.suit_symbols = {
            '♠': '♠',
            '♥': '♥',
            '♦': '♦',
            '♣': '♣'
        }
        self.suit_colors = {
            '♠': (0, 0, 0),
            '♥': (255, 0, 0),
            '♦': (255, 0, 0),
            '♣': (0, 0, 0)
        }
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
            suit_color = self.suit_colors[card.suit]
            rank_text = self.rank_font.render(card.rank, True, suit_color)
            suit_text = self.suit_font.render(self.suit_symbols[card.suit], True, suit_color)
            padding = 5
            
            rank_rect_top = rank_text.get_rect(topleft=(x + padding, y + padding))
            suit_rect_top = suit_text.get_rect(topleft=(x + padding, y + rank_rect_top.height + 2))
            
            rank_rect_bottom = rank_text.get_rect(
                bottomright=(x + self.card_width - padding, y + self.card_height - padding)
            )
            suit_rect_bottom = suit_text.get_rect(
                bottomright=(x + self.card_width - padding, y + self.card_height - rank_rect_bottom.height - 2)
            )
            
            surface.blit(rank_text, rank_rect_top)
            surface.blit(suit_text, suit_rect_top)
            
            rotated_rank = pygame.transform.rotate(rank_text, 180)
            rotated_suit = pygame.transform.rotate(suit_text, 180)
            surface.blit(rotated_rank, rank_rect_bottom)
            surface.blit(rotated_suit, suit_rect_bottom)

    def render_card_back(self, surface, x, y, back_color):
        pygame.draw.rect(surface, WHITE, (x, y, self.card_width, self.card_height))
        pygame.draw.rect(surface, back_color, (x + 3, y + 3, self.card_width - 6, self.card_height - 6))
        pygame.draw.rect(surface, BLACK, (x, y, self.card_width, self.card_height), 2)

    def render_deck(self, surface, x, y, deck_size, back_color):
        if deck_size > 0:
            self.render_card_back(surface, x, y, back_color)

class CardAnimation:
    def __init__(self, card_width, card_height):
        self.card_width = card_width
        self.card_height = card_height
        self.animation_duration = 1000  # Increased to 1000ms for slower reveal
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
            self.flip_progress = 0  # 0 to 1
            
    def start_card_reveal(self, cards, start_positions):
        current_time = pygame.time.get_ticks()
        self.animations = []
        
        for i, (card, pos) in enumerate(zip(cards, start_positions)):
            start_time = current_time + (i * 200)  # Stagger reveals
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
        self.animation_duration = 3000  # 3 seconds
        self.frames_per_roll = 20
        self.roll_interval = 50
        self.current_values = [1, 1]
        self.final_values = [1, 1]
        self.start_time = 0
        self.is_rolling = False
        self.last_roll_time = 0
        
    def start_roll(self, final_values):
        self.start_time = pygame.time.get_ticks()
        self.final_values = final_values
        self.is_rolling = True
        self.last_roll_time = self.start_time
        
    def update(self, current_time):
        if not self.is_rolling:
            return self.final_values
            
        elapsed = current_time - self.start_time
        
        if elapsed >= self.animation_duration:
            self.is_rolling = False
            self.current_values = self.final_values
        else:
            progress = elapsed / self.animation_duration
            if current_time - self.last_roll_time >= self.roll_interval:
                if progress < 0.8:
                    self.current_values = [random.randint(1, 6), random.randint(1, 6)]
                else:
                    for i in range(2):
                        if random.random() > (progress - 0.8) * 5:
                            self.current_values[i] = random.randint(1, 6)
                        else:
                            self.current_values[i] = self.final_values[i]
                self.last_roll_time = current_time
                
        return self.current_values
        
    def draw(self, screen, x, y, value):
        if self.is_rolling:
            wobble = random.randint(-2, 2)
            x += wobble
            y += wobble
            
        pygame.draw.rect(screen, WHITE, (x, y, self.dice_size, self.dice_size))
        pygame.draw.rect(screen, BLACK, (x, y, self.dice_size, self.dice_size), 2)
        
        dot_positions = {
            1: [(self.dice_size//2, self.dice_size//2)],
            2: [(self.dice_size//4, self.dice_size//4),
                (3*self.dice_size//4, 3*self.dice_size//4)],
            3: [(self.dice_size//4, self.dice_size//4),
                (self.dice_size//2, self.dice_size//2),
                (3*self.dice_size//4, 3*self.dice_size//4)],
            4: [(self.dice_size//4, self.dice_size//4),
                (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//4, 3*self.dice_size//4),
                (3*self.dice_size//4, 3*self.dice_size//4)],
            5: [(self.dice_size//4, self.dice_size//4),
                (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//2, self.dice_size//2),
                (self.dice_size//4, 3*self.dice_size//4),
                (3*self.dice_size//4, 3*self.dice_size//4)],
            6: [(self.dice_size//4, self.dice_size//4),
                (3*self.dice_size//4, self.dice_size//4),
                (self.dice_size//4, self.dice_size//2),
                (3*self.dice_size//4, self.dice_size//2),
                (self.dice_size//4, 3*self.dice_size//4),
                (3*self.dice_size//4, 3*self.dice_size//4)]
        }
        
        for dot_x, dot_y in dot_positions[value]:
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

    def show_results(self, cards, dice_values, bets):
        self.results.clear()
        dice_total = sum(dice_values)
        highest_die = max(dice_values)

        if "1D" in bets:
            amount = bets["1D"]
            card_ranks = [card.rank for card in cards]
            if str(highest_die) in card_ranks:
                self.results.append(("1D", amount, amount * 2, "Win!"))
            else:
                self.results.append(("1D", amount, 0, "Loss"))

        if "2D" in bets:
            amount = bets["2D"]
            if 11 <= dice_total <= 12:
                self.results.append(("2D", amount, 0, "Loss - Dice total 11 or 12"))
            else:
                card_ranks = [card.rank for card in cards]
                if str(dice_total) in card_ranks:
                    self.results.append(("2D", amount, amount * 2, "Win!"))
                else:
                    self.results.append(("2D", amount, 0, "Loss"))

        if "O" in bets:
            amount = bets["O"]
            if dice_values.count(1) == 2:
                self.results.append(("O", amount, 0, "Loss - Double ones"))
            elif 1 in dice_values:
                self.results.append(("O", amount, amount * 3, "Win!"))
            else:
                self.results.append(("O", amount, 0, "Loss"))

        if "TE" in bets:
            amount = bets["TE"]
            if dice_total in [11, 12]:
                self.results.append(("TE", amount, amount * 11, "Win!"))
            else:
                self.results.append(("TE", amount, 0, "Loss"))

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

        for bet_type, _, winnings, _ in self.results:
            if self.flash_state:
                color = GREEN_COLOR if winnings > 0 else RED_COLOR
                pygame.draw.circle(screen, color, bet_circles[bet_type].center,
                                   bet_circles[bet_type].width // 2, 5)

    def stop_flashing(self):
        self.showing_results = False

class UI:
    def __init__(self):
        self.chip_font = pygame.font.Font(None, 16)
        self.button_font = pygame.font.Font(None, 24)
        self.wallet_font = pygame.font.Font(None, 30)
        self.bet_button = Button((SCREEN_WIDTH - BUTTON_WIDTH) // 2 - 60, 500, BUTTON_WIDTH, BUTTON_HEIGHT, "Bet")
        self.undo_button = Button((SCREEN_WIDTH - BUTTON_WIDTH) // 2 + 60, 500, BUTTON_WIDTH, BUTTON_HEIGHT, "Undo")
        self.history_button = Button((SCREEN_WIDTH - BUTTON_WIDTH) // 2, 550, BUTTON_WIDTH, BUTTON_HEIGHT, "History")
        self.return_button = Button((SCREEN_WIDTH - BUTTON_WIDTH) // 2, 600, BUTTON_WIDTH, BUTTON_HEIGHT, "Return")
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
        dice_start_x = (SCREEN_WIDTH - (2 * DICE_SIZE + 20)) // 2
        y = 450
        current_values = self.dice_animator.update(pygame.time.get_ticks())
        for i, value in enumerate(current_values):
            x = dice_start_x + i * (DICE_SIZE + 20)
            self.dice_animator.draw(screen, x, y, value)

    def draw_deck(self, screen, deck):
        x = SCREEN_WIDTH - CARD_WIDTH - 20
        y = SCREEN_HEIGHT - CARD_HEIGHT - 20
        self.card_renderer.render_deck(screen, x, y, len(deck), DARK_BLUE)

ui = UI()

def draw_board(screen):
    board_circles = {}
    circle_radius = 40
    padding = 10
    start_x = (SCREEN_WIDTH - (2 * circle_radius + padding) * 2) // 2 + 46
    start_y = (SCREEN_HEIGHT - (2 * circle_radius + padding) * 2) // 2 + 60

    positions = [
        ("O", (start_x, start_y)),
        ("2D", (start_x + circle_radius * 2 + padding, start_y)),
        ("TE", (start_x, start_y + circle_radius * 2 + padding)),
        ("1D", (start_x + circle_radius * 2 + padding, start_y + circle_radius * 2 + padding))
    ]

    font = pygame.font.Font(None, 28)
    for label, pos in positions:
        pygame.draw.circle(screen, WHITE, pos, circle_radius)
        pygame.draw.circle(screen, BLACK, pos, circle_radius, 5)

        text = font.render(label, True, BLACK)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)

        # Calculate and display the total amount bet on each space
        total_bet = sum(chip[1] for chip, _, lbl in betting_chips if lbl == label)
        
        # Only display the amount if there is a bet placed
        if total_bet > 0:
            # Render currency symbol and amount separately with different colors
            currency_text = font.render("£", True, BLACK)
            amount_text = font.render(f"{total_bet}", True, RED_COLOR)
            
            # Calculate the total width needed
            total_width = currency_text.get_width() + amount_text.get_width()
            
            # Position both texts
            if label in ["TE", "O"]:
                currency_x = pos[0] - circle_radius - 5 - total_width
                amount_x = currency_x + currency_text.get_width()
                y = pos[1] - currency_text.get_height() // 2
            else:
                currency_x = pos[0] + circle_radius + 5
                amount_x = currency_x + currency_text.get_width()
                y = pos[1] - currency_text.get_height() // 2
            
            # Draw both texts
            screen.blit(currency_text, (currency_x, y))
            screen.blit(amount_text, (amount_x, y))

        board_circles[label] = pygame.Rect(pos[0] - circle_radius, pos[1] - circle_radius,
                                           circle_radius * 2, circle_radius * 2)
    return board_circles

def draw_betting_chips(screen):
    for chip, center, _ in betting_chips:
        pygame.draw.circle(screen, chip[0], center, CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
        chip_text = pygame.font.Font(None, 16).render(f"£{chip[1]}", True, BLACK)
        text_rect = chip_text.get_rect(center=center)
        screen.blit(chip_text, text_rect)

def roll_dice():
    global dice_values, is_rolling, animation_start_time
    dice_values = [random.randint(1, 6), random.randint(1, 6)]
    is_rolling = True
    animation_start_time = time.time()
    ui.dice_animator.start_roll(dice_values)

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
    global is_rolling, is_dealing, results_displayed, results_display_start_time, cards_revealed
    current_time = time.time()
    
    if is_rolling and current_time - animation_start_time > 3.0:
        is_rolling = False
        deal_cards()
    
    if is_dealing and ui.card_animator.is_animation_complete():
        is_dealing = False
        results_displayed = True
        results_display_start_time = pygame.time.get_ticks()
        cards_revealed = True
        bets = {label: sum(chip[1] for chip, _, lbl in betting_chips if lbl == label) for label in placed_bets}
        ui.results_display.show_results(current_cards, dice_values, bets)

def handle_mouse_click(pos, bet_circles):
    global active_chip, betting_chips, wallet_balance, placed_bets
    global results_displayed, round_count, showing_history, is_rolling, cards_revealed, history_data, showing_wallet_info
    
    try:
        if showing_wallet_info:
            showing_wallet_info = False
            return
        
        if ui.bet_button.is_clicked(pos):
            if active_chip and placed_bets and not results_displayed:
                showing_history = False
                showing_wallet_info = False
                roll_dice()
                history.append((current_cards, dice_values))
            elif results_displayed:
                showing_history = False
                showing_wallet_info = False
                reset_round()
            ui.results_display.stop_flashing()
            
        elif ui.undo_button.is_clicked(pos) and betting_chips and not results_displayed:
            last_chip = betting_chips.pop()
            wallet_balance += last_chip[0][1]
            placed_bets.remove(last_chip[2])

        elif ui.history_button.is_clicked(pos):
            if history and not is_rolling and not is_dealing:
                showing_history = not showing_history
                showing_wallet_info = False
                if showing_history:
                    history_data = history[-1]
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
                chip_rect = pygame.Rect(chip_center[0] - CHIP_RADIUS,
                                        chip_center[1] - CHIP_RADIUS,
                                        CHIP_RADIUS * 2, CHIP_RADIUS * 2)
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
    full_deck = deck * 3
    random.shuffle(full_deck)
    return full_deck

def calculate_winnings(cards, dice_values, bets):
    winnings = 0
    dice_total = sum(dice_values)
    highest_die = max(dice_values)

    # One Different (1D)
    if "1D" in bets:
        card_ranks = [card.rank for card in cards]
        if str(highest_die) in card_ranks:
            winnings += bets["1D"] * 2

    # Two Different (2D)
    if "2D" in bets:
        if 11 <= dice_total <= 12:
            pass
        else:
            card_ranks = [card.rank for card in cards]
            if str(dice_total) in card_ranks:
                winnings += bets["2D"] * 2

    # One (O)
    if "O" in bets:
        if dice_values.count(1) == 2:
            pass
        elif 1 in dice_values:
            winnings += bets["O"] * 6

    # Two Equal (TE)
    if "TE" in bets:
        if dice_total in [11, 12]:
            winnings += bets["TE"] * 11

    return winnings

def reset_round():
    global results_displayed, betting_chips, placed_bets, round_count, current_cards, cards_revealed, wallet_balance
    
    if current_cards and dice_values:
        bets = {}
        for chip, _, label in betting_chips:
            bets[label] = bets.get(label, 0) + chip[1]
        
        winnings = calculate_winnings(current_cards, dice_values, bets)
        wallet_balance += winnings

    results_displayed = False
    betting_chips.clear()
    placed_bets.clear()
    current_cards.clear()
    cards_revealed = False
    round_count += 1

def display_history(screen, data):
    if not data:
        return
    cards, dice = data
    history_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    history_surface.fill(WHITE)
    screen.blit(history_surface, (0, 0))

    font = pygame.font.Font(None, 36)
    text = font.render("Previous Round", True, BLACK)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 160))
    screen.blit(text, text_rect)

    total_width = 4 * (CARD_WIDTH + 20)
    start_x = (SCREEN_WIDTH - total_width) // 2 + 8
    card_positions = [(start_x + i * (CARD_WIDTH + 20), 200) for i in range(4)]

    for card, pos in zip(cards, card_positions):
        ui.card_renderer.render_card(screen, card, pos[0], pos[1])

    dice_start_x = (SCREEN_WIDTH - (2 * DICE_SIZE + 20)) // 2
    y = 200 + CARD_HEIGHT + 40
    dice_text = font.render("Dice Roll:", True, BLACK)
    dice_text_rect = dice_text.get_rect(center=(SCREEN_WIDTH // 2, y - 20))
    screen.blit(dice_text, dice_text_rect)

    for i, value in enumerate(dice):
        x = dice_start_x + i * (DICE_SIZE + 20)
        ui.dice_animator.draw(screen, x, y, value)

def display_wallet_info(screen):
    wallet_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    wallet_surface.fill(WHITE)
    screen.blit(wallet_surface, (0, 0))

    # Bold font only for the "CREDITS" text
    font_bold = pygame.font.SysFont('timesnewroman', 24, bold=True)
    text_credits = font_bold.render("CREDITS", True, BLACK)
    text_credits_rect = text_credits.get_rect(center=(SCREEN_WIDTH // 2, 100))
    screen.blit(text_credits, text_credits_rect)

    # Normal font for the other lines, also centered
    font_normal = pygame.font.SysFont('timesnewroman', 24, bold=False)

    info_text = [
        "Dealer:",
        "Wesley Nyanhongo",
        "",
        "Kind regards,",
        "Game founder:",
        "Wesley Nyanhongo",
        "",
        "Copyright © 2025 Wesley Tashinga Nyanhongo. All rights reserved"
    ]

    # All lines will be centered horizontally on each line
    for i, line in enumerate(info_text):
        if "Copyright" in line:
            line_text = pygame.font.SysFont('timesnewroman', 20, bold=False).render(line, True, BLACK)
        else:
            line_text = font_normal.render(line, True, BLACK)
        line_rect = line_text.get_rect(center=(SCREEN_WIDTH // 2, 150 + i * 40))
        screen.blit(line_text, line_rect)

def main(surface=None, embedded=False, wallet=None):
    global betting_chips, round_count
    global placed_bets, history
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
                display_wallet_info(screen)
            elif showing_history and history_data:
                display_history(screen, history_data)
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
    run_game_standalone(sys.modules[__name__], "Di'el")