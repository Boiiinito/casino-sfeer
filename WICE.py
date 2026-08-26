import pygame
import math
import sys
import time
import random

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
# Trimmed from 900: the real content (wheel, betting board, wallet/chips)
# only spans roughly the top 700px of the canvas, leaving a lot of unused
# space below it. Shrinking the native canvas height (all layout below is
# computed proportionally from WINDOW_HEIGHT, so nothing overlaps or gets
# clipped, it just tightens the built-in margins) lets the game render
# noticeably bigger once it's scaled to fit the app window, without
# affecting any other game's sizing. The outer menu/standalone launcher
# already reserves its own clearance below the Menu/Quit button and above
# the bottom edge, so this internal margin only needs to be a small buffer.
WINDOW_HEIGHT = 740
CIRCLE_RADIUS = 50
WHEEL_RADIUS = 200
DOT_RADIUS = 10
BLOCK_SIZE = 30
TEXT_BOX_SIZE = 30
BETTING_CIRCLE_BORDER = 4
CHIP_RADIUS = 20
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
FLASH_DURATION = 0.5
FLASH_CYCLES = 3
WIN_DELAY = 0.1
SLOW_ROTATION_SPEED = 5
SPIN_SPEED_MULTIPLIER = 3    # Multiplier for spin rounds
DICE_ANIMATION_DURATION = 0.5  # Duration for dice shake/roll animation
BLOCK_HIT_TOLERANCE = 18  # Pixels; the pointer must be close to the center of a letter block

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GOLD  = (255, 215, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GRAY  = (200, 200, 200)
LIGHT_GREEN = (144, 238, 144)
LIGHT_RED = (255, 182, 193)
PINK = (255, 192, 203)

# Match the chip colors used in Chance O' Chill.
CHIPS = [
    {"value": 10, "color": (255, 51, 255)},    # Neon pink
    {"value": 20, "color": (57, 255, 20)},     # Neon green
    {"value": 50, "color": (0, 255, 255)},     # Neon blue
    {"value": 100, "color": (255, 255, 0)},    # Neon yellow
    {"value": 200, "color": (255, 127, 0)}     # Neon orange
]

# LETTERS order: odd letters first then even letters.
LETTERS = "ACEGIKMOQSUWYBDFHJLNPRTVXZ"

# Regular betting spaces order as per original specification.
BETTING_SPACES = [
    "AM", "BN", "CO",
    "DP", "EQ", "FR",
    "GS", "HT", "IU",
    "JV", "KW", "LX",
    "ZY"
]

# COMBINED_SPACES now equals BETTING_SPACES.
COMBINED_SPACES = BETTING_SPACES

# Set up the display (deferred when embedded in Casino Sfeer menu)
screen = None


def _init_display(caption="Wice"):
    global screen
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(caption)
    return screen

class Bet:
    def __init__(self, position, chip, space_index):
        self.position = position  # (x, y)
        self.chip = chip          # Dictionary containing chip info
        self.space_index = space_index  # Index into COMBINED_SPACES
        self.is_winner = False    # Status for winning bet

class WheelState:
    def __init__(self):
        self.reset_initial()
        self.spin_duration = 0  # Spin duration from dice roll
        self.anticlockwise = True
        self.upcoming_direction = True  # True for anticlockwise, False for clockwise
        self.last_update_time = time.time()
        self.final_spin_angle = None
        self.previous_winners = []  # List to store previous round winning letters

    def reset_initial(self):
        self.current_angle = random.uniform(0, 360)
        self.start_angle = self.current_angle
        self.is_spinning = False
        self.spin_start_time = 0
        self.final_angle = 0
        self.has_spun = False
        self.result_processed = False
        self.flash_start_time = None
        self.winning_letter = None
        self.stop_time = None
        self.final_spin_angle = None
        self.current_dice_values = None
        # Flag to ensure idle direction flips only once after round ends.
        self.idle_switch_done = False

    def new_round(self, upcoming_anticlockwise):
        # Store previous round winner if exists.
        if self.winning_letter:
            self.previous_winners.append(self.winning_letter)
            if len(self.previous_winners) > 10:
                self.previous_winners.pop(0)
        self.start_angle = self.current_angle
        self.is_spinning = False
        self.spin_start_time = 0
        self.final_angle = 0
        self.has_spun = False
        self.result_processed = False
        self.flash_start_time = None
        self.winning_letter = None
        self.stop_time = None
        self.final_spin_angle = None
        self.current_dice_values = None
        self.anticlockwise = upcoming_anticlockwise
        self.idle_switch_done = False

    def start_spin(self, spin_duration, anticlockwise, dice_values):
        self.spin_duration = spin_duration  # Set spin duration based on dice roll
        self.anticlockwise = anticlockwise
        self.upcoming_direction = anticlockwise
        self.start_angle = self.current_angle
        self.is_spinning = True
        self.spin_start_time = time.time()
        self.current_dice_values = dice_values
        base_rotation = SPIN_SPEED_MULTIPLIER * (1440 + random.uniform(0, 360))
        if anticlockwise:
            base_rotation = -base_rotation
        self.final_angle = self.start_angle + base_rotation
        self.has_spun = True
        self.result_processed = False
        self.flash_start_time = None
        self.stop_time = None
        self.final_spin_angle = None
        self.idle_switch_done = False

    def _ease_in_out_cubic(self, x):
        return 4 * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 3) / 2

    def _calculate_winner(self, angle, center_x, center_y, wheel_radius):
        # The triangle pointer points at the wheel from below, so use that tip as the reference.
        pointer_x = center_x
        pointer_y = center_y + wheel_radius + 10

        sector_angle = 360 / len(LETTERS)
        best_letter = None
        best_distance = float("inf")

        for index, letter in enumerate(LETTERS):
            rad = math.radians(angle + index * sector_angle)
            box_x = center_x + math.cos(rad) * wheel_radius
            box_y = center_y + math.sin(rad) * wheel_radius
            distance = math.hypot(box_x - pointer_x, box_y - pointer_y)
            if distance < best_distance:
                best_distance = distance
                best_letter = letter

        if best_distance <= BLOCK_HIT_TOLERANCE:
            return best_letter
        return None

    def get_winning_letter(self):
        return self.winning_letter

    def get_previous_winners(self):
        return self.previous_winners

    def update(self, center_x, center_y, wheel_radius):
        current_time = time.time()
        dt = current_time - self.last_update_time

        if self.is_spinning:
            elapsed = current_time - self.spin_start_time
            progress = elapsed / self.spin_duration
            if progress >= 1.0:
                progress = 1.0
                self.is_spinning = False
                self.stop_time = current_time
                self.final_spin_angle = (self.start_angle + (self.final_angle - self.start_angle) *
                                         self._ease_in_out_cubic(progress)) % 360
                self.current_angle = self.final_spin_angle
            else:
                eased_progress = self._ease_in_out_cubic(progress)
                angle_diff = self.final_angle - self.start_angle
                self.current_angle = (self.start_angle + angle_diff * eased_progress) % 360
        else:
            if self.final_spin_angle is not None and not self.result_processed:
                if current_time - self.stop_time >= WIN_DELAY:
                    self.winning_letter = self._calculate_winner(
                        self.final_spin_angle,
                        center_x,
                        center_y,
                        wheel_radius,
                    )
                    self.result_processed = True
            if self.result_processed and not self.idle_switch_done:
                self.anticlockwise = not self.anticlockwise
                self.idle_switch_done = True
            if self.anticlockwise:
                self.current_angle = (self.current_angle - SLOW_ROTATION_SPEED * dt) % 360
            else:
                self.current_angle = (self.current_angle + SLOW_ROTATION_SPEED * dt) % 360

        self.last_update_time = current_time

