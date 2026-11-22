"""Geometria e colisões puras; sem entidades, janelas ou áudio."""

from __future__ import annotations

from dataclasses import dataclass

from pygame import Rect, Vector2


@dataclass(frozen=True)
class Contact:
    """Contacto entre a forma A (a que se quer mover) e a forma B (fixa).

    `normal` aponta de A para B. Para separar A de B, mover A por `push_out`;
    assim quem resolve colisões não precisa de se lembrar do sentido do sinal.
    """

    normal: Vector2
    penetration: float

    @property
    def push_out(self) -> Vector2:
        """Deslocamento que deixa A exatamente encostado a B, sem sobreposição."""
        return -self.normal * self.penetration


def aabb_overlap(a: Rect, b: Rect) -> bool:
    return a.colliderect(b)


def circle_circle(
    center_a: Vector2, radius_a: float, center_b: Vector2, radius_b: float
) -> Contact | None:
    delta = center_b - center_a
    distance = delta.length()
    radii = radius_a + radius_b
    if distance >= radii:
        return None
    # Centros coincidentes: não há direção natural, escolhe-se uma estável.
    normal = delta / distance if distance else Vector2(0, -1)
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
    if distance_sq > 0:
        distance = distance_sq**0.5
        return Contact(normal=delta / distance, penetration=radius - distance)

    # O centro está dentro do retângulo: sai-se pela face mais próxima.
    faces = (
        (center.x - rect.left, Vector2(-1, 0)),
        (rect.right - center.x, Vector2(1, 0)),
        (center.y - rect.top, Vector2(0, -1)),
        (rect.bottom - center.y, Vector2(0, 1)),
    )
    depth, outward = min(faces, key=lambda face: face[0])
    return Contact(normal=-outward, penetration=depth + radius)


def broad_phase(pairs: list[tuple[Rect, Rect]]) -> list[tuple[Rect, Rect]]:
    """Filtra pares candidatos por AABB antes do narrow phase."""
    return [(a, b) for a, b in pairs if aabb_overlap(a, b)]


def segment_circle_hit(
    start: Vector2, end: Vector2, center: Vector2, radius: float
) -> float | None:
    """Fração t em [0, 1] do primeiro ponto do segmento dentro do círculo.

    Teste "varrido": um projétil rápido não atravessa um alvo entre dois frames.
    """
    direction = end - start
    offset = start - center
    c = offset.length_squared() - radius * radius
    if c <= 0:
        return 0.0  # já começa dentro
    a = direction.length_squared()
    if a == 0:
        return None
    b = 2 * offset.dot(direction)
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    t = (-b - discriminant**0.5) / (2 * a)
    return t if 0 <= t <= 1 else None


def segment_aabb_hit(start: Vector2, end: Vector2, rect: Rect) -> float | None:
    """Fração t em [0, 1] em que o segmento entra no retângulo (método das "slabs")."""
    direction = end - start
    t_enter, t_exit = 0.0, 1.0
    for origin, delta, low, high in (
        (start.x, direction.x, rect.left, rect.right),
        (start.y, direction.y, rect.top, rect.bottom),
    ):
        if delta == 0:
            if origin < low or origin > high:
                return None
            continue
        t1, t2 = (low - origin) / delta, (high - origin) / delta
        if t1 > t2:
            t1, t2 = t2, t1
        t_enter, t_exit = max(t_enter, t1), min(t_exit, t2)
        if t_enter > t_exit:
            return None
    return t_enter


class SpatialGrid[T]:
    """Broad phase: grelha uniforme que devolve só os candidatos perto de uma área.

    Evita testar todos os pares (O(n²)); a forma exata continua a ser confirmada
    pelo narrow phase (`circle_circle`, `segment_circle_hit`, ...). A ordem dos
    resultados segue a ordem de inserção, para os testes serem reproduzíveis.
    """

    def __init__(self, cell_size: int = 128) -> None:
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], list[T]] = {}

    def clear(self) -> None:
        self._cells.clear()

    def _cells_of(self, rect: Rect):
        size = self._cell_size
        for cx in range(rect.left // size, rect.right // size + 1):
            for cy in range(rect.top // size, rect.bottom // size + 1):
                yield (cx, cy)

    def insert(self, item: T, rect: Rect) -> None:
        for cell in self._cells_of(rect):
            self._cells.setdefault(cell, []).append(item)

    def query(self, rect: Rect) -> list[T]:
        found: dict[int, T] = {}
        for cell in self._cells_of(rect):
            for item in self._cells.get(cell, ()):
                found.setdefault(id(item), item)
        return list(found.values())
