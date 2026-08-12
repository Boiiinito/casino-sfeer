import pygame
from pygame.locals import *
import sys
import os
import importlib
import random

from embedded_utils import (
    MENU_WIDTH,
    MENU_HEIGHT,
    BACK_BUTTON_WIDTH,
    BACK_BUTTON_HEIGHT,
    BACK_BUTTON_MARGIN,
    cleanup_after_game,
    get_game_size,
    get_back_font,
)
from wallet import PlayerWallet

# Without this, Windows DPI virtualization can misreport the screen/window
# geometry for a frozen exe, pushing the title bar (and its close/minimize/
# maximize buttons) off the top of the visible screen.
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# Initialize Pygame
pygame.init()

# Set up the window with adjusted dimensions - Increased width to be larger than the We'eL game window
# Shrink the window to fit within the visible desktop area (screen minus the
# title bar, menu bar, and dock) so the bottom of the window is never hidden
# behind the dock, then center/pin it near the top of the screen.
try:
    desktop_sizes = pygame.display.get_desktop_sizes()
    screen_w, screen_h = desktop_sizes[0] if desktop_sizes else (MENU_WIDTH, MENU_HEIGHT)
except Exception:
    screen_w, screen_h = MENU_WIDTH, MENU_HEIGHT

# Reserve space for OS chrome: window title bar, menu bar (top) and dock (bottom).
VERTICAL_CHROME_RESERVE = 130
HORIZONTAL_CHROME_RESERVE = 40

WIDTH = min(MENU_WIDTH, max(700, screen_w - HORIZONTAL_CHROME_RESERVE))
HEIGHT = min(MENU_HEIGHT, max(600, screen_h - VERTICAL_CHROME_RESERVE))

# Keep the embedded-game sizing constants in sync with the actual window size
# used here, so games launched from the menu stay correctly centered.
MENU_WIDTH = WIDTH
MENU_HEIGHT = HEIGHT

if sys.platform.startswith("win"):
    # Let Windows center the window itself so the title bar (and its
    # close/minimize/maximize buttons) is always fully on-screen and
    # draggable, instead of pinning it to the very top edge.
    os.environ["SDL_VIDEO_WINDOW_POS"] = "center"
