import pygame
import random
import time

# --- Initialization ---
pygame.init()

# --- Screen Dimensions ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cosmic Looter")

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (217, 30, 24)
GREEN = (34, 139, 34)
BLUE = (65, 105, 225)
YELLOW = (255, 223, 0)
GRAY = (40, 40, 40)
LIGHT_GRAY = (100, 100, 100)

# --- Fonts ---
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 36)
font_large = pygame.font.Font(None, 64)

# --- Game State ---
class GameState:
    PLAYER_TURN = 1
    ENEMY_TURN = 2
    GAME_OVER = 3
    VICTORY = 4

# --- Card Class ---
class Card:
    def __init__(self, name, cost, effect, description):
        self.name = name
        self.cost = cost
        self.effect = effect
        self.description = description

    def play(self, player, enemy):
        """Applies the card's effect."""
        self.effect(player, enemy)

# --- Card Effects (as functions) ---
def attack_10(player, enemy):
    damage = 10
    enemy.take_damage(damage)
    player.status_text = f"Dealt {damage} damage!"

def attack_20(player, enemy):
    damage = 20
    enemy.take_damage(damage)
    player.status_text = f"Dealt {damage} damage with a Heavy Blast!"

def shield_10(player, enemy):
    shield_gain = 10
    player.gain_shield(shield_gain)
    player.status_text = f"Gained {shield_gain} shield."
    
def shield_5_draw_1(player, enemy):
    shield_gain = 5
    player.gain_shield(shield_gain)
    player.draw_cards(1)
    player.status_text = f"Gained {shield_gain} shield and drew 1 card."

# --- Card Definitions ---
ALL_CARDS = {
    "Laser Shot": Card("Laser Shot", 1, attack_10, "Deal 10 damage."),
    "Heavy Blast": Card("Heavy Blast", 2, attack_20, "Deal 20 damage."),
    "Deflectors": Card("Deflectors", 1, shield_10, "Gain 10 shield."),
    "Evasive Maneuver": Card("Evasive Maneuver", 1, shield_5_draw_1, "Gain 5 shield. Draw 1 card."),
}

