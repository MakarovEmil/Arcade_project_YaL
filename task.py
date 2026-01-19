import arcade
import enum
import random
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, \
    UIMessageBox  # Это разные виджеты
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from pyglet.graphics import Batch
from arcade.camera import Camera2D

SCREEN_W = 1500
SCREEN_H = 1000
SCREEN_TITLE = "Аркадный Бегун"
GRAVITY = 7
JUMP_SPEED = 40
LADDER_SPEED = 3

CAMERA_LERP = 0.12
TILE_SIZE = 70
WORLD_W = TILE_SIZE * 53
WORLD_H = TILE_SIZE * 28

COYOTE_TIME = 0.08
JUMP_BUFFER = 0.12
MAX_JUMPS = 1   #Добавить двойной прыжок
JUMP_BACKWARD_SPEED = 8
JUMP_FORWARD_SPEED = 8




class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_texture = arcade.load_texture('buildings-bg.png')

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()
        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        name_of_game = UILabel(text="КУРЬЕР ХАОСА",
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.box_layout.add(name_of_game)

        description_text = UITextArea(text="Игра в стиле run and gun.\nМножество режимов игры.",
                               width=250,
                               height=50,
                               font_size=14)
        self.box_layout.add(description_text)

        authorization_button = UIFlatButton(text="Авторизоваться", width=200, height=50, color=arcade.color.BLUE)
        authorization_button.on_click = self.authorization
        self.box_layout.add(authorization_button)

        registration_button = UIFlatButton(text="Регистрация", width=200, height=50, color=arcade.color.BLUE)
        registration_button.on_click = self.registration
        self.box_layout.add(registration_button)

    def authorization(self, event):
        pass

    def registration(self, event):
        pass

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.background_texture, arcade.rect.XYWH(self.window.width // 2,
                                                                           self.window.height // 2,
                                                                           self.window.width,
                                                                           self.window.height))
        self.manager.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            game_view = GameView()
            self.window.show_view(game_view)


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK) #Добавить фон и музыку

        self.world_camera = Camera2D(
            viewport=arcade.rect.XYWH(SCREEN_W // 2, SCREEN_H // 2, SCREEN_W, SCREEN_H),
            position=(SCREEN_W // 2, SCREEN_H // 2)
        )
        self.gui_camera = Camera2D(
            viewport=arcade.rect.XYWH(SCREEN_W // 2, SCREEN_H // 2, SCREEN_W, SCREEN_H),
            position=(SCREEN_W // 2, SCREEN_H // 2)
        )

        self.player = None
        self.player_list = arcade.SpriteList()

        self.engine = None

        self.left = self.right = self.up = self.down = False
        self.jump_pressed = self.is_ctrl_pressed = self.is_x_pressed = self.is_z_pressed = self.is_e_pressed = False
        self.was_e_pressed = False
        self.stable_on_ladder = False
        self.stable_grounded = False
        self.state_counter = 0

        self.ladder_counter = 0
        self.ground_counter = 0

        self.jump_buffer_timer = 0.0
        self.time_since_ground = 999.0
        self.jumps_left = MAX_JUMPS

        self.score = 0
        self.batch = Batch()
        self.text_info = arcade.Text("WASD/стрелки — ходьба/лестницы • SPACE — прыжок",
                                     16, 16, arcade.color.BLACK, 14, batch=self.batch)

        self.setup()

    def setup(self):
        self.player_list.clear()
        self.player = Player()
        self.player_list.append(self.player)

        self.tile_map = arcade.load_tilemap(
            'norm_map.tmx',
            scaling=1)

        self.walls = self.tile_map.sprite_lists['Collisions']
        self.walls.use_spatial_hash = True
        self.platforms = self.tile_map.sprite_lists['Moving platforms']
        self.ladders = self.tile_map.sprite_lists['libres']
        self.hazards = self.tile_map.sprite_lists['hassasts']
        self.main = self.tile_map.sprite_lists['Main']
        self.spawn_layer = self.tile_map.sprite_lists['Spawn Layer']

        self.valid_spawn_positions = []
        for tile_sprite in self.spawn_layer:
            spawn_x = tile_sprite.center_x
            spawn_y = tile_sprite.top
            self.valid_spawn_positions.append((spawn_x, spawn_y))



        self.engine = arcade.PhysicsEnginePlatformer(
            player_sprite=self.player,
            gravity_constant=GRAVITY,
            walls=self.walls,
            platforms=self.platforms,
            ladders=self.ladders
        )

        self.jump_buffer_timer = 0
        self.time_since_ground = 999.0
        self.jumps_left = MAX_JUMPS

        self.stable_on_ladder = False
        self.stable_grounded = False
        self.state_counter = 0

        self.ladder_counter = 0
        self.ground_counter = 0

        self.reload_timer = 0
        self.reload_time = 0.5

        self.enemy_turet_list = arcade.SpriteList(use_spatial_hash=True)
        for _ in range(1):
            center_x, center_y = self.get_valid_spawn_positions()
            enemy = Enemy_turret(center_x, center_y)
            enemy.player_reference = self.player
            enemy.wall_list = self.walls
            self.enemy_turet_list.append(enemy)

        self.enemy_swordsman_list = arcade.SpriteList(use_spatial_hash=True)
        for _ in range(1):
            center_x, center_y = self.get_valid_spawn_positions()
            enemy = Enemy_swordsman(center_x, center_y)
            enemy.player_reference = self.player
            enemy.game_view = self
            enemy.engine = arcade.PhysicsEnginePlatformer(
                player_sprite=enemy,
                gravity_constant=1,
                walls=self.walls,
                platforms=None,
                ladders=None
            )
            self.enemy_swordsman_list.append(enemy)

        self.package_list = arcade.SpriteList()
        self.package = Package(self.player.center_x, self.player.center_y, 100)
        self.package_engine = arcade.PhysicsEnginePlatformer(
                player_sprite=self.package,
                gravity_constant=5,
                walls=self.walls,
                platforms=None,
                ladders=None
            )
        self.package_list.append(self.package)

    def get_valid_spawn_positions(self):
        return random.choice(self.valid_spawn_positions)

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        self.main.draw()
        self.walls.draw()
        self.platforms.draw()
        self.ladders.draw()
        self.player_list.draw()
        self.package_list.draw()
        self.player.bullet_list.draw()
        self.enemy_turet_list.draw()
        self.enemy_swordsman_list.draw()
        for enemy in self.enemy_turet_list:
            enemy.bullet_list.draw()
        for enemy in self.enemy_swordsman_list:
            arcade.draw_point(enemy.check_point.center_x, enemy.check_point.center_y, arcade.color.BLACK, 10)
            arcade.draw_line(enemy.x, enemy.y, enemy.test_gap_line_x, enemy.test_gap_line_y, arcade.color.BLACK)

        self.gui_camera.use()
        self.batch.draw()



    def on_update(self, delta_time):

        # ПРОВЕРКА СМЕРТИ ИГРОКА
        if self.player.current_health <= 0:
            self.player.current_health = self.player.health
            self.player.center_x, self.player.center_y = self.player.spawn_point


        #АКТИВНОСТЬ ИГРОКА

        current_on_ladder = self.engine.is_on_ladder()
        current_grounded = self.engine.can_jump(y_distance=6)

        if (current_on_ladder != self.stable_on_ladder or
                current_grounded != self.stable_grounded):
            self.state_counter += 1
            if self.state_counter >= 3:
                self.stable_on_ladder = current_on_ladder
                self.stable_grounded = current_grounded
                self.state_counter = 0
        else:
            self.state_counter = 0

        on_ladder = self.stable_on_ladder
        grounded = self.stable_grounded

        #Состояние игрока
        self.reset_all_states()
        if on_ladder and (self.up or self.down):
            self.player.is_climbing = True
        elif not on_ladder and not grounded:
            self.player.is_jumping_vertical = True
        elif self.is_ctrl_pressed and (self.left or self.right):
            self.player.is_running = True
        elif not self.is_ctrl_pressed and (self.left or self.right):
            self.player.is_walking = True
        elif self.is_x_pressed:
            self.player.is_prepare_shooting = True


        # Лестницы
        if self.player.is_climbing:
            if self.up and not self.down:
                self.player.change_y = LADDER_SPEED
            elif self.down and not self.up:
                self.player.change_y = -LADDER_SPEED
        else:
            self.player.change_y = 0

        # Прыжок
        if grounded:
            self.time_since_ground = 0
            self.jumps_left = MAX_JUMPS
            self.player.is_jumping_forward = False
            self.player.is_jumping_backward = False
            self.player.is_jumping_vertical = False
            self.player.is_jumping = False
            self.player.jump_horizontal_speed = 0
        else:
            self.time_since_ground += delta_time

        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= delta_time

        want_jump = (self.jump_pressed or (self.jump_buffer_timer > 0)) and not on_ladder

        if want_jump:
            can_coyote = (self.time_since_ground <= COYOTE_TIME)
            if grounded or can_coyote:
                jumping_forward = False
                jumping_backward = False

                any_horizontal = self.left or self.right

                if any_horizontal:
                    current_face_direction = self.player.face_direction

                    if current_face_direction == FaceDirection.RIGHT:
                        if self.right:
                            jumping_forward = True
                        elif self.left:
                            jumping_backward = True
                    else:
                        if self.left:
                            jumping_forward = True
                        elif self.right:
                            jumping_backward = True

                if jumping_forward:
                    self.player.is_jumping_forward = True
                    self.player.is_jumping = True
                elif jumping_backward:
                    self.player.is_jumping_backward = True
                    self.player.is_jumping = True
                else:
                    self.player.is_jumping_vertical = True
                    self.player.is_jumping = True

                if self.player.is_jumping_forward:
                    if self.player.face_direction == FaceDirection.RIGHT:
                        self.player.jump_horizontal_speed = JUMP_FORWARD_SPEED
                    else:
                        self.player.jump_horizontal_speed = -JUMP_FORWARD_SPEED
                elif self.player.is_jumping_backward:
                    if self.player.face_direction == FaceDirection.RIGHT:
                        self.player.jump_horizontal_speed = -JUMP_BACKWARD_SPEED
                    else:
                        self.player.jump_horizontal_speed = JUMP_BACKWARD_SPEED
                else:
                    self.player.jump_horizontal_speed = 0

                self.engine.jump(JUMP_SPEED)
                self.jump_buffer_timer = 0


        # Выстрел
        self.reload_timer -= delta_time
        if (self.player.can_shoot and self.is_z_pressed and self.is_x_pressed and self.player.is_prepare_shooting
                and self.reload_timer <= 0):
            bullet = Bullet(self.player.center_x, self.player.center_y, self.player.face_direction, 45, 20,
                            damage=self.player.damage)
            self.player.bullet_list.append(bullet)
            self.player.can_shoot = False
            self.reload_timer = self.reload_time
            #self.player.center_x -= 10 #Доделать отдачу или убрать
        if not self.is_z_pressed:
            self.player.can_shoot = True

        # Бег или ходьба
        move = 0

        if not self.player.is_jumping:
            if self.left and not self.right:
                if self.player.is_walking:
                    move = -self.player.walk_speed
                    self.player.face_direction = FaceDirection.LEFT
                elif self.player.is_running:
                    move = -self.player.run_speed
                    self.player.face_direction = FaceDirection.LEFT
            elif self.right and not self.left:
                if self.player.is_walking:
                    move = self.player.walk_speed
                    self.player.face_direction = FaceDirection.RIGHT
                elif self.player.is_running:
                    move = self.player.run_speed
                    self.player.face_direction = FaceDirection.RIGHT

        if self.player.is_jumping:
            self.player.change_x = self.player.jump_horizontal_speed + move
        else:
            self.player.change_x = move

        if move == 0:
            self.player.is_walking = False
            self.player.is_running = False

        #ОБНОВЛЕНИЕ СОСТОЯНИЯ ПОСЫЛКИ И ОБНОВЛЕНИЕ ТАЙМЕРА
        if self.package.abandoned_timer > 0:
            self.package.abandoned_timer -= delta_time
        else:
            self.package.can_be_abandoned = True


        print(f'raised:{self.package.is_raised}, lies:{self.package.is_lies}, abandoned:{self.package.is_abandoned}')
        print(f'e_pressed:{self.is_e_pressed}')
        print(f'can_be_abandoned:{self.package.can_be_abandoned}')
        print(f'timer:{self.package.abandoned_timer}')
        if self.is_e_pressed and not self.was_e_pressed:
            if self.package.can_be_abandoned:
                self.package.abandoned_timer = self.package.abandoned_time
                self.package.can_be_abandoned = False
                was_raised = self.package.is_raised
                was_abandoned = self.package.is_abandoned
                was_lies = self.package.is_lies
                self.package.is_abandoned = self.package.is_raised = self.package.is_lies = False
                if was_raised:
                    if self.left or self.right:
                        self.package.is_abandoned = True
                        self.package.change_y = self.package.y_speed
                        if self.left and not self.right:
                            self.package.change_x = -self.package.x_speed
                        elif self.right and not self.left:
                            self.package.change_x = self.package.x_speed
                    else:
                        self.package.is_lies = True
                elif (abs(self.player.center_x - self.package.center_x) <= self.package.raised_radius and
                      abs(self.player.center_y - self.package.center_y) < 50
                      and was_lies and not was_abandoned):
                    self.package.is_raised = True
        self.was_e_pressed = self.is_e_pressed




        #ПРОВЕРКА СТОЛКНОВЕНИЙ

        for hazard in self.hazards:
            if (abs(hazard.top - self.player.bottom) < 10 and
                    self.player.center_x - 10 < hazard.center_x < self.player.center_x + 10):
                if not self.player.invincible:
                    self.player.current_health -= 3
                    self.player.is_hurt = True
                    self.player.hurt_timer = 0
                    self.player.invincible = True
                    self.player.invincible_timer = 1.0


        # ОБНОВЛЕНИЕ ВРАГОВ И ПУЛЬ
        for enemy in self.enemy_turet_list:
            enemy.player_reference = self.player

            bullets_hit = arcade.check_for_collision_with_list(self.player, enemy.bullet_list)
            if bullets_hit and not self.player.invincible:
                self.player.is_hurt = True
                self.player.hurt_timer = 0
                self.player.invincible = True
                self.player.invincible_timer = 1.0

                for bullet in bullets_hit:
                    self.player.current_health -= bullet.damage
                    bullet.remove_from_sprite_lists()

            bullets_hit = arcade.check_for_collision_with_list(enemy, self.player.bullet_list)
            if bullets_hit:
                for bullet in bullets_hit:
                    enemy.health -= bullet.damage
                    bullet.remove_from_sprite_lists()

            if enemy.health <= 0:
                enemy.remove_from_sprite_lists()

            enemy.bullet_list.update()
            enemy.bullet_list.update_animation()
        for enemy in self.enemy_swordsman_list:
            enemy.player_reference = self.player
            bullets_hit = arcade.check_for_collision_with_list(enemy, self.player.bullet_list)
            if bullets_hit:
                for bullet in bullets_hit:
                    enemy.current_health -= bullet.damage
                    bullet.remove_from_sprite_lists()
            if enemy.current_health <= 0:
                enemy.remove_from_sprite_lists()

        # ОБНОВЛЕНИЕ ТАЙМЕРОВ ИГРОКА
        if self.player.is_hurt:
            self.player.hurt_timer += delta_time
            if self.player.hurt_timer >= self.player.hurt_animation_time:
                self.player.is_hurt = False

        if self.player.invincible:
            self.player.invincible_timer -= delta_time
            if self.player.invincible_timer <= 0:
                self.player.invincible = False

        # ОБНОВЛЕНИЕ ФИЗИКИ
        self.engine.update()

        if self.package.is_lies or self.package.is_abandoned:
            self.package_engine.update()
            if self.package_engine.can_jump() and self.package.is_abandoned:
                self.package.is_abandoned = False
                self.package.is_lies = True
                self.package.is_raised = False
                self.package.change_x = 0
                self.package.change_y = 0
        elif self.package.is_raised:
            self.package.center_x = self.player.center_x
            self.package.center_y = self.player.center_y


        # АНИМАЦИИ
        self.player.update_animation(delta_time)
        self.enemy_turet_list.update_animation(delta_time)
        self.enemy_turet_list.update()
        self.enemy_swordsman_list.update_animation(delta_time)
        self.enemy_swordsman_list.update()
        self.player.bullet_list.update()
        self.player.bullet_list.update_animation()

        #КАМЕРА
        target = (self.player.center_x, self.player.center_y)
        cx, cy = self.world_camera.position
        smooth = (cx + (target[0] - cx) * CAMERA_LERP,
                  cy + (target[1] - cy) * CAMERA_LERP)

        half_w = self.world_camera.viewport_width / 2
        half_h = self.world_camera.viewport_height / 2
        cam_x = max(half_w, min(WORLD_W - half_w, smooth[0]))
        cam_y = max(half_h, min(WORLD_H - half_h, smooth[1]))

        self.world_camera.position = (cam_x, cam_y)
        self.gui_camera.position = (SCREEN_W / 2, SCREEN_H / 2)

        #ОБНОВЛЕНИЕ ТЕКСТОВЫХ ДАННЫХ НА ЭКРАНЕ
        self.text_health = arcade.Text(f"Здоровье: {self.player.current_health}",
                                      16, SCREEN_H - 36, arcade.color.BLACK,
                                      20, batch=self.batch)

    def reset_all_states(self):
        self.player.is_walking = False
        self.player.is_running = False
        self.player.is_climbing = False
        self.player.is_prepare_shooting = False

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            pause_view = PauseView(self)
            self.window.show_view(pause_view)
        if key == arcade.key.SPACE:
            self.jump_pressed = True
            self.jump_buffer_timer = JUMP_BUFFER
        if key in (arcade.key.LCTRL, arcade.key.RCTRL):
            self.is_ctrl_pressed = True
        if modifiers & arcade.key.MOD_CTRL:
            self.is_ctrl_pressed = True
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right = True
        if key in (arcade.key.UP, arcade.key.W):
            self.up = True
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.down = True
        if key == arcade.key.X:
            self.is_x_pressed = True
        if key == arcade.key.Z:
            self.is_z_pressed = True
        if key == arcade.key.E:
            self.is_e_pressed = True

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LCTRL, arcade.key.RCTRL):
            self.is_ctrl_pressed = False
        if not modifiers & arcade.key.MOD_CTRL:
            self.is_ctrl_pressed = False
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right = False
        if key in (arcade.key.UP, arcade.key.W):
            self.up = False
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.down = False
        if key == arcade.key.SPACE:
            self.jump_pressed = False
            if self.player.change_y > 0:
                self.player.change_y *= 0.45
        if key == arcade.key.X:
            self.is_x_pressed = False
        if key == arcade.key.Z:
            self.is_z_pressed = False
        if key == arcade.key.E:
            self.is_e_pressed = False


class FaceDirection(enum.Enum):
    LEFT = 0
    RIGHT = 1


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__('player/idle/idle-4.png', scale=2)
        self.center_x = 280
        self.center_y = 140

        self.walk_speed = 2
        self.run_speed = 5

        self.health = self.current_health = 300
        self.spawn_point = (280, 140)
        self.damage = 100
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

class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, direction, dif_x, dif_y, speed=600, damage=10):
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

        self.textures = []
        for i in range(1, 4):
            texture = arcade.load_texture(f'misc/shot/shot-{i}.png')
            self.textures.append(texture)

    def update(self, delta_time):
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


class Enemy_turret(arcade.Sprite):
    def __init__(self, center_x, bottom_y, damage=10):
        super().__init__('misc/turret/turret-1.png', scale=4)
        self.center_x = center_x
        self.center_y = bottom_y + self.height // 2
        self.damage = damage
        self.health = 50
        self.detection_radius = 9 * TILE_SIZE
        self.player_reference = None
        self.wall_list = None
        self.state = 'idle'
        self.attack_direction = FaceDirection.RIGHT
        self.idle_textures = []
        for i in range(1, 7):
            texture = arcade.load_texture(f'misc/turret/turret-{i}.png')
            self.idle_textures.append(texture)

        self.attack_texture = arcade.load_texture('misc/turret/turret-5.png')

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

        self.reload_timer = 0
        self.reload_time = 2.0

        self.check_timer = 0
        self.check_interval = 1.5
        self.can_see_player_cash = False

        self.bullet_list = arcade.SpriteList()

    def update_animation(self, delta_time: float = 1 / 60):
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
        distance = arcade.get_distance_between_sprites(self, self.player_reference)
        if distance <= self.detection_radius and abs(self.player_reference.center_y - self.center_y) <= 70:
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
                                    damage=self.damage)
                    self.bullet_list.append(bullet)
                    self.reload_timer = self.reload_time
        else:
            self.state = 'idle'

    def can_see_player(self):
        return arcade.has_line_of_sight(observer=(self.center_x, self.center_y),
                                        target=(self.player_reference.center_x, self.player_reference.center_y),
                                        walls=self.wall_list)

class Enemy_swordsman(arcade.Sprite):
    def __init__(self, center_x, bottom_y, damage=10):
        super().__init__('Free Swordsman Character/Animations/Idle/Idle_000.png', scale=0.2)
        self.center_x = center_x
        self.center_y = bottom_y + self.height // 2
        self.damage = damage
        self.health = self.current_health = 100
        self.detection_radius = 13 * TILE_SIZE
        self.height_dif = 280
        self.radius_of_attack = 1 * TILE_SIZE
        self.player_reference = None
        self.game_view = None
        self.engine = None
        self.face_direction = FaceDirection.RIGHT

        self.check_point = arcade.Sprite()
        self.check_point.width = self.check_point.height = 4
        self.check_point.visible = False

        self.check_timer = 0
        self.check_interval = 2.5

        self.has_jumped = False

        self.max_height_of_wall = 3 * TILE_SIZE
        self.max_width_of_gap = 5 * TILE_SIZE

        self.state = 'idle'
        self.jump_type = None

        self.speed = 3
        self.wall_horizontal_jump_power = 10
        self.gap_horizontal_jump_power = 15
        self.jump_speed = 25

        self.idle_texture = arcade.load_texture(f'Free Swordsman Character/Animations/Idle/Idle_000.png')
        self.texture = self.idle_texture

        self.run_textures = []
        for i in range(10):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Run/Run_00{i}.png')
            self.run_textures.append(texture)

        self.attack_1_textures = []
        for i in range(10):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Attack/Attack_00{i}.png')
            self.attack_1_textures.append(texture)

        self.attack_2_textures = []
        for i in range(9):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Attack 2/Attack 2_00{i}.png')
            self.attack_2_textures.append(texture)

        self.jumping_textures = []
        for i in range(10):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Jump Start/Jump Start_00{i}.png')
            self.jumping_textures.append(texture)

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

        self.reload_time = 1.5
        self.reload_timer = 1.5
        self.can_attack = False
        self.jump_timer = 0

        self.test_gap_line_x = self.test_gap_line_y = self.x = self.y = 0

    def update_animation(self, delta_time: float = 1 / 60):
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
                else:  # 'attack_2'
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
        for hazard in self.game_view.hazards:
            if (abs(hazard.top - self.bottom) < 10 and
                    self.center_x - 10 < hazard.center_x < self.center_x + 10):
                self.current_health -= 1
        self.reload_timer -= delta_time
        if self.reload_timer <= 0:
            self.can_attack = True
            self.reload_timer = self.reload_time
        self.check_timer += delta_time
        distance = arcade.get_distance_between_sprites(self, self.player_reference)
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
        if distance <= self.detection_radius and abs(self.player_reference.center_y - self.center_y) <= self.height_dif:
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

        elif self.state == 'jumping':
            self.jump_timer += delta_time
            if not self.has_jumped:
                self.execute_jump(direction)
            if self.jump_timer > 0.4:
                if self.engine.can_jump():
                    self.state = 'running'
                    self.has_jumped = False
                    self.jump_timer = 0
        elif self.state == 'running':
            if direction != 0:
                self.face_direction = FaceDirection.RIGHT if direction == 1 else FaceDirection.LEFT
                self.change_x = self.speed * direction
            else:
                self.change_x = 0
        self.engine.update()

    def define_state(self, direction):
        if self.state == 'jumping':
            return
        is_there_a_wall = arcade.has_line_of_sight(observer=(self.center_x, self.center_y),
                                                   target=(self.center_x + direction * 70, self.center_y),
                                                   walls=self.game_view.walls)
        if not is_there_a_wall:
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
        self.check_point.center_x = self.center_x + direction * 40
        self.check_point.center_y = self.bottom - 10
        if arcade.check_for_collision_with_list(self.check_point, self.game_view.hazards):
            if self.current_health <= self.health * 0.33:
                self.state = 'idle'
                return
            else:
                self.state = 'running'
                return

        is_there_a_gap = arcade.has_line_of_sight(observer=(self.center_x, self.center_y),
                                                  target=(self.center_x + direction * 210, self.bottom - 10),
                                                  walls=self.game_view.walls)
        self.test_gap_line_x = self.center_x + direction * 210
        self.test_gap_line_y = self.bottom - 10
        self.x = self.center_x
        self.y = self.center_y
        if is_there_a_gap:
            self.check_point.center_x = self.center_x + direction * self.max_width_of_gap + 70
            self.check_point.center_y = self.bottom - 10
            if not arcade.check_for_collision_with_list(self.check_point, self.game_view.walls):
                self.state = 'jumping'
                self.jump_type = 'gap'
                return
            else:
                self.state = 'idle'
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


class Package(arcade.Sprite):
    def __init__(self, center_x, center_y, health):
        super().__init__('package_texture.png', scale=0.1)
        self.center_x = center_x
        self.center_y = center_y
        self.health = health
        self.is_lies = self.is_abandoned = False
        self.is_raised = True
        self.can_be_abandoned = False
        self.x_speed = 25
        self.y_speed = 50
        self.raised_radius = TILE_SIZE * 0.8
        self.abandoned_time = 2.0
        self.abandoned_timer = 2.0


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.batch = Batch()
        self.pause_text = arcade.Text("Пауза", self.window.width / 2, self.window.height / 2,
                                      arcade.color.WHITE, font_size=40, anchor_x="center", batch=self.batch)
        self.space_text = arcade.Text("Нажми SPACE, чтобы продолжить", self.window.width / 2,
                                      self.window.height / 2 - 50,
                                      arcade.color.WHITE, font_size=20, anchor_x="center", batch=self.batch)

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.window.show_view(self.game_view)


if __name__ == "__main__":
    window = arcade.Window(SCREEN_W, SCREEN_H, SCREEN_TITLE)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()