def process_winning_bets(placed_bets, winning_letter, wallet):
    # If no letter/box is hit, it's a push: the player gets the original bet back
    # and receives no payout.
    if winning_letter is None:
        for bet in placed_bets:
            bet.is_winner = False
            wallet += bet.chip["value"]
        return wallet

    for bet in placed_bets:
        space_label = COMBINED_SPACES[bet.space_index]
        bet.is_winner = False
        if winning_letter in space_label:
            bet.is_winner = True
            payout = bet.chip["value"] * 14
            wallet += payout
    return wallet

def draw_button(x, y, width, height, text):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 4)
    font = pygame.font.Font(None, 32)
    text_surface = font.render(text, True, RED)
    text_rect = text_surface.get_rect(center=(x + width / 2, y + height / 2))
    screen.blit(text_surface, text_rect)

def draw_wheel(wheel_state, placed_bets):
    center_x = WINDOW_WIDTH * 3 // 4
    center_y = WINDOW_HEIGHT // 3
    num_letters = 26
    base_angle = wheel_state.current_angle
    highlighted_letters = set()
    for bet in placed_bets:
        space_label = COMBINED_SPACES[bet.space_index]
        highlighted_letters.update(space_label)
    for i in range(0, num_letters, 2):
        angle = math.radians(base_angle + i * (360 / 26))
        opp_angle = math.radians(base_angle + i * (360 / 26) + 180)
        start_x = center_x + math.cos(angle) * WHEEL_RADIUS
        start_y = center_y + math.sin(angle) * WHEEL_RADIUS
        end_x = center_x + math.cos(opp_angle) * WHEEL_RADIUS
        end_y = center_y + math.sin(opp_angle) * WHEEL_RADIUS
        pygame.draw.line(screen, BLACK, (start_x, start_y), (end_x, end_y), 4)
    regular_font = pygame.font.SysFont(None, 24)
    for i in range(num_letters):
        letter = LETTERS[i]
        rad = math.radians(base_angle + i * (360 / 26))
        box_x = center_x + math.cos(rad) * WHEEL_RADIUS
        box_y = center_y + math.sin(rad) * WHEEL_RADIUS
        rect = pygame.Rect(0, 0, TEXT_BOX_SIZE, TEXT_BOX_SIZE)
        rect.center = (box_x, box_y)
        pygame.draw.rect(screen, WHITE, rect)
        border_color = RED if letter in highlighted_letters else BLACK
        pygame.draw.rect(screen, border_color, rect, 4)
        text_surface = regular_font.render(letter, True, BLACK)
        text_rect = text_surface.get_rect(center=(box_x, box_y))
        screen.blit(text_surface, text_rect)
    pygame.draw.circle(screen, RED, (center_x, center_y), DOT_RADIUS)
    return center_x, center_y

