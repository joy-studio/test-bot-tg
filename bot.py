import telebot
import requests
import json
import logging


# Ваш токен
bot = telebot.TeleBot("8415183073:AAEZImJs4tm28tRLBhpC6X0sRlQkYZRFRNI")

# Удаляем вебхук перед запуском поллинга
bot.remove_webhook()

# Затем запускаем поллинг
print("Бот запущен...")
bot.infinity_polling()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация
TELEGRAM_TOKEN = "8415183073:AAEZImJs4tm28tRLBhpC6X0sRlQkYZRFRNI"
YANDEX_API_KEY = "AQVNyIecsLF9OK3bUGnG6XMWHPFeh9akBoNoB9qX"
YANDEX_FOLDER_ID = "b1gemt0roqlr2v92e61p"

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# URL для Yandex GPT API
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def ask_yandex_gpt(prompt):
    """
    Функция для взаимодействия с Yandex GPT API
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }
    
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты полезный ассистент. Отвечай вежливо и по делу."
            },
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    
    try:
        response = requests.post(YANDEX_GPT_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result['result']['alternatives'][0]['message']['text']
    
    except Exception as e:
        logging.error(f"Ошибка при обращении к Yandex GPT: {e}")
        return "Извините, произошла ошибка при обработке запроса."

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
Привет! 👋 Я бот с искусственным интеллектом от Yandex GPT.

Просто напиши мне сообщение, и я постараюсь помочь!

Команды:
/start - показать это сообщение
/help - помощь
"""
    bot.reply_to(message, welcome_text)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Я использую Yandex GPT для ответов на ваши вопросы.

Просто напишите мне любой вопрос или сообщение, и я постараюсь дать полезный ответ!

Примеры вопросов:
- "Напиши план для похода в магазин"
- "Объясни квантовую физику простыми словами"
- "Помоги составить список дел на день"
"""
    bot.reply_to(message, help_text)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Показываем, что бот печатает
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ от Yandex GPT
        response = ask_yandex_gpt(message.text)
        
        # Отправляем ответ пользователю
        bot.reply_to(message, response)
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")

# Запуск бота
if __name__ == "__main__":
    logging.info("Бот запущен...")
    bot.infinity_polling()
