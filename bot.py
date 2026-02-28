import telebot
from telebot.types import ReplyKeyboardMarkup
from enum import Enum
from typing import Dict, Optional

from logic import Bot as JobBot

TOKEN = "Your_Telegram_Bot_Token_Here"
DB_PATH = "jobs.db"
CATEGORIES = ["IT", "Дизайн", "Маркетинг", "Наука", "Бизнес"]

# =======================
# INIT
# =======================

job_bot = JobBot(DB_PATH)
job_bot.init_db()

bot = telebot.TeleBot(TOKEN)


class UserState(str, Enum):
    SEARCH = "await_search"
    PROFILE_INTERESTS = "await_profile_interests"
    PROFILE_LEVEL = "await_profile_level"
    ADD_JOB = "await_add_job"


USER_STATES: Dict[int, UserState] = {}


def set_state(user_id: int, state: Optional[UserState]):
    """Установить или очистить состояние пользователя."""
    if state is None:
        USER_STATES.pop(user_id, None)
    else:
        USER_STATES[user_id] = state


def get_state(user_id: int) -> Optional[UserState]:
    """Получить текущее состояние пользователя."""
    return USER_STATES.get(user_id)


def main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Рекомендации", "🔍 Поиск")
    markup.row("🧭 Профиль", "➕ Добавить вакансию")
    markup.row("❓ Помощь")
    return markup


def category_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с категориями вакансий."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in CATEGORIES:
        markup.row(category)
    markup.row("⬅️ Назад")
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    """Команда /start."""
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
    """Команда /help."""
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
    """Основной обработчик текстовых сообщений."""
    uid = message.from_user.id
    state = get_state(uid)

    try:
        if state:
            return handle_state(message, state)
        handle_menu(message)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуй снова.")
        print(f"Error: {e}")
        set_state(uid, None)


def handle_state(message, state: UserState):
    """Обработчик сообщений в различных состояниях."""
    uid = message.from_user.id
    text = message.text.strip()

    if text == "⬅️ Назад":
        set_state(uid, None)
        return bot.send_message(
            message.chat.id,
            "Возвращаю в меню.",
            reply_markup=main_keyboard()
        )

    if state == UserState.SEARCH:
        jobs = (
            job_bot.find_jobs(category=text)
            if text in CATEGORIES
            else job_bot.find_jobs(keyword=text)
        )
        send_jobs(message.chat.id, jobs)

    elif state == UserState.PROFILE_INTERESTS:
        job_bot.add_or_update_user(uid, name=message.from_user.first_name, interests=text)
        bot.send_message(message.chat.id, "Сохранено ✅", reply_markup=main_keyboard())

    elif state == UserState.PROFILE_LEVEL:
        job_bot.add_or_update_user(uid, name=message.from_user.first_name, level=text)
        bot.send_message(message.chat.id, "Сохранено ✅", reply_markup=main_keyboard())

    elif state == UserState.ADD_JOB:
        handle_add_job(message)

    set_state(uid, None)


def handle_add_job(message):
    """Обработчик добавления вакансии."""
    uid = message.from_user.id
    parts = [p.strip() for p in message.text.split("|")]

    if len(parts) != 7:
        return bot.send_message(
            message.chat.id,
            "❌ Неверный формат:\ncompany|title|salary_from|salary_to|skills|level|category"
        )

    company, title, sf, st, skills, level, category = parts

    try:
        jid = job_bot.add_job(company, title, int(sf or 0), int(st or 0), skills, level, category)
        bot.send_message(
            message.chat.id,
            f"✅ Вакансия добавлена! ID={jid}",
            reply_markup=main_keyboard()
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка: зарплата должна быть числом")

    set_state(uid, None)


def handle_menu(message):
    """Обработчик главного меню."""
    uid = message.from_user.id
    text = message.text.strip()

    menu_actions = {
        "🔍 Поиск": lambda: (
            bot.send_message(
                message.chat.id,
                "Введите ключевое слово или выберите категорию:",
                reply_markup=category_keyboard()
            ),
            set_state(uid, UserState.SEARCH)
        ),
        "🚀 Рекомендации": lambda: send_jobs(
            message.chat.id,
            job_bot.recommend_jobs(uid) or job_bot.find_jobs(limit=5)
        ),
        "🧭 Профиль": lambda: show_profile(message, uid),
        "Редактировать интересы": lambda: (
            bot.send_message(message.chat.id, "Введите новые интересы (через запятую):"),
            set_state(uid, UserState.PROFILE_INTERESTS)
        ),
        "Изменить уровень": lambda: (
            bot.send_message(message.chat.id, "Введите уровень (junior/middle/senior):"),
            set_state(uid, UserState.PROFILE_LEVEL)
        ),
        "➕ Добавить вакансию": lambda: (
            bot.send_message(
                message.chat.id,
                "Введите вакансию:\ncompany|title|salary_from|salary_to|skills|level|category"
            ),
            set_state(uid, UserState.ADD_JOB)
        ),
        "❓ Помощь": lambda: help_cmd(message),
    }

    if text in menu_actions:
        menu_actions[text]()
    else:
        bot.send_message(
            message.chat.id,
            "Выберите кнопку 👇",
            reply_markup=main_keyboard()
        )


def show_profile(message, uid):
    """Показать профиль пользователя."""
    user = job_bot.get_user(uid)

    if not user:
        bot.send_message(message.chat.id, "Введите интересы (через запятую):")
        return set_state(uid, UserState.PROFILE_INTERESTS)

    profile_text = (
        f"👤 {user.get('name') or 'Аноним'}\n"
        f"Интересы: {user.get('interests') or '-'}\n"
        f"Уровень: {user.get('level') or '-'}"
    )

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Редактировать интересы", "Изменить уровень")
    markup.row("⬅️ Назад")

    bot.send_message(message.chat.id, profile_text, reply_markup=markup)


def send_jobs(chat_id, jobs):
    """Отправить список вакансий."""
    if not jobs:
        return bot.send_message(chat_id, "😔 Ничего не найдено.")

    for job in jobs[:8]:
        bot.send_message(chat_id, job_bot.format_job(job), parse_mode="HTML")


if __name__ == "__main__":
    print("🚀 Бот запущен!")
    bot.infinity_polling(skip_pending=True)