def show_credits_page():
    credits_running = True

    # Create the required fonts - Times New Roman for all text with increased sizes
    try:
        title_font = pygame.font.SysFont("Times New Roman", 42, bold=True)  # Increased from 36 to 42
        regular_font = pygame.font.SysFont("Times New Roman", 30)  # Increased from 24 to 30
        copyright_font = pygame.font.SysFont("Times New Roman", 24)  # Increased from 18 to 24
    except:
        # Fallback if Times New Roman is not available
        title_font = pygame.font.Font(None, 42)
        regular_font = pygame.font.Font(None, 30)
        copyright_font = pygame.font.Font(None, 24)
        print("Warning: Times New Roman font not available, using default font.")

    # Updated content with dealer line
    credits_lines = [
        {"text": "CREDITS", "font": title_font, "y_offset": 150},
        {"text": "Kind regards,", "font": regular_font, "y_offset": 220},
        {"text": "Dealer: Wesley Nyanhongo", "font": regular_font, "y_offset": 280},
        {"text": "Game founder:", "font": regular_font, "y_offset": 340},
        {"text": "Wesley Nyanhongo", "font": regular_font, "y_offset": 400},
        {"text": "Copyright © 2025 Wesley Tashinga Nyanhongo. All rights reserved", "font": copyright_font, "y_offset": 480}
    ]

    while credits_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                credits_running = False

        screen.fill(WHITE)

        # Draw each line using its specific font and position
        for line in credits_lines:
            text_surface = line["font"].render(line["text"], True, BLACK)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, line["y_offset"]))
            screen.blit(text_surface, text_rect)

        pygame.display.flip()
        pygame.time.delay(50)

