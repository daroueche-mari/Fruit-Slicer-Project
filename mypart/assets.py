import pygame
from settings import *

pygame.font.init()

def get_font(size):
    return pygame.font.SysFont(["impact", "arialblack", "arial"], size)
# --- Polices ---
font_letter = get_font(35)
font_small = get_font(22)
font_huge = get_font(50)

def load_sounds():
    pygame.mixer.init()
    sounds = {}
    sound_files = {
        "ice": "sound/ice.wav",
        "lightning": "sound/lightning.wav",
        "slash": "sound/slash.wav",
        "bomb": "sound/bomb.wav",
        "halo": "sound/halo.wav",
        "fruit_cut": "sound/fruit.wav",
    }
    
    for name, file in sound_files.items():
        try:
            sounds[name] = pygame.mixer.Sound(file)
        except:
            # Si le fichier manque, on crée un objet vide pour éviter que le jeu plante
            sounds[name] = None 
            print(f"Attention : Son {file} non trouvé")
    return sounds

def play_music(state):
    """Gère le changement de musique selon l'état du jeu"""
    try:
        if state == "MENU":
            pygame.mixer.music.load("sound/mainsong.mp3") # Remplace par ton nom de fichier
        elif state == "PLAY":
            pygame.mixer.music.load("sound/ambiance_game.mp3") # Musique d'action
            
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1) # -1 pour boucler à l'infini
    except pygame.error:
        print(f"Erreur : Impossible de charger la musique pour {state}")



# --- Liste des images (Clés en anglais) ---
def load_game_assets():
    IMAGES_LIST = {
        "apricot": "image/abricot.png",
        "pineapple": "image/ananas.png",
        "banana": "image/banane.png",
        "bomb": "image/bombe.png",
        "cherry": "image/cerise.png",
        "lemon": "image/citron.png",
        "strawberry": "image/fraise.png",
        "raspberry": "image/framboise.png",
        "dragon_fruit": "iamge/fruit_du_dragon.png",
        "ice_block": "image/glaçon.png",
        "kiwi": "image/kiwi.png",
        "mango": "image/mangue.png",
        "melon": "image/melon.png",
        "blueberry": "image/myrtille.png",
        "coconut": "image/noix_de_coco.png",
        "orange": "image/orange.png",
        "watermelon": "image/pasteque.png",
        "peach": "image/peche.png",
        "pear": "image/poire.png",
        "apple": "image/pomme.png",
        "grape": "image/raisin.png",
        "shuriken": "image/shuriken.png",
        "lightning": "image/eclair.png",
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