"""Demo: mover o jogador com WASD/setas, disparar animação com ESPAÇO. Corre com:  python demo.py"""
import pygame
from sprites import SpriteBank

pygame.init()
screen = pygame.display.set_mode((640, 400))
pygame.display.set_caption("Demo sprites")
clock = pygame.time.Clock()
bank = SpriteBank("pixel_art_pygame_pack_v2")

idle = bank.directional("player/player_idle.png")
walk = bank.directional("player/player_walk.png")
shoot = bank.directional("player/player_shoot.png")
zombie = bank.directional("enemies/enemy_basic_walk.png")
shadow = bank.cell("player/player_shadow.png")
floor = bank.cell("environment/floor_tiles.png", 0, 0)

pos = pygame.Vector2(320, 200)
facing, shooting = "down", False
enemy_pos = pygame.Vector2(120, 120)

running = True
while running:
    dt = clock.tick(60) / 1000
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and not shooting:
            shooting = True
            shoot[facing].reset()

    k = pygame.key.get_pressed()
    d = pygame.Vector2(k[pygame.K_d] - k[pygame.K_a] + k[pygame.K_RIGHT] - k[pygame.K_LEFT],
                       k[pygame.K_s] - k[pygame.K_w] + k[pygame.K_DOWN] - k[pygame.K_UP])
    moving = d.length_squared() > 0
    if moving:
        d = d.normalize()
        pos += d * 140 * dt
        facing = ("right" if d.x > 0 else "left") if abs(d.x) > abs(d.y) else ("down" if d.y > 0 else "up")

    if shooting:
        anim = shoot[facing]
    else:
        anim = walk[facing] if moving else idle[facing]
    anim.update(dt)
    if shooting and anim.done:
        shooting = False

    to_p = pos - enemy_pos
    if to_p.length() > 40:
        v = to_p.normalize()
        enemy_pos += v * 60 * dt
        ed = ("right" if v.x > 0 else "left") if abs(v.x) > abs(v.y) else ("down" if v.y > 0 else "up")
        zombie[ed].update(dt)
        zimg = zombie[ed].image
    else:
        zimg = zombie["down"].frames[0]

    for x in range(0, 640, 64):
        for y in range(0, 400, 64):
            screen.blit(floor, (x, y))
    for img, p in ((shadow, pos), (anim.image, pos), (shadow, enemy_pos), (zimg, enemy_pos)):
        screen.blit(img, img.get_rect(center=(int(p.x), int(p.y))))
    pygame.display.flip()
pygame.quit()
