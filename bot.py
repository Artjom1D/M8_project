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


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = message.from_user.id
    text = message.text.strip()
    state = get_state(uid)

    try:
        if state:
            handle_state(message, state)
            return

        handle_menu(message)

    except Exception as e:
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка. Попробуй снова."
        )
        print(f"Error: {e}")
        set_state(uid, None)


def handle_state(message, state: UserState):
    uid = message.from_user.id
    text = message.text.strip()

    if state == UserState.SEARCH:
        if text == "⬅️ Назад":
            set_state(uid, None)
            bot.send_message(message.chat.id, "Возвращаю в меню.", reply_markup=main_keyboard())
            return

        if text in CATEGORIES:
            jobs = job_bot.find_jobs(category=text)
        else:
            jobs = job_bot.find_jobs(keyword=text)

        send_jobs(message.chat.id, jobs)
        set_state(uid, None)
        bot.send_message(message.chat.id, "Готово ✅", reply_markup=main_keyboard())

    elif state == UserState.PROFILE_INTERESTS:
        job_bot.add_or_update_user(
            uid,
            name=message.from_user.first_name,
            interests=text
        )
        bot.send_message(message.chat.id, "Интересы сохранены ✅", reply_markup=main_keyboard())
        set_state(uid, None)

    elif state == UserState.PROFILE_LEVEL:
        job_bot.add_or_update_user(
            uid,
            name=message.from_user.first_name,
            level=text
        )
        bot.send_message(message.chat.id, "Уровень сохранён ✅", reply_markup=main_keyboard())
        set_state(uid, None)

    elif state == UserState.ADD_JOB:
        handle_add_job(message)


def handle_add_job(message):
    uid = message.from_user.id

    parts = [p.strip() for p in message.text.split("|")]

    if len(parts) != 7:
        bot.send_message(
            message.chat.id,
            "Неверный формат:\ncompany|title|salary_from|salary_to|skills|level|category"
        )
        return

    company, title, sf, st, skills, level, category = parts

    jid = job_bot.add_job(
        company,
        title,
        int(sf or 0),
        int(st or 0),
        skills,
        level,
        category
    )

    bot.send_message(
        message.chat.id,
        f"Вакансия добавлена ✅ ID={jid}",
        reply_markup=main_keyboard()
    )

    set_state(uid, None)

def handle_menu(message):
    uid = message.from_user.id
    text = message.text.strip()

    if text == "🔍 Поиск":
        bot.send_message(
            message.chat.id,
            "Введите ключевое слово или выберите категорию:",
            reply_markup=category_keyboard()
        )
        set_state(uid, UserState.SEARCH)

    elif text == "🚀 Рекомендации":
        jobs = job_bot.recommend_jobs(uid)
        if not jobs:
            jobs = job_bot.find_jobs(limit=5)

        send_jobs(message.chat.id, jobs)

    elif text == "🧭 Профиль":
        user = job_bot.get_user(uid)

        if not user:
            bot.send_message(
                message.chat.id,
                "Введите интересы через запятую:",
            )
            set_state(uid, UserState.PROFILE_INTERESTS)
            return

        profile_text = (
            f"👤 {user.get('name')}\n"
            f"Интересы: {user.get('interests')}\n"
            f"Уровень: {user.get('level')}"
        )

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("Редактировать интересы", "Изменить уровень")
        markup.row("⬅️ Назад")

        bot.send_message(message.chat.id, profile_text, reply_markup=markup)

    elif text == "Редактировать интересы":
        bot.send_message(message.chat.id, "Введите новые интересы:")
        set_state(uid, UserState.PROFILE_INTERESTS)

    elif text == "Изменить уровень":
        bot.send_message(message.chat.id, "Введите уровень (junior/middle/senior):")
        set_state(uid, UserState.PROFILE_LEVEL)

    elif text == "➕ Добавить вакансию":
        bot.send_message(
            message.chat.id,
            "Введите вакансию:\ncompany|title|salary_from|salary_to|skills|level|category"
        )
        set_state(uid, UserState.ADD_JOB)

    elif text == "❓ Помощь":
        help_cmd(message)

    else:
        bot.send_message(message.chat.id, "Выберите кнопку 👇", reply_markup=main_keyboard())


def send_jobs(chat_id, jobs):
    if not jobs:
        bot.send_message(chat_id, "Ничего не найдено.")
        return

    for job in jobs[:5]:
        bot.send_message(chat_id, job_bot.format_job(job), parse_mode="HTML")

if __name__ == "__main__":
    print("Бот запущен 🚀")
    bot.infinity_polling(skip_pending=True)