# --- Ship Class (Player and Enemy) ---
class Ship:
    def __init__(self, name, x, y, hp, color):
        self.name = name
        self.rect = pygame.Rect(x, y, 100, 150)
        self.max_hp = hp
        self.hp = hp
        self.shield = 0
        self.color = color
        self.status_text = ""

    def take_damage(self, amount):
        if self.shield > 0:
            shield_damage = min(self.shield, amount)
            self.shield -= shield_damage
            amount -= shield_damage
        
        if amount > 0:
            self.hp -= amount
            if self.hp < 0:
                self.hp = 0

    def gain_shield(self, amount):
        self.shield += amount

    def draw(self, surface):
        # Draw ship body
        pygame.draw.rect(surface, self.color, self.rect)
        # Draw HP bar
        hp_bar_bg = pygame.Rect(self.rect.x, self.rect.y - 30, self.rect.width, 20)
        pygame.draw.rect(surface, RED, hp_bar_bg)
        hp_ratio = self.hp / self.max_hp
        hp_bar_fg = pygame.Rect(self.rect.x, self.rect.y - 30, self.rect.width * hp_ratio, 20)
        pygame.draw.rect(surface, GREEN, hp_bar_fg)
        
        # Draw HP/Shield text
        stats_text = font_small.render(f"{self.hp}/{self.max_hp} HP | {self.shield} Shield", True, WHITE)
        surface.blit(stats_text, (self.rect.centerx - stats_text.get_width() // 2, self.rect.y - 55))

# --- Player Class ---
class Player(Ship):
    def __init__(self, x, y):
        super().__init__("Player", x, y, 100, BLUE)
        self.deck = []
        self.hand = []
        self.discard = []
        self.max_energy = 3
        self.energy = 3
        self.build_starter_deck()
        self.shuffle_deck()
    
    def build_starter_deck(self):
        self.deck = [ALL_CARDS["Laser Shot"]] * 6 + [ALL_CARDS["Deflectors"]] * 4
    
    def shuffle_deck(self):
        random.shuffle(self.deck)

    def draw_cards(self, num):
        for _ in range(num):
            if not self.deck:
                if not self.discard:
                    return # No cards left anywhere
                self.deck = self.discard
                self.discard = []
                self.shuffle_deck()
            self.hand.append(self.deck.pop())
            
    def start_turn(self):
        self.energy = self.max_energy
        self.shield = 0 # Shields decay each turn
        self.draw_cards(5)
        self.status_text = "Your turn!"

    def end_turn(self):
        self.discard.extend(self.hand)
        self.hand = []
        return GameState.ENEMY_TURN

# --- Enemy Class ---
class Enemy(Ship):
    def __init__(self, x, y):
        super().__init__("Enemy Raider", x, y, 80, RED)
        self.actions = [
            {"name": "Attack", "damage": 12},
            {"name": "Defend", "shield": 8}
        ]
        self.next_action = None

    def choose_action(self):
        self.next_action = random.choice(self.actions)

    def take_turn(self, player):
        if self.next_action["name"] == "Attack":
            player.take_damage(self.next_action["damage"])
            self.status_text = f"Attacked for {self.next_action['damage']}!"
        elif self.next_action["name"] == "Defend":
            self.gain_shield(self.next_action["shield"])
            self.status_text = f"Gained {self.next_action['shield']} shield."
        
        self.choose_action() # Choose next turn's action
        return GameState.PLAYER_TURN
        
# --- Main Game Object ---
class Game:
    def __init__(self):
        self.player = Player(200, 300)
        self.enemy = Enemy(SCREEN_WIDTH - 300, 300)
        self.game_state = GameState.PLAYER_TURN
        self.card_rects = []
        self.end_turn_button = pygame.Rect(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 70, 180, 50)
        self.player.start_turn()
        self.enemy.choose_action()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.update()
            self.draw()
            pygame.display.flip()
            
            # Brief pause for enemy turn
            if self.game_state == GameState.ENEMY_TURN:
                time.sleep(1.5)
                self.game_state = self.enemy.take_turn(self.player)
                self.player.start_turn()

        pygame.quit()

    def handle_click(self, pos):
        if self.game_state != GameState.PLAYER_TURN:
            return

        # Check for card clicks
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(pos):
                card = self.player.hand[i]
                if self.player.energy >= card.cost:
                    self.player.energy -= card.cost
                    card.play(self.player, self.enemy)
                    self.player.discard.append(self.player.hand.pop(i))
                    return

        # Check for end turn button click
        if self.end_turn_button.collidepoint(pos):
            self.game_state = self.player.end_turn()

    def update(self):
        if self.enemy.hp <= 0 and self.game_state != GameState.VICTORY:
            self.game_state = GameState.VICTORY
        if self.player.hp <= 0 and self.game_state != GameState.GAME_OVER:
            self.game_state = GameState.GAME_OVER

    def draw_hand(self):
        self.card_rects = []
        hand_size = len(self.player.hand)
        card_width, card_height = 140, 200
        start_x = (SCREEN_WIDTH - (hand_size * (card_width + 10))) / 2
        for i, card in enumerate(self.player.hand):
            card_x = start_x + i * (card_width + 10)
            card_y = SCREEN_HEIGHT - card_height - 20
            rect = pygame.Rect(card_x, card_y, card_width, card_height)
            self.card_rects.append(rect)

            # Draw card background
            pygame.draw.rect(screen, LIGHT_GRAY, rect, border_radius=10)
            if rect.collidepoint(pygame.mouse.get_pos()):
                 pygame.draw.rect(screen, YELLOW, rect, 2, border_radius=10)


            # Draw card text
            name_text = font_medium.render(card.name, True, BLACK)
            cost_text = font_large.render(str(card.cost), True, BLUE)
            desc_text = font_small.render(card.description, True, BLACK)

            screen.blit(name_text, (rect.x + 10, rect.y + 10))
            screen.blit(cost_text, (rect.x + 10, rect.y + 40))
            screen.blit(desc_text, (rect.x + 10, rect.y + 150))
    
    def draw_ui(self):
        # Draw Player energy
        energy_text = font_medium.render(f"Energy: {self.player.energy}/{self.player.max_energy}", True, WHITE)
        screen.blit(energy_text, (20, SCREEN_HEIGHT - 60))

        # Draw Deck/Discard counts
        deck_text = font_small.render(f"Deck: {len(self.player.deck)}", True, WHITE)
        discard_text = font_small.render(f"Discard: {len(self.player.discard)}", True, WHITE)
        screen.blit(deck_text, (20, SCREEN_HEIGHT - 120))
        screen.blit(discard_text, (20, SCREEN_HEIGHT - 90))

        # Draw End Turn button
        pygame.draw.rect(screen, LIGHT_GRAY, self.end_turn_button, border_radius=8)
        end_turn_text = font_medium.render("End Turn", True, BLACK)
        text_rect = end_turn_text.get_rect(center=self.end_turn_button.center)
        screen.blit(end_turn_text, text_rect)
        
        # Draw status text
        p_status = font_medium.render(self.player.status_text, True, YELLOW)
        e_status = font_medium.render(self.enemy.status_text, True, YELLOW)
        screen.blit(p_status, (self.player.rect.centerx - p_status.get_width() // 2, self.player.rect.bottom + 20))
        screen.blit(e_status, (self.enemy.rect.centerx - e_status.get_width() // 2, self.enemy.rect.bottom + 20))

        # Draw Enemy's next action
        if self.enemy.next_action:
            action_text = f"Next: {self.enemy.next_action['name']}"
            if "damage" in self.enemy.next_action:
                action_text += f" ({self.enemy.next_action['damage']})"
            intent_render = font_medium.render(action_text, True, YELLOW)
            screen.blit(intent_render, (self.enemy.rect.centerx - intent_render.get_width() // 2, self.enemy.rect.top - 80))


    def draw(self):
        screen.fill(GRAY)
        self.player.draw(screen)
        self.enemy.draw(screen)
        self.draw_ui()
        self.draw_hand()
        
        if self.game_state == GameState.GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            text = font_large.render("DEFEAT", True, RED)
            screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/2 - text.get_height()/2))
            
        if self.game_state == GameState.VICTORY:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            text = font_large.render("VICTORY!", True, GREEN)
            screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, SCREEN_HEIGHT/2 - text.get_height()/2))

        pygame.display.flip()

# --- Run Game ---
if __name__ == "__main__":
    game = Game()
    game.run()
