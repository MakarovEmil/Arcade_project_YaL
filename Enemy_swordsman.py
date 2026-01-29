import arcade
from FaceDirection import FaceDirection
from pyglet.graphics import Batch
import random
TILE_SIZE = 70


class Enemy_swordsman(arcade.Sprite):
    def __init__(self, center_x, bottom_y, damage=10, health=30):
        super().__init__('Free Swordsman Character/Animations/Idle/Idle_000.png', scale=0.2)
        self.center_x = center_x
        self.center_y = bottom_y + self.height // 2
        self.damage = damage
        self.reward_for_kill = 2
        self.health = self.current_health = health
        self.detection_radius_squared = (12 * TILE_SIZE) ** 2
        self.height_dif = 280
        self.radius_of_attack = 1 * TILE_SIZE
        self.player_reference = None
        self.game_view = None
        self.engine = None
        self.face_direction = FaceDirection.RIGHT
        self.batch = Batch()
        self.health_text = arcade.Text(f'', self.center_x, self.center_y + 70,
                                       arcade.color.RED, batch=self.batch, font_size=24)

        self.check_point = arcade.Sprite()
        self.check_point.width = self.check_point.height = 4
        self.check_point.visible = False

        self.check_timer = 0
        self.check_interval = 2.5

        self.has_jumped = False
        self.is_visible = False

        self.max_height_of_wall = 3 * TILE_SIZE
        self.max_width_of_gap = 5 * TILE_SIZE

        self.state = 'idle'
        self.jump_type = None

        self.speed = 3
        self.wall_horizontal_jump_power = 10
        self.gap_horizontal_jump_power = 15
        self.jump_speed = 25

        self.idle_texture = None
        self.run_textures = None
        self.attack_1_textures = None
        self.attack_2_textures = None
        self.jumping_textures = None

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

        self.reload_time = 1.5
        self.reload_timer = 1.5
        self.can_attack = False
        self.jump_timer = 0
        self.is_check_hazards = False
        self.hazards_check_interval = 1.0
        self.hazards_check_timer = 0

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_visible:
            if self.state == 'idle':
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.idle_texture
                elif self.face_direction == FaceDirection.LEFT:
                    self.texture = self.idle_texture.flip_horizontally()
            elif self.state.startswith('attack_'):
                self.texture_change_time += delta_time
                if self.texture_change_time >= self.texture_change_delay:
                    self.texture_change_time = 0
                    self.current_texture += 1
                    if self.state == 'attack_1':
                        textures = self.attack_1_textures
                    else:
                        textures = self.attack_2_textures
                    if self.current_texture >= len(textures):
                        if self.state.startswith('attack_'):
                            self.state = 'idle'
                            self.current_texture = 0
                        return
                    if self.face_direction == FaceDirection.RIGHT:
                        self.texture = textures[self.current_texture]
                    else:
                        self.texture = textures[self.current_texture].flip_horizontally()
            elif self.state == 'running':
                self.texture_change_time += delta_time
                if self.texture_change_time >= self.texture_change_delay:
                    self.texture_change_time = 0
                    self.current_texture += 1
                    if self.current_texture >= len(self.run_textures):
                        self.current_texture = 0
                    if self.face_direction == FaceDirection.RIGHT:
                        self.texture = self.run_textures[self.current_texture]
                    elif self.face_direction == FaceDirection.LEFT:
                        self.texture = self.run_textures[self.current_texture].flip_horizontally()
            elif self.state == 'jumping':
                self.texture_change_time += delta_time
                if self.texture_change_time >= self.texture_change_delay:
                    self.texture_change_time = 0
                    self.current_texture += 1
                    if self.current_texture >= len(self.jumping_textures):
                        self.current_texture = 0
                    if self.face_direction == FaceDirection.RIGHT:
                        self.texture = self.jumping_textures[self.current_texture]
                    elif self.face_direction == FaceDirection.LEFT:
                        self.texture = self.jumping_textures[self.current_texture].flip_horizontally()

    def update(self, delta_time):
        if not self.is_visible:
            return
        self.engine.update()

        self.health_text.x, self.health_text.y = self.center_x, self.center_y + 70
        self.hazards_check_timer += delta_time
        if self.hazards_check_timer >= self.hazards_check_interval:
            self.hazards_check_timer = 0
            self.is_check_hazards = True
        if self.is_check_hazards:
            self.is_check_hazards = False
            if arcade.check_for_collision_with_list(self, self.game_view.hazards):
                self.current_health -= 3
        self.reload_timer -= delta_time
        if self.reload_timer <= 0:
            self.can_attack = True
            self.reload_timer = self.reload_time
        self.check_timer += delta_time
        dx = self.player_reference.center_x - self.center_x
        dy = self.player_reference.center_y - self.center_y
        distance_squared = dx * dx + dy * dy
        direction = self.get_stable_direction()

        if self.state == 'jumping':
            self.height_dif = 650
        else:
            self.height_dif = 280

        if self.state.startswith('attack_'):
            self.change_x = 0
            in_range_x = abs(self.center_x - self.player_reference.center_x) <= self.radius_of_attack
            in_range_y = abs(self.center_y - self.player_reference.center_y) < 50

            if in_range_x and in_range_y and self.current_texture >= 3 and not self.player_reference.invincible:
                self.player_reference.current_health -= self.damage
                self.player_reference.is_hurt = True
                self.player_reference.hurt_timer = 0
                self.player_reference.invincible = True
                self.player_reference.invincible_timer = 1.0
            return
        if (distance_squared <= self.detection_radius_squared and abs(self.player_reference.center_y - self.center_y)
                <= self.height_dif):
            if (self.state != 'jumping' and abs(self.center_x - self.player_reference.center_x) <= self.radius_of_attack
                    and abs(self.center_y - self.player_reference.center_y) <= 20):
                if self.can_attack:
                    choosing_attack = random.choice([1, 2])
                    self.state = f'attack_{choosing_attack}'
                    self.change_x = 0
                    self.can_attack = False
                    self.current_texture = 0
                    self.texture_change_time = 0
                else:
                    self.state = 'idle'
            elif self.check_timer >= self.check_interval:
                self.define_state(direction)
                self.check_timer = 0
        else:
            self.state = 'idle'

        if self.state == 'idle':
            self.change_x = 0
            return

        elif self.state == 'jumping':
            self.jump_timer += delta_time
            if not self.has_jumped:
                self.execute_jump(direction)
            if self.jump_timer > 0.4:
                if self.engine.can_jump():
                    self.state = 'running'
                    self.has_jumped = False
                    self.jump_timer = 0
            return
        elif self.state == 'running':
            if direction != 0:
                self.face_direction = FaceDirection.RIGHT if direction == 1 else FaceDirection.LEFT
                self.change_x = self.speed * direction
            else:
                self.change_x = 0
            return

    def define_state(self, direction):
        if self.state == 'jumping':
            return
        self.check_point.center_x = self.center_x + direction * 80
        self.check_point.center_y = self.bottom + 10
        if arcade.check_for_collision_with_list(self.check_point, self.game_view.walls):
            self.check_point.center_x = self.center_x + direction * 80
            self.check_point.center_y = self.bottom + self.max_height_of_wall + 10
            if not arcade.check_for_collision_with_list(self.check_point, self.game_view.walls):
                if self.engine.can_jump():
                    self.state = 'jumping'
                    self.jump_type = 'wall'
                    return
                else:
                    self.state = 'idle'
                    return
            else:
                self.state = 'idle'
                return
        self.check_point.center_x = self.center_x + direction * 210
        self.check_point.center_y = self.bottom - 20
        if not arcade.check_for_collision_with_list(self.check_point, self.game_view.walls):
            self.check_point.center_x = self.center_x + direction * self.max_width_of_gap + 70
            self.check_point.center_y = self.bottom - 10
            if not arcade.check_for_collision_with_list(self.check_point, self.game_view.walls):
                self.state = 'jumping'
                self.jump_type = 'gap'
                return
            else:
                self.state = 'idle'
                return
        self.check_point.center_x = self.center_x + direction * 40
        self.check_point.center_y = self.bottom + 10
        if arcade.check_for_collision_with_list(self.check_point, self.game_view.hazards):
            if self.current_health <= self.health * 0.33:
                self.state = 'idle'
                return
            else:
                self.state = 'running'
                return
        self.state = 'running'

    def get_stable_direction(self):
        dx = self.player_reference.center_x - self.center_x
        if abs(dx) < 15:
            return 0
        if abs(dx) > 30:
            if dx > 0:
                return 1
            else:
                return -1
        return 1 if self.face_direction == FaceDirection.RIGHT else -1

    def execute_jump(self, direction):
        self.has_jumped = True
        self.is_jumping_now = True
        if self.jump_type == 'wall':
            self.change_x = self.wall_horizontal_jump_power * direction
            self.change_y = self.jump_speed
        elif self.jump_type == 'gap':
            self.change_x = self.gap_horizontal_jump_power * direction
            self.change_y = self.jump_speed
