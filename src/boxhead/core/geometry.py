"""Geometria e colisões puras; sem entidades, janelas ou áudio."""

from __future__ import annotations

from dataclasses import dataclass

from pygame import Rect, Vector2


@dataclass(frozen=True)
class Contact:
    normal: Vector2
    penetration: float


def aabb_overlap(a: Rect, b: Rect) -> bool:
    return a.colliderect(b)


def circle_circle(center_a: Vector2, radius_a: float,
                  center_b: Vector2, radius_b: float) -> Contact | None:
    delta = center_b - center_a
    distance = delta.length()
    radii = radius_a + radius_b
    if distance >= radii or distance == 0:
        return None
    normal = delta / distance
    return Contact(normal=normal, penetration=radii - distance)


def circle_aabb(center: Vector2, radius: float, rect: Rect) -> Contact | None:
    closest = Vector2(
        max(rect.left, min(center.x, rect.right)),
        max(rect.top, min(center.y, rect.bottom)),
    )
    delta = closest - center
    distance_sq = delta.length_squared()
    if distance_sq >= radius * radius:
        return None
    distance = distance_sq ** 0.5
    normal = delta / distance if distance else Vector2(0, -1)
    return Contact(normal=normal, penetration=radius - distance)


def broad_phase(pairs: list[tuple[Rect, Rect]]) -> list[tuple[Rect, Rect]]:
    """Filtra pares candidatos por AABB antes do narrow phase."""
    return [(a, b) for a, b in pairs if aabb_overlap(a, b)]