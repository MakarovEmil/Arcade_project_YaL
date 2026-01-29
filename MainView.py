import sqlite3
from BaseGUIView import BaseGUIView
from arcade.gui import UIFlatButton, UILabel, UIMessageBox, UIBoxLayout



class MainView(BaseGUIView):
    def __init__(self, window, username):
        super().__init__(window, 'Backgrounds/near-buildings-bg.png')
        self.con = sqlite3.connect('Chaos_Courier.sqlite')
        self.cursor = self.con.cursor()
        self.modifiers = ["Толстокожие враги", "Скорострелы", "Бегуны", "Стеклянная челюсть",
                          "Неуклюжесть", "Жажда наживы", "Туман"]
        self.selected_modifiers = []
        self.username = username
        self.left_layout = UIBoxLayout(vertical=True, space_between=15)
        self.right_layout = UIBoxLayout(vertical=True, space_between=15)
        self.layout = UIBoxLayout(vertical=False, space_between=70)
        self.setup_widgets()
        self.anchor_layout.add(self.layout)

    def setup_widgets(self):
        self.username_label = UILabel(font_size=24, bold=True)
        self.battle_cry_label = UILabel(font_size=24, bold=True)
        self.credits_label = UILabel(font_size=24, bold=True)
        self.damage_label = UILabel(font_size=24, bold=True)
        self.health_label = UILabel(font_size=24, bold=True)
        self.total_games = UILabel(font_size=24, bold=True)
        self.total_seconds = UILabel(font_size=24, bold=True)
        self.load_data(self.username)
        self.left_layout.add(self.username_label)
        self.left_layout.add(self.battle_cry_label)
        self.left_layout.add(UILabel(text="Модификаторы для игры", font_size=24, bold=True))
        self.right_layout.add(self.total_games)
        self.right_layout.add(self.total_seconds)
        self.right_layout.add(self.credits_label)
        self.right_layout.add(self.health_label)
        self.right_layout.add(self.damage_label)
        self.add_health_button = UIFlatButton(text='Увеличить здоровье (15 кредитов)', width=300)
        self.add_health_button.on_click = self.add_health
        self.right_layout.add(self.add_health_button)
        self.add_damage_button = UIFlatButton(text='Увеличить урон (10 кредитов)', width=300)
        self.add_damage_button.on_click = self.add_damage
        self.right_layout.add(self.add_damage_button)
        self.start_game_button = UIFlatButton(text='ИГРАТЬ', width=300)
        self.start_game_button.on_click = self.start_game
        self.right_layout.add(self.start_game_button)
        self.cancel_button = UIFlatButton(text='Вернуть на главную', width=300)
        self.cancel_button.on_click = self.get_cancel
        self.right_layout.add(self.cancel_button)
        for row, modifier in enumerate(self.modifiers):
            button = UIFlatButton(text=modifier, width=300)
            button.modifier_name = modifier
            button.is_selected = False
            button.on_click = self.turn_into_selected
            self.left_layout.add(button)
        self.layout.add(self.left_layout)
        self.layout.add(self.right_layout)

    def add_health(self, event):
        current_health = int(self.health_label.text.split()[-1])
        current_credits = int(self.credits_label.text.split()[-1])
        if current_credits < 15:
            message_box = UIMessageBox(
                width=300, height=200,
                message_text='Недостаточно кредитов',
                buttons=["OK"]
            )
            self.manager.add(message_box)
        else:
            current_credits -= 15
            current_health += 3
            with self.con:
                self.cursor.execute("UPDATE Players SET credits = ?, health = ? WHERE username = ?",
                                    (current_credits, current_health, self.username))
                self.con.commit()
                self.load_data(self.username)

    def add_damage(self, event):
        current_damage = int(self.damage_label.text.split()[-1])
        current_credits = int(self.credits_label.text.split()[-1])
        if current_credits < 10:
            message_box = UIMessageBox(
                width=300, height=200,
                message_text='Недостаточно кредитов',
                buttons=["OK"]
            )
            self.manager.add(message_box)
        else:
            current_credits -= 10
            current_damage += 2
            with self.con:
                self.cursor.execute("UPDATE Players SET credits = ?, damage = ? WHERE username = ?",
                                    (current_credits, current_damage, self.username))
                self.con.commit()
                self.load_data(self.username)

    def start_game(self, event):
        from GameView import GameView
        if len(self.selected_modifiers) > 3:
            message_box = UIMessageBox(
                width=300, height=200,
                message_text='Выбрано слишком много модификаторов',
                buttons=["OK"]
            )
            self.manager.add(message_box)
            return
        current_health = int(self.health_label.text.split()[-1])
        current_damage = int(self.damage_label.text.split()[-1])
        if 'Стеклянная челюсть' in self.selected_modifiers:
            current_health *= 0.6
            current_damage *= 1.5
        game_view = GameView(self.window, self.username, self.selected_modifiers, current_damage, current_health)
        self.window.show_view(game_view)

    def load_data(self, username):
        with self.con:
            data = self.cursor.execute('''
                SELECT username, battle_cry, total_games_played, total_play_time_seconds, credits, damage, health
                FROM Players WHERE username = ?
                ''', (username,)).fetchone()
            self.username_label.text = f"Курьер: {data[0]}"
            self.battle_cry_label.text = f"Боевой клич: {data[1]}"
            self.credits_label.text = f"Кредитов: {data[4]}"
            self.damage_label.text = f"Урон: {data[5]}"
            self.health_label.text = f"Здоровье: {data[6]}"
            self.total_games.text = f"Сыграно игр: {data[2]}"
            self.total_seconds.text = f"Общее время в игре: {data[3]:.2f}"

    def turn_into_selected(self, event):
        button = event.source

        if not button.is_selected:
            button.text = f"ВЫБРАНО: {button.modifier_name}"
            if button.modifier_name not in self.selected_modifiers:
                self.selected_modifiers.append(button.modifier_name)
            button.is_selected = True
        else:
            if button.modifier_name in self.selected_modifiers:
                self.selected_modifiers.remove(button.modifier_name)
            button.text = button.modifier_name
            button.is_selected = False

    def get_cancel(self, event):
        from MenuView import MenuView
        menu_view = MenuView(self.window)
        self.window.show_view(menu_view)