else:
    window_x = max(0, (screen_w - WIDTH) // 2)
    window_y = 0
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{window_x},{window_y}"

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Casino Sfeer")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Font setup
available_fonts = pygame.font.get_fonts()
symbol_font = None
font_preferences = ['segoeuisymbol', 'segoeui', 'dejavusans', 'arial']

for font_name in font_preferences:
    if font_name in available_fonts:
        symbol_font = pygame.font.SysFont(font_name, 28, bold=True)
        title_font = pygame.font.SysFont('times new roman', 82, bold=True)
        button_font = pygame.font.SysFont(font_name, 28, bold=True)
        credits_heading_font = pygame.font.SysFont(font_name, 48, bold=True)
        credits_font = pygame.font.SysFont(font_name, 32)
        break

if symbol_font is None:
    title_font = pygame.font.SysFont('times new roman', 82, bold=True)
    button_font = pygame.font.Font(None, 28)
    button_font.set_bold(True)
    symbol_font = pygame.font.Font(None, 28)
    symbol_font.set_bold(True)
    credits_heading_font = pygame.font.Font(None, 48)
    credits_font = pygame.font.Font(None, 32)

class Button:
    def __init__(self, text, x, y, width, height, color):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hovered = False

    def draw(self):
        # Draw button background
        pygame.draw.rect(window, WHITE, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(window, self.color, (self.x, self.y, self.width, self.height))
        border_width = 5
        # Set border color: for Di'eL, Sui'tz, and We'eL buttons, use red, otherwise use black
        if self.text == "Fanirafana":
            border_color = RED
        elif self.text in ["Di'eL", "Sui'tz", "Wice"]:
            border_color = RED
        else:
            border_color = BLACK
        pygame.draw.rect(window, border_color, (self.x, self.y, self.width, self.height), border_width)
        
        # Set text color: for Di'eL, Sui'tz, and We'eL buttons, use black, otherwise red
        if self.text == "Fanirafana":
            text_color = BLACK
        elif self.text in ["Di'eL", "Sui'tz", "Wice"]:
            text_color = BLACK
        else:
            text_color = RED
        text_surface = button_font.render(self.text, True, text_color)
        text_x = self.x + (self.width - text_surface.get_width()) // 2
        text_y = self.y + (self.height - text_surface.get_height()) // 2
        window.blit(text_surface, (text_x, text_y))

    def is_clicked(self, pos):
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

# Button setup - 8 games arranged in 2 neat columns with 4 buttons each
button_width = 230
button_height = 60
button_spacing = 20

# Title position and dimensions
title_height = 170
title_bottom = 170  # Approximate bottom position of the title

# Calculate positions for a balanced 2-column layout
center_x = WIDTH // 2
column_gap = 40
left_column_x = center_x - (button_width + column_gap // 2)
right_column_x = center_x + (column_gap // 2)
row_height = button_height + button_spacing
start_y = 300

# Create buttons with the new 4 + 4 layout
game_buttons = []
game_names = [
    "L'oL",
    "Di'eL",
    "ChanceO'Chill",
    "Sui'tz",
    "Su'tz",
    "Wice",
    "Foust",
    "Fanirafana",
]

for index, game_name in enumerate(game_names):
    if index < 4:
        x = left_column_x
        y = start_y + index * row_height
    else:
        x = right_column_x
        y = start_y + (index - 4) * row_height
    game_buttons.append(Button(game_name, x, y, button_width, button_height, WHITE))

rules_button = Button("Rules", 20, 20, 120, 46, WHITE)
rules_back_button = Button("Back", 20, 20, 120, 46, WHITE)

rule_button_width = 220
rule_button_height = 48
rule_button_spacing = 16
rule_button_col_gap = 40
rule_button_y_start = 190
rule_button_left_x = WIDTH // 2 - rule_button_width - rule_button_col_gap // 2
rule_button_right_x = WIDTH // 2 + rule_button_col_gap // 2

rules_screen_buttons = []
for index, game_name in enumerate([
    "L'oL",
    "Di'eL",
    "ChanceO'Chill",
    "Sui'tz",
    "Su'tz",
    "Wice",
    "Foust",
    "Fanirafana",
]):
    if index < 4:
        x = rule_button_left_x
        y = rule_button_y_start + index * (rule_button_height + rule_button_spacing)
    else:
        x = rule_button_right_x
        y = rule_button_y_start + (index - 4) * (rule_button_height + rule_button_spacing)
    rules_screen_buttons.append(Button(game_name, x, y, rule_button_width, rule_button_height, WHITE))

# Symbol setup
class Symbol:
    def __init__(self, symbol, x, y, speed):
        self.symbol = symbol
        self.x = x
        self.y = y
        self.base_speed = speed
        self.current_speed = speed
        
    def move(self):
        self.y += self.current_speed
        if self.y > HEIGHT:
            self.y = -22
            self.x = random.randint(0, WIDTH - 22)
            self.current_speed = self.base_speed  # Reset to base speed
            
    def draw(self):
        color = RED if self.symbol in ['♥', '♦'] else BLACK
        symbol_text = symbol_font.render(self.symbol, True, color)
        window.blit(symbol_text, (self.x, self.y))

# Create symbols
symbols = []
grid_cols, grid_rows = 15, 12
cell_width = WIDTH // grid_cols
cell_height = HEIGHT // grid_rows
total_cells = grid_cols * grid_rows
symbols_per_suit = total_cells // 4

all_symbols = (['♠'] * symbols_per_suit +
               ['♣'] * symbols_per_suit +
               ['♥'] * symbols_per_suit +
               ['♦'] * symbols_per_suit)
random.shuffle(all_symbols)

for i, symbol in enumerate(all_symbols):
    row = i // grid_cols
    col = i % grid_cols
    x = col * cell_width + random.randint(0, cell_width - 22)
    y = row * cell_height + random.randint(0, cell_height - 22)
    speed = random.uniform(0.5, 1.0)
    symbols.append(Symbol(symbol, x, y, speed))

def draw_card_symbols():
    for symbol in symbols:
        symbol.move()
        symbol.draw()

GAME_MODULES = {
    "L'oL": "LOL",
    "Di'eL": "DIEL",
    "ChanceO'Chill": "CHANCEOCHILL",
    "Sui'tz": "SUITZ",
    "Su'tz": "SUTZ",
    "Wice": "WICE",
    "Foust": "FOUST",
    "Fanirafana": "FANIRAFANA",
}


def draw_wallet(player_wallet):
    wallet_label = button_font.render(f"Wallet: £{player_wallet.balance}", True, BLACK)
    padding_x, padding_y = 16, 8
    bg_width = wallet_label.get_width() + padding_x * 2
    bg_height = wallet_label.get_height() + padding_y * 2
    bg_x = WIDTH - bg_width - 20
    bg_y = 18
    bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)
    pygame.draw.rect(window, WHITE, bg_rect)
    pygame.draw.rect(window, RED, bg_rect, 3)
    window.blit(wallet_label, (bg_x + padding_x, bg_y + padding_y))
    return bg_rect


def draw_wrapped_text(surface, text, x, y, max_width, font, color, line_spacing=8):
    words = text.split()
    line = ""
    current_y = y

    for word in words:
        test_line = f"{line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            line = test_line
        else:
            if line:
                text_surface = font.render(line, True, color)
                surface.blit(text_surface, (x, current_y))
                current_y += font.get_height() + line_spacing
            line = word

    if line:
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (x, current_y))


def wrap_text_lines(text, font, max_width):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines


def draw_scrollable_text(surface, text, viewport_rect, font, color, scroll_offset, line_spacing=8):
    """Draws wrapped text clipped to viewport_rect, offset vertically by scroll_offset.

    Returns the total content height so callers can clamp the scroll offset.
    """
    lines = wrap_text_lines(text, font, viewport_rect.width)
    line_height = font.get_height() + line_spacing
    content_height = len(lines) * line_height

    previous_clip = surface.get_clip()
    surface.set_clip(viewport_rect)

    current_y = viewport_rect.y - scroll_offset
    for line in lines:
        if current_y + line_height >= viewport_rect.y and current_y <= viewport_rect.bottom:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (viewport_rect.x, current_y))
        current_y += line_height

    surface.set_clip(previous_clip)
    return content_height


def get_scrollbar_rects(viewport_rect, content_height, scroll_offset):
    """Returns (track_rect, thumb_rect) for the scrollbar, or (None, None) if content fits."""
    if content_height <= viewport_rect.height:
        return None, None

    track_rect = pygame.Rect(viewport_rect.right + 8, viewport_rect.y, 8, viewport_rect.height)
    thumb_height = max(30, int(viewport_rect.height * viewport_rect.height / content_height))
    max_scroll = content_height - viewport_rect.height
    scroll_ratio = scroll_offset / max_scroll if max_scroll > 0 else 0
    thumb_y = viewport_rect.y + int((viewport_rect.height - thumb_height) * scroll_ratio)
    thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
    return track_rect, thumb_rect


def scroll_offset_for_thumb_y(thumb_y, viewport_rect, content_height, thumb_height):
    """Converts a desired thumb top position back into a clamped scroll offset."""
    max_scroll = max(0, content_height - viewport_rect.height)
    track_span = viewport_rect.height - thumb_height
    ratio = 0 if track_span <= 0 else (thumb_y - viewport_rect.y) / track_span
    ratio = max(0.0, min(1.0, ratio))
    return int(ratio * max_scroll)


def draw_scrollbar(surface, viewport_rect, content_height, scroll_offset):
    """Draws a simple scrollbar on the right edge of viewport_rect when content overflows."""
    track_rect, thumb_rect = get_scrollbar_rects(viewport_rect, content_height, scroll_offset)
    if track_rect is None:
        return

    pygame.draw.rect(surface, (220, 220, 220), track_rect)
    pygame.draw.rect(surface, RED, thumb_rect)


def launch_game(game_name, player_wallet):
    module_name = GAME_MODULES.get(game_name)
    if not module_name:
        return True

    try:
        module = importlib.import_module(module_name)
        importlib.reload(module)
        global window
        window = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        pygame.display.set_caption(f"Casino Sfeer - {game_name}")

        game_width, game_height = get_game_size(module)
        game_surface = pygame.Surface((game_width, game_height))
        # Convert to the display's native pixel format. Without this,
        # smoothscale can subtly shift solid colors (e.g. pure white coming
        # out a shade darker), which showed up as a faint tinted "box" around
        # scaled-down games. Converting first keeps colors exact while still
        # getting smoothscale's anti-aliased (non-jagged) resizing.
        game_surface = game_surface.convert()

        # Reserve a band below the Menu button (top) and a small gap above
        # the bottom edge, then scale the game to fit within that band (only
        # shrinking if needed) and center it there. This keeps oversized
        # games (e.g. Wice's 1024x900 surface) from overlapping the Menu
        # button or touching the window edges.
        top_reserve = BACK_BUTTON_MARGIN + BACK_BUTTON_HEIGHT + 16
        bottom_reserve = 24
        available_height = max(1, MENU_HEIGHT - top_reserve - bottom_reserve)

        scale = min(1.0, MENU_WIDTH / game_width, available_height / game_height)
        scaled_width = max(1, round(game_width * scale))
        scaled_height = max(1, round(game_height * scale))

        target_rect = pygame.Rect(
            (MENU_WIDTH - scaled_width) // 2,
            top_reserve + (available_height - scaled_height) // 2,
            scaled_width,
            scaled_height,
        )
        back_button_rect = pygame.Rect(
            BACK_BUTTON_MARGIN,
            BACK_BUTTON_MARGIN,
            BACK_BUTTON_WIDTH,
            BACK_BUTTON_HEIGHT,
        )

        original_flip = pygame.display.flip
        original_update = pygame.display.update
        original_event_get = pygame.event.get
        original_mouse_get_pos = pygame.mouse.get_pos

        def draw_overlay():
            if window is not None and game_surface is not None:
                window.fill(WHITE)
                if scale < 1.0:
                    scaled_surface = pygame.transform.smoothscale(game_surface, (scaled_width, scaled_height))
                    window.blit(scaled_surface, target_rect)
                else:
                    window.blit(game_surface, target_rect)
                pygame.draw.rect(window, (255, 255, 255), back_button_rect)
                pygame.draw.rect(window, (255, 0, 0), back_button_rect, 2)
                text = get_back_font().render("Menu", True, (255, 0, 0))
                text_rect = text.get_rect(center=back_button_rect.center)
                window.blit(text, text_rect)

        def overlay_flip():
            draw_overlay()
            return original_flip()

        def overlay_update(*args):
            draw_overlay()
            return original_update(*args)

        def translated_mouse_pos():
            x, y = original_mouse_get_pos()
            rel_x = (x - target_rect.x) / scale
            rel_y = (y - target_rect.y) / scale
            if 0 <= rel_x < game_width and 0 <= rel_y < game_height:
                return (int(rel_x), int(rel_y))
            return (-1, -1)

        def translated_event_get():
            events = original_event_get()
            transformed_events = []
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and back_button_rect.collidepoint(event.pos):
                    transformed_events.append(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
                    continue
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    if hasattr(event, "pos") and event.pos is not None:
                        event.pos = translated_mouse_pos() if event.pos != (-1, -1) else (-1, -1)
                transformed_events.append(event)
            return transformed_events

        pygame.display.flip = overlay_flip
        pygame.display.update = overlay_update
        pygame.event.get = translated_event_get
        pygame.mouse.get_pos = translated_mouse_pos
        try:
            result = module.main(surface=game_surface, embedded=True, wallet=player_wallet)
        finally:
            pygame.display.flip = original_flip
            pygame.display.update = original_update
            pygame.event.get = original_event_get
            pygame.mouse.get_pos = original_mouse_get_pos

        cleanup_after_game()
        window = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Casino Sfeer")
        return result != "quit"
    except Exception as e:
        print(f"Error launching {game_name}: {e}")
        window = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Casino Sfeer")
        return True

def draw_credits():
    window.fill(WHITE)
    
    credits_text = [
        ("CREDITS", credits_heading_font),
        ("", credits_font),
        ("Kind regards,", credits_font),
        ("", credits_font),
        ("Founder:", credits_font),
        ("Wesley Nyanhongo", credits_font),
        ("", credits_font),
        ("Copyright © 2025 Wesley Tashinga Nyanhongo.", credits_font),
        ("All rights reserved.", credits_font)
    ]
    
    total_text_height = (
        credits_heading_font.get_height() +
        sum(credits_font.get_height() for _ in range(len(credits_text) - 1)) +
        (len(credits_text) - 1) * 10
    )
    
    start_y = (HEIGHT - total_text_height) // 2
    y_offset = start_y

    for line, font in credits_text:
        if line.strip():
            text_surface = font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, y_offset))
            
            padding_x, padding_y = 10, 5
            bg_left = text_rect.left - padding_x
            bg_top = text_rect.top - padding_y
            bg_width = text_surface.get_width() + (padding_x * 2)
            bg_height = text_surface.get_height() + (padding_y * 2)
            
            pygame.draw.rect(window, WHITE, (bg_left, bg_top, bg_width, bg_height), border_radius=8)
            window.blit(text_surface, text_rect)
        
        y_offset += font.get_height() + 10

