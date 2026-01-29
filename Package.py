import arcade

TILE_SIZE = 70
class Package(arcade.Sprite):
    def __init__(self, center_x, center_y, health):
        super().__init__('package/package_texture.png', scale=0.1)
        self.center_x = center_x
        self.center_y = center_y
        self.health = self.current_health = health
        self.is_lies = self.is_abandoned = False
        self.is_raised = True
        self.can_be_abandoned = False
        self.x_speed = 25
        self.y_speed = 50
        self.raised_radius = TILE_SIZE * 0.8
        self.abandoned_time = 2.0
        self.abandoned_timer = 2.0