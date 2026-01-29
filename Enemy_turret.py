import arcade
from pyglet.graphics import Batch
from FaceDirection import FaceDirection
from Bullet import Bullet
TILE_SIZE = 70


class Enemy_turret(arcade.Sprite):
    def __init__(self, center_x, bottom_y, damage=20, health=30):
        super().__init__('misc/turret/turret-1.png', scale=4)
        self.center_x = center_x
        self.center_y = bottom_y + self.height // 2
        self.damage = damage
        self.health = health
        self.batch = Batch()
        self.health_text = arcade.Text(f'', self.center_x - 20, self.center_y + 70, arcade.color.RED,
                                       batch=self.batch, font_size=24)

        self.reward_for_kill = 3
        self.detection_radius_squared = (12 * TILE_SIZE) ** 2
        self.player_reference = None
        self.wall_list = None
        self.state = 'idle'
        self.attack_direction = FaceDirection.RIGHT

        self.idle_textures = None
        self.attack_texture = None

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

        self.reload_timer = 0
        self.reload_time = 2.0

        self.check_timer = 0
        self.check_interval = 2.5
        self.can_see_player_cash = False
        self.is_visible = False

        self.bullet_list = arcade.SpriteList()
        self.bullet_textures = None

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_visible:
            if self.state == 'idle':
                self.texture_change_time += delta_time
                if self.texture_change_time >= self.texture_change_delay:
                    self.texture_change_time = 0
                    self.current_texture += 1
                    if self.current_texture >= len(self.idle_textures):
                        self.current_texture = 0
                    self.texture = self.idle_textures[self.current_texture]
            elif self.state == 'attack':
                if self.attack_direction == FaceDirection.RIGHT:
                    self.texture = self.attack_texture
                elif self.attack_direction == FaceDirection.LEFT:
                    self.texture = self.attack_texture.flip_horizontally()

    def update(self, delta_time):
        if not self.is_visible:
            return
        dx = self.player_reference.center_x - self.center_x
        dy = self.player_reference.center_y - self.center_y
        distance_squared = dx * dx + dy * dy
        if (distance_squared <= self.detection_radius_squared and abs(
            self.player_reference.center_y - self.center_y)
            <= 70):
            self.check_timer += delta_time
            if self.check_timer >= self.check_interval:
                self.can_see_player_cash = self.can_see_player()
                self.check_timer = 0
            if self.can_see_player_cash:
                self.state = 'attack'
                if self.player_reference.center_x <= self.center_x:
                    self.attack_direction = FaceDirection.LEFT
                elif self.player_reference.center_x > self.center_x:
                    self.attack_direction = FaceDirection.RIGHT
                self.reload_timer -= delta_time
                if self.reload_timer <= 0:
                    bullet = Bullet(self.center_x, self.center_y, self.attack_direction, 45, 25,
                                    self.wall_list, damage=self.damage)
                    bullet.textures = self.bullet_textures
                    self.bullet_list.append(bullet)
                    self.reload_timer = self.reload_time
        else:
            self.state = 'idle'

    def can_see_player(self, steps=10):
        px, py = self.player_reference.center_x, self.player_reference.center_y
        tx, ty = self.center_x, self.center_y
        for i in range(steps + 1):
            t = i / steps
            check_x = tx + (px - tx) * t
            check_y = ty + (py - ty) * t
            test_point = arcade.SpriteSolidColor(5, 5, arcade.color.TRANSPARENT_BLACK)
            test_point.center_x = check_x
            test_point.center_y = check_y
            walls_at_point = arcade.check_for_collision_with_list(test_point, self.wall_list)
            if walls_at_point:
                return False
        return True