import arcade
from FaceDirection import FaceDirection
TILE_SIZE = 70
WORLD_W = TILE_SIZE * 200
WORLD_H = TILE_SIZE * 60


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, direction, dif_x, dif_y, walls, speed=600, damage=10, max_distance=800):
        super().__init__('misc/shot/shot-1.png', scale=2)
        if direction == FaceDirection.RIGHT:
            self.center_x = start_x + dif_x
            self.center_y = start_y + dif_y
        elif direction == FaceDirection.LEFT:
            self.center_x = start_x - dif_x
            self.center_y = start_y + dif_y
        self.direction = direction
        self.speed = speed
        self.damage = damage

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.05
        self.check_timer = 0

        self.textures = None
        self.walls = walls

    def update(self, delta_time):
        self.check_timer += delta_time
        if self.check_timer >= 0.15:
            if arcade.check_for_collision_with_list(self, self.walls):
                self.remove_from_sprite_lists()
        if self.direction == FaceDirection.RIGHT:
            self.change_x = self.speed
        elif self.direction == FaceDirection.LEFT:
            self.change_x = -self.speed

        if (self.center_x < 0 or self.center_x > WORLD_W or
                self.center_y < 0 or self.center_y > WORLD_H):
            self.remove_from_sprite_lists()
        self.center_x += self.change_x * delta_time

    def update_animation(self, delta_time: float = 1 / 60):
        self.texture_change_time += delta_time
        if self.texture_change_time >= self.texture_change_delay:
            self.texture_change_time = 0
            self.current_texture += 1
            if self.current_texture >= len(self.textures):
                self.current_texture = 0
            if self.direction == FaceDirection.RIGHT:
                self.texture = self.textures[self.current_texture]
            elif self.direction == FaceDirection.LEFT:
                self.texture = self.textures[self.current_texture].flip_horizontally()


