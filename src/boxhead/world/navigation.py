"""Navegação A* numa grelha local; geometria independente das FSM e dos sprites."""
from heapq import heappop, heappush
from math import hypot

from pygame import Vector2

from boxhead.core.geometry import circle_aabb, circle_circle, segment_circle_hit, swept_circle_aabb_hit


class Navigator:
    STEP = 96
    MAX_VISITS = 2500

    def __init__(self, terrain):
        self.terrain = terrain
        self._paths = {}
        self._point_cache = {}
        self._edge_cache = {}
        self._plans_remaining = 3

    def clear(self) -> None:
        self._paths.clear()
        self._point_cache.clear()
        self._edge_cache.clear()

    def begin_frame(self) -> None:
        # Distribui replans entre frames para evitar um pico com 25 inimigos.
        self._plans_remaining = 3

    def _grid_clear(self, cell, radius):
        key = (cell, radius)
        if key not in self._point_cache:
            self._point_cache[key] = self.clear_point(self._point(cell), radius)
        return self._point_cache[key]

    def _edge_clear(self, a, b, radius):
        key = (min(a,b), max(a,b), radius)
        if key not in self._edge_cache:
            self._edge_cache[key] = self.clear_segment(self._point(a),self._point(b),radius)
        return self._edge_cache[key]

    def retain(self, ids) -> None:
        self._paths = {key:value for key,value in self._paths.items() if key in ids}

    def clear_point(self, point, radius):
        area = self.terrain.playable_bounds
        if not (area.left+radius <= point.x <= area.right-radius
                and area.top+radius <= point.y <= area.bottom-radius):
            return False
        for obstacle in self.terrain.obstacles:
            hit = (circle_circle(point,radius,Vector2(obstacle.rect.center),obstacle.rect.width/2)
                   if obstacle.circular else circle_aabb(point,radius,obstacle.rect))
            if hit is not None:
                return False
        return True

    def clear_segment(self, start, end, radius):
        for obstacle in self.terrain.obstacles:
            hit = (segment_circle_hit(start,end,Vector2(obstacle.rect.center),obstacle.rect.width/2+radius)
                   if obstacle.circular else swept_circle_aabb_hit(start,end,radius,obstacle.rect))
            if hit is not None:
                return False
        return True

    def _point(self, cell):
        return Vector2(cell[0]*self.STEP,cell[1]*self.STEP)

    def _snap(self, point, radius):
        cx,cy = round(point.x/self.STEP),round(point.y/self.STEP)
        cells = [(cx+x,cy+y) for x in range(-2,3) for y in range(-2,3)]
        cells.sort(key=lambda c:self._point(c).distance_squared_to(point))
        for cell in cells:
            candidate = self._point(cell)
            if self._grid_clear(cell,radius) and self.clear_segment(point,candidate,radius):
                return cell
        # Um alvo junto de uma parede pode não admitir o raio do inimigo.
        return next((c for c in cells if self._grid_clear(c,radius)),None)

    def _plan(self, start, target, radius):
        origin,goal = self._snap(start,radius),self._snap(target,radius)
        if origin is None or goal is None:
            return []
        queue=[(0,origin)]; costs={origin:0}; parent={}
        visits=0
        while queue and visits < self.MAX_VISITS:
            _,cell=heappop(queue);visits+=1
            if cell == goal:
                path=[cell]
                while path[-1] != origin:
                    path.append(parent[path[-1]])
                return [self._point(c) for c in reversed(path)]
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                neighbor=(cell[0]+dx,cell[1]+dy)
                cost=costs[cell]+hypot(dx,dy)
                if cost >= costs.get(neighbor,float('inf')):
                    continue
                if not self._grid_clear(neighbor,radius) or not self._edge_clear(cell,neighbor,radius):
                    continue
                costs[neighbor]=cost;parent[neighbor]=cell
                priority=cost+hypot(neighbor[0]-goal[0],neighbor[1]-goal[1])
                heappush(queue,(priority,neighbor))
        return []

    def direction(self, actor_id, start, target, radius):
        offset=target-start
        if self.clear_segment(start,target,radius):
            self._paths.pop(actor_id,None)
            return offset.normalize() if offset.length_squared() else Vector2()
        goal=(round(target.x/self.STEP),round(target.y/self.STEP))
        cached=self._paths.get(actor_id)
        if cached is None or cached[0] != goal:
            if self._plans_remaining > 0:
                self._plans_remaining -= 1
                cached=(goal,self._plan(start,target,radius+2))
                self._paths[actor_id]=cached
            elif cached is None:
                return Vector2()
        path=cached[1]
        while path and start.distance_to(path[0]) < 12:
            path.pop(0)
        if not path:
            return Vector2()
        offset=path[0]-start
        if not self.clear_segment(start,path[0],radius):
            self._paths.pop(actor_id,None)
            return Vector2()
        return offset.normalize() if offset.length_squared() else Vector2()
