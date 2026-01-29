import arcade
from MenuView import MenuView
SCREEN_W = 1500
SCREEN_H = 1000
SCREEN_TITLE = "Курьер Хаоса"

if __name__ == "__main__":
    window = arcade.Window(SCREEN_W, SCREEN_H, SCREEN_TITLE)
    menu_view = MenuView(window)
    window.show_view(menu_view)
    arcade.run()

