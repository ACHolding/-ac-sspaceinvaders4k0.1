import pygame
import sys
import random
import array

# --- Game Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
CYAN = (50, 255, 255)
YELLOW = (255, 255, 50)

# Game States
MENU = 0
PLAYING = 1
GAME_OVER = 2
VICTORY = 3

# --- Audio Generation (No external files) ---
def generate_sound(freq, duration, vol=0.1, wave_type='square'):
    """Generates simple retro sound waves in memory."""
    try:
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h') # Signed 16-bit integer array
        
        if freq == 0:
            for _ in range(n_samples):
                buf.append(0)
        else:
            period = sample_rate / freq
            for i in range(n_samples):
                if wave_type == 'square':
                    # Square wave for harsh retro beeps
                    if (i // (period / 2)) % 2 == 0:
                        buf.append(int(32767 * vol))
                    else:
                        buf.append(int(-32767 * vol))
                elif wave_type == 'noise':
                    # White noise for explosions
                    buf.append(int(random.uniform(-32767, 32767) * vol))
                    
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        # Fallback if audio device has issues
        class DummySound:
            def play(self): pass
        return DummySound()

# --- Atari-Style Pixel Art ---
# 1 means a block, 0 means empty space
ALIEN_SPRITES = [
    [ # Squid (Top row)
        "  1111  ",
        " 111111 ",
        "11 11 11",
        "11111111",
        "  1  1  ",
        " 1 11 1 ",
        "1      1"
    ],
    [ # Crab (Middle rows)
        "  1   1  ",
        "   1 1   ",
        " 1111111 ",
        "11 111 11",
        "111111111",
        " 11   11 ",
        "1       1"
    ],
    [ # Octopus (Bottom rows)
        "   11   ",
        "  1111  ",
        " 111111 ",
        "11 11 11",
        "11111111",
        " 1 11 1 ",
        "1 1  1 1"
    ]
]

class Player:
    def __init__(self):
        self.width = 50
        self.height = 20
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 50
        self.color = GREEN
        self.cooldown = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self):
        # MOUSE CONTROL: Follow the mouse X position
        mouse_x, _ = pygame.mouse.get_pos()
        self.x = mouse_x - self.width // 2
        
        # Keep inside screen
        if self.x < 0: self.x = 0
        if self.x > WIDTH - self.width: self.x = WIDTH - self.width
            
        self.rect.x = self.x
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, surface):
        # Draw retro tank shape
        pygame.draw.rect(surface, self.color, (self.x, self.y + 10, self.width, 10))
        pygame.draw.rect(surface, self.color, (self.x + 20, self.y, 10, 10))
        pygame.draw.rect(surface, self.color, (self.x + 23, self.y - 5, 4, 5))

class Alien:
    def __init__(self, x, y, alien_type):
        self.x = x
        self.y = y
        self.type = alien_type
        self.pixel_size = 4
        self.sprite = ALIEN_SPRITES[alien_type]
        self.width = len(self.sprite[0]) * self.pixel_size
        self.height = len(self.sprite) * self.pixel_size
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        if alien_type == 0: self.color = CYAN
        elif alien_type == 1: self.color = YELLOW
        else: self.color = WHITE

    def draw(self, surface):
        for row_idx, row in enumerate(self.sprite):
            for col_idx, char in enumerate(row):
                if char == '1':
                    px = self.x + col_idx * self.pixel_size
                    py = self.y + row_idx * self.pixel_size
                    pygame.draw.rect(surface, self.color, (px, py, self.pixel_size, self.pixel_size))

    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y

class Laser:
    def __init__(self, x, y, speed, color):
        self.rect = pygame.Rect(x, y, 4, 15)
        self.speed = speed
        self.color = color

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class Bunker:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pixel_size = 5
        self.blocks = []
        # Create an arch-shaped bunker
        shape = [
            "  #######  ",
            " ######### ",
            "###########",
            "###     ###",
            "###     ###"
        ]
        for row_idx, row in enumerate(shape):
            for col_idx, char in enumerate(row):
                if char == '#':
                    bx = self.x + col_idx * self.pixel_size
                    by = self.y + row_idx * self.pixel_size
                    self.blocks.append(pygame.Rect(bx, by, self.pixel_size, self.pixel_size))

    def draw(self, surface):
        for block in self.blocks:
            pygame.draw.rect(surface, GREEN, block)

