import pygame
import random
import json
import os
from settings import *
from models import GameObject, LightningEffect, Particle, FruitSlice
from assets import font_small, font_huge, load_game_assets, load_sounds, play_music

# --- Configuration ---
pygame.init()
sounds = load_sounds()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
game_surface = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Slicer Game")
clock = pygame.time.Clock()

image_data = load_game_assets()

# --- Leaderboard (fichier JSON persistant) ---
LEADERBOARD_FILE = "leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10


# --- Variables Globales ---
game_state = "MENU"
sub_mode, score, lives = "CLASSIC", 0, 3
active_objects, slices, particles, slashes, lightning_effects = [], [], [], [], []
speed_multiplier, shake_intensity, flash_timer = 1.0, 0, 0
challenge_timer, is_iced, ice_timer = 3600, False, 0
is_overcharged, overcharge_timer, special_gauge = False, 0, 0
MAX_GAUGE = 100

# --- Variables pour l'écran USERNAME ---
current_username = ""  # Nom en cours de saisie
saved_username = ""  # Dernier nom validé (pour le remplir par défaut)
pending_mode = "CLASSIC"  # Le mode à lancer après la saisie du nom
username_input_active = True  # Pour gérer le focus de l'input
username_error = ""  # Message d'erreur affiché sur l'écran USERNAME

SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 900)


# Chargement du leaderboard depuis le fichier JSON
def load_leaderboard():
    """Charge le tableau des scores depuis le fichier JSON"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


# Sauvegarde du leaderboard dans le fichier JSON
def save_leaderboard(leaderboard):
    """Sauvegarde le tableau des scores dans le fichier JSON"""
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=2)


# Ajout ou mise à jour d'une entrée dans le leaderboard
def add_to_leaderboard(name, score, mode):
    """Ajoute le score à un joueur existant ou crée une nouvelle entrée"""
    leaderboard = load_leaderboard()

    # Chercher si le joueur existe déjà pour ce mode
    player_found = False
    for entry in leaderboard:
        if entry["name"] == name and entry["mode"] == mode:
            entry["score"] += score  # On ajoute les points au total existant
            player_found = True
            break

    if not player_found:
        # Si c'est un nouveau joueur ou nouveau mode pour ce joueur
        leaderboard.append({"name": name, "score": score, "mode": mode})

    # Tri par score total décroissant
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    leaderboard = leaderboard[:MAX_LEADERBOARD_ENTRIES]
    save_leaderboard(leaderboard)
    return leaderboard


# Obtenir le rang d'un joueur dans le leaderboard
def get_player_rank(name, score, mode):
    """Retourne le rang du joueur (1-indexé) ou None si pas dans le top"""
    leaderboard = load_leaderboard()
    for i, entry in enumerate(leaderboard):
        if entry["name"] == name and entry["score"] == score and entry["mode"] == mode:
            return i + 1
    return None


# Vérifie si un nom est déjà pris dans le leaderboard
def is_name_taken(name):
    """Vérifie si le nom existe déjà dans le leaderboard"""
    leaderboard = load_leaderboard()
    return any(entry["name"] == name for entry in leaderboard)


# Fonction pour couper tous les objets non-bombes à l'écran
def trigger_area_cut(particle_color=WHITE):
    """Coupe tous les objets non-bombes à l'écran"""
    global score
    targets = [obj for obj in active_objects if obj.type != "bomb"]
    count = len(targets)
    for obj in active_objects[:]:
        if obj.type != "bomb":
            # Calcul du score bonus
            if particle_color == GOLD and count > 1:
                score += count - 1
            else:
                score += count

            slices.extend(
                [
                    FruitSlice(obj.image_orig, obj.x, obj.y, "left"),
                    FruitSlice(obj.image_orig, obj.x, obj.y, "right"),
                ]
            )
            for _ in range(3):
                particles.append(Particle(obj.x + 30, obj.y + 30, particle_color))
            active_objects.remove(obj)


