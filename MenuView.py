from BaseGUIView import BaseGUIView
from arcade.gui.widgets.layout import UIBoxLayout
from arcade.gui import UIFlatButton, UILabel, UITextArea
import arcade




class MenuView(BaseGUIView):
    def __init__(self, window):
        super().__init__(window, 'Backgrounds/buildings-bg.png')
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)
        self.setup_widgets()
        self.anchor_layout.add(self.box_layout)

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
        from authorization import AuthorizationView
        authorization_view = AuthorizationView(self.window)
        self.window.show_view(authorization_view)

    def registration(self, event):
        from RegistrationView import RegistrationView
        registration_view = RegistrationView(self.window)
        self.window.show_view(registration_view)