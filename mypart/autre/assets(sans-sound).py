import pygame
from settings import *

pygame.font.init()

def get_font(size):
    return pygame.font.SysFont(["impact", "arialblack", "arial"], size)
# --- Polices ---
font_letter = get_font(35)
font_small = get_font(22)
font_huge = get_font(50)

# --- Liste des images (Clés en anglais) ---
def load_game_assets():
    IMAGES_LIST = {
        "apricot": "abricot.png",
        "pineapple": "ananas.png",
        "banana": "banane.png",
        "bomb": "bombe.png",
        "cherry": "cerise.png",
        "lemon": "citron.png",
        "strawberry": "fraise.png",
        "raspberry": "framboise.png",
        "dragon_fruit": "fruit_du_dragon.png",
        "ice_block": "glaçon.png",
        "kiwi": "kiwi.png",
        "mango": "mangue.png",
        "melon": "melon.png",
        "blueberry": "myrtille.png",
        "coconut": "noix_de_coco.png",
        "orange": "orange.png",
        "watermelon": "pasteque.png",
        "peach": "peche.png",
        "pear": "poire.png",
        "apple": "pomme.png",
        "grape": "raisin.png",
        "shuriken": "shuriken.png",
        "lightning": "eclair.png",
    }

    image_data = {}
    for name, filename in IMAGES_LIST.items():
        try:
            img = pygame.image.load(filename).convert_alpha()
            image_data[name] = pygame.transform.scale(img, (60, 60))
        except:
            # Fallback visuel si l'image est manquante
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            color = ICE_BLUE if name == "ice_block" else (ELECTRIC_ORANGE if name == "lightning" else GREEN)
            pygame.draw.circle(surf, color, (30, 30), 25)
            image_data[name] = surf 
    
    return image_data