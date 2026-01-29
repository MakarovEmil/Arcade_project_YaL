from BaseGUIView import BaseGUIView
import sqlite3
from arcade.gui.widgets.layout import UIBoxLayout
from arcade.gui import UIFlatButton, UILabel
from MainView import MainView
from datetime import date


class End_game_view(BaseGUIView):
    def __init__(self, window, username, total_time, reward_for_kills, greed_mod=False, success=True):
        super().__init__(window, 'Backgrounds/buildings-bg.png')
        self.con = sqlite3.connect('Chaos_Courier.sqlite')
        self.username, self.total_time, self.reward_for_kills, self.success, self.greed_mod = (username, total_time,
                                                                                               reward_for_kills,
                                                                                               success, greed_mod)
        self.reward_for_delivery = self.calculate_reward_for_delivery(self.total_time, self.success, self.greed_mod)
        self.cursor = self.con.cursor()
        self.setup_widgets()
        self.anchor_layout.add(self.layout)
        self.update_data(username)

    def calculate_reward_for_delivery(self, total_time, success, greed_mod):
        reward = 0
        if not success:
            return reward
        elif total_time <= 180:
            reward = 15
        elif total_time <= 240:
            reward = 10
        elif total_time <= 300:
            reward = 5
        elif total_time <= 360:
            reward = 3
        else:
            reward = 0
        return reward * 0.75 if greed_mod else reward

    def setup_widgets(self):
        self.layout = UIBoxLayout(vertical=True, space_between=15)
        if self.success:
            self.layout.add(UILabel(text='Поздравляем с успешной доставкой!', font_size=24, bold=True))
        else:
            self.layout.add(UILabel(text='К сожалению, доставка не получилась!', font_size=24, bold=True))
        self.layout.add(UILabel(text=f'Игрок: {self.username}', font_size=24, bold=True))
        self.layout.add(UILabel(text=f'Время доставки: {self.total_time:.2f}', font_size=24, bold=True))
        self.layout.add(UILabel(text=f'Награда за убийства: {self.reward_for_kills}', font_size=24, bold=True))
        self.layout.add(UILabel(text=f'Награда за доставку: {self.reward_for_delivery}', font_size=24, bold=True))
        self.get_main_button = UIFlatButton(text='Вернуться в аккаунт', width=300)
        self.get_main_button.on_click = self.get_main
        self.layout.add(self.get_main_button)

    def update_data(self, username):
        with self.con:
            self.cursor.execute("UPDATE Players SET credits = credits + ? + ?, "
                                "total_games_played = total_games_played + 1, "
                                "total_play_time_seconds = total_play_time_seconds + ?, last_seen_date = ?"
                                "WHERE username = ?",
                                (self.reward_for_delivery, self.reward_for_kills, self.total_time, date.today(),
                                 self.username))
            self.con.commit()

    def get_main(self, event):
        main_view = MainView(self.window, self.username)
        self.window.show_view(main_view)