# Réinitialisation de la partie
def reset_game(mode):
    """Réinitialise la partie"""
    global game_state, sub_mode, score, lives, speed_multiplier, challenge_timer
    global active_objects, slices, particles, slashes, flash_timer
    global is_overcharged, overcharge_timer, special_gauge, lightning_effects, is_iced
    game_state, sub_mode = "PLAY", mode
    score, lives, speed_multiplier, challenge_timer, flash_timer = 0, 3, 1.0, 3600, 0
    is_iced = is_overcharged = False
    overcharge_timer = special_gauge = 0
    active_objects, slices, particles, slashes, lightning_effects = [], [], [], [], []
    play_music("PLAY")

# Transition vers l'écran de saisie du nom
def go_to_username_screen(mode):
    """Transition vers l'écran de saisie du nom avant de lancer une partie"""
    global game_state, pending_mode, current_username, username_input_active, username_error
    game_state = "USERNAME"
    pending_mode = mode
    current_username = saved_username  # Pré-remplir avec le dernier nom utilisé
    username_input_active = True
    username_error = ""
    pygame.key.start_text_input()



play_music("MENU")
# --- Boucle de Jeu ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(DARK_BLUE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Gestion de la saisie de texte pour USERNAME ---
        if game_state == "USERNAME":
            if event.type == pygame.TEXTINPUT:
                # On n'accepte que des caractères alphanumériques et espaces
                filtered = "".join(c for c in event.text if c.isalnum() or c == " ")
                if len(current_username) + len(filtered) <= 16:
                    current_username += filtered
                    username_error = ""  # Effacer l'erreur dès que le texte change

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    current_username = current_username[:-1]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Valider le nom et lancer la partie
                    if current_username.strip():
                        saved_username = current_username.strip()
                        username_error = ""
                        pygame.key.stop_text_input()
                        reset_game(pending_mode)
                    # Si le nom est vide, on ne fait rien (on reste sur l'écran)
                elif event.key == pygame.K_ESCAPE:
                    # Annuler et retour au menu
                    pygame.key.stop_text_input()
                    game_state = "MENU"
            continue  # On ne traite pas les autres événements sur cet écran

        # --- Gestion des clics et touches selon l'état du jeu ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "MENU":
                if WIDTH // 2 - 150 < mouse_pos[0] < WIDTH // 2 + 150:
                    if 280 < mouse_pos[1] < 340:
                        go_to_username_screen("CLASSIC")
                    elif 370 < mouse_pos[1] < 430:
                        go_to_username_screen("CHALLENGE")
            elif game_state == "PAUSE":
                if pygame.Rect(WIDTH // 2 - 150, 300, 300, 60).collidepoint(mouse_pos):
                    game_state = "PLAY"
                elif pygame.Rect(WIDTH // 2 - 150, 380, 300, 60).collidepoint(
                    mouse_pos
                ):
                    game_state = "MENU"
                    play_music("MENU")
            elif game_state == "GAMEOVER":
                # Bouton : voir le tableau des scores
                if pygame.Rect(WIDTH // 2 - 150, 280, 300, 60).collidepoint(mouse_pos):
                    game_state = "LEADERBOARD"
                # Bouton : recommencer (va d'abord demander le nom)
                elif pygame.Rect(WIDTH // 2 - 150, 370, 300, 60).collidepoint(
                    mouse_pos
                ):
                    go_to_username_screen(sub_mode)
                # Bouton : retour au menu
                elif pygame.Rect(WIDTH // 2 - 150, 460, 300, 60).collidepoint(
                    mouse_pos
                ):
                    game_state = "MENU"
                    play_music("MENU")
            elif game_state == "LEADERBOARD":
                # Bouton : recommencer depuis le leaderboard
                if pygame.Rect(WIDTH // 2 - 310, HEIGHT - 140, 300, 50).collidepoint(
                    mouse_pos
                ):
                    go_to_username_screen(sub_mode)
                # Bouton : retour au menu depuis le leaderboard
                elif pygame.Rect(WIDTH // 2 + 10, HEIGHT - 140, 300, 50).collidepoint(
                    mouse_pos
                ):
                    game_state = "MENU"
        # --- Gestion des touches clavier en mode PLAY ---
        if event.type == pygame.KEYDOWN:
            if game_state == "PLAY":
                play_music("PLAY")
                if combo_timer > 0:
                    combo_timer -= 1
                if event.key == pygame.K_ESCAPE:
                    game_state = "PAUSE"
                else:
                    key_pressed = pygame.key.name(event.key).lower()
                    BONUS_KEYS = ["a", "w", "s", "d"]
                    FRUIT_KEYS = ["j", "k", "l"]

                    # Capacité spéciale "Grand Slash"
                    if (
                        event.key == pygame.K_SPACE
                        and is_overcharged
                        and special_gauge >= MAX_GAUGE
                    ):
                        slashes.append(
                            {
                                "start": (0, HEIGHT // 2),
                                "end": (WIDTH, HEIGHT // 2),
                                "life": 255,
                            }
                        )
                        trigger_area_cut(ELECTRIC_ORANGE)
                        if sounds["slash"]:
                            sounds["slash"].play()
                        special_gauge = 0
                        shake_intensity = 25

                    # Détection de collision (touche clavier)
                    for obj in active_objects[:]:
                        hit = False
                        if is_overcharged:
                            hit = key_pressed == obj.letter
                        elif obj.is_bonus and key_pressed in BONUS_KEYS:
                            hit = key_pressed == obj.letter
                        elif not obj.is_bonus and key_pressed in FRUIT_KEYS:
                            hit = key_pressed == obj.letter

                        if hit:
                            obj.hp -= 1
                            if obj.hp <= 0:
                                if obj.type == "bomb":
                                    if sounds["bomb"]:
                                        sounds["bomb"].play()
                                    lives = 0
                                    shake_intensity = 50
                                    # Enregistrer le score avant GAMEOVER
                                    add_to_leaderboard(saved_username, score, sub_mode)
                                    game_state = "GAMEOVER"
                                elif obj.is_enrobed:
                                    if sounds["halo"]:
                                        sounds["halo"].play()
                                    score += 1
                                    flash_timer, shake_intensity = 10, 25
                                    trigger_area_cut(GOLD)
                                elif obj.type == "lightning":
                                    if sounds["lightning"]:
                                        sounds["lightning"].play()
                                    score += 1
                                    is_overcharged, overcharge_timer = True, 300
                                elif obj.type == "shuriken":
                                    if sounds["slash"]:
                                        sounds["slash"].play()
                                    score += 1
                                    slashes.append(
                                        {
                                            "start": (0, obj.y + 30),
                                            "end": (WIDTH, obj.y + 30),
                                            "life": 255,
                                        }
                                    )
                                    trigger_area_cut(WHITE)
                                elif obj.type == "ice_block":
                                    if sounds["ice"]:
                                        sounds["ice"].play()
                                    score += 1
                                    is_iced, ice_timer = True, 300
                                else:
                                    # Fruit classique + Combo
                                    if sounds["fruit_cut"]:
                                        sounds["fruit_cut"].play()
                                    if combo_timer > 0:
                                        score += 2
                                        combo_count += 1
                                    else:
                                        score += 1
                                        combo_count = 1
                                    combo_timer = COMBO_THRESHOLD
                                    if is_overcharged:
                                        special_gauge = min(
                                            MAX_GAUGE, special_gauge + 10
                                        )

                                    slices.extend(
                                        [
                                            FruitSlice(
                                                obj.image_orig, obj.x, obj.y, "left"
                                            ),
                                            FruitSlice(
                                                obj.image_orig, obj.x, obj.y, "right"
                                            ),
                                        ]
                                    )
                                    for _ in range(4):
                                        particles.append(
                                            Particle(obj.x + 30, obj.y + 30)
                                        )

                                if obj in active_objects:
                                    active_objects.remove(obj)
                            break

        # --- Gestion du spawn des objets ---
        if event.type == SPAWN_EVENT and game_state == "PLAY":
            if not is_iced:
                spawn_count = min(4, 1 + (score // 1000))
                if is_overcharged:
                    spawn_count = 6
                for _ in range(spawn_count):
                    active_objects.append(
                        GameObject(image_data, is_overcharged, speed_multiplier)
                    )

            # Accélération du jeu
            base_delay = max(400, 900 - (score // 10))
            pygame.time.set_timer(SPAWN_EVENT, 300 if is_overcharged else base_delay)

    # --- Logique de mise à jour ---
    if game_state in ["PLAY", "PAUSE"]:
        if game_state == "PLAY":
            # 1. Gestion des timers (Bonus et Challenge)
            if is_iced:
                ice_timer -= 1
                is_iced = ice_timer > 0
            else:
                # On ne baisse le chrono Challenge QUE si le gel est inactif
                if sub_mode == "CHALLENGE":
                    challenge_timer -= 1
                    if challenge_timer <= 0:
                        # Temps écoulé en Challenge : enregistrer le score
                        add_to_leaderboard(saved_username, score, sub_mode)
                        game_state = "GAMEOVER"

            if is_overcharged:
                overcharge_timer -= 1
                if overcharge_timer <= 0:
                    is_overcharged = False
                    slashes.append(
                        {
                            "start": (0, HEIGHT // 2),
                            "end": (WIDTH, HEIGHT // 2),
                            "life": 255,
                        }
                    )
                    trigger_area_cut(ELECTRIC_ORANGE)
                    if sounds["slash"]:
                        sounds["slash"].play()
                    shake_intensity = 25
                elif random.random() < 0.2:
                    lightning_effects.append(LightningEffect())

            # 2. Animations (Particules et morceaux de fruits)
            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

            for s in slices[:]:
                s.update()
                if s.y > HEIGHT + 100:
                    slices.remove(s)

            # 3. Mouvement des objets principaux (Fruits non coupés)
            for obj in active_objects[:]:
                obj.move(is_slowed=is_iced)

                if obj.y > HEIGHT + 100:
                    if not is_iced and not is_overcharged:
                        if (
                            obj.type not in ["bomb", "ice_block", "lightning"]
                            and sub_mode == "CLASSIC"
                        ):
                            lives -= 1
                    active_objects.remove(obj)

            # 4. Traits de coupe
            for sl in slashes[:]:
                sl["life"] -= 50
                if sl["life"] <= 0:
                    slashes.remove(sl)

        # --- Rendu Visuel ---
        game_surface.fill(DARK_BLUE)
        for p in particles:
            p.draw(game_surface)
        for s in slices:
            s.draw(game_surface)
        for l in lightning_effects:
            l.draw(game_surface)
        for obj in active_objects:
            obj.draw(game_surface)
        for sl in slashes:
            pygame.draw.line(game_surface, WHITE, sl["start"], sl["end"], 15)

        # Tremblement d'écran
        offset = (
            [
                random.randint(-shake_intensity, shake_intensity),
                random.randint(-shake_intensity, shake_intensity),
            ]
            if shake_intensity > 0
            else [0, 0]
        )
        if game_state == "PLAY":
            shake_intensity = max(0, shake_intensity - 1)
        screen.blit(game_surface, offset)

        # Overlays Surcharge / Glaçon
        if is_overcharged:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((255, 165, 0, 40))
            screen.blit(ov, (0, 0))
            pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 370, 20, 200, 20))
            bar_col = ELECTRIC_ORANGE if special_gauge >= MAX_GAUGE else WHITE
            pygame.draw.rect(
                screen,
                bar_col,
                (WIDTH - 370, 20, (special_gauge / MAX_GAUGE) * 200, 20),
            )
            screen.blit(
                font_small.render("GRAND SLASH (ESPACE)", True, bar_col),
                (WIDTH - 370, 45),
            )

        if is_iced:
            ice_ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ice_ov.fill((100, 200, 255, 60))
            screen.blit(ice_ov, (0, 0))

        # Affichage du Score et des Vies (Interface)
        score_text = f"SCORE: {score}"
        if combo_timer > 0 and combo_count > 1:
            score_text += f" | COMBO X2 ({combo_count}) !"
        hud_text = (
            score_text
            + " | "
            + (
                f"VIES: {lives}"
                if sub_mode == "CLASSIC"
                else f"TEMPS: {challenge_timer // 60}s"
            )
        )
        # Afficher le nom du joueur en haut à droite
        name_text = font_small.render(
            f"Joueur: {saved_username}", True, (180, 180, 255)
        )
        screen.blit(name_text, (WIDTH - name_text.get_width() - 20, 20))

        screen.blit(
            font_small.render(
                hud_text, True, (255, 215, 0) if combo_timer > 0 else WHITE
            ),
            (20, 20),
        )

        # Flash à l'écran lors d'un cut spécial
        if game_state == "PAUSE":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            txt = font_huge.render("PAUSE", True, YELLOW)
            screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 200)))
            for i, label in enumerate(["REPRENDRE", "MENU"]):
                rect = pygame.Rect(WIDTH // 2 - 150, 300 + i * 80, 300, 60)
                col = YELLOW if rect.collidepoint(mouse_pos) else WHITE
                pygame.draw.rect(screen, col, rect, 2, border_radius=10)
                btn = font_small.render(label, True, col)
                screen.blit(btn, btn.get_rect(center=rect.center))

        if sub_mode == "CLASSIC" and lives <= 0:
            # Enregistrer le score avant GAMEOVER (si pas déjà fait par la bomba)
            if game_state != "GAMEOVER":
                add_to_leaderboard(saved_username, score, sub_mode)
            game_state = "GAMEOVER"

    # --- Écran USERNAME ---
    elif game_state == "USERNAME":
        # Fond semi-transparent sur DARK_BLUE
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 200))
        screen.blit(overlay, (0, 0))

        # Titre
        titre = font_huge.render("ENTRER VOTRE NOM", True, WHITE)
        screen.blit(titre, titre.get_rect(center=(WIDTH // 2, 140)))

        # Sous-titre (mode à lancer)
        mode_label = (
            "Mode : CLASSIQUE" if pending_mode == "CLASSIC" else "Mode : CHALLENGE"
        )
        sous_titre = font_small.render(mode_label, True, (180, 180, 255))
        screen.blit(sous_titre, sous_titre.get_rect(center=(WIDTH // 2, 200)))

        # Zone d'input (rectangle arrondi)
        input_rect = pygame.Rect(WIDTH // 2 - 200, 260, 400, 60)
        pygame.draw.rect(screen, (40, 40, 70), input_rect, border_radius=12)
        pygame.draw.rect(screen, (100, 100, 180), input_rect, 2, border_radius=12)

        # Texte dans l'input
        if current_username:
            input_text = font_huge.render(current_username, True, WHITE)
        else:
            input_text = font_huge.render("...", True, (100, 100, 100))  # placeholder
        screen.blit(input_text, input_text.get_rect(center=input_rect.center))

        # Curseur clignotant
        cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
        if cursor_visible:
            cursor_x = input_rect.centerx + input_text.get_width() // 2 + 4
            if not current_username:
                cursor_x = input_rect.centerx - 8
            pygame.draw.line(
                screen,
                WHITE,
                (cursor_x, input_rect.top + 10),
                (cursor_x, input_rect.bottom - 10),
                2,
            )

        # Instructions
        instruct1 = font_small.render(
            "Tapez votre nom puis appuyez sur ENTRÉE", True, (180, 180, 180)
        )
        screen.blit(instruct1, instruct1.get_rect(center=(WIDTH // 2, 350)))
        instruct2 = font_small.render(
            "(16 caractères max — ESC pour annuler)", True, (120, 120, 120)
        )
        screen.blit(instruct2, instruct2.get_rect(center=(WIDTH // 2, 380)))

        # Message d'erreur (nom déjà pris)
        if username_error:
            err_surf = font_small.render(username_error, True, RED)
            screen.blit(err_surf, err_surf.get_rect(center=(WIDTH // 2, 410)))

        # Bouton Valider (visuel, mais la validation se fait avec ENTRÉE)
        valider_rect = pygame.Rect(WIDTH // 2 - 100, 430, 200, 55)
        can_validate = len(current_username.strip()) > 0
        if can_validate:
            btn_col = YELLOW if valider_rect.collidepoint(mouse_pos) else GREEN
        else:
            btn_col = (80, 80, 80)  # grisé si vide
        pygame.draw.rect(screen, btn_col, valider_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, valider_rect, 2, border_radius=10)
        valider_txt = font_small.render("VALIDER", True, WHITE)
        screen.blit(valider_txt, valider_txt.get_rect(center=valider_rect.center))

        # Click sur le bouton Valider avec la souris
        if (
            pygame.mouse.get_pressed()[0]
            and valider_rect.collidepoint(mouse_pos)
            and can_validate
        ):
            if (
                is_name_taken(current_username.strip())
                and current_username.strip() != saved_username
            ):
                username_error = "Ce nom est déjà utilisé !"
            else:
                username_error = ""
                saved_username = current_username.strip()
                pygame.key.stop_text_input()
                reset_game(pending_mode)

    # --- GAMEOVER ---
    elif game_state == "GAMEOVER":
        # Overlay sombre
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Titre
        txt = font_huge.render("PARTIE TERMINEE", True, RED)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 100)))

        # Nom du joueur et score
        name_score = font_small.render(
            f"{saved_username} — SCORE FINAL : {score}", True, WHITE
        )
        screen.blit(name_score, name_score.get_rect(center=(WIDTH // 2, 170)))

        # Rank du joueur dans le leaderboard
        rank = get_player_rank(saved_username, score, sub_mode)
        if rank:
            if rank == 1:
                rank_color = (255, 215, 0)  # Or
                rank_txt = f"🏆 NOUVEAU RECORD ! RANG #{rank}"
            elif rank <= 3:
                rank_color = (255, 165, 0)  # Bronze/Argent
                rank_txt = f"⭐ RANG #{rank} AU TABLEAU !"
            else:
                rank_color = (100, 200, 255)
                rank_txt = f"Rang #{rank} au tableau des scores"
            rank_surface = font_small.render(rank_txt, True, rank_color)
            screen.blit(rank_surface, rank_surface.get_rect(center=(WIDTH // 2, 220)))

        # Boutons (3 boutons verticaux)
        buttons_gameover = [
            ("TABLEAU DES SCORES", (WIDTH // 2 - 150, 280)),
            ("RECOMMENCER", (WIDTH // 2 - 150, 370)),
            ("MENU", (WIDTH // 2 - 150, 460)),
        ]
        for label, (bx, by) in buttons_gameover:
            rect = pygame.Rect(bx, by, 300, 60)
            col = YELLOW if rect.collidepoint(mouse_pos) else WHITE
            pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            btn = font_small.render(label, True, col)
            screen.blit(btn, btn.get_rect(center=rect.center))

    # --- LEADERBOARD ---
    elif game_state == "LEADERBOARD":
        leaderboard = load_leaderboard()

        # Fond
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 220))
        screen.blit(overlay, (0, 0))

        # Titre
        titre = font_huge.render("TABLEAU DES SCORES", True, (255, 215, 0))
        screen.blit(titre, titre.get_rect(center=(WIDTH // 2, 45)))

        # En-têtes du tableau
        headers = ["#", "NOM", "SCORE", "MODE"]
        col_widths = [50, 220, 150, 160]
        table_x = WIDTH // 2 - sum(col_widths) // 2
        header_y = 90

        # Ligne séparatrice sous le titre
        pygame.draw.line(
            screen,
            (100, 100, 150),
            (table_x - 10, 80),
            (table_x + sum(col_widths) + 10, 80),
            1,
        )

        # Afficher les en-têtes
        x_offset = table_x
        for i, header in enumerate(headers):
            h_surf = font_small.render(header, True, (150, 150, 200))
            screen.blit(
                h_surf,
                (x_offset + col_widths[i] // 2 - h_surf.get_width() // 2, header_y),
            )
            x_offset += col_widths[i]

        pygame.draw.line(
            screen,
            (100, 100, 150),
            (table_x - 10, header_y + 28),
            (table_x + sum(col_widths) + 10, header_y + 28),
            1,
        )

        # Afficher les entrées du leaderboard
        row_height = 42
        start_y = header_y + 40

        if not leaderboard:
            # Message si le tableau est vide
            empty_txt = font_small.render(
                "Aucun score enregistré pour le moment.", True, (120, 120, 120)
            )
            screen.blit(
                empty_txt, empty_txt.get_rect(center=(WIDTH // 2, start_y + 40))
            )
        else:
            for idx, entry in enumerate(leaderboard):
                row_y = start_y + idx * row_height
                rank_num = idx + 1

                # Couleur de fond alternée pour la lisibilité
                row_rect = pygame.Rect(
                    table_x - 10, row_y - 4, sum(col_widths) + 20, row_height - 4
                )
                if idx % 2 == 0:
                    pygame.draw.rect(screen, (25, 25, 50), row_rect, border_radius=4)
                else:
                    pygame.draw.rect(screen, (35, 35, 65), row_rect, border_radius=4)

                # Mettre en relief le joueur actuel
                is_current = (
                    entry["name"] == saved_username
                    and entry["score"] == score
                    and entry["mode"] == sub_mode
                )
                if is_current:
                    pygame.draw.rect(screen, (60, 60, 120), row_rect, border_radius=4)
                    pygame.draw.rect(
                        screen, (255, 215, 0), row_rect, 2, border_radius=4
                    )

                # Couleurs des rangs
                if rank_num == 1:
                    rank_color = (255, 215, 0)  # Or
                elif rank_num == 2:
                    rank_color = (192, 192, 192)  # Argent
                elif rank_num == 3:
                    rank_color = (205, 127, 50)  # Bronze
                else:
                    rank_color = WHITE

                # Données à afficher
                values = [
                    str(rank_num),
                    entry["name"],
                    str(entry["score"]),
                    entry["mode"],
                ]

                x_offset = table_x
                for col_idx, val in enumerate(values):
                    color = (
                        rank_color
                        if col_idx == 0
                        else (WHITE if is_current else (220, 220, 220))
                    )
                    cell_surf = font_small.render(val, True, color)
                    cell_x = (
                        x_offset + col_widths[col_idx] // 2 - cell_surf.get_width() // 2
                    )
                    screen.blit(cell_surf, (cell_x, row_y))
                    x_offset += col_widths[col_idx]

        # Boutons en bas
        btn_y = HEIGHT - 140
        btn_restart_rect = pygame.Rect(WIDTH // 2 - 310, btn_y, 300, 50)
        btn_menu_rect = pygame.Rect(WIDTH // 2 + 10, btn_y, 300, 50)

        for rect, label in [(btn_restart_rect, "RECOMMENCER"), (btn_menu_rect, "MENU")]:
            col = YELLOW if rect.collidepoint(mouse_pos) else WHITE
            pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            btn = font_small.render(label, True, col)
            screen.blit(btn, btn.get_rect(center=rect.center))

    # --- MENU ---
    else:  # MENU
        txt = font_huge.render("FRUIT SLICER GAME", True, WHITE)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 150)))

        # Bouton vers le leaderboard depuis le menu (au-dessus des commandes)
        lb_rect = pygame.Rect(WIDTH // 2 - 150, 440, 300, 30)
        lb_col = (255, 215, 0) if lb_rect.collidepoint(mouse_pos) else (150, 150, 200)
        lb_txt = font_small.render("📊 Voir le tableau des scores", True, lb_col)
        screen.blit(lb_txt, lb_txt.get_rect(center=lb_rect.center))
        if pygame.mouse.get_pressed()[0] and lb_rect.collidepoint(mouse_pos):
            game_state = "LEADERBOARD"

        # Guide des touches
        texte_bouton = font_small.render("COMMANDE EN JEU :", True, (255, 255, 255))
        texte_rect = texte_bouton.get_rect(center=(WIDTH // 2, 495))
        screen.blit(texte_bouton, texte_rect)

        pygame.draw.rect(
            screen, (255, 80, 80), (WIDTH // 2 - 250, 520, 200, 50), 2, border_radius=10
        )
        lbl_l = font_small.render("BONUS : A W S D", True, (255, 80, 80))
        screen.blit(lbl_l, lbl_l.get_rect(center=(WIDTH // 2 - 150, 542)))

        pygame.draw.rect(
            screen, (80, 255, 80), (WIDTH // 2 + 50, 520, 200, 50), 2, border_radius=10
        )
        lbl_r = font_small.render("FRUITS : J K L", True, (80, 255, 80))
        screen.blit(lbl_r, lbl_r.get_rect(center=(WIDTH // 2 + 150, 542)))

        for i, label in enumerate(["CLASSIQUE", "CHALLENGE"]):
            rect = pygame.Rect(WIDTH // 2 - 150, 280 + i * 90, 300, 60)
            col = (GREEN if i == 0 else RED) if rect.collidepoint(mouse_pos) else WHITE
            pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            btn = font_huge.render(label, True, col)
            screen.blit(btn, btn.get_rect(center=rect.center))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()