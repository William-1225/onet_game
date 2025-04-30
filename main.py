import pygame
import sys
import random
import os

pygame.init()
WIDTH, HEIGHT = 720, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Onet Game - Stacked Mode")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Segoe UI Emoji", 30)

BLACK = (0, 0, 0)
WARM_WHITE = (255, 255, 250)

emoji_dict = {
    "🍎": "apple",
    "🍌": "banana",
    "🍒": "cherries",
    "🍇": "grapes",
    "🍏": "green_apple",
    "🥝": "kiwifruit",
    "🍋": "lemon",
    "🍑": "peach",
    "🍐": "pear",
    "🍓": "strawberry",
    "🍉": "watermelon"
}

CARD_SIZE = 72
MAX_LAYERS = 3

class Card:
    def __init__(self, emoji, pos, layer):
        self.emoji = emoji
        self.base_pos = pos
        self.layer = layer
        self.rect = pygame.Rect(pos[0], pos[1], CARD_SIZE, CARD_SIZE)
        self.visible = True
        self.selected = False
        # Load the image based on the emoji
        if emoji in emoji_dict:
            image_name = emoji_dict[emoji]
            image_path = os.path.join("emoji_images", f"{image_name}.png")
            if os.path.exists(image_path):
                original_image = pygame.image.load(image_path).convert_alpha()  # Load the image with alpha channel
                # smoothscale
                self.image = pygame.transform.smoothscale(original_image, (CARD_SIZE * 4 // 5, CARD_SIZE * 4 // 5))
            else:
                raise FileNotFoundError(f"Image for emoji '{emoji}' not found in 'emoji_images' folder.")
        else:
            raise ValueError(f"Emoji '{emoji}' is not defined in emoji_dict.")

    def draw(self, surface):
        if not self.visible:
            return
        draw_rect = self.rect.copy()
        shadow_rect = draw_rect.move(4, 4)
        pygame.draw.rect(surface, (200, 200, 200), shadow_rect, border_radius=12)  # shadow
        pygame.draw.rect(surface, WARM_WHITE, draw_rect, border_radius=12)  # background
        pygame.draw.rect(surface, BLACK, draw_rect, width=2, border_radius=12)  # border
        # draw emoji
        image_rect = self.image.get_rect(center=draw_rect.center)
        surface.blit(self.image, image_rect)

    def is_fully_unblocked(self, cards):
        """Check if the card is not blocked by any card above it."""
        for other in cards:
            if other.visible and other != self and other.layer > self.layer:
                overlap_rect = self.rect.clip(other.rect)
                # If there is any overlap, the card is considered blocked
                if overlap_rect.width > 0 and overlap_rect.height > 0:
                    return False
        return True

def generate_cards(pair_count, layers):
    base_emojis = random.choices(list(emoji_dict.keys()), k=pair_count)
    emoji_pool = base_emojis * 2
    random.shuffle(emoji_pool)

    cards = []
    while emoji_pool:
        x = random.randint(50, WIDTH - CARD_SIZE - 50)
        y = random.randint(100, HEIGHT - CARD_SIZE - 50)
        layer = random.randint(0, layers - 1)
        new_rect = pygame.Rect(x, y, CARD_SIZE, CARD_SIZE)
        overlap = any(c.rect.colliderect(new_rect) and c.layer == layer for c in cards)
        if not overlap:
            cards.append(Card(emoji_pool.pop(), (x, y), layer))
    return cards

def draw_text(text, color, y_offset=0, align_left=True):
    rendered = font.render(text, True, color)
    if align_left:
        rect = rendered.get_rect(topleft=(150, HEIGHT // 2 + y_offset))
    else:
        rect = rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    screen.blit(rendered, rect)

def draw_ui(score, time_left):
    score_text = font.render(f"Score 🏆: {score}", True, BLACK)
    time_text = font.render(f"Time ⌚: {int(time_left)}s", True, BLACK)
    screen.blit(score_text, (10, 10))
    screen.blit(time_text, (10, 60))

def draw_menu():
    screen.fill(WARM_WHITE)
    draw_text("Welcome to Onet Game! 👀", BLACK, -60, False)
    draw_text("[1] - Level 1: Easy", BLACK, 0)
    draw_text("[2] - Level 2: Hard", BLACK, 60)
    draw_text("[Q] - Quit", BLACK, 120)
    pygame.display.update()

def draw_game_over(score, all_cleared, reason=None):
    """
    Draw the game over screen.
    :param score: The player's score.
    :param all_cleared: Whether all cards were cleared.
    :param reason: The reason for game over ("no_moves" or "time_up").
    """
    screen.fill(WARM_WHITE)
    if all_cleared:
        draw_text("Congratulations! 🎉", BLACK, -160, False)
    else:
        draw_text("Game Over! 🚀", BLACK, -160, False)
        if reason == "no_moves":
            draw_text("No more moves 😢, Better luck next time! ✨", BLACK, 180, False)
        elif reason == "time_up":
            draw_text("Time's up! ⏰, Better luck next time! ✨", BLACK, 180, False)
    draw_text(f"Score 🏆: {score}", BLACK, -60)
    draw_text("[R] - Restart", BLACK, 0)
    draw_text("[Q] - Quit", BLACK, 60)
    pygame.display.update()

def wait_for_restart():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return
                elif event.key == pygame.K_q:
                    pygame.quit(); sys.exit()

def get_all_unblocked(cards):
    return [c for c in cards if c.visible and c.is_fully_unblocked(cards)]

def has_valid_pair(unblocked):
    for i in range(len(unblocked)):
        for j in range(i+1, len(unblocked)):
            if unblocked[i].emoji == unblocked[j].emoji:
                if unblocked[i].layer == unblocked[j].layer:
                    return True
    return False

def update_card_layers(cards):
    # Ensure unblocked cards are moved to the top layer.
    for card in cards:
        if card.visible and card.is_fully_unblocked(cards):
            card.layer = MAX_LAYERS - 1  # Move to the top layer

def game_loop(pair_count):
    score = 0
    start_time = pygame.time.get_ticks()
    time_limit = 180  # 2 minutes
    cards = generate_cards(pair_count, MAX_LAYERS)
    selected = []

    running = True
    while running:
        screen.fill(WARM_WHITE)
        current_time = (pygame.time.get_ticks() - start_time) / 1000
        time_left = max(0, time_limit - current_time)

        # Update card layers to ensure unblocked cards are on top
        update_card_layers(cards)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = None
                for card in sorted(cards, key=lambda c: -c.layer):
                    if card.visible and card.rect.collidepoint(event.pos) and card.is_fully_unblocked(cards):
                        clicked = card
                        break
                if clicked:
                    if selected and selected[0] == clicked:
                        continue
                    selected.append(clicked)
                    clicked.selected = True
                    if len(selected) >= 2:
                        a, b = selected[0], selected[1]
                        # Ensure cards are on the same layer, both are unblocked, and overlap rules are respected
                        if (
                            a.emoji == b.emoji and
                            a.is_fully_unblocked(cards) and
                            b.is_fully_unblocked(cards) and
                            a.layer == b.layer  # Ensure they are on the same layer
                        ):
                            a.visible = b.visible = False
                            score += 10
                        selected.clear()

        for card in sorted(cards, key=lambda c: c.layer):
            card.draw(screen)

        draw_ui(score, time_left)
        pygame.display.flip()
        clock.tick(60)

        if all(not c.visible for c in cards):
            draw_game_over(score, True)
            wait_for_restart()
            return

        if time_left <= 0:
            draw_game_over(score, False, reason="time_up")
            wait_for_restart()
            return


        unblocked = get_all_unblocked(cards)
        if not has_valid_pair(unblocked):
            draw_game_over(score, False, reason="no_moves")
            wait_for_restart()
            return

def main():
    while True:
        draw_menu()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        game_loop(50)
                        waiting = False
                    elif event.key == pygame.K_2:
                        game_loop(100)
                        waiting = False
                    elif event.key == pygame.K_q:
                        pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()


