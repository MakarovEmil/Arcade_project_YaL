import arcade
from arcade.gui import UIManager
from arcade.gui.widgets.layout import UIAnchorLayout


class BaseGUIView(arcade.View):
    def __init__(self, window, background_texture_path=None):
        super().__init__()
        self.window = window
        if background_texture_path:
            self.background_texture = arcade.load_texture(background_texture_path)
        else:
            self.background_texture = None
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.manager.add(self.anchor_layout)

    def on_draw(self):
        self.clear()
        if self.background_texture:
            arcade.draw_texture_rect(
                self.background_texture,
                arcade.rect.XYWH(
                    self.window.width // 2,
                    self.window.height // 2,
                    self.window.width,
                    self.window.height
                )
            )
        self.manager.draw()

    def on_hide_view(self):
        self.manager.disable()