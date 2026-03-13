import telebot
import gspread
from google.oauth2.service_account import Credentials

# --- НАСТРОЙКИ --- #
TOKEN = '8442639780:AAHPADtcaFwuyFUz0DSGWFkNxlYvgA-I0WM'
SPREADSHEET_ID = '1qj-KRQ5-tOfVMrIG2nvIgMnNwRKMrdzSOVrEfvbVjKg'
CREDENTIALS_FILE = 'credentials.json'

# --- ПОДКЛЮЧЕНИЕ К GOOGLE ТАБЛИЦЕ --- #
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet('TSP_Выплаты АБ')

# --- СОЗДАНИЕ БОТА --- #
bot = telebot.TeleBot(TOKEN)

user_state = {}

# --- КОМАНДА /start --- #
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "👋 Привет!\n\n"
        "Нажми /status чтобы узнать статус клиента по ИНН"
    )

# --- КОМАНДА /status — запрашиваем ИНН --- #
@bot.message_handler(commands=['status'])
def ask_inn(message):
    user_state[message.chat.id] = 'waiting_inn'
    bot.reply_to(message, "🔍 Введи ИНН клиента:")

# --- ОБРАБОТКА ТЕКСТА — ловим ИНН --- #
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_inn')
def get_by_inn(message):
    inn = message.text.strip()
    user_state.pop(message.chat.id, None)

    try:
        records = sheet.get_all_records()

        # ОТЛАДКА — показывает названия колонок в терминале
        if records:
            print("Колонки:", list(records[0].keys()))
            print("Первая запись:", records[0])

        found = None
        for row in records:
            if str(row.get('ИНН', '')).strip() == inn:
                found = row
                break

        if found:
            name = found.get('Наименование клиента', 'Не указано')
            status = found.get('Статус', 'Нет данных')
            date = found.get('Дата передачи лида', 'Нет данных')

            bot.reply_to(
                message,
                f"📋 *Клиент:* {name}\n"
                f"🔖 *Статус:* {status}\n"
                f"📅 *Дата:* {date}",
                parse_mode='Markdown'
            )
        else:
            bot.reply_to(
                message,
                f"❌ ИНН {inn} не найден в таблице\n\n"
                f"Проверь правильность и попробуй снова /status"
            )

    except Exception as e:
        bot.reply_to(message, f"🚨 Ошибка: {e}")
        print(f"Ошибка подробно: {e}")

# --- ЗАПУСК --- #
print("✅ Бот запущен! Нажми Ctrl+C чтобы остановить")
bot.polling(none_stop=True)
