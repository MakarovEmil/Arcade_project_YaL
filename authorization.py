import sqlite3
from BaseGUIView import BaseGUIView
from arcade.gui import UIFlatButton, UILabel, UIInputText, UIMessageBox, UIGridLayout, UIBoxLayout




class AuthorizationView(BaseGUIView):
    def __init__(self, window):
        super().__init__(window, 'Backgrounds/skyline-a.png')
        self.con = sqlite3.connect('Chaos_Courier.sqlite')
        self.grid = UIGridLayout(
            column_count=2,
            row_count=5,
            vertical_spacing=15,
            horizontal_spacing=20
        )
        self.setup_widgets()
        self.anchor_layout.add(self.grid)

    def setup_widgets(self):
        self.grid.add(
            UILabel(text="Авторизация в 'Курьер Хаоса'", font_size=24, bold=True),
            col_num=0, row_num=0,
            col_span=2
        )
        self.user_name = UIInputText(width=250, height=40)
        self.grid.add(UILabel(text="Имя игрока:", align="right"), 0, 1)
        self.grid.add(self.user_name, 1, 1)

        button_box = UIBoxLayout(vertical=False, space_between=30)
        self.authorization_button = UIFlatButton(text="Авторизоваться", width=150)
        self.cancel_button = UIFlatButton(text="Отмена", width=150)
        button_box.add(self.authorization_button)
        button_box.add(self.cancel_button)

        self.authorization_button.on_click = self.get_authorization
        self.cancel_button.on_click = self.get_cancel

        self.grid.add(button_box, 0, 4, col_span=2)

    def get_authorization(self, event):
        user_name = self.user_name.text
        with self.con:
            cursor = self.con.cursor()
            data = cursor.execute('''
            SELECT username FROM Players WHERE username = ?
            ''', (user_name,)).fetchall()
            if not data:
                message_box = UIMessageBox(
                    width=300, height=200,
                    message_text='Пользователь не найден',
                    buttons=["OK"]
                )
                self.manager.add(message_box)
            else:
                from MainView import MainView
                main_view = MainView(self.window, user_name)
                self.window.show_view(main_view)

    def get_cancel(self, event):
        from MenuView import MenuView
        menu_view = MenuView(self.window)
        self.window.show_view(menu_view)