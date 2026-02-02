import pygame
import random
import os

# --- Configuration ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
game_surf = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Ninja Ultimate - Final Fix")
clock = pygame.time.Clock()

# Couleurs
DARK_BLUE = (44, 62, 80)
YELLOW, RED, GREEN, WHITE = (241, 196, 15), (231, 76, 60), (46, 204, 113), (255, 255, 255)
GOLD, PURPLE, ICE_BLUE = (255, 215, 0), (155, 89, 182), (100, 200, 255)

def get_font(size):
    return pygame.font.SysFont(["impact", "arialblack", "arial"], size)

font_letter = get_font(35)
font_small = get_font(22)
font_huge = get_font(50)

# --- Dictionnaire ---
if os.path.exists("mots.txt"):
    with open("mots.txt", "r", encoding="utf-8") as f:
        DICTIONNAIRE = [line.strip().upper() for line in f if line.strip()]
else:
    DICTIONNAIRE = ["FRUIT", "PYTHON", "NINJA", "SABRE", "GOLDEN"]

# --- Images ---
IMAGES_LIST = {
    "abricot": "abricot.png", "ananas": "ananas.png", "banane": "banane.png",
    "bombe": "bombe.png", "cerise": "cerise.png", "citron": "citron.png", 
    "fraise": "fraise.png", "framboise": "framboise.png", "fruit_du_dragon": "fruit_du_dragon.png",
    "ice block": "glaçon.png", "kiwi": "kiwi.png", "mangue": "mangue.png",
    "melon": "melon.png", "myrtille": "myrtille.png", "noix_de_coco": "noix_de_coco.png",
    "orange": "orange.png", "pasteque": "pasteque.png", "peche": "peche.png",
    "poire": "poire.png", "pomme": "pomme.png", "raisin": "raisin.png",
    "spinner": "shuriken.png", "grimoire": "grimoire.png", 'eclair': 'eclair.png'
}

IMG_DATA = {}
for name, filename in IMAGES_LIST.items():
    try:
        img = pygame.image.load(filename).convert_alpha()
        IMG_DATA[name] = pygame.transform.scale(img, (60, 60))
    except:
        surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        c = PURPLE if name == "grimoire" else (ICE_BLUE if name == "ice block" else GREEN)
        pygame.draw.circle(surf, c, (30, 30), 25)
        IMG_DATA[name] = surf

# --- Classes ---
class Particle:
    def __init__(self, x, y, color=WHITE):
        self.x, self.y, self.color = x, y, color
        self.vx, self.vy, self.life = random.uniform(-5, 5), random.uniform(-5, 5), 255
    def update(self): self.x += self.vx; self.y += self.vy; self.life -= 15
    def draw(self, surf):
        if self.life > 0:
            p = pygame.Surface((5, 5), pygame.SRCALPHA); p.fill((*self.color, self.life)); surf.blit(p, (self.x, self.y))

