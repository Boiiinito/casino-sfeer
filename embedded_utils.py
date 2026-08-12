import os
import sys

import pygame

MENU_WIDTH = 1100
MENU_HEIGHT = 850
BACK_BUTTON_WIDTH = 120
BACK_BUTTON_HEIGHT = 36
BACK_BUTTON_MARGIN = 12

_back_font = None


def get_back_font():
    global _back_font
    if _back_font is None:
        _back_font = pygame.font.SysFont(None, 22, bold=True)
    return _back_font


def draw_back_button(screen):
    rect = pygame.Rect(
        BACK_BUTTON_MARGIN,
        BACK_BUTTON_MARGIN,
        BACK_BUTTON_WIDTH,
        BACK_BUTTON_HEIGHT,
    )
    pygame.draw.rect(screen, (255, 255, 255), rect)
    pygame.draw.rect(screen, (255, 0, 0), rect, 2)
    text = get_back_font().render("Menu", True, (255, 0, 0))
    text_rect = text.get_rect(center=rect.center)
    screen.blit(text, text_rect)
    return rect


def check_embedded_exit(event, embedded, back_rect):
    if not embedded:
        return None
    if event.type == pygame.QUIT:
        return "quit"
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "menu"
    if (
        event.type == pygame.MOUSEBUTTONDOWN
        and back_rect is not None
        and back_rect.collidepoint(event.pos)
    ):
        return "menu"
    return None


def cleanup_after_game():
    pygame.event.clear()
    for event_id in range(pygame.USEREVENT, pygame.NUMEVENTS):
        pygame.time.set_timer(event_id, 0)


def get_game_size(module):
    width = getattr(module, "SCREEN_WIDTH", getattr(module, "WINDOW_WIDTH", 800))
    height = getattr(module, "SCREEN_HEIGHT", getattr(module, "WINDOW_HEIGHT", 600))
    return width, height


def get_fitted_window_size():
    """Compute the outer window size used by the main menu: capped at
    MENU_WIDTH x MENU_HEIGHT but shrunk to fit the visible desktop area so
    the window is never taller/wider than the screen minus OS chrome
    (title bar, menu bar, dock/taskbar)."""
    try:
        desktop_sizes = pygame.display.get_desktop_sizes()
        screen_w, screen_h = desktop_sizes[0] if desktop_sizes else (MENU_WIDTH, MENU_HEIGHT)
    except Exception:
        screen_w, screen_h = MENU_WIDTH, MENU_HEIGHT

    vertical_chrome_reserve = 130
    horizontal_chrome_reserve = 40

    width = min(MENU_WIDTH, max(700, screen_w - horizontal_chrome_reserve))
    height = min(MENU_HEIGHT, max(600, screen_h - vertical_chrome_reserve))
    return width, height


def run_game_standalone(module, title):
    """Run a game module directly (e.g. `python LOL.py`) in its own window,
    sized and positioned exactly like the Casino Sfeer main menu window, with
    the game's native surface centered inside it.

    This mirrors how Casino_Sfeer_Menu.py embeds games: it creates an outer
    window fitted to the screen, draws the game onto its own smaller surface,
    and blits that surface centered in the outer window. A back button (which
    simply closes the window, since there is no menu to return to) is shown
    in the top-left corner.
    """
    pygame.init()

    width, height = get_fitted_window_size()

    try:
        desktop_sizes = pygame.display.get_desktop_sizes()
        screen_w, _ = desktop_sizes[0] if desktop_sizes else (width, height)
    except Exception:
        screen_w = width

    window_x = max(0, (screen_w - width) // 2)
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{window_x},0"

    window = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)

    game_width, game_height = get_game_size(module)
    game_surface = pygame.Surface((game_width, game_height))
    # Convert to the display's native pixel format. Without this,
    # smoothscale can subtly shift solid colors (e.g. pure white coming out
    # a shade darker), which showed up as a faint tinted "box" around
    # scaled-down games. Converting first keeps colors exact while still
    # getting smoothscale's anti-aliased (non-jagged) resizing.
    game_surface = game_surface.convert()

    # Reserve a band below the Quit button (top) and a small gap above the
    # bottom edge, then scale the game to fit within that band (only
    # shrinking if needed) and center it there. This keeps oversized games
    # (e.g. Wice's 1024x900 surface) from overlapping the Quit button or
    # touching the window edges.
    top_reserve = BACK_BUTTON_MARGIN + BACK_BUTTON_HEIGHT + 16
    bottom_reserve = 24
    available_height = max(1, height - top_reserve - bottom_reserve)

    scale = min(1.0, width / game_width, available_height / game_height)
    scaled_width = max(1, round(game_width * scale))
    scaled_height = max(1, round(game_height * scale))

    target_rect = pygame.Rect(
        (width - scaled_width) // 2,
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
        window.fill((255, 255, 255))
        if scale < 1.0:
            scaled_surface = pygame.transform.smoothscale(game_surface, (scaled_width, scaled_height))
            window.blit(scaled_surface, target_rect)
        else:
            window.blit(game_surface, target_rect)
        pygame.draw.rect(window, (255, 255, 255), back_button_rect)
        pygame.draw.rect(window, (255, 0, 0), back_button_rect, 2)
        text = get_back_font().render("Quit", True, (255, 0, 0))
        text_rect = text.get_rect(center=back_button_rect.center)
        window.blit(text, text_rect)

    def overlay_flip():
        draw_overlay()
        return original_flip()

    def overlay_update(*args):
        draw_overlay()
        return original_update(*args)

    def translated_mouse_pos():
        mouse_x, mouse_y = original_mouse_get_pos()
        rel_x = (mouse_x - target_rect.x) / scale
        rel_y = (mouse_y - target_rect.y) / scale
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
        from wallet import PlayerWallet

        module.main(surface=game_surface, embedded=True, wallet=PlayerWallet())
    finally:
        pygame.display.flip = original_flip
        pygame.display.update = original_update
        pygame.event.get = original_event_get
        pygame.mouse.get_pos = original_mouse_get_pos

    pygame.quit()
    sys.exit()
