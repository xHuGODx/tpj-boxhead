"""Edge pointers for the final off-screen enemies; presentation only."""
import pygame
from pygame import Vector2

TRACK_LAST = 5


def targets(world, camera, size):
    alive = [enemy for enemy in world.enemies if enemy.alive]
    if not 0 < len(alive) <= TRACK_LAST:
        return []
    if world.director is not None and world.director.pending > 0:
        return []
    screen = pygame.Rect((0, 0), size)
    # Keep pointers clear of the stats header and weapon/ammo footer.
    safe = pygame.Rect(38, min(218, size[1]//3), size[0]-76,
                       size[1]-min(218, size[1]//3)-108)
    origin = camera.world_to_screen(world.player.position)
    result = []
    for enemy in alive:
        position = camera.world_to_screen(enemy.position)
        radius = enemy.radius * 1.45
        visible = pygame.Rect(round(position.x-radius), round(position.y-radius),
                              round(radius*2), round(radius*2))
        if screen.colliderect(visible):
            continue
        direction = position-origin
        if not direction.length_squared():
            continue
        direction = direction.normalize()
        # Ray from the displayed player through the target to the safe edge.
        start = Vector2(max(safe.left,min(safe.right,origin.x)),
                        max(safe.top,min(safe.bottom,origin.y)))
        times = []
        if direction.x > 0: times.append((safe.right-start.x)/direction.x)
        if direction.x < 0: times.append((safe.left-start.x)/direction.x)
        if direction.y > 0: times.append((safe.bottom-start.y)/direction.y)
        if direction.y < 0: times.append((safe.top-start.y)/direction.y)
        point = start + direction*min(times)
        # Nearby bearings share a marker rather than drawing over each other.
        group = next((item for item in result if item['point'].distance_to(point)<36),None)
        if group:
            group['count'] += 1
        else:
            result.append(dict(point=point, direction=direction, count=1))
    return result


class EnemyTracker:
    def __init__(self):
        self.font = pygame.font.Font(None, 20)

    def draw(self, surface, world, camera):
        for item in targets(world,camera,surface.get_size()):
            point, direction = item['point'], item['direction']
            side = direction.rotate(90)
            pygame.draw.circle(surface,(15,22,33),point,20)
            pygame.draw.circle(surface,(102,84,47),point,20,1)
            pygame.draw.polygon(surface,(255,209,105),
                                (point+direction*13, point-direction*7+side*8,
                                 point-direction*3, point-direction*7-side*8))
            if item['count'] <= 1:
                continue
            label = self.font.render(f"x{item['count']}",True,(255,224,161))
            center = point-direction*40
            rect = label.get_rect(center=center)
            rect.clamp_ip(surface.get_rect().inflate(-8,-8))
            pygame.draw.rect(surface,(15,22,33),rect.inflate(8,4),border_radius=4)
            surface.blit(label,rect)
