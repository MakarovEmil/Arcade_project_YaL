import arcade
from pyglet.graphics import Batch
from arcade.camera import Camera2D
from Player import Player
from Enemy_swordsman import Enemy_swordsman
from Enemy_turret import Enemy_turret
from Package import Package
import random
from End_game_view import End_game_view
from FaceDirection import FaceDirection
from Bullet import Bullet
from pause import PauseView
from arcade.particles import FadeParticle, Emitter, EmitBurst
SMOKE_TEX = arcade.make_soft_circle_texture(20, arcade.color.LIGHT_GRAY, 255, 80)
PUFF_TEX = arcade.make_soft_circle_texture(12, arcade.color.WHITE, 255, 50)

SCREEN_W = 1500
SCREEN_H = 1000
SCREEN_TITLE = "Курьер Хаоса"
GRAVITY = 7

CAMERA_LERP = 0.12
TILE_SIZE = 70
WORLD_W = TILE_SIZE * 200
WORLD_H = TILE_SIZE * 60

COYOTE_TIME = 0.08
JUMP_BUFFER = 0.12
MAX_JUMPS = 1



class GameView(arcade.View):
    def __init__(self, window, username, modifiers, player_damage, player_health):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
        self.background_music = arcade.load_sound("Sounds/cyber city 2-b.mp3")
        self.shot_sound = arcade.load_sound("Sounds/beam.ogg")

        self.modifiers = modifiers
        self.reward_for_kills = 0
        self.total_time_of_game = 0
        self.username = username
        self.window = window

        self.greed_mod = 'Жажда наживы' in self.modifiers


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

        self.batch = Batch()
        self.text_info = arcade.Text("WASD/стрелки — ходьба/лестницы • SPACE — прыжок",
                                     16, 16, arcade.color.BLACK, 14, batch=self.batch)
        self.particle_effects = []

        self.setup(player_damage, player_health)

    def setup(self, player_damage, player_health):
        self.player_list.clear()
        self.player = Player(damage=player_damage, health=player_health)
        if 'Неуклюжесть' in self.modifiers:
            self.player.ladder_speed *= 0.7
            self.player.walk_speed *= 0.5
            self.player.run_speed *= 0.5
            self.player.jump_forward_speed *= 0.7
            self.player.jump_backward_speed *= 0.7
            self.player.jump_speed *= 1.4
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
        self.package_layer = self.tile_map.sprite_lists['Package_layer']

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
        self.distance_check_timer = 0

        self.idle_texture_sword = arcade.load_texture(f'Free Swordsman Character/Animations/Idle/Idle_000.png')

        self.run_textures_sword = []
        for i in range(10):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Run/Run_00{i}.png')
            self.run_textures_sword.append(texture)

        self.attack_1_textures_sword = []
        for i in range(10):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Attack/Attack_00{i}.png')
            self.attack_1_textures_sword.append(texture)

        self.attack_2_textures_sword = []
        for i in range(9):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Attack 2/Attack 2_00{i}.png')
            self.attack_2_textures_sword.append(texture)

        self.jumping_textures_sword = []
        for i in range(10):
            texture = arcade.load_texture(f'Free Swordsman Character/Animations/Jump Start/Jump Start_00{i}.png')
            self.jumping_textures_sword.append(texture)

        self.idle_textures_tur = []
        for i in range(1, 7):
            texture = arcade.load_texture(f'misc/turret/turret-{i}.png')
            self.idle_textures_tur.append(texture)

        self.bullet_textures = []
        for i in range(1, 4):
            texture = arcade.load_texture(f'misc/shot/shot-{i}.png')
            self.bullet_textures.append(texture)

        self.attack_texture_tur = arcade.load_texture('misc/turret/turret-5.png')

        self.enemy_turet_list = arcade.SpriteList(use_spatial_hash=True)
        for _ in range(50):
            center_x, center_y = self.get_valid_spawn_positions()
            damage, health = int(self.player.health * 0.5), int(self.player.health * 1.3)
            enemy = Enemy_turret(center_x, center_y, damage=damage, health=health)
            enemy.idle_textures = self.idle_textures_tur
            enemy.attack_texture = self.attack_texture_tur
            enemy.bullet_textures = self.bullet_textures
            if 'Толстокожие враги' in self.modifiers:
                enemy.health *= 2
                enemy.reward_for_kill *= 1.2
            if 'Скорострелы' in self.modifiers:
                enemy.damage *= 0.7
                enemy.reload_time //= 2
            enemy.player_reference = self.player
            enemy.wall_list = self.walls
            self.enemy_turet_list.append(enemy)

        self.enemy_swordsman_list = arcade.SpriteList(use_spatial_hash=True)
        for _ in range(50):
            center_x, center_y = self.get_valid_spawn_positions()
            damage, health = int(self.player.health * 0.3), int(self.player.health * 1.1)
            enemy = Enemy_swordsman(center_x, center_y, damage=damage, health=health)
            enemy.idle_texture = self.idle_texture_sword
            enemy.run_textures = self.run_textures_sword
            enemy.attack_1_textures = self.attack_1_textures_sword
            enemy.attack_2_textures = self.attack_2_textures_sword
            enemy.jumping_textures = self.jumping_textures_sword
            if 'Толстокожие враги' in self.modifiers:
                enemy.health *= 2
                enemy.current_health *= 2
                enemy.reward_for_kill *= 1.2
            if 'Скорострелы' in self.modifiers:
                enemy.damage *= 0.7
                enemy.reload_time //= 2
                enemy.reload_timer //= 2
            if 'Бегуны' in self.modifiers:
                enemy.speed *= 1.5
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

        self.text_health = arcade.Text("", 16, SCREEN_H - 36, arcade.color.BLACK, 20, batch=self.batch)
        self.text_package_health = arcade.Text("", 16, SCREEN_H - 72, arcade.color.BLACK,
                                               20, batch=self.batch)
        self.text_total_game_time = arcade.Text("", 16, SCREEN_H - 108, arcade.color.BLACK,
                                                20, batch=self.batch)
        self.text_reward_for_kills = arcade.Text("", 16, SCREEN_H - 144, arcade.color.BLACK,
                                                 20, batch=self.batch)

    def create_spawn_effect(self, x, y):
        spark_tex = arcade.make_soft_circle_texture(10, arcade.color.PASTEL_YELLOW)
        explosion = Emitter(
            center_xy=(x, y),
            emit_controller=EmitBurst(80),
            particle_factory=lambda e: FadeParticle(
                filename_or_texture=spark_tex,
                change_xy=arcade.math.rand_in_circle((0.0, 0.0), 7.0),
                lifetime=random.uniform(0.5, 1.2),
                start_alpha=255,
                end_alpha=0,
                scale=random.uniform(0.5, 0.8),
            ),
        )

        self.particle_effects.append(explosion)

    def get_valid_spawn_positions(self):
        return random.choice(self.valid_spawn_positions)

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        self.main.draw()
        self.walls.draw()
        self.platforms.draw()
        self.ladders.draw()
        self.hazards.draw()
        self.player_list.draw()
        self.package_list.draw()
        self.player.bullet_list.draw()
        self.enemy_turet_list.draw()
        self.enemy_swordsman_list.draw()
        for enemy in self.enemy_turet_list:
            enemy.bullet_list.draw()
            enemy.batch.draw()
        for enemy in self.enemy_swordsman_list:
            enemy.batch.draw()
        if 'Туман' in self.modifiers:
            arcade.draw_rect_filled(arcade.rect.XYWH(WORLD_W // 2, WORLD_H // 2, WORLD_W, WORLD_H),
                                    (20, 20, 20, 200))
        for effect in self.particle_effects:
            effect.draw()

        self.gui_camera.use()
        self.batch.draw()

    def on_update(self, delta_time):
        if self.package.current_health <= 0:
            end_game_view = End_game_view(self.window, self.username, self.total_time_of_game, self.reward_for_kills,
                                          greed_mod=self.greed_mod, success=False)
            self.window.show_view(end_game_view)

        self.total_time_of_game += delta_time

        if arcade.check_for_collision_with_list(self.package, self.package_layer) and self.package.current_health > 0:
            end_game_view = End_game_view(self.window, self.username, self.total_time_of_game, self.reward_for_kills)
            self.window.show_view(end_game_view)
            return

        if self.player.current_health <= 0:
            if self.package.is_raised:
                self.package.is_lies = True
                self.package.is_abandoned = self.package.is_raised = False
                self.package.center_x, self.package.center_y = self.player.center_x, self.player.center_y
            self.player.center_x, self.player.center_y = self.player.spawn_point
            self.create_spawn_effect(self.player.center_x, self.player.center_y)
            self.player.current_health = self.player.health
            return

        for effect in self.particle_effects[:]:
            effect.update(delta_time)
            if effect.can_reap():
                self.particle_effects.remove(effect)

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

        self.reset_all_states()
        if on_ladder and (self.up or self.down):
            self.player.is_climbing = True

        elif on_ladder and (self.player.is_jumping_forward or self.player.is_jumping_backward):
            self.player.is_jumping_backward = False
            self.player.is_jumping_forward = False
            self.player.is_jumping_vertical = False
            self.player.is_jumping = False
        elif not on_ladder and not grounded:
            self.player.is_jumping_vertical = True
        elif self.is_ctrl_pressed and (self.left or self.right):
            self.player.is_running = True
        elif not self.is_ctrl_pressed and (self.left or self.right):
            self.player.is_walking = True
        elif self.is_x_pressed:
            self.player.is_prepare_shooting = True

        if self.player.is_climbing:
            if self.up and not self.down:
                self.player.change_y = self.player.ladder_speed
            elif self.down and not self.up:
                self.player.change_y = -self.player.ladder_speed
        else:
            self.player.change_y = 0

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
                        self.player.jump_horizontal_speed = self.player.jump_forward_speed
                    else:
                        self.player.jump_horizontal_speed = -self.player.jump_forward_speed
                elif self.player.is_jumping_backward:
                    if self.player.face_direction == FaceDirection.RIGHT:
                        self.player.jump_horizontal_speed = -self.player.jump_backward_speed
                    else:
                        self.player.jump_horizontal_speed = self.player.jump_backward_speed
                else:
                    self.player.jump_horizontal_speed = 0

                self.engine.jump(self.player.jump_speed)
                self.jump_buffer_timer = 0

        self.reload_timer -= delta_time
        if (self.player.can_shoot and self.is_z_pressed and self.is_x_pressed and self.player.is_prepare_shooting
                and self.reload_timer <= 0):
            bullet = Bullet(self.player.center_x, self.player.center_y, self.player.face_direction, 45, 20,
                            self.walls, damage=self.player.damage)
            bullet.textures = self.bullet_textures
            self.player.bullet_list.append(bullet)
            self.player.can_shoot = False
            self.reload_timer = self.reload_time
            self.shot_sound.play()
        if not self.is_z_pressed:
            self.player.can_shoot = True

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
        if self.package.abandoned_timer > 0:
            self.package.abandoned_timer -= delta_time
        else:
            self.package.can_be_abandoned = True
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
                      abs(self.player.center_y - self.package.center_y) < 80
                      and was_lies and not was_abandoned):
                    self.package.is_raised = True
        if not self.package.is_raised and not self.package.is_lies and not self.package.is_abandoned:
            self.package.is_lies = True
        self.was_e_pressed = self.is_e_pressed

        if self.player.is_check_hazards:
            self.player.is_check_hazards = False
            if arcade.check_for_collision_with_list(self.player, self.hazards):
                self.player.current_health -= 3
                if self.package.is_raised:
                    self.package.current_health -= 2
                self.player.is_hurt = True
                self.player.hurt_timer = 0

        all_bullets = arcade.SpriteList()
        for enemy in self.enemy_turet_list:
            if enemy.bullet_list:
                all_bullets.extend(enemy.bullet_list)
        if all_bullets:
            all_bullets.update()
            all_bullets.update_animation()
        bullets_hit = arcade.check_for_collision_with_list(self.player, all_bullets)
        if bullets_hit and not self.player.invincible:
            self.player.is_hurt = True
            self.player.hurt_timer = 0
            self.player.invincible = True
            self.player.invincible_timer = 1.0
            for bullet in bullets_hit:
                self.player.current_health -= bullet.damage
                if self.package.is_raised:
                    self.package.current_health -= bullet.damage * 0.4
                bullet.remove_from_sprite_lists()
        for enemy in self.enemy_turet_list:
            if enemy.is_visible:
                bullets_hit = arcade.check_for_collision_with_list(enemy, self.player.bullet_list)
                if bullets_hit:
                    for bullet in bullets_hit:
                        enemy.health -= bullet.damage
                        if enemy.health <= 0:
                            if self.greed_mod:
                                self.reward_for_kills += enemy.reward_for_kill * 1.5
                            else:
                                self.reward_for_kills += enemy.reward_for_kill
                        bullet.remove_from_sprite_lists()
                enemy.health_text.text = f'{enemy.health}'
                if enemy.health <= 0:
                    enemy.remove_from_sprite_lists()
        for enemy in self.enemy_swordsman_list:
            if enemy.is_visible:
                enemy.player_reference = self.player
                bullets_hit = arcade.check_for_collision_with_list(enemy, self.player.bullet_list)
                if bullets_hit:
                    for bullet in bullets_hit:
                        enemy.current_health -= bullet.damage
                        if enemy.current_health <= 0:
                            if self.greed_mod:
                                self.reward_for_kills += enemy.reward_for_kill * 1.5
                            else:
                                self.reward_for_kills += enemy.reward_for_kill
                        bullet.remove_from_sprite_lists()
                enemy.health_text.text = f'{enemy.current_health}'
                if enemy.current_health <= 0:
                    enemy.remove_from_sprite_lists()

        if self.player.is_hurt:
            self.player.hurt_timer += delta_time
            if self.player.hurt_timer >= self.player.hurt_animation_time:
                self.player.is_hurt = False
        if self.player.invincible:
            self.player.invincible_timer -= delta_time
            if self.player.invincible_timer <= 0:
                self.player.invincible = False
        self.player.hazards_check_timer += delta_time
        if self.player.hazards_check_timer >= self.player.hazards_check_interval:
            self.player.hazards_check_timer = 0
            self.player.is_check_hazards = True

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

        self.player.update_animation(delta_time)
        self.player.bullet_list.update()
        self.player.bullet_list.update_animation()
        self.distance_check_timer += delta_time
        if self.distance_check_timer >= 0.3:
            self.update_visible_enemies()
            self.distance_check_timer = 0
        self.enemy_turet_list.update_animation(delta_time)
        self.enemy_turet_list.update()
        self.enemy_swordsman_list.update_animation(delta_time)
        self.enemy_swordsman_list.update()

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

        self.text_health.text = f"Здоровье: {self.player.current_health:.2f}"
        self.text_package_health.text = f"Здоровье посылки: {self.package.current_health:.2f}"
        self.text_total_game_time.text = f"Время игры: {self.total_time_of_game:.2f}"
        self.text_reward_for_kills.text = f"Награда за врагов: {self.reward_for_kills:.2f}"

    def update_visible_enemies(self):
        vertical_threshold = 6 * TILE_SIZE
        horizontal_threshold = 20 * TILE_SIZE
        for enemy in self.enemy_turet_list:
            if (abs(enemy.center_y - self.player.center_y) <= vertical_threshold and
                    abs(enemy.center_x - self.player.center_x) <= horizontal_threshold):
                enemy.is_visible = True
            else:
                enemy.is_visible = False
        for enemy in self.enemy_swordsman_list:
            if (abs(enemy.center_y - self.player.center_y) <= vertical_threshold and
                    abs(enemy.center_x - self.player.center_x) <= horizontal_threshold):
                enemy.is_visible = True
            else:
                enemy.is_visible = False

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

    def on_show_view(self):
        self.backgound_player = self.background_music.play(loop=True, volume=0.1)

    def on_hide_view(self):
        arcade.stop_sound(self.backgound_player)
