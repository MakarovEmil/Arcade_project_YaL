from BaseGUIView import BaseGUIView
import sqlite3
from arcade.gui import UIFlatButton, UILabel, UIInputText, UIMessageBox, UIGridLayout
from arcade.gui.widgets.layout import UIBoxLayout
from datetime import date
from MenuView import MenuView


class RegistrationView(BaseGUIView):
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
            UILabel(text="Регистрация в 'Курьер Хаоса'", font_size=24, bold=True),
            col_num=0, row_num=0,
            col_span=2
        )
        self.user_name = UIInputText(width=250, height=40)
        self.battle_cry = UIInputText(width=250, height=40)
        self.grid.add(UILabel(text="Имя игрока:", align="right"), 0, 1)
        self.grid.add(UILabel(text="Боевой клич", align="right"), 0, 2)

        self.grid.add(self.user_name, 1, 1)
        self.grid.add(self.battle_cry, 1, 2)

        button_box = UIBoxLayout(vertical=False, space_between=30)
        self.registration_button = UIFlatButton(text="Зарегистрировать", width=150)
        self.cancel_button = UIFlatButton(text="Отмена", width=150)
        button_box.add(self.registration_button)
        button_box.add(self.cancel_button)

        self.registration_button.on_click = self.get_registration
        self.cancel_button.on_click = self.get_cancel

        self.grid.add(button_box, 0, 4, col_span=2)

    def get_registration(self, event):
        user_name = self.user_name.text
        battle_cry = self.battle_cry.text

        is_valid, comment = self.validate_data(user_name, battle_cry)
        if not is_valid:
            message_box = UIMessageBox(
                width=300, height=200,
                message_text=comment,
                buttons=["OK"]
            )
            self.manager.add(message_box)
        else:
            with self.con:
                cursor = self.con.cursor()
                cursor.execute('''
                        INSERT INTO Players (username, battle_cry, first_seen_date, last_seen_date, 
                        total_games_played, total_play_time_seconds, credits, damage, health)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_name, battle_cry, date.today(), date.today(), 0, 0, 50, 3, 50))
                self.con.commit()
            menu_view = MenuView(self.window)
            self.window.show_view(menu_view)

    def validate_data(self, name, battle_cry):
        with self.con:
            cursor = self.con.cursor()
            if not name:
                return False, 'Ошибка: Имя обязательно при регистрации'
            if len(name) < 3:
                return False, "Имя должно содержать минимум 3 символа"
            if len(name) >= 15:
                return False, 'Ошибка: Имя слишком длинное. Пожалуйста придумайте другое'
            if len(battle_cry) >= 20:
                return False, 'Ошибка: Боевой клич слишком длинный. Пожалуйста придумайте другой'
            exist_name = cursor.execute("SELECT username FROM Players WHERE username = ?", (name,)).fetchone()
            if exist_name is not None:
                return False, 'Ошибка: Такое имя уже есть. Пожалуйста придумайте другое'
            return True, ''

    def get_cancel(self, event):
        menu_view = MenuView(self.window)
        self.window.show_view(menu_view)