class FruitSlice:
    def __init__(self, image, x, y, direction):
        w, h = image.get_size()
        self.image = pygame.Surface((w//2, h), pygame.SRCALPHA)
        self.image.blit(image, (0, 0), (0 if direction == "left" else w//2, 0, w//2, h))
        self.vx, self.x, self.y, self.vy, self.angle = (-7 if direction == "left" else 7), x, y, -10, 0
    def update(self): self.vy += 0.5; self.x += self.vx; self.y += self.vy; self.angle += 12
    def draw(self, surf):
        rot = pygame.transform.rotate(self.image, self.angle); surf.blit(rot, (self.x, self.y))

class GameObject:
    def __init__(self, speed_mult=1.0):
        self.is_enrobed = random.random() < 0.15 
        rand = random.random()
        if rand < 0.05: self.type = "grimoire"      
        elif rand < 0.10: self.type = "ice block"
        elif rand < 0.18: self.type = "spinner" 
        elif rand < 0.28: self.type = "bombe"   
        else: self.type = random.choice([k for k in IMG_DATA.keys() if k not in ["spinner", "bombe", "grimoire", "ice block"]])
        self.image_orig, self.letter = IMG_DATA[self.type], random.choice("abcdefghijklmnopqrstuvwxyz")
        self.x, self.y = random.randint(100, WIDTH - 100), HEIGHT + 20
        self.vy, self.vx = random.uniform(-14, -18) * speed_mult, random.uniform(-1.5, 1.5)
        self.angle, self.rot_speed, self.hp = 0, random.randint(-4, 4), (2 if self.is_enrobed else 1)
    def move(self, slow=False):
        f = 0.3 if slow else 1.0
        self.vy += 0.35 * f; self.y += self.vy * f; self.x += self.vx * f; self.angle += self.rot_speed * f
    def draw(self, surf):
        if self.is_enrobed and self.hp > 0: pygame.draw.circle(surf, GOLD, (int(self.x + 30), int(self.y + 30)), 42, 5)
        rotated = pygame.transform.rotate(self.image_orig, self.angle)
        rect = rotated.get_rect(center=(self.x + 30, self.y + 30)); surf.blit(rotated, rect.topleft)
        color = PURPLE if self.type == "grimoire" else (ICE_BLUE if self.type == "ice block" else YELLOW)
        txt = font_letter.render(self.letter.upper(), True, color); surf.blit(txt, (self.x + 15, self.y + 60))

def trigger_bonus_cut(color_p=WHITE):
    global score
    for o in active_objects[:]:
        if o.type != "bombe":
            slices.extend([FruitSlice(o.image_orig, o.x, o.y, "left"), FruitSlice(o.image_orig, o.x, o.y, "right")])
            score += 10
            for _ in range(3): particles.append(Particle(o.x+30, o.y+30, color_p))
            active_objects.remove(o)

# --- Variables Globales ---
game_mode = "MENU"
current_sub_mode, score, high_score, vies = "CLASSIC", 0, 0, 3
active_objects, slices, particles, slashes, found_words = [], [], [], [], []
speed_multiplier, shake_amount, flash_timer = 1.0, 0, 0
challenge_timer, is_frozen, is_iced, freeze_timer, ice_timer, input_text = 3600, False, False, 0, 0, ""

SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 900)

def reset_game(mode):
    global game_mode, current_sub_mode, score, vies, speed_multiplier, challenge_timer, active_objects, slices, particles, found_words, is_frozen, is_iced, slashes, flash_timer
    game_mode, current_sub_mode = "PLAY", mode
    score, vies, speed_multiplier, challenge_timer, flash_timer = 0, 3, 1.0, 3600, 0
    is_frozen = is_iced = False
    active_objects, slices, particles, found_words, slashes = [], [], [], [], []

# --- Boucle ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(DARK_BLUE)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_mode == "MENU":
                if WIDTH//2-150 < mouse_pos[0] < WIDTH//2+150:
                    if 280 < mouse_pos[1] < 340: reset_game("CLASSIC")
                    elif 370 < mouse_pos[1] < 430: reset_game("CHALLENGE")
            elif game_mode == "PAUSE":
                if pygame.Rect(WIDTH//2-150, 300, 300, 60).collidepoint(mouse_pos): game_mode = "PLAY"
                elif pygame.Rect(WIDTH//2-150, 380, 300, 60).collidepoint(mouse_pos): game_mode = "MENU"
            elif game_mode == "GAMEOVER":
                if pygame.Rect(WIDTH//2-150, 320, 300, 60).collidepoint(mouse_pos): reset_game(current_sub_mode)
                elif pygame.Rect(WIDTH//2-150, 410, 300, 60).collidepoint(mouse_pos): game_mode = "MENU"

        if event.type == pygame.KEYDOWN and game_mode == "PLAY":
            if event.key == pygame.K_ESCAPE: game_mode = "PAUSE"
            elif is_frozen:
                if event.key == pygame.K_RETURN:
                    mot = input_text.upper().strip()
                    if mot in DICTIONNAIRE and mot not in found_words: 
                        found_words.append(mot); score += 50
                    input_text = ""
                elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                else:
                    if event.unicode.isalpha() and len(input_text) < 12: input_text += event.unicode
            else:
                key = pygame.key.name(event.key).lower()
                for obj in active_objects[:]:
                    if obj.letter == key:
                        obj.hp -= 1
                        if obj.hp <= 0:
                            if obj.is_enrobed:
                                flash_timer, shake_amount, score = 10, 25, score + 50
                                trigger_bonus_cut(GOLD)
                            elif obj.type == "spinner":
                                y_pos = obj.y + 30
                                slashes.append({"start": (0, y_pos), "end": (WIDTH, y_pos), "life": 255})
                                trigger_bonus_cut(WHITE)
                            elif obj.type == "grimoire": 
                                is_frozen, freeze_timer, input_text, found_words = True, 600, "", []
                            elif obj.type == "ice block": 
                                is_iced, ice_timer = True, 400
                            elif obj.type == "bombe":
                                if current_sub_mode == "CLASSIC": vies -= 1
                                else: score = max(0, score - 50)
                                shake_amount = 30
                            else:
                                score += 10
                                slices.extend([FruitSlice(obj.image_orig, obj.x, obj.y, "left"), FruitSlice(obj.image_orig, obj.x, obj.y, "right")])
                                for _ in range(4): particles.append(Particle(obj.x+30, obj.y+30))
                            
                            if obj in active_objects: active_objects.remove(obj)
                            speed_multiplier = 1.0 + (score // 700) * 0.1
                        break

        if event.type == SPAWN_EVENT and game_mode == "PLAY" and not is_frozen:
            active_objects.append(GameObject(speed_multiplier))

    # --- Rendu Jeu ---
    if game_mode in ["PLAY", "PAUSE"]:
        if game_mode == "PLAY":
            game_surf.fill(DARK_BLUE)
            if is_frozen: freeze_timer -= 1; is_frozen = (freeze_timer > 0)
            else:
                if is_iced: ice_timer -= 1; is_iced = (ice_timer > 0)
                if current_sub_mode == "CHALLENGE":
                    challenge_timer -= 1
                    if challenge_timer <= 0: game_mode = "GAMEOVER"

            for p in particles[:]: p.update(); p.draw(game_surf); (particles.remove(p) if p.life <= 0 else None)
            for s in slices[:]: s.update(); s.draw(game_surf); (slices.remove(s) if s.y > HEIGHT + 100 else None)
            for obj in active_objects[:]:
                if not is_frozen: obj.move(slow=is_iced)
                obj.draw(game_surf)
                if obj.y > HEIGHT + 100:
                    if not is_iced and obj.type not in ["bombe", "grimoire", "ice block"] and current_sub_mode == "CLASSIC": vies -= 1
                    active_objects.remove(obj)
            
            for sl in slashes[:]:
                pygame.draw.line(game_surf, WHITE, sl["start"], sl["end"], 15)
                sl["life"] -= 50; (slashes.remove(sl) if sl["life"] <= 0 else None)

            off = [random.randint(-shake_amount, shake_amount), random.randint(-shake_amount, shake_amount)] if shake_amount > 0 else [0,0]
            shake_amount = max(0, shake_amount - 1); screen.blit(game_surf, off)

            if flash_timer > 0:
                f_surf = pygame.Surface((WIDTH, HEIGHT)); f_surf.fill(GOLD); f_surf.set_alpha(flash_timer * 20)
                screen.blit(f_surf, (0,0)); flash_timer -= 1
            
            # --- EFFET GEL GLAÇON ---
            if is_iced and not is_frozen:
                ice_ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ice_ov.fill((100, 200, 255, 80))
                screen.blit(ice_ov, (0,0))

            # --- EFFET GEL grimoire ---
            if is_frozen:
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0, 0, 0, 220)); screen.blit(ov, (0,0))
                screen.blit(font_huge.render(f"grimoire: {max(0, freeze_timer//60+1)}s", True, GOLD), (WIDTH//2-110, 80))
                pygame.draw.rect(screen, PURPLE, (WIDTH//2-200, HEIGHT//2-30, 400, 60), 2, border_radius=15)
                screen.blit(font_huge.render(input_text.upper(), True, WHITE), (WIDTH//2-180, HEIGHT//2-22))
                y_off = HEIGHT//2 + 60
                screen.blit(font_small.render("MOTS VALIDES :", True, GREEN), (WIDTH//2-70, y_off))
                for i, m in enumerate(found_words[-5:]):
                    screen.blit(font_small.render(m, True, WHITE), (WIDTH//2-30, y_off + 30 + i*25))

            screen.blit(font_small.render(f"SCORE: {score} | " + (f"VIES: {vies}" if current_sub_mode=="CLASSIC" else f"TPS: {challenge_timer//60}s"), True, WHITE), (20, 20))
            if current_sub_mode == "CLASSIC" and vies <= 0: game_mode = "GAMEOVER"

        if game_mode == "PAUSE":
            screen.blit(game_surf, (0,0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0,0))
            txt_p = font_huge.render("PAUSE", True, YELLOW)
            screen.blit(txt_p, txt_p.get_rect(center=(WIDTH//2, 200)))
            for i, text in enumerate(["REPRENDRE", "MENU"]):
                rect = pygame.Rect(WIDTH//2-150, 300+i*80, 300, 60)
                col = YELLOW if rect.collidepoint(mouse_pos) else WHITE
                pygame.draw.rect(screen, col, rect, 2, border_radius=10)
                btn = font_small.render(text, True, col)
                screen.blit(btn, btn.get_rect(center=rect.center))

    elif game_mode == "GAMEOVER":
        txt_gv = font_huge.render("PARTIE TERMINEE", True, RED)
        screen.blit(txt_gv, txt_gv.get_rect(center=(WIDTH//2, 120)))
        for i, text in enumerate(["RECOMMENCER", "MENU"]):
            rect = pygame.Rect(WIDTH//2-150, 320+i*90, 300, 60)
            col = YELLOW if rect.collidepoint(mouse_pos) else WHITE
            pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            btn = font_small.render(text, True, col); screen.blit(btn, btn.get_rect(center=rect.center))
    
    else: # MENU
        txt_title = font_huge.render("FRUIT NINJA ULTIMATE", True, WHITE)
        screen.blit(txt_title, txt_title.get_rect(center=(WIDTH//2, 150)))
        for i, text in enumerate(["CLASSIQUE", "CHALLENGE"]):
            rect = pygame.Rect(WIDTH//2-150, 280+i*90, 300, 60)
            col = (GREEN if i==0 else RED) if rect.collidepoint(mouse_pos) else WHITE
            pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            btn = font_huge.render(text, True, col); screen.blit(btn, btn.get_rect(center=rect.center))

    pygame.display.flip(); clock.tick(60)
pygame.quit()