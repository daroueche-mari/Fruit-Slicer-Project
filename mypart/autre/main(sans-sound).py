import pygame
import random
from settings import *
from models import GameObject, LightningEffect, Particle, FruitSlice
from assets import font_small, font_huge, load_game_assets

# --- Configuration ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
game_surface = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Slicer Ultimate")
clock = pygame.time.Clock()

image_data = load_game_assets()

# --- Variables Globales ---
game_state = "MENU"
sub_mode, score, lives = "CLASSIC", 0, 3
active_objects, slices, particles, slashes, lightning_effects = [], [], [], [], []
speed_multiplier, shake_intensity, flash_timer = 1.0, 0, 0
challenge_timer, is_iced, ice_timer = 3600, False, 0
is_overcharged, overcharge_timer, special_gauge = False, 0, 0
MAX_GAUGE = 100

SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 900)


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


def reset_game(mode):
    """Réinitialise la partie"""
    global game_state, sub_mode, score, lives, speed_multiplier, challenge_timer, active_objects, slices, particles, slashes, flash_timer, is_overcharged, overcharge_timer, special_gauge, lightning_effects, is_iced
    game_state, sub_mode = "PLAY", mode
    score, lives, speed_multiplier, challenge_timer, flash_timer = 0, 3, 1.0, 3600, 0
    is_iced = is_overcharged = False
    overcharge_timer = special_gauge = 0
    active_objects, slices, particles, slashes, lightning_effects = [], [], [], [], []



# --- Boucle de Jeu ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(DARK_BLUE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "MENU":
                if WIDTH // 2 - 150 < mouse_pos[0] < WIDTH // 2 + 150:
                    if 280 < mouse_pos[1] < 340:
                        reset_game("CLASSIC")
                    elif 370 < mouse_pos[1] < 430:
                        reset_game("CHALLENGE")
            elif game_state == "PAUSE":
                if pygame.Rect(WIDTH // 2 - 150, 300, 300, 60).collidepoint(mouse_pos):
                    game_state = "PLAY"
                elif pygame.Rect(WIDTH // 2 - 150, 380, 300, 60).collidepoint(
                    mouse_pos
                ):
                    game_state = "MENU"
            elif game_state == "GAMEOVER":
                if pygame.Rect(WIDTH // 2 - 150, 320, 300, 60).collidepoint(mouse_pos):
                    reset_game(sub_mode)
                elif pygame.Rect(WIDTH // 2 - 150, 410, 300, 60).collidepoint(
                    mouse_pos
                ):
                    game_state = "MENU"

        if event.type == pygame.KEYDOWN:
            if game_state == "PLAY":
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
                                    lives = 0
                                    shake_intensity = 50
                                    game_state = "GAMEOVER"
                                elif obj.is_enrobed:
                                    score += 1
                                    flash_timer, shake_intensity = 10, 25
                                    trigger_area_cut(GOLD)
                                elif obj.type == "lightning":
                                    score += 1
                                    is_overcharged, overcharge_timer = True, 300
                                elif obj.type == "shuriken":
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
                                    score += 1
                                    is_iced, ice_timer = True, 300
                                else:
                                    # Fruit classique + Combo
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
                    shake_intensity = 25
                elif random.random() < 0.2:
                    lightning_effects.append(LightningEffect())

            # 2. Animations (Particules et morceaux de fruits)
            # On les laisse en dehors du "if not is_iced" pour qu'ils tombent toujours
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
                # Ils se figent grâce à is_slowed=is_iced (si factor=0 dans la classe)
                obj.move(is_slowed=is_iced)

                if obj.y > HEIGHT + 100:
                    # On ne perd des vies que si le temps n'est pas figé
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
            pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 220, 20, 200, 20))
            bar_col = ELECTRIC_ORANGE if special_gauge >= MAX_GAUGE else WHITE
            pygame.draw.rect(
                screen,
                bar_col,
                (WIDTH - 220, 20, (special_gauge / MAX_GAUGE) * 200, 20),
            )
            screen.blit(
                font_small.render("GRAND SLASH (ESPACE)", True, bar_col),
                (WIDTH - 220, 45),
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
                else f"TEMPS: {challenge_timer//60}s"
            )
        )
        screen.blit(
            font_small.render(
                hud_text, True, (255, 215, 0) if combo_timer > 0 else WHITE
            ),
            (20, 20),
        )

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
            game_state = "GAMEOVER"

    elif game_state == "GAMEOVER":
        txt = font_huge.render("PARTIE TERMINEE", True, RED)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 120)))
        score_txt = font_small.render(f"SCORE FINAL : {score}", True, WHITE)
        screen.blit(score_txt, score_txt.get_rect(center=(WIDTH // 2, 200)))
        for i, label in enumerate(["RECOMMENCER", "MENU"]):
            rect = pygame.Rect(WIDTH // 2 - 150, 320 + i * 90, 300, 60)
            col = YELLOW if rect.collidepoint(mouse_pos) else WHITE
            pygame.draw.rect(screen, col, rect, 2, border_radius=10)
            btn = font_small.render(label, True, col)
            screen.blit(btn, btn.get_rect(center=rect.center))

    else:  # MENU
        txt = font_huge.render("FRUIT SLICER ULTIMATE", True, WHITE)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 150)))

        # Guide des touches
        pygame.draw.rect(
            screen, (255, 80, 80), (WIDTH // 2 - 250, 520, 200, 50), 2, border_radius=10
        )
        texte_bouton = font_small.render("COMMANDE EN JEU :", True, (255, 255, 255))
        texte_rect = texte_bouton.get_rect(center=(WIDTH // 2 - -50 + -50, 460 + 25))
        screen.blit(texte_bouton, texte_rect)

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
