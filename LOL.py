import pygame
import sys
import math
from collections import namedtuple
import random

pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
CARD_WIDTH = 80
CARD_HEIGHT = 120
CHIP_RADIUS = 20
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
CARD_SLOT_WIDTH = 100
CARD_SLOT_HEIGHT = 140
CHIP_COLORS = [
    (255, 51, 255),    # Neon pink for £10
    (57, 255, 20),     # Neon green for £20
    (0, 255, 255),     # Neon blue for £50
    (255, 255, 0),     # Neon yellow for £100
    (255, 127, 0)      # Neon orange for £200
]
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CARD_BACK_COLOR = (0, 0, 128)
RED_COLOR = (255, 0, 0)

# Named tuple for Card
Card = namedtuple('Card', ['rank', 'suit'])

# Initialize Screen (deferred when embedded in Casino Sfeer menu)
screen = None
clock = None


def _init_display(caption="LoL"):
    global screen, clock
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(caption)
    if clock is None:
        clock = pygame.time.Clock()
    return screen

# Initialize Deck
INITIAL_DECK = [
    Card('Ace', '♣'), Card('Ace', '♥'), Card('Ace', '♠'), Card('Ace', '♦'),
    Card('King', '♣'), Card('King', '♥'), Card('King', '♠'), Card('King', '♦'),
    Card('Queen', '♣'), Card('Queen', '♥'), Card('Queen', '♠'), Card('Queen', '♦'),
    Card('Jester', '♣'), Card('Jester', '♥'), Card('Jester', '♠'), Card('Jester', '♦'),
    Card('Joker', 'Black'), Card('Joker', 'Red')
] * 3

deck = INITIAL_DECK.copy()
random.shuffle(deck)

# Game State Variables
drawn_cards = []
history = []
betting_chips = []
round_count = 0
showing_history = False
placed_bets = set()

# Wallet and Chip Values
wallet_balance = 1000
CHIP_VALUES = [10, 20, 50, 100, 200]

# Additional State Variables
current_cards = []
current_winning_bets = []
current_losing_bets = []
results_displayed = False
active_chip = None  # Track the currently selected chip

class Button:
    def __init__(self, x, y, width, height, text, font_size=28):
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

