import arcade
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


COYOTE_TIME = 0.08
JUMP_BUFFER = 0.12
MAX_JUMPS = 1      #Добавить двойной прыжок

CAMERA_LERP = 0.12
TILE_SIZE = 70


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

        self.world_camera = Camera2D()
        self.gui_camera = Camera2D()

        self.player = None
        self.player_list = arcade.SpriteList()

        self.engine = None

        self.left = self.right = self.up = self.down = self.jump_pressed = self.is_ctrl_pressed = False
        self.jump_buffer_timer = 0.0
        self.time_since_ground = 999.0
        self.jumps_left = MAX_JUMPS

        self.score = 0
        self.batch = Batch()
        self.text_info = arcade.Text("WASD/стрелки — ходьба/лестницы • SPACE — прыжок",
                                     16, 16, arcade.color.GRAY, 14, batch=self.batch)

        self.world_w = TILE_SIZE * 30
        self.world_h = TILE_SIZE * 28

        self.spawn_point = (280, 140)

        self.setup()

    def setup(self):
        self.player_list.clear()
        self.player = Player()
        self.player_list.append(self.player)

        self.tile_map = arcade.load_tilemap(
            'norm_map.tmx',
            scaling=1)

        self.walls = self.tile_map.sprite_lists['Collisions']
        self.platforms = self.tile_map.sprite_lists['Moving platforms']
        self.ladders = self.tile_map.sprite_lists['libres']
        self.hazards = self.tile_map.sprite_lists['hassasts']
        self.main = self.tile_map.sprite_lists['Main']

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

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        self.main.draw()
        self.walls.draw()
        self.platforms.draw()
        self.ladders.draw()
        self.hazards.draw()
        self.player_list.draw()

        self.gui_camera.use()
        self.batch.draw()



    def on_update(self, delta_time):
        #Состояние игрока
        on_ladder = self.engine.is_on_ladder()
        grounded = self.engine.can_jump(y_distance=6)
        if on_ladder and (self.up or self.down):
            self.player.is_climbing = True
            self.player.is_walking = False
            self.player.is_running = False
        elif not grounded and not on_ladder:
            self.player.is_walking = False
            self.player.is_climbing = False
            self.player.is_running = False
        elif self.is_ctrl_pressed and (self.left or self.right):
            self.player.is_walking = False
            self.player.is_climbing = False
            self.player.is_running = True
        elif not self.is_ctrl_pressed and (self.left or self.right):
            self.player.is_walking = True
            self.player.is_running = False
            self.player.is_climbing = False
        else:
            self.player.is_walking = False
            self.player.is_climbing = False
            self.player.is_running = False

        # Лестницы
        if self.player.is_climbing:
            if self.up and not self.down:
                self.player.change_y = LADDER_SPEED
            elif self.down and not self.up:
                self.player.change_y = -LADDER_SPEED
        else:
            self.player.change_y = 0

        #Прыжок
        if grounded:
            self.time_since_ground = 0
            self.jumps_left = MAX_JUMPS
        else:
            self.time_since_ground += delta_time

        # Учтём «запомненный» пробел
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= delta_time

        want_jump = self.jump_pressed or (self.jump_buffer_timer > 0)

        # Можно прыгать, если стоим на земле или в пределах койот-времени
        if want_jump:
            can_coyote = (self.time_since_ground <= COYOTE_TIME)
            if grounded or can_coyote:
                # Просим движок прыгнуть: он корректно задаст начальную вертикальную скорость
                self.engine.jump(JUMP_SPEED)
                self.jump_buffer_timer = 0

        # Бег или хотьба
        move = 0
        if self.left and not self.right:
            if self.player.is_walking:
                move = -self.player.walk_speed
            elif self.player.is_running:
                move = -self.player.run_speed
        elif self.right and not self.left:
            if self.player.is_walking:
                move = self.player.walk_speed
            elif self.player.is_running:
                move = self.player.run_speed
        self.player.change_x = move



        # Обновляем физику — движок сам двинет игрока и платформы
        self.engine.update()
        self.player.update_animation()

        if arcade.check_for_collision_with_list(self.player, self.hazards):
            # «Ау» -> респавн
            self.player.center_x, self.player.center_y = self.spawn_point
            self.player.change_x = self.player.change_y = 0
            self.time_since_ground = 999
            self.jumps_left = MAX_JUMPS

        # Камера — плавно к игроку и в рамках мира
        target = (self.player.center_x, self.player.center_y)
        cx, cy = self.world_camera.position
        smooth = (cx + (target[0] - cx) * CAMERA_LERP,
                  cy + (target[1] - cy) * CAMERA_LERP)

        half_w = self.world_camera.viewport_width / 2
        half_h = self.world_camera.viewport_height / 2
        cam_x = max(half_w, min(self.world_w - half_w, smooth[0]))
        cam_y = max(half_h, min(self.world_h - half_h, smooth[1]))

        self.world_camera.position = (cam_x, cam_y)
        self.gui_camera.position = (SCREEN_W / 2, SCREEN_H / 2)

        # Обновим счёт
        self.text_score = arcade.Text(f"Счёт: {self.score}",
                                      16, SCREEN_H - 36, arcade.color.DARK_SLATE_GRAY,
                                      20, batch=self.batch)

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


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__('player/idle/idle-4.png', scale=2)
        self.center_x = 280
        self.center_y = 140

        self.walk_speed = 2
        self.run_speed = 5

        self.idle_texture = arcade.load_texture('player/idle/idle-4.png')
        self.texture = self.idle_texture

        self.walk_textures = []
        self.run_textures = []
        self.climb_textures = []
        self.is_walking = self.is_running = self.is_climbing = False

        for i in range(1, 17):
            texture = arcade.load_texture(f'player/walk/walk-{i}.png')
            self.walk_textures.append(texture)

        for i in range(1, 9):
            texture = arcade.load_texture(f'player/run/run-{i}.png')
            self.run_textures.append(texture)

        for i in range(1, 7):
            texture = arcade.load_texture(f'player/climb/climb-{i}.png')
            self.climb_textures.append(texture)

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_walking:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.walk_textures):
                    self.current_texture = 0
                self.texture = self.walk_textures[self.current_texture]

        elif self.is_running:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.run_textures):
                    self.current_texture = 0
                self.texture = self.run_textures[self.current_texture]

        elif self.is_climbing:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.climb_textures):
                    self.current_texture = 0
                self.texture = self.climb_textures[self.current_texture]
        else:
            self.texture = self.idle_texture



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