class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ac's space invader")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("Courier", 64, bold=True)
        self.font_small = pygame.font.SysFont("Courier", 24)
        
        # Hide mouse cursor for immersion
        pygame.mouse.set_visible(False)
        
        # Generate Sounds
        self.snd_shoot = generate_sound(880, 0.1, 0.1) # High pitched beep
        self.snd_hit = generate_sound(150, 0.15, 0.1, wave_type='noise') # Explosion noise
        self.snd_move = generate_sound(60, 0.05, 0.1) # Low thud
        self.snd_gameover = generate_sound(200, 0.8, 0.2, wave_type='noise')
        
        self.state = MENU
        self.score = 0
        self.reset_game()

    def reset_game(self):
        self.player = Player()
        self.lasers = []
        self.alien_lasers = []
        self.bunkers = [Bunker(100 + i * 200, HEIGHT - 150) for i in range(4)]
        self.score = 0
        self.init_aliens()

    def init_aliens(self):
        self.aliens = []
        self.alien_dir = 1
        self.alien_speed = 2
        self.alien_move_timer = 0
        self.alien_move_delay = 30 # Frames between alien group movements
        
        for row in range(5):
            for col in range(11):
                alien_type = 0 if row == 0 else (1 if row in (1, 2) else 2)
                x = 100 + col * 50
                y = 80 + row * 40
                self.aliens.append(Alien(x, y, alien_type))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == MENU:
                    self.state = PLAYING
                elif self.state in (GAME_OVER, VICTORY):
                    self.reset_game()
                    self.state = MENU
                elif self.state == PLAYING:
                    # Shoot!
                    if self.player.cooldown == 0:
                        self.lasers.append(Laser(self.player.rect.centerx - 2, self.player.rect.y, -10, GREEN))
                        self.player.cooldown = 20
                        self.snd_shoot.play()

    def update(self):
        if self.state != PLAYING:
            return

        self.player.update()

        # Move Player Lasers
        for laser in self.lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                self.lasers.remove(laser)
                continue
                
            # Check Alien Hit
            hit = False
            for alien in self.aliens[:]:
                if laser.rect.colliderect(alien.rect):
                    self.aliens.remove(alien)
                    hit = True
                    self.score += (30 if alien.type == 0 else (20 if alien.type == 1 else 10))
                    self.snd_hit.play()
                    break
            if hit:
                self.lasers.remove(laser)
                continue
                
            # Check Bunker Hit
            for bunker in self.bunkers:
                for block in bunker.blocks[:]:
                    if laser.rect.colliderect(block):
                        bunker.blocks.remove(block)
                        if laser in self.lasers: self.lasers.remove(laser)
                        break

        # Alien logic
        self.alien_move_timer += 1
        if self.alien_move_timer >= self.alien_move_delay:
            self.alien_move_timer = 0
            self.snd_move.play()
            move_down = False
            
            # Speed up as they dwindle
            self.alien_move_delay = max(5, int(len(self.aliens) * 0.6))
            
            # Check edges
            for alien in self.aliens:
                if alien.x <= 20 and self.alien_dir == -1:
                    move_down = True
                    break
                if alien.x + alien.width >= WIDTH - 20 and self.alien_dir == 1:
                    move_down = True
                    break
                    
            if move_down:
                self.alien_dir *= -1
                for alien in self.aliens:
                    alien.y += 20
                    alien.update_rect()
                    # Game Over if aliens reach player
                    if alien.y + alien.height >= self.player.y:
                        self.snd_gameover.play()
                        self.state = GAME_OVER
            else:
                for alien in self.aliens:
                    alien.x += 15 * self.alien_dir
                    alien.update_rect()

        # Alien Shooting
        if self.aliens and random.randint(1, 60) == 1:
            shooter = random.choice(self.aliens)
            self.alien_lasers.append(Laser(shooter.rect.centerx, shooter.rect.bottom, 5, RED))

        # Move Alien Lasers
        for laser in self.alien_lasers[:]:
            laser.update()
            if laser.rect.top > HEIGHT:
                self.alien_lasers.remove(laser)
                continue
                
            # Hit Player
            if laser.rect.colliderect(self.player.rect):
                self.snd_gameover.play()
                self.state = GAME_OVER
                
            # Hit Bunker
            for bunker in self.bunkers:
                for block in bunker.blocks[:]:
                    if laser.rect.colliderect(block):
                        bunker.blocks.remove(block)
                        if laser in self.alien_lasers: self.alien_lasers.remove(laser)
                        break

        # Win Condition
        if not self.aliens:
            self.state = VICTORY

    def draw_text(self, text, font, color, surface, x, y, center=False):
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        surface.blit(text_obj, text_rect)

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == MENU:
            self.draw_text("ac's space invader", self.font_large, GREEN, self.screen, WIDTH//2, HEIGHT//3, center=True)
            self.draw_text("USE MOUSE TO MOVE. CLICK TO SHOOT.", self.font_small, WHITE, self.screen, WIDTH//2, HEIGHT//2, center=True)
            self.draw_text("CLICK ANYWHERE TO START", self.font_small, YELLOW, self.screen, WIDTH//2, HEIGHT//1.5, center=True)
            
        elif self.state == PLAYING:
            self.player.draw(self.screen)
            for alien in self.aliens:
                alien.draw(self.screen)
            for bunker in self.bunkers:
                bunker.draw(self.screen)
            for laser in self.lasers:
                laser.draw(self.screen)
            for laser in self.alien_lasers:
                laser.draw(self.screen)
                
            # Score
            self.draw_text(f"SCORE: {self.score}", self.font_small, WHITE, self.screen, 20, 20)
            
        elif self.state == GAME_OVER:
            self.draw_text("GAME OVER", self.font_large, RED, self.screen, WIDTH//2, HEIGHT//3, center=True)
            self.draw_text(f"FINAL SCORE: {self.score}", self.font_small, WHITE, self.screen, WIDTH//2, HEIGHT//2, center=True)
            self.draw_text("CLICK TO RETURN TO MENU", self.font_small, YELLOW, self.screen, WIDTH//2, HEIGHT//1.5, center=True)
            
        elif self.state == VICTORY:
            self.draw_text("YOU SAVED EARTH!", self.font_large, CYAN, self.screen, WIDTH//2, HEIGHT//3, center=True)
            self.draw_text(f"FINAL SCORE: {self.score}", self.font_small, WHITE, self.screen, WIDTH//2, HEIGHT//2, center=True)
            self.draw_text("CLICK TO RETURN TO MENU", self.font_small, YELLOW, self.screen, WIDTH//2, HEIGHT//1.5, center=True)

        # Draw a custom crosshair where the mouse is
        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(self.screen, RED, (mx - 10, my), (mx + 10, my), 2)
        pygame.draw.line(self.screen, RED, (mx, my - 10), (mx, my + 10), 2)

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()