def draw_wallet_and_chips(center_x, center_y, wheel_state, selected_chip, wallet, current_time):
    block_y = center_y + WHEEL_RADIUS + 50
    indicator_size = 80
    triangle_points = [
        (center_x, block_y - indicator_size / 2),
        (center_x - indicator_size / 2, block_y + indicator_size / 2),
        (center_x + indicator_size / 2, block_y + indicator_size / 2)
    ]
    pygame.draw.polygon(screen, WHITE, triangle_points)
    pygame.draw.polygon(screen, BLACK, triangle_points, 4)
    spin_y = block_y + indicator_size / 2
    spin_x = center_x - BUTTON_WIDTH / 2
    if wheel_state.is_spinning:
        remaining = wheel_state.spin_start_time + wheel_state.spin_duration - current_time
        remaining = max(remaining, 0)
        button_text = str(int(math.ceil(remaining)))
    else:
        button_text = "Spin"
    draw_button(spin_x, spin_y, BUTTON_WIDTH, BUTTON_HEIGHT, button_text)
    betting_start_x = WINDOW_WIDTH // 7
    betting_start_y = WINDOW_HEIGHT // 6
    zy_col = 1
    zy_row = 4
    zy_x = betting_start_x + zy_col * (CIRCLE_RADIUS * 2.5)
    zy_y = betting_start_y + zy_row * (CIRCLE_RADIUS * 2.2)
    undo_x = zy_x - BUTTON_WIDTH / 2
    undo_y = zy_y + CIRCLE_RADIUS + 40
    draw_button(undo_x, undo_y, BUTTON_WIDTH, BUTTON_HEIGHT, "Undo")
    board_x = WINDOW_WIDTH // 7
    board_center = board_x + (CIRCLE_RADIUS * 2.5)
    ui_x = (board_center + center_x) / 2
    wallet_y = spin_y + BUTTON_HEIGHT + 40
    font_wallet = pygame.font.Font(None, 36)
    wallet_text = font_wallet.render(f"Wallet: £{wallet}", True, BLACK)
    wallet_rect = wallet_text.get_rect(center=(ui_x, wallet_y))
    screen.blit(wallet_text, wallet_rect)

    chips_y = wallet_y + 50
    chip_spacing = CHIP_RADIUS * 2.2
    chips_start_x = ui_x - ((len(CHIPS)-1)*chip_spacing)/2
    chip_font = pygame.font.Font(None, 20)
    for i, chip in enumerate(CHIPS):
        chip_x = chips_start_x + i * chip_spacing
        pygame.draw.circle(screen, chip["color"], (int(chip_x), chips_y), CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, (int(chip_x), chips_y), CHIP_RADIUS, 4)
        value_text = chip_font.render(f"£{chip['value']}", True, BLACK)
        value_rect = value_text.get_rect(center=(int(chip_x), chips_y))
        screen.blit(value_text, value_rect)
        if chip == selected_chip:
            pygame.draw.circle(screen, GOLD, (int(chip_x), chips_y), CHIP_RADIUS + 4, 4)
    if not wheel_state.is_spinning and wheel_state.has_spun:
        # None means the pointer landed on a blank space (a push), so show nothing.
        winning_letter = wheel_state.get_winning_letter()
        if winning_letter:
            font_indicator = pygame.font.Font(None, 36)
            win_text = font_indicator.render(winning_letter, True, RED)
            centroid_x = sum(pt[0] for pt in triangle_points) / 3
            centroid_y = sum(pt[1] for pt in triangle_points) / 3
            win_rect = win_text.get_rect(center=(centroid_x, centroid_y))
            screen.blit(win_text, win_rect)
    return spin_x, spin_y, undo_x, undo_y, chips_y, chips_start_x, wallet_rect

