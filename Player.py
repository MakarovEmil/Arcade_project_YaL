import arcade
from FaceDirection import FaceDirection


class Player(arcade.Sprite):
    def __init__(self, damage=3, health=20):
        super().__init__('player/idle/idle-4.png', scale=2)
        self.spawn_point = (280, 140)
        self.center_x, self.center_y = self.spawn_point

        self.walk_speed = 2
        self.run_speed = 5
        self.jump_backward_speed = 8
        self.jump_forward_speed = 8
        self.jump_speed = 40
        self.ladder_speed = 3

        self.health = self.current_health = health

        self.damage = damage
        self.bullet_list = arcade.SpriteList()

        self.face_direction = FaceDirection.RIGHT

        self.idle_texture = arcade.load_texture('player/idle/idle-4.png')
        self.texture = self.idle_texture

        self.walk_textures = []
        self.run_textures = []
        self.climb_textures = []
        self.jump_forward_textures = []
        self.jump_backward_textures = []
        self.is_walking = self.is_running = self.is_climbing = self.is_prepare_shooting = self.is_jumping = False
        self.is_jumping_vertical = self.is_jumping_backward = self.is_jumping_forward = False
        self.is_hurt = False
        self.can_shoot = True
        self.was_climbing = False
        self.jump_horizontal_speed = 0
        self.is_raised_package = True

        for i in range(1, 17):
            texture = arcade.load_texture(f'player/walk/walk-{i}.png')
            self.walk_textures.append(texture)

        for i in range(1, 9):
            texture = arcade.load_texture(f'player/run/run-{i}.png')
            self.run_textures.append(texture)

        for i in range(1, 7):
            texture = arcade.load_texture(f'player/climb/climb-{i}.png')
            self.climb_textures.append(texture)

        for i in range(1, 4):
            texture = arcade.load_texture(f'player/jump/jump-{i}.png')
            self.jump_forward_textures.append(texture)

        for i in range(1, 7):
            texture = arcade.load_texture(f'player/back-jump/back-jump-{i}.png')
            self.jump_backward_textures.append(texture)

        self.prepare_shooting_texture = arcade.load_texture('player/shoot/shoot.png')

        self.jump_vertical_texture = arcade.load_texture('player/back-jump/back-jump-5.png')

        self.hurt_texture = arcade.load_texture('player/hurt/hurt.png')

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1
        self.hurt_timer = 0
        self.hurt_animation_time = 0.3
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1.0
        self.is_check_hazards = False
        self.hazards_check_interval = 0.5
        self.hazards_check_timer = 0

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_hurt:
            self.texture = self.hurt_texture
            return
        elif self.is_climbing:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.climb_textures):
                    self.current_texture = 0
                self.texture = self.climb_textures[self.current_texture]
        elif self.is_jumping_backward:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.jump_backward_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.jump_backward_textures[self.current_texture]
                elif self.face_direction == FaceDirection.LEFT:
                    self.texture = self.jump_backward_textures[self.current_texture].flip_horizontally()
        elif self.is_jumping_forward:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.jump_forward_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.jump_forward_textures[self.current_texture]
                elif self.face_direction == FaceDirection.LEFT:
                    self.texture = self.jump_forward_textures[self.current_texture].flip_horizontally()
        elif self.is_jumping_vertical:
            if self.face_direction == FaceDirection.RIGHT:
                self.texture = self.jump_vertical_texture
            elif self.face_direction == FaceDirection.LEFT:
                self.texture = self.jump_vertical_texture.flip_horizontally()
        elif self.is_prepare_shooting:
            if self.face_direction == FaceDirection.RIGHT:
                self.texture = self.prepare_shooting_texture
            elif self.face_direction == FaceDirection.LEFT:
                self.texture = self.prepare_shooting_texture.flip_horizontally()
        elif self.is_walking:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.walk_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.walk_textures[self.current_texture]
                elif self.face_direction == FaceDirection.LEFT:
                    self.texture = self.walk_textures[self.current_texture].flip_horizontally()
        elif self.is_running:
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
        else:
            if self.face_direction == FaceDirection.RIGHT:
                self.texture = self.idle_texture
            elif self.face_direction == FaceDirection.LEFT:
                self.texture = self.idle_texture.flip_horizontally()