def main_menu():
    clock = pygame.time.Clock()
    show_credits = False
    player_wallet = PlayerWallet()
    screen_state = "menu"
    selected_rules_game = None
    rules_scroll_offset = 0
    rules_content_height = 0
    rules_viewport_rect = None
    rules_scrollbar_dragging = False
    rules_scrollbar_drag_grab_offset = 0

    RULES_TEXT = {
        "L'oL": "L'ol is a card game. There are 4 cards, and each card represents the card for their respective row. Place bets on the betting spaces to predict which card will appear in each row. For example, if you place a bet on the joker bet space in row 1, you are predicting that the first card will be a joker. The rest works the same for the other rows and betting spaces. The suits bets are for the middle cards (column 1 and 2 only). For example, if you place a bet on diamonds in column 2 (on the left), then you are betting that card number 2 will be diamonds, and the same applies to column 3. The 4T bet space is for betting that the 2 cards in column 2 and 3 will total either 2 or 4. Each card has a specific numeric value that applies only to the 4T bet space. Card values are Ace = 1, Jester = 1, King = 2, Queen = 2, and Joker = 2. For example, if the 2 middle cards are Jester + Joker, it is a loss because 1 + 2 = 3, but Ace + Jester wins because 1 + 1 = 2, and King + Queen wins because 2 + 2 = 4. Note: There is an 8-card rule. If the first 4 cards flipped over contain 2 or more cards of the same face value and/or 3 or more cards of the same suit, the game redraws a new set of 4 cards and the next 4 cards become the winning cards for that round.",
        "Di'eL": "Di'el is a card and dice game that uses the dice and cards to determine winnings for the betting spaces. If you bet on 1D, you are betting that there is a card matching one of the values on the die. If you bet on 2D, you are betting that there is a card with the total value of both dice. For example, if one die rolls 2 and the other die rolls 2, the 1D bet space wins if there is a card with the number 2, and the 2D bet space wins if there is a card with the number 4. If there are no cards that show 2 or 4, both bet spaces lose. The O bet space wins if only one die rolls 1, and the TE bet space wins if both dice total 11 or 12.",
        "ChanceO'Chill": "ChanceO'Chill is a card and dice game that uses cards and dice to determine the winner. The total value of the dice represents the threshold for both the dealer and the player. The player and dealer both have their own hand, and the one with a hand closest to the total value of both dice wins the round. Card values are Ace = 1, Jester = 2, King = 3, Queen = 4, and Joker = 5. All cards with numbers equal zero are considered power cards. For example, if the dice total 6, the hand closest to the dice wins, meaning if the player totals 5 and the dealer totals 8, the player wins. The 13F bet space is a bonus bet space that applies to the dice with the highest value only. If any die rolls a total of 1, 3, or 5, the 13F bet space wins. For example, if one die rolls 2 and the other rolls 5, the 13F bet wins, but if one die rolls 1 and the other rolls 3, it is a loss.",
        "Sui'tz": "Sui'tz is a card and dice game that uses the dice to determine the card slot that will contain the winning card for the round. Players must place bets on a suit or the joker bet space, and the dice will roll and give a number. For example, if the player bets on diamonds and hearts and the dice rolls 3, then the card in slot 3 should be either diamonds or hearts. If the dice rolls 5, it will use slot 2 as the winning slot, and if it rolls 6, it will use slot 4 as the winning slot.",
        "Su'tz": "Su'tz is a card multiplier game. The objective is for the player's cards to match the suits on the dealer's dice. For example, if the dealer rolls a die with 2 or more of the same suit, the game unlocks, but the player must get cards with the quantity of suits that the dealer's dice has or less, without exceeding the threshold. If the player exceeds the amount of suits in their hand, it is considered a bust and the player loses. Another example: if the dealer rolls 3 dice of hearts, the player must get any cards as long as there are 3 cards of hearts present in their hand and they get paid 3:1 on their original bet. If the player gets 4 or more cards of hearts, it is considered a bust and the player loses, but if they get 2 cards of the winning suit, they get paid 2:1. Players may not get 1 card of the winning suit unless it is a joker, which pays 1:1 and the joker must match the color of the winning suit. For example, if the winning suit is either spades or clubs, a black joker wins, and if it is hearts or diamonds, a red joker wins. The joker results in a 1:1 payout regardless of the multiplier. So for example, if the dealer rolls 4 dice of hearts and the player gets a red joker, the player wins and gets paid 1:1, but if they get a black joker, it results in a loss.",
        "Wice": "Wice is a dice and wheel betting game that uses the dice and wheel to determine winning bets. Players must place bets on the corresponding letters or bet spaces to predict where the indicator will land. Once bets are placed, the dice will roll. If the total value of the dice equals 12 or below, the player loses for the round. However, if the dice roll 13 or above, it grants the player access to the wheel, and the wheel will spin for the number of seconds equal to the total dice value. For example, if all 4 dice roll 5, the total equals 20, so the wheel will spin for 20 seconds. If the indicator does not land on a specific letter box, it results in a loss for the player.",
        "Foust": "Foust is a card racing game between the player and the dealer. The player must bet either on the player (C) or dealer (D). Both player and dealer get 4 cards and they must take turns drawing 1 card until one hand has 4 cards of a complete color. Whoever gets 4 cards of the same color wins the game. For example, if the dealer has 2 red cards and 2 black cards, and the player has 2 red cards and 2 black cards, they will automatically take turns drawing 1 card until they have a full set of one color, either red or white. Note: the Joker card is a power card, so anyone who gets a joker card results in an instant win regardless of the color.",
        "Fanirafana": "Fanirafana is a card and die game that uses the dealer's die to determine the winning outcomes for the round. The player must get a card that equals the total of the numerical die, and that card must have 1 of the suits from both dice. For example, if the dice roll a diamond, 2, 2, and a heart, the player must get a card with the number 4 that is either diamonds or hearts.",
    }

    def draw_rules_list_screen():
        window.fill(WHITE)
        title_surface = credits_heading_font.render("Game Rules", True, BLACK)
        window.blit(title_surface, (WIDTH // 2 - title_surface.get_width() // 2, 70))
        subtitle_surface = credits_font.render("Choose a game to see a quick summary.", True, BLACK)
        window.blit(subtitle_surface, (WIDTH // 2 - subtitle_surface.get_width() // 2, 130))
        rules_back_button.draw()
        for button in rules_screen_buttons:
            button.draw()

    def draw_rules_detail_screen():
        nonlocal rules_content_height, rules_viewport_rect
        window.fill(WHITE)
        title_surface = credits_heading_font.render(selected_rules_game or "Rules", True, BLACK)
        window.blit(title_surface, (WIDTH // 2 - title_surface.get_width() // 2, 70))
        rules_back_button.draw()

        body_text = RULES_TEXT.get(selected_rules_game, "No rules available yet.")
        rules_viewport_rect = pygame.Rect(45, 150, WIDTH - 110, HEIGHT - 190)
        rules_content_height = draw_scrollable_text(
            window,
            body_text,
            rules_viewport_rect,
            credits_font,
            BLACK,
            rules_scroll_offset,
            line_spacing=8,
        )
        draw_scrollbar(window, rules_viewport_rect, rules_content_height, rules_scroll_offset)

    # Calculate title background dimensions
    title_parts = [
        ("Casino ", BLACK),
        ("Sfeer", RED),
    ]
    total_width = sum(title_font.size(part[0])[0] for part in title_parts)
    bg_padding = 22
    bg_width = total_width + bg_padding * 2
    bg_height = title_font.get_height() + bg_padding * 2
    bg_x = WIDTH / 2 - bg_width / 2
    bg_y = 70 - bg_padding

    while True:
        window.fill(WHITE)

        if screen_state == "menu":
            if show_credits:
                draw_credits()
            else:
                draw_card_symbols()

                current_x = (WIDTH - total_width) // 2
                # Draw title background
                pygame.draw.rect(window, WHITE, (bg_x, bg_y, bg_width, bg_height))
                pygame.draw.rect(window, RED, (bg_x, bg_y, bg_width, bg_height), 10)

                # Draw title text with shadow
                for text, color in title_parts:
                    text_surface = title_font.render(text, True, color)
                    shadow_surface = title_font.render(text, True, (200, 200, 200))
                    window.blit(shadow_surface, (current_x + 4, 73))
                    window.blit(text_surface, (current_x, 70))
                    current_x += text_surface.get_width()

                for button in game_buttons:
                    button.draw()

                rules_button.draw()
                wallet_rect = draw_wallet(player_wallet)
        elif screen_state == "rules_list":
            draw_rules_list_screen()
        elif screen_state == "rules_detail":
            draw_rules_detail_screen()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if screen_state == "menu":
                    if show_credits:
                        show_credits = False
                    else:
                        # Check if the title block is clicked to show credits
                        if bg_x <= pos[0] <= bg_x + bg_width and bg_y <= pos[1] <= bg_y + bg_height:
                            show_credits = True
                        elif rules_button.is_clicked(pos):
                            screen_state = "rules_list"
                        elif wallet_rect.collidepoint(pos):
                            player_wallet.balance = PlayerWallet.DEFAULT_BALANCE
                        else:
                            for button in game_buttons:
                                if button.is_clicked(pos):
                                    if not launch_game(button.text, player_wallet):
                                        pygame.quit()
                                        sys.exit()
                elif screen_state == "rules_list":
                    if rules_back_button.is_clicked(pos):
                        screen_state = "menu"
                    else:
                        for button in rules_screen_buttons:
                            if button.is_clicked(pos):
                                selected_rules_game = button.text
                                screen_state = "rules_detail"
                                rules_scroll_offset = 0
                                break
                elif screen_state == "rules_detail":
                    if rules_back_button.is_clicked(pos):
                        screen_state = "rules_list"
                    elif rules_viewport_rect is not None:
                        track_rect, thumb_rect = get_scrollbar_rects(
                            rules_viewport_rect, rules_content_height, rules_scroll_offset
                        )
                        if thumb_rect is not None and thumb_rect.inflate(10, 0).collidepoint(pos):
                            rules_scrollbar_dragging = True
                            rules_scrollbar_drag_grab_offset = pos[1] - thumb_rect.y
                        elif track_rect is not None and track_rect.inflate(10, 0).collidepoint(pos):
                            rules_scroll_offset = scroll_offset_for_thumb_y(
                                pos[1] - thumb_rect.height // 2,
                                rules_viewport_rect,
                                rules_content_height,
                                thumb_rect.height,
                            )
                            rules_scrollbar_dragging = True
                            rules_scrollbar_drag_grab_offset = thumb_rect.height // 2
            elif event.type == MOUSEBUTTONUP:
                rules_scrollbar_dragging = False
            elif event.type == MOUSEMOTION and rules_scrollbar_dragging and rules_viewport_rect is not None:
                track_rect, thumb_rect = get_scrollbar_rects(
                    rules_viewport_rect, rules_content_height, rules_scroll_offset
                )
                if thumb_rect is not None:
                    rules_scroll_offset = scroll_offset_for_thumb_y(
                        event.pos[1] - rules_scrollbar_drag_grab_offset,
                        rules_viewport_rect,
                        rules_content_height,
                        thumb_rect.height,
                    )
            elif event.type == MOUSEWHEEL and screen_state == "rules_detail" and rules_viewport_rect is not None:
                max_scroll = max(0, rules_content_height - rules_viewport_rect.height)
                rules_scroll_offset -= event.y * 40
                rules_scroll_offset = max(0, min(rules_scroll_offset, max_scroll))
            elif event.type == KEYDOWN and screen_state == "rules_detail" and rules_viewport_rect is not None:
                max_scroll = max(0, rules_content_height - rules_viewport_rect.height)
                if event.key == K_DOWN:
                    rules_scroll_offset = min(rules_scroll_offset + 40, max_scroll)
                elif event.key == K_UP:
                    rules_scroll_offset = max(rules_scroll_offset - 40, 0)
                elif event.key == K_PAGEDOWN:
                    rules_scroll_offset = min(rules_scroll_offset + rules_viewport_rect.height, max_scroll)
                elif event.key == K_PAGEUP:
                    rules_scroll_offset = max(rules_scroll_offset - rules_viewport_rect.height, 0)

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()
