import telebot
from telebot.types import ReplyKeyboardMarkup
from logic import Bot as JobBot

TOKEN = "8088459553:AAFax_h0eKX6qhk18mkhQqJm-pXZoxdhXuQ"
DB_PATH = "jobs.db"

CATEGORIES = ["IT", "Дизайн", "Маркетинг", "Наука", "Бизнес"]

SEARCH = "search"
PROFILE_INTERESTS = "interests"
PROFILE_LEVEL = "level"
ADD_JOB = "add_job"

USER_STATES = {}

job_bot = JobBot(DB_PATH)
job_bot.init_db()

bot = telebot.TeleBot(TOKEN)


def set_state(uid, state=None):
    """Установка или сброс состояния пользователя"""
    if state:
        USER_STATES[uid] = state
    else:
        USER_STATES.pop(uid, None)


def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚀 Рекомендации", "🔍 Поиск")
    kb.row("🧭 Профиль", "➕ Добавить вакансию")
    kb.row("❓ Помощь")
    return kb


def category_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for c in CATEGORIES:
        kb.row(c)
    kb.row("📌 По интересам")
    kb.row("⬅️ Назад")
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "Привет! 👋\n"
        "Я бот для поиска вакансий.\n\n"
        "• 🔍 Поиск вакансий\n"
        "• 🚀 Рекомендации\n"
        "• 🧭 Профиль\n"
        "• ➕ Добавить вакансию\n"
        "• ❓ Помощь"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "/start – меню\n🔍 Поиск – поиск вакансий\n🚀 Рекомендации – случайные вакансии\n🧭 Профиль – настройки\n➕ Добавить вакансию – добавить новую вакансию\n❓ Помощь – получить помощь"
    )


@bot.message_handler(func=lambda m: True)
def handler(message):
    """Основной обработчик входящих сообщений"""
    uid = message.from_user.id
    state = USER_STATES.get(uid)

    try:
        if state:
            handle_state(message, state)
        else:
            handle_menu(message)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "⚠️ Ошибка")
        set_state(uid)


def handle_state(message, state):
    """Обработка сообщений в зависимости от состояния"""
    uid = message.from_user.id
    text = message.text.strip()

    if text == "⬅️ Назад":
        set_state(uid)
        bot.send_message(message.chat.id, "Меню", reply_markup=main_keyboard())
        return

    if state == SEARCH:
        if text == "📌 По интересам":
            jobs = job_bot.recommend_jobs(uid)
        elif text in CATEGORIES:
            jobs = job_bot.find_jobs(category=text)
        else:
            jobs = job_bot.find_jobs(keyword=text)

        send_jobs(message.chat.id, jobs)

    elif state == PROFILE_INTERESTS:
        job_bot.add_or_update_user(uid, message.from_user.first_name, interests=text)
        bot.send_message(message.chat.id, "Интересы сохранены", reply_markup=main_keyboard())

    elif state == PROFILE_LEVEL:
        job_bot.add_or_update_user(uid, level=text)
        bot.send_message(message.chat.id, "Уровень сохранен", reply_markup=main_keyboard())

    elif state == ADD_JOB:
        add_job(message)

    set_state(uid)


def handle_menu(message):
    """Обработка команд главного меню"""
    uid = message.from_user.id
    text = message.text

    if text == "🔍 Поиск":
        bot.send_message(message.chat.id, "Введите слово или выберите категорию:", reply_markup=category_keyboard())
        set_state(uid, SEARCH)

    elif text == "🚀 Рекомендации":
        jobs = job_bot.recommend_jobs(uid) or job_bot.find_jobs(limit=5)
        send_jobs(message.chat.id, jobs)

    elif text == "🧭 Профиль":
        show_profile(message, uid)

    elif text == "Редактировать интересы":
        bot.send_message(message.chat.id, "Введите интересы:", reply_markup=category_keyboard())
        set_state(uid, PROFILE_INTERESTS)

    elif text == "Изменить уровень":
        bot.send_message(message.chat.id, "Введите уровень (junior/middle/senior):")
        set_state(uid, PROFILE_LEVEL)

    elif text == "➕ Добавить вакансию":
        bot.send_message(message.chat.id, "Формат:\ncompany|title|salary_from|salary_to|skills|level|category")
        set_state(uid, ADD_JOB)

    elif text == "❓ Помощь":
        help_cmd(message)

    elif text == "⬅️ Назад":
        bot.send_message(message.chat.id, "Меню", reply_markup=main_keyboard())

    else:
        bot.send_message(message.chat.id, "Выберите кнопку", reply_markup=main_keyboard())


def show_profile(message, uid):
    """Отображение профиля пользователя с настройками"""
    user = job_bot.get_user(uid)

    if not user:
        bot.send_message(message.chat.id, "Введите интересы:")
        set_state(uid, PROFILE_INTERESTS)
        return

    text = (
        f"👤 {user['name']}\n"
        f"Интересы: {user['interests']}\n"
        f"Уровень: {user['level']}"
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Редактировать интересы", "Изменить уровень")
    kb.row("⬅️ Назад")

    bot.send_message(message.chat.id, text, reply_markup=kb)


def add_job(message):
    """Парсинг и добавление новой вакансии"""
    parts = [p.strip() for p in message.text.split("|")]

    if len(parts) != 7:
        bot.send_message(message.chat.id, "Неверный формат")
        return

    company, title, sf, st, skills, level, category = parts

    try:
        jid = job_bot.add_job(company, title, int(sf or 0), int(st or 0), skills, level, category)
        bot.send_message(message.chat.id, f"Вакансия добавлена ID={jid}", reply_markup=main_keyboard())
    except:
        bot.send_message(message.chat.id, "Ошибка зарплаты")


def send_jobs(chat_id, jobs):
    """Отправка списка найденных вакансий пользователю"""
    if not jobs:
        bot.send_message(chat_id, "Ничего не найдено", reply_markup=main_keyboard())
        return

    for job in jobs[:8]:
        bot.send_message(chat_id, job_bot.format_job(job), parse_mode="HTML")

    bot.send_message(chat_id, "Для нового поиска нажмите 🔍 Поиск", reply_markup=main_keyboard())


print("🚀 Бот запущен")
bot.infinity_polling(skip_pending=True)