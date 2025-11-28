import telebot

# Токен бота (получи у @BotFather)
TOKEN = "8415183073:AAEZImJs4tm28tRLBhpC6X0sRlQkYZRFRNI"

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я простой бот. Напиши /help для списка команд")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Доступные команды:
/start - начать работу
/help - показать это сообщение
/about - информация о боте
/echo [текст] - повторить текст
    """
    bot.reply_to(message, help_text)

# Обработчик команды /about
@bot.message_handler(commands=['about'])
def send_about(message):
    bot.reply_to(message, "Я простой тестовый бот на Python")

# Обработчик команды /echo
@bot.message_handler(commands=['echo'])
def echo_message(message):
    # Получаем текст после команды /echo
    text = message.text[6:].strip()  # Убираем "/echo " из сообщения
    if text:
        bot.reply_to(message, f"Вы сказали: {text}")
    else:
        bot.reply_to(message, "Напиши текст после команды /echo")

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_text = message.text.lower()
    
    if 'привет' in user_text:
        bot.reply_to(message, "И тебе привет! 👋")
    elif 'как дела' in user_text:
        bot.reply_to(message, "Отлично! А у тебя? 😊")
    elif 'пока' in user_text or 'до свидания' in user_text:
        bot.reply_to(message, "До встречи! 👋")
    else:
        bot.reply_to(message, "Не понял тебя. Напиши /help для списка команд")

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    # Удаляем вебхук если он был установлен
    bot.remove_webhook()
    # Запускаем опрос сервера
    bot.infinity_polling()
