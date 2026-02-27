import os
from enum import Enum
from typing import Dict, Optional

import telebot
from telebot.types import ReplyKeyboardMarkup

from logic import Bot as JobBot
# =======================
# CONFIG
# =======================

DB = "jobs.db"
token = "8088459553:AAFax_h0eKX6qhk18mkhQqJm-pXZoxdhXuQ" 

CATEGORIES = ["IT", "Дизайн", "Маркетинг", "Наука", "Бизнес"]

job_bot = JobBot(DB)
job_bot.init_db()

bot = telebot.TeleBot(token)


class UserState(str, Enum):
    SEARCH = "await_search"
    PROFILE_INTERESTS = "await_profile_interests"
    PROFILE_LEVEL = "await_profile_level"
    ADD_JOB = "await_add_job"


USER_STATES: Dict[int, UserState] = {}


def set_state(user_id: int, state: Optional[UserState]):
    if state is None:
        USER_STATES.pop(user_id, None)
    else:
        USER_STATES[user_id] = state


def get_state(user_id: int) -> Optional[UserState]:
    return USER_STATES.get(user_id)


def main_keyboard() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Рекомендации", "🔍 Поиск")
    markup.row("🧭 Профиль", "➕ Добавить вакансию")
    markup.row("❓ Помощь")
    return markup


def category_keyboard() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in CATEGORIES:
        markup.row(category)
    markup.row("⬅️ Назад")
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "Привет! 👋\n"
        "Я бот для поиска вакансий и рекомендаций.\n\n"
        "Могу:\n"
        "• Найти вакансии\n"
        "• Дать персональные рекомендации\n"
        "• Сохранить твои интересы"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


@bot.message_handler(commands=["help"])
def help_cmd(message):
    text = (
        "/start – главное меню\n\n"
        "🔍 Поиск – поиск по слову или категории\n"
        "🚀 Рекомендации – персональные варианты\n"
        "🧭 Профиль – управление интересами\n"
        "➕ Добавить вакансию – для администратора"
    )
    bot.send_message(message.chat.id, text)







if __name__ == "__main__":
    print("Бот запущен 🚀")
    bot.infinity_polling(skip_pending=True)