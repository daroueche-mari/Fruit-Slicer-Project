import pygame
import random
from settings import *
from assets import font_letter

# --- Classes ---
class LightningEffect:
    """ Gère les éclairs visuels pendant la surcharge """
    def __init__(self):
        self.points = []
        self.life = 10
        curr_pos = [random.randint(0, WIDTH), 0]
        self.points.append(curr_pos)
        while curr_pos[1] < HEIGHT:
            curr_pos = [
                curr_pos[0] + random.randint(-50, 50),
                curr_pos[1] + random.randint(20, 80),
            ]
            self.points.append(curr_pos)

    def draw(self, surf):
        if self.life > 0:
            pygame.draw.lines(surf, WHITE, False, self.points, 3)
            pygame.draw.lines(surf, ICE_BLUE, False, self.points, 1)
            self.life -= 1


class Particle:
    """ Particules d'explosion lors de la découpe """
    def __init__(self, x, y, color=WHITE):
        self.x, self.y, self.color = x, y, color
        self.vx, self.vy, self.life = random.uniform(-5, 5), random.uniform(-5, 5), 255

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 15

    def draw(self, surf):
        if self.life > 0:
            p = pygame.Surface((5, 5), pygame.SRCALPHA)
            p.fill((*self.color, self.life))
            surf.blit(p, (self.x, self.y))


class FruitSlice:
    """ Moitiés de fruits après découpe """
    def __init__(self, image, x, y, side):
        w, h = image.get_size()
        self.image = pygame.Surface((w // 2, h), pygame.SRCALPHA)
        self.image.blit(image, (0, 0), (0 if side == "left" else w // 2, 0, w // 2, h))
        self.vx = -7 if side == "left" else 7
        self.x, self.y, self.vy, self.angle = x, y, -10, 0

    def update(self):
        self.vy += 0.5
        self.x += self.vx
        self.y += self.vy
        self.angle += 12

    def draw(self, surf):
        rot = pygame.transform.rotate(self.image, self.angle)
        surf.blit(rot, (self.x, self.y))


class GameObject:
    """ Fruits, bombes et bonus """
    def __init__(self, image_data, is_overcharged, speed_mult=1.0):
        # Halo doré
        self.is_enrobed = (random.random() < 0.15) if not is_overcharged else False

        # Sélection du type d'objet
        if is_overcharged:
            self.type = random.choice([k for k in image_data.keys() if k not in ["bomb", "shuriken", "ice_block", "lightning"]])
        else:
            rand = random.random()
            if rand < 0.05: self.type = "ice_block"
            elif rand < 0.10: self.type = "lightning"
            elif rand < 0.18: self.type = "shuriken"
            elif rand < 0.28: self.type = "bomb"
            else:
                self.type = random.choice([k for k in image_data.keys() if k not in ["shuriken", "bomb", "ice_block", "lightning"]])
        
        self.image_orig = image_data[self.type]
        self.is_bonus = self.type in ["bomb", "ice_block", "lightning", "shuriken"]

        # Attribution des touches et positions (Bonus à gauche, Fruits à droite)
        if self.is_bonus:
            self.letter = random.choice("awsd")
            self.color_label = RED
            self.x = random.randint(50, WIDTH // 2 - 50)
        else:
            self.letter = random.choice("jkl")
            self.color_label = GREEN
            self.x = random.randint(WIDTH // 2 + 50, WIDTH - 100)

        self.y = HEIGHT + 20
        self.vy = random.uniform(-16, -21) * speed_mult
        self.vx = random.uniform(-1.5, 1.5)
        self.angle, self.rot_speed = 0, random.randint(-4, 4)
        self.hp = 2 if self.is_enrobed else 1

    def move(self, is_slowed=False):
        # Application du bonus glaçon
        factor = 0 if is_slowed else 1.0
        self.vy += 0.35 * factor
        self.y += self.vy * factor
        self.x += self.vx * factor
        self.angle += self.rot_speed * factor

    def draw(self, surf):
        if self.is_enrobed and self.hp > 0:
            pygame.draw.circle(surf, GOLD, (int(self.x + 30), int(self.y + 30)), 42, 5)
        rotated = pygame.transform.rotate(self.image_orig, self.angle)
        rect = rotated.get_rect(center=(self.x + 30, self.y + 30))
        surf.blit(rotated, rect.topleft)
        
        # Affichage des lettres (clavier)
        shadow = font_letter.render(self.letter.upper(), True, (20, 20, 20))
        surf.blit(shadow, (self.x + 17, self.y + 62))
        txt = font_letter.render(self.letter.upper(), True, self.color_label)
        surf.blit(txt, (self.x + 15, self.y + 60))