def draw_betting_circles(placed_bets, wheel_state, winning_letter):
    start_x = WINDOW_WIDTH // 7
    start_y = WINDOW_HEIGHT // 6
    italic_font = pygame.font.SysFont(None, 28, italic=True)
    payout_font = pygame.font.SysFont(None, 18)
    circle_positions = []
    for i in range(len(BETTING_SPACES)):
        if BETTING_SPACES[i] == "ZY":
            row = 4
            col = 1
        else:
            row = i // 3
            col = i % 3
        x = start_x + col * (CIRCLE_RADIUS * 2.5)
        y = start_y + row * (CIRCLE_RADIUS * 2.2)
        pygame.draw.circle(screen, WHITE, (x, y), CIRCLE_RADIUS)
        border_color = GREEN if (wheel_state.has_spun and not wheel_state.is_spinning and 
                                  winning_letter and winning_letter in BETTING_SPACES[i]) else BLACK
        pygame.draw.circle(screen, border_color, (x, y), CIRCLE_RADIUS, BETTING_CIRCLE_BORDER)
        space_label = BETTING_SPACES[i]
        text = italic_font.render(space_label, True, BLACK)
        text_rect = text.get_rect(center=(x, y - 10))
        screen.blit(text, text_rect)
        payout_text = payout_font.render("13:1", True, RED)
        payout_rect = payout_text.get_rect(center=(x, y + TEXT_BOX_SIZE // 2))
        screen.blit(payout_text, payout_rect)
        circle_positions.append((x, y))
    for bet in placed_bets:
        x, y = bet.position
        pygame.draw.circle(screen, bet.chip["color"], (int(x), int(y)), CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, (int(x), int(y)), CHIP_RADIUS, 4)
        chip_font = pygame.font.Font(None, 20)
        value_text = chip_font.render(f"£{bet.chip['value']}", True, BLACK)
        value_rect = value_text.get_rect(center=(x, y))
        screen.blit(value_text, value_rect)
    return circle_positions

def roll_dice():
    return (
        random.randint(1, 6),
        random.randint(1, 6),
        random.randint(1, 6),
        random.randint(1, 6)
    )

def draw_dice(dice_values, center_x, center_y):
    dice_size = 50
    dice_spacing = 20
    dice_y_bottom = center_y + WHEEL_RADIUS + 90
    total_width = dice_size * 3 + dice_spacing * 2
    dice_start_x = (WINDOW_WIDTH - total_width) // 2
    dot_radius = 5
    def get_dot_positions(x, y, size):
        return {
            'top_left': (x + size * 0.25, y + size * 0.25),
            'top_right': (x + size * 0.75, y + size * 0.25),
            'middle_left': (x + size * 0.25, y + size * 0.5),
            'middle_right': (x + size * 0.75, y + size * 0.5),
            'bottom_left': (x + size * 0.25, y + size * 0.75),
            'bottom_right': (x + size * 0.75, y + size * 0.75),
            'center': (x + size * 0.5, y + size * 0.5)
        }
    for i in range(3):
        x = dice_start_x + i * (dice_size + dice_spacing)
        y = dice_y_bottom
        pygame.draw.rect(screen, WHITE, (x, y, dice_size, dice_size))
        pygame.draw.rect(screen, BLACK, (x, y, dice_size, dice_size), 4)
        positions = get_dot_positions(x, y, dice_size)
        value = dice_values[i]
        if value == 1:
            pygame.draw.circle(screen, RED, positions['center'], dot_radius)
        elif value == 2:
            pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
        elif value == 3:
            pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['center'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
        elif value == 4:
            pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['top_right'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
        elif value == 5:
            pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['top_right'], dot_radius)
            pygame.draw.circle(screen, RED, positions['center'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
        elif value == 6:
            pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['top_right'], dot_radius)
            pygame.draw.circle(screen, RED, positions['middle_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['middle_right'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_left'], dot_radius)
            pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
    x_second = dice_start_x + (dice_size + dice_spacing)
    y_fourth = dice_y_bottom - (dice_size + dice_spacing)
    pygame.draw.rect(screen, WHITE, (x_second, y_fourth, dice_size, dice_size))
    pygame.draw.rect(screen, BLACK, (x_second, y_fourth, dice_size, dice_size), 4)
    positions = get_dot_positions(x_second, y_fourth, dice_size)
    value = dice_values[3]
    if value == 1:
        pygame.draw.circle(screen, RED, positions['center'], dot_radius)
    elif value == 2:
        pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
    elif value == 3:
        pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['center'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
    elif value == 4:
        pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['top_right'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
    elif value == 5:
        pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['top_right'], dot_radius)
        pygame.draw.circle(screen, RED, positions['center'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)
    elif value == 6:
        pygame.draw.circle(screen, RED, positions['top_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['top_right'], dot_radius)
        pygame.draw.circle(screen, RED, positions['middle_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['middle_right'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_left'], dot_radius)
        pygame.draw.circle(screen, RED, positions['bottom_right'], dot_radius)

# Helper function: returns the letter from the first betting space that contains the given letter,
# and returns its counterpart (the letter that is not the given one).
def get_shared_letter(letter):
    for space in BETTING_SPACES:
        if letter in space:
            other = space.replace(letter, "")
            return other if other else None
    return None

# Function to show results in a separate "page" when the center is clicked.
def show_result_page(wheel_state, dice_values):
    result_running = True
    # None means either the dice rolled 12 or below (a loss) or the wheel landed on a blank space (a push).
    winning_letter = wheel_state.get_winning_letter()
    dice_sum = sum(dice_values)
    dice_lost = dice_sum <= 12
    shared_letter = get_shared_letter(winning_letter) if winning_letter else "N/A"
    if dice_lost:
        result_text = "Result: Loss (dice rolled 12 or below)"
        bets_text = "Bet forfeited, no refund."
    elif winning_letter is None:
        result_text = "Result: Push"
        bets_text = "Original bets returned."
    else:
        result_text = "Result: Winner"
        bets_text = ""
    result_lines = [
        f"Dice Values: {dice_values[0]}, {dice_values[1]}, {dice_values[2]}, {dice_values[3]} (Sum: {dice_sum})",
        f"Winning Letter: {winning_letter if winning_letter is not None else 'None'}",
        f"Shared Bet Letter: {shared_letter}",
        result_text,
        bets_text,
        "Press any key to return."
    ]
    while result_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                result_running = False
        screen.fill(WHITE)
        font = pygame.font.Font(None, 36)
        for idx, line in enumerate(result_lines):
            text = font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 150 + idx * 50))
            screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(50)

placed_bets = []

def main(surface=None, embedded=False, wallet=None):
    global placed_bets, screen

    from embedded_utils import check_embedded_exit, draw_back_button

    if surface is not None:
        screen = surface
    elif screen is None:
        _init_display()

    clock = pygame.time.Clock()
    running = True
    back_rect = None
    wheel_state = WheelState()
    selected_chip = None
    shared_wallet = wallet
    wallet = shared_wallet.balance if shared_wallet is not None else 1000
    round_ended = False
    dice_lost = False
    round_counter = 0
    dice_values = roll_dice()
    dice_animating = False
    dice_animation_end_time = 0
    upcoming_dir = True if round_counter % 2 == 0 else False
    wheel_state.new_round(upcoming_anticlockwise=upcoming_dir)
    
    # Initialize wallet_rect
    wallet_rect = None
    try:
        while running:
            current_time = time.time()
            screen.fill(WHITE)
            winning_letter = wheel_state.get_winning_letter()
            circle_positions = draw_betting_circles(placed_bets, wheel_state, winning_letter)
            center_x, center_y = draw_wheel(wheel_state, placed_bets)
            spin_x, spin_y, undo_x, undo_y, chips_y, chips_start_x, wallet_rect = draw_wallet_and_chips(center_x, center_y, wheel_state, selected_chip, wallet, current_time)
            if dice_animating:
                if current_time < dice_animation_end_time:
                    dice_values = (random.randint(1, 6), random.randint(1, 6), random.randint(1, 6), random.randint(1, 6))
                else:
                    dice_animating = False
                    final_dice = roll_dice()
                    dice_values = final_dice
                    dice_total = sum(final_dice)
                    if dice_total <= 12:
                        print("Total dice value is 12 or below. Player loses their bet immediately.")
                        dice_lost = True
                        round_ended = True
                    else:
                        spin_duration = dice_total
                        wheel_state.start_spin(spin_duration, anticlockwise=(round_counter % 2 == 0), dice_values=dice_values)
            draw_dice(dice_values, center_x, center_y)
            if not wheel_state.is_spinning and wheel_state.result_processed:
                round_ended = True
            if embedded:
                back_rect = None
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
                    mouse_pos = pygame.mouse.get_pos()
                    distance_from_center = math.dist(mouse_pos, (center_x, center_y))
                    # If click on center (within 30 px) show the result page unconditionally.
                    if distance_from_center <= 30:
                        show_result_page(wheel_state, dice_values)
                        continue
                    if wheel_state.is_spinning or round_ended:
                        if round_ended and spin_x <= mouse_pos[0] <= (spin_x + BUTTON_WIDTH) and spin_y <= mouse_pos[1] <= (spin_y + BUTTON_HEIGHT):
                            if dice_lost:
                                # Dice rolled 12 or below: player loses the bet outright, no refund.
                                placed_bets = []
                            else:
                                wallet = process_winning_bets(placed_bets, wheel_state.winning_letter, wallet)
                                placed_bets = []
                            round_ended = False
                            dice_lost = False
                            round_counter += 1
                            upcoming_dir = True if round_counter % 2 == 0 else False
                            wheel_state.new_round(upcoming_anticlockwise=upcoming_dir)
                        continue
                    if wallet_rect and wallet_rect.collidepoint(mouse_pos):
                        show_credits_page()
                    elif not wheel_state.is_spinning and not round_ended:
                        if spin_x <= mouse_pos[0] <= (spin_x + BUTTON_WIDTH) and spin_y <= mouse_pos[1] <= (spin_y + BUTTON_HEIGHT):
                            if placed_bets and not dice_animating:
                                dice_animating = True
                                dice_animation_end_time = current_time + DICE_ANIMATION_DURATION
                        elif undo_x <= mouse_pos[0] <= (undo_x + BUTTON_WIDTH) and undo_y <= mouse_pos[1] <= (undo_y + BUTTON_HEIGHT):
                            if placed_bets:
                                for bet in placed_bets:
                                    wallet += bet.chip["value"]
                                placed_bets = []
                        else:
                            bet_removed = False
                            for bet in placed_bets:
                                if math.dist(mouse_pos, bet.position) <= CHIP_RADIUS:
                                    if wallet >= bet.chip["value"]:
                                        placed_bets.append(Bet(bet.position, bet.chip, bet.space_index))
                                        wallet -= bet.chip["value"]
                                    bet_removed = True
                                    break
                            if not bet_removed:
                                for i, chip in enumerate(CHIPS):
                                    chip_x = chips_start_x + i * (CHIP_RADIUS * 2.2)
                                    if (chip_x - CHIP_RADIUS <= mouse_pos[0] <= chip_x + CHIP_RADIUS and
                                        chips_y - CHIP_RADIUS <= mouse_pos[1] <= chips_y + CHIP_RADIUS):
                                        if wallet >= chip["value"]:
                                            selected_chip = chip
                                if selected_chip:
                                    for i, (circle_x, circle_y) in enumerate(circle_positions):
                                        if math.dist(mouse_pos, (circle_x, circle_y)) <= CIRCLE_RADIUS:
                                            if wallet >= selected_chip["value"]:
                                                placed_bets.append(Bet((circle_x, circle_y), selected_chip, i))
                                                wallet -= selected_chip["value"]
                                            break
            wheel_state.update(center_x, center_y, WHEEL_RADIUS)
            pygame.display.flip()
            clock.tick(60)
    finally:
        if shared_wallet is not None:
            shared_wallet.balance = wallet

    if not embedded:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    from embedded_utils import run_game_standalone
    run_game_standalone(sys.modules[__name__], "Wice")