class UI:
    def __init__(self):
        self.chip_font = pygame.font.Font(None, 20)
        self.button_font = pygame.font.Font(None, 28)
        self.wallet_font = pygame.font.Font(None, 36)
        self.bet_button = Button(350, 550, BUTTON_WIDTH, BUTTON_HEIGHT, "Bet")
        self.undo_button = Button(350, 600, BUTTON_WIDTH, BUTTON_HEIGHT, "Undo")
        self.history_button = Button(500, 575, 80, 30, "History")

    def draw_wallet(self, screen):
        wallet_text = self.wallet_font.render(f"Wallet: £{wallet_balance}", True, BLACK)
        self.wallet_rect = wallet_text.get_rect(topleft=(20, 550))
        screen.blit(wallet_text, self.wallet_rect)

    def draw_chips(self, screen):
        global active_chip
        for i, color in enumerate(CHIP_COLORS):
            chip_center = (40 + i * 60, 620)
            if active_chip and active_chip[0] == color:
                pygame.draw.circle(screen, (255, 255, 0), chip_center, CHIP_RADIUS + 3)  # Highlight
            pygame.draw.circle(screen, color, chip_center, CHIP_RADIUS)
            pygame.draw.circle(screen, BLACK, chip_center, CHIP_RADIUS, 3)
            chip_text = self.chip_font.render(f"£{CHIP_VALUES[i]}", True, BLACK)
            text_rect = chip_text.get_rect(center=chip_center)
            screen.blit(chip_text, text_rect)

    def draw_card_slots(self, screen):
        for i in range(4):
            card_slot = pygame.Rect(125 + i * 150, 20, CARD_SLOT_WIDTH, CARD_SLOT_HEIGHT)
            pygame.draw.rect(screen, WHITE, card_slot)
            pygame.draw.rect(screen, BLACK, card_slot, 2)

    def draw_card_pile(self, screen):
        card_pile = pygame.Rect(700, 550, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(screen, CARD_BACK_COLOR, card_pile)
        pygame.draw.rect(screen, BLACK, card_pile, 3)

    def draw_buttons(self, screen):
        self.bet_button.draw(screen)
        self.undo_button.draw(screen)
        self.history_button.draw(screen)

    def draw_ui_elements(self, screen):
        self.draw_wallet(screen)
        self.draw_chips(screen)
        self.draw_buttons(screen)
        self.draw_card_slots(screen)
        self.draw_card_pile(screen)

ui = UI()

def draw_board(screen):
    board_rect = pygame.Rect(100, 180, 600, 300)
    pygame.draw.rect(screen, WHITE, board_rect)

    pygame.draw.line(screen, BLACK, (250, 180), (250, 480), 2)
    pygame.draw.line(screen, BLACK, (550, 180), (550, 480), 2)
    pygame.draw.line(screen, BLACK, (100, 280), (700, 280), 2)
    pygame.draw.line(screen, BLACK, (100, 380), (700, 380), 2)
    pygame.draw.line(screen, BLACK, (400, 180), (400, 280), 2)
    pygame.draw.line(screen, BLACK, (325, 280), (325, 380), 2)
    pygame.draw.line(screen, BLACK, (475, 280), (475, 380), 2)

    try:
        font = pygame.font.SysFont('dejavusans', 48)
    except:
        font = pygame.font.Font(None, 36)

    label_font = pygame.font.Font(None, 36)
    vertical_labels = ['Ace', 'Jester', 'Joker']

    text_C = font.render('\u2663', True, BLACK)  # Clubs
    text_H = font.render('\u2665', True, RED_COLOR)  # Hearts
    text_D = font.render('\u2666', True, RED_COLOR)  # Diamonds
    text_S = font.render('\u2660', True, BLACK)  # Spades

    suit_positions = {
        'Club': (287, 300),
        'Heart': (362, 300),
        'Spade': (287, 350),
        'Diamond': (362, 350),
        'Club2': (437, 300),
        'Heart2': (512, 300),
        'Spade2': (437, 350),
        'Diamond2': (512, 350)
    }

    screen.blit(text_C, text_C.get_rect(center=suit_positions['Club']))
    screen.blit(text_H, text_H.get_rect(center=suit_positions['Heart']))
    screen.blit(text_S, text_S.get_rect(center=suit_positions['Spade']))
    screen.blit(text_D, text_D.get_rect(center=suit_positions['Diamond']))

    screen.blit(text_C, text_C.get_rect(center=suit_positions['Club2']))
    screen.blit(text_H, text_H.get_rect(center=suit_positions['Heart2']))
    screen.blit(text_S, text_S.get_rect(center=suit_positions['Spade2']))
    screen.blit(text_D, text_D.get_rect(center=suit_positions['Diamond2']))

    pygame.draw.line(screen, BLACK, (400, 280), (400, 380), 2)
    pygame.draw.line(screen, BLACK, (250, 330), (550, 330), 2)

    merged_text = label_font.render('4T', True, BLACK)
    merged_rect = merged_text.get_rect(center=(400, 430))
    screen.blit(merged_text, merged_rect)

    for i in range(4):
        for j in range(3):
            if (i == 1 and j == 2) or (i == 2 and j == 2):
                continue

            if i == 0 or i == 3:
                label = vertical_labels[j]
                text = label_font.render(label, True, BLACK)
                text_rect = text.get_rect(center=(100 + i * 150 + 75, 180 + j * 100 + 50))
                screen.blit(text, text_rect)

            elif i == 1:
                if j == 0:
                    label = "King"
                    text = label_font.render(label, True, BLACK)
                    text_rect = text.get_rect(center=(100 + i * 150 + 75, 180 + j * 100 + 50))
                    screen.blit(text, text_rect)
            elif i == 2:
                if j == 0:
                    label = "Queen"
                    text = label_font.render(label, True, BLACK)
                    text_rect = text.get_rect(center=(100 + i * 150 + 75, 180 + j * 100 + 50))
                    screen.blit(text, text_rect)

def draw_card(screen, x, y, card, flip_angle):
    card_width = CARD_WIDTH
    card_height = CARD_HEIGHT

    visible_width = abs(int(card_width * math.cos(math.radians(flip_angle))))

    card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)

    if flip_angle < 90 or flip_angle > 270:
        card_surface.fill(CARD_BACK_COLOR)
    elif 90 <= flip_angle <= 270:
        if card.rank and card.suit:
            card_surface.fill(WHITE)

            is_joker = card.rank == 'Joker'
            font_style = pygame.font.SysFont('timesnewroman', 28, bold=is_joker, italic=is_joker)

            color = RED_COLOR if card.suit in ['♥', '♦', 'Red'] else BLACK

            rank_text = font_style.render(card.rank, True, color)
            suit_text = font_style.render(card.suit, True, color)

            rank_pos = ((card_width - rank_text.get_width()) // 2, 20)
            suit_pos = ((card_width - suit_text.get_width()) // 2, 60)

            card_surface.blit(rank_text, rank_pos)
            card_surface.blit(suit_text, suit_pos)
        else:
            card_surface.fill(CARD_BACK_COLOR)

    if visible_width > 0:
        scaled_surface = pygame.transform.scale(card_surface, (visible_width, card_height))
        screen.blit(scaled_surface, (x + (card_width - visible_width) // 2, y))

    pygame.draw.rect(screen, BLACK,
                     (x + (card_width - visible_width) // 2, y, visible_width, card_height), 2)

def flip_cards(screen, cards):
    for i, card in enumerate(cards):
        x = 135 + i * 150
        y = 30

        screen.fill(WHITE)
        draw_board(screen)
        ui.draw_ui_elements(screen)
        for j in range(i):
            draw_card(screen, 135 + j * 150, 30, cards[j], 180)
        draw_card(screen, x, y, card, 0)
        for j in range(i + 1, 4):
            draw_card(screen, 135 + j * 150, 30, Card('', ''), 0)
        draw_betting_chips(screen)
        pygame.display.flip()

        for angle in range(0, 181, 10):
            screen.fill(WHITE)
            draw_board(screen)
            ui.draw_ui_elements(screen)

            for j in range(i):
                draw_card(screen, 135 + j * 150, 30, cards[j], 180)

            draw_card(screen, x, y, card, angle)

            for j in range(i + 1, 4):
                draw_card(screen, 135 + j * 150, 30, Card('', ''), 0)

            draw_betting_chips(screen)

            pygame.display.flip()
            pygame.time.wait(50)
        pygame.event.pump()

def draw_cards_without_animation(screen, cards):
    """Draw all cards at once without flip animation"""
    screen.fill(WHITE)
    draw_board(screen)
    ui.draw_ui_elements(screen)
    for i, card in enumerate(cards):
        draw_card(screen, 135 + i * 150, 30, card, 180)
    draw_betting_chips(screen)
    pygame.display.flip()

def draw_betting_chips(screen):
    for chip, center in betting_chips:
        color, value = chip  # Unpack color and value
        pygame.draw.circle(screen, color, center, CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
        chip_text = pygame.font.Font(None, 20).render(f"£{value}", True, BLACK)
        text_rect = chip_text.get_rect(center=center)
        screen.blit(chip_text, text_rect)

def show_history(screen, history):
    global showing_history
    showing_history = True
    while showing_history:
        screen.fill(WHITE)
        
        if history and len(history[-1]) == 8:
            history_rect = pygame.Rect(150, 200, 500, 200)
        else:
            history_rect = pygame.Rect(200, 200, 400, 200)
        
        if history:
            last_hand = history[-1]
            num_cards = len(last_hand)
            
            start_x = history_rect.x + (history_rect.width - num_cards * 90) // 2
            start_y = history_rect.y + 50
            
            if num_cards == 8:
                for i, card in enumerate(last_hand):
                    x_pos = start_x + (i % 4) * 90
                    y_pos = start_y if i < 4 else start_y + 100
                    draw_card(screen, x_pos, y_pos, card, 180)
            else:
                for i, card in enumerate(last_hand):
                    draw_card(screen, start_x + i * 90, start_y, card, 180)

        ui.draw_buttons(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                showing_history = False

def show_credits(screen):
    running = True
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill(WHITE)
    overlay.set_alpha(240)
    
    # Create fonts with Times New Roman and adjusted sizes
    title_font = pygame.font.SysFont('timesnewroman', 36, bold=True)
    text_font = pygame.font.SysFont('timesnewroman', 24)
    copyright_font = pygame.font.SysFont('timesnewroman', 20)
    
    # Render text with new fonts
    title = title_font.render("CREDITS", True, BLACK)
    dealer_label = text_font.render("Dealer:", True, BLACK)
    dealer_name = text_font.render("Wesley Nyanhongo", True, BLACK)
    regards = text_font.render("Kind regards,", True, BLACK)
    founder_label = text_font.render("Game founder:", True, BLACK)
    founder_name = text_font.render("Wesley Nyanhongo", True, BLACK)
    copyright = copyright_font.render("Copyright © 2025 Wesley Tashinga Nyanhongo. All rights reserved", True, BLACK)
    
    while running:
        screen.blit(overlay, (0, 0))
        
        # Adjust vertical spacing for better readability
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 120))
        screen.blit(dealer_label, (SCREEN_WIDTH//2 - dealer_label.get_width()//2, 200))
        screen.blit(dealer_name, (SCREEN_WIDTH//2 - dealer_name.get_width()//2, 230))
        screen.blit(regards, (SCREEN_WIDTH//2 - regards.get_width()//2, 290))
        screen.blit(founder_label, (SCREEN_WIDTH//2 - founder_label.get_width()//2, 320))
        screen.blit(founder_name, (SCREEN_WIDTH//2 - founder_name.get_width()//2, 350))
        screen.blit(copyright, (SCREEN_WIDTH//2 - copyright.get_width()//2, 440))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False
                    
        pygame.display.flip()

def replenish_deck():
    global deck, history
    deck = INITIAL_DECK.copy()
    random.shuffle(deck)
    history.clear()

def check_conditions_and_draw(deck, screen, label_positions):
    # Check if we have enough cards for a potential double draw (8 cards)
    if len(deck) < 8:
        replenish_deck()
        shuffle_animation(screen, deck)

    initial_cards = [deck.pop() for _ in range(4)]
    flip_cards(screen, initial_cards)
    
    character_count = {}
    suit_count = {}
    for card in initial_cards:
        character_count[card.rank] = character_count.get(card.rank, 0) + 1
        if card.suit not in ['Black', 'Red']:
            suit_count[card.suit] = suit_count.get(card.suit, 0) + 1

    all_cards = initial_cards.copy()

    if any(count >= 2 for count in character_count.values()) or any(count >= 3 for count in suit_count.values()):
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 2000:
            screen.fill(WHITE)
            draw_board(screen)
            ui.draw_ui_elements(screen)
            for i, card in enumerate(initial_cards):
                draw_card(screen, 135 + i * 150, 30, card, 180)
            draw_betting_chips(screen)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        
        # Check deck size again before drawing additional cards
        if len(deck) < 4:
            replenish_deck()
            shuffle_animation(screen, deck)
        additional_cards = [deck.pop() for _ in range(4)]
        all_cards = additional_cards.copy()
        draw_cards_without_animation(screen, additional_cards)

    winning_bets, losing_bets, total_winnings = resolve_bets(all_cards, betting_chips, label_positions)
    
    global wallet_balance, current_cards, results_displayed
    wallet_balance += total_winnings
    current_cards = all_cards
    
    handle_bet_results(screen, winning_bets, losing_bets, all_cards)
    
    return all_cards

def shuffle_animation(screen, deck):
    card_pile_rect = pygame.Rect(700, 550, CARD_WIDTH, CARD_HEIGHT)

    for _ in range(10):
        screen.fill(WHITE)
        draw_board(screen)
        ui.draw_ui_elements(screen)
        draw_betting_chips(screen)

        temp_deck = deck.copy()
        random.shuffle(temp_deck)
        for i, card in enumerate(temp_deck[:min(10, len(temp_deck))]):
            x = 700 + random.randint(-10, 10)
            y = 550 + random.randint(-10, 10)
            draw_card(screen, x, y, card, 0)

        pygame.display.flip()
        pygame.time.wait(50)

    screen.fill(WHITE)
    draw_board(screen)
    ui.draw_ui_elements(screen)
    draw_betting_chips(screen)
    pygame.draw.rect(screen, CARD_BACK_COLOR, card_pile_rect)
    pygame.draw.rect(screen, BLACK, card_pile_rect, 3)
    pygame.display.flip()
    pygame.time.wait(200)

def handle_mouse_click(pos, label_positions):
    global betting_chips, drawn_cards, round_count, deck, placed_bets, history, wallet_balance
    global current_cards, current_winning_bets, current_losing_bets, results_displayed, active_chip

    if ui.bet_button.is_clicked(pos):
        if results_displayed:
            current_cards = []
            current_winning_bets = []
            current_losing_bets = []
            results_displayed = False
            betting_chips = []
            return
        elif betting_chips:
            # Check if we need to replenish the deck
            if len(deck) < 8:
                replenish_deck()
                shuffle_animation(screen, deck)
            try:
                cards = check_conditions_and_draw(deck, screen, label_positions)
                drawn_cards = cards
                if len(history) > 20:
                    history = history[-20:]
                history.append(drawn_cards.copy())
                round_count += 1
            except Exception as e:
                print(f"Error during card draw: {e}")
                replenish_deck()
                shuffle_animation(screen, deck)
        return

    if not results_displayed and not current_cards:
        # Handle chip selection
        for i, color in enumerate(CHIP_COLORS):
            chip_center = (40 + i * 60, 620)
            chip_rect = pygame.Rect(chip_center[0] - CHIP_RADIUS, chip_center[1] - CHIP_RADIUS,
                                    2 * CHIP_RADIUS, 2 * CHIP_RADIUS)
            if chip_rect.collidepoint(pos):
                chip_value = CHIP_VALUES[i]
                if wallet_balance >= chip_value:
                    # Toggle chip selection
                    if active_chip and active_chip[0] == color:
                        active_chip = None
                    else:
                        active_chip = (color, chip_value)
                return

        # Handle betting with active chip
        if active_chip:
            for label, center in label_positions.items():
                label_rect = pygame.Rect(center[0] - 30, center[1] - 30, 60, 60)
                if label_rect.collidepoint(pos):
                    color, chip_value = active_chip
                    if wallet_balance >= chip_value:
                        wallet_balance -= chip_value
                        betting_chips.append((active_chip, center))
                    return

    if ui.undo_button.is_clicked(pos):
        # Only allow undo if we're not displaying results and no cards are shown
        if not results_displayed and not current_cards:
            for chip, _ in betting_chips:
                _, chip_value = chip
                wallet_balance += chip_value
            betting_chips.clear()
            placed_bets.clear()
    elif ui.history_button.is_clicked(pos):
        show_history(screen, history)
    elif ui.wallet_rect.collidepoint(pos):
        show_credits(screen)

def resolve_bets(cards, betting_chips, label_positions):
    winning_bets = []
    losing_bets = []
    total_winnings = 0
    
    card_values = {
        'Ace': 1,
        'Jester': 1,
        'King': 2,
        'Queen': 2,
        'Joker': 0
    }
    
    for chip, center in betting_chips:
        color, bet_value = chip
        is_winning_bet = False
        payout = 0
        
        if center == label_positions['Jester']:
            if cards[0].rank == 'Jester':
                is_winning_bet = True
                payout = bet_value * 2 + bet_value
        elif center == label_positions['Ace']:
            if cards[0].rank == 'Ace':
                is_winning_bet = True
                payout = bet_value * 2 + bet_value
        elif center == label_positions['Joker']:
            if cards[0].rank == 'Joker':
                is_winning_bet = True
                payout = bet_value * 4 + bet_value

        elif center == label_positions['King']:
            if cards[1].rank == 'King':
                is_winning_bet = True
                payout = bet_value * 2 + bet_value

        elif center == label_positions['Queen']:
            if cards[2].rank == 'Queen':
                is_winning_bet = True
                payout = bet_value * 2 + bet_value

        elif center == label_positions['Jester2']:
            if cards[3].rank == 'Jester':
                is_winning_bet = True
                payout = bet_value * 2 + bet_value
        elif center == label_positions['Ace2']:
            if cards[3].rank == 'Ace':
                is_winning_bet = True
                payout = bet_value * 2 + bet_value
        elif center == label_positions['Joker2']:
            if cards[3].rank == 'Joker':
                is_winning_bet = True
                payout = bet_value * 4 + bet_value

        elif center == label_positions['4T']:
            middle_card1_value = card_values.get(cards[1].rank, 0)
            middle_card2_value = card_values.get(cards[2].rank, 0)
            if middle_card1_value + middle_card2_value in [2, 4]:
                is_winning_bet = True
                payout = bet_value + bet_value

        elif center in [label_positions['Club'], label_positions['Heart'], 
                      label_positions['Spade'], label_positions['Diamond']]:
            if ((center == label_positions['Club'] and cards[1].suit == '♣') or
                (center == label_positions['Heart'] and cards[1].suit == '♥') or
                (center == label_positions['Spade'] and cards[1].suit == '♠') or
                (center == label_positions['Diamond'] and cards[1].suit == '♦')):
                is_winning_bet = True
                payout = bet_value * 3 + bet_value
                
        elif center in [label_positions['Club2'], label_positions['Heart2'], 
                      label_positions['Spade2'], label_positions['Diamond2']]:
            if ((center == label_positions['Club2'] and cards[2].suit == '♣') or
                (center == label_positions['Heart2'] and cards[2].suit == '♥') or
                (center == label_positions['Spade2'] and cards[2].suit == '♠') or
                (center == label_positions['Diamond2'] and cards[2].suit == '♦')):
                is_winning_bet = True
                payout = bet_value * 3 + bet_value
        
        if is_winning_bet:
            winning_bets.append((chip, center))
            total_winnings += payout
        else:
            losing_bets.append((chip, center))
    
    return winning_bets, losing_bets, total_winnings

def handle_bet_results(screen, winning_bets, losing_bets, current_cards):
    global current_winning_bets, current_losing_bets, results_displayed
    current_winning_bets = winning_bets
    current_losing_bets = losing_bets
    results_displayed = True

    screen.fill(WHITE)
    draw_board(screen)
    ui.draw_ui_elements(screen)
    
    for i, card in enumerate(current_cards):
        draw_card(screen, 135 + i * 150, 30, card, 180)
    
    for chip, center in current_losing_bets:
        pygame.draw.circle(screen, (255, 0, 0), center, CHIP_RADIUS + 2)
        pygame.draw.circle(screen, chip[0], center, CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
        chip_text = pygame.font.Font(None, 20).render(f"£{chip[1]}", True, BLACK)
        text_rect = chip_text.get_rect(center=center)
        screen.blit(chip_text, text_rect)
    
    for chip, center in current_winning_bets:
        pygame.draw.circle(screen, (0, 255, 0), center, CHIP_RADIUS + 2)
        pygame.draw.circle(screen, chip[0], center, CHIP_RADIUS)
        pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
        chip_text = pygame.font.Font(None, 20).render(f"£{chip[1]}", True, BLACK)
        text_rect = chip_text.get_rect(center=center)
        screen.blit(chip_text, text_rect)
    
    pygame.display.flip()

def main(surface=None, embedded=False, wallet=None):
    global betting_chips, drawn_cards, round_count, deck, placed_bets, history
    global current_cards, current_winning_bets, current_losing_bets, results_displayed
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

    label_positions = {
        'Ace': (175, 230),
        'Jester': (175, 330),
        'Joker': (175, 430),
        'King': (325, 230),
        'Queen': (475, 230),
        '4T': (400, 430),
        'Club': (287, 300),
        'Heart': (362, 300),
        'Spade': (287, 350),
        'Diamond': (362, 350),
        'Club2': (437, 300),
        'Heart2': (512, 300),
        'Spade2': (437, 350),
        'Diamond2': (512, 350),
        'Ace2': (625, 230),
        'Jester2': (625, 330),
        'Joker2': (625, 430),
    }

    try:
        while running:
            screen.fill(WHITE)
            draw_board(screen)
            ui.draw_ui_elements(screen)

            if results_displayed:
                for i, card in enumerate(current_cards):
                    draw_card(screen, 135 + i * 150, 30, card, 180)
                
                for chip, center in current_losing_bets:
                    pygame.draw.circle(screen, (255, 0, 0), center, CHIP_RADIUS + 2)
                    pygame.draw.circle(screen, chip[0], center, CHIP_RADIUS)
                    pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
                    chip_text = pygame.font.Font(None, 20).render(f"£{chip[1]}", True, BLACK)
                    text_rect = chip_text.get_rect(center=center)
                    screen.blit(chip_text, text_rect)
                
                for chip, center in current_winning_bets:
                    pygame.draw.circle(screen, (0, 255, 0), center, CHIP_RADIUS + 2)
                    pygame.draw.circle(screen, chip[0], center, CHIP_RADIUS)
                    pygame.draw.circle(screen, BLACK, center, CHIP_RADIUS, 3)
                    chip_text = pygame.font.Font(None, 20).render(f"£{chip[1]}", True, BLACK)
                    text_rect = chip_text.get_rect(center=center)
                    screen.blit(chip_text, text_rect)
            else:
                draw_betting_chips(screen)

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
                    handle_mouse_click(event.pos, label_positions)

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
    run_game_standalone(sys.modules[__name__], "LoL")