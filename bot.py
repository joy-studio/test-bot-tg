import telebot
import requests
import json
import logging
import random
import time
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация
TELEGRAM_TOKEN = "8415183073:AAEZImJs4tm28tRLBhpC6X0sRlQkYZRFRNI"
YANDEX_API_KEY = "AQVN2cwTgUZXGzhVLjkX94psR1HbdGEzA5pBsOTh"
YANDEX_FOLDER_ID = "b1gemt0roqlr2v92e61p"

# ID канала откуда брать фото (замените на ваш)
CHANNEL_USERNAME = "-1004933847306"  # или CHANNEL_ID = "-1001234567890"

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# URL для Yandex GPT API
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Глобальные переменные для хранения фото
channel_photos = []
last_update_time = 0
UPDATE_INTERVAL = 3600  # Обновлять список фото каждые 60 минут

def get_channel_photos():
    """
    Функция для получения всех фото из канала
    """
    global channel_photos, last_update_time
    
    # Проверяем, не обновляли ли мы недавно список
    current_time = time.time()
    if current_time - last_update_time < UPDATE_INTERVAL and channel_photos:
        return channel_photos
    
    try:
        photos = []
        offset = 0
        limit = 100
        
        while True:
            # Получаем сообщения из канала
            messages = bot.get_chat_history(
                chat_id=CHANNEL_USERNAME,
                limit=limit,
                offset=offset
            )
            
            if not messages:
                break
                
            for message in messages:
                # Проверяем, есть ли в сообщении фото
                if message.photo:
                    # Сохраняем file_id самого большого фото
                    largest_photo = max(message.photo, key=lambda p: p.file_size)
                    photos.append({
                        'file_id': largest_photo.file_id,
                        'message_id': message.message_id,
                        'date': message.date
                    })
                # Также проверяем документы (на случай если фото как документ)
                elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
                    photos.append({
                        'file_id': message.document.file_id,
                        'message_id': message.message_id,
                        'date': message.date,
                        'is_document': True
                    })
            
            offset += limit
            
            # Ограничиваем количество загружаемых сообщений для производительности
            if offset > 1000:
                break
                
        channel_photos = photos
        last_update_time = current_time
        logging.info(f"Загружено {len(channel_photos)} фото из канала")
        return photos
        
    except Exception as e:
        logging.error(f"Ошибка при получении фото из канала: {e}")
        return channel_photos  # Возвращаем старый список если есть

def get_random_photo():
    """
    Функция для получения случайного фото из канала
    """
    photos = get_channel_photos()
    if not photos:
        return None
    
    return random.choice(photos)

def post_random_photo(chat_id, caption=None):
    """
    Функция для отправки случайного фото в указанный чат
    """
    try:
        photo_data = get_random_photo()
        if not photo_data:
            bot.send_message(chat_id, "❌ Не удалось найти фото в канале")
            return
        
        if photo_data.get('is_document'):
            # Если фото было отправлено как документ
            bot.send_document(
                chat_id=chat_id,
                document=photo_data['file_id'],
                caption=caption
            )
        else:
            # Обычное фото
            bot.send_photo(
                chat_id=chat_id,
                photo=photo_data['file_id'],
                caption=caption
            )
        
        logging.info(f"Отправлено случайное фото в чат {chat_id}")
        
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка при отправке фото")

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
/random_photo - случайное фото из канала
/photo_stats - статистика по фото
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

Дополнительные команды:
/random_photo - получить случайное фото из канала
/photo_stats - показать статистику по доступным фото
"""
    bot.reply_to(message, help_text)

# Обработчик команды /random_photo
@bot.message_handler(commands=['random_photo'])
def send_random_photo(message):
    try:
        # Показываем, что бот загружает фото
        bot.send_chat_action(message.chat.id, 'upload_photo')
        
        # Отправляем случайное фото
        caption = "📸 Случайное фото из канала!"
        post_random_photo(message.chat.id, caption)
        
    except Exception as e:
        logging.error(f"Ошибка в команде random_photo: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при получении фото")

# Обработчик команды /photo_stats
@bot.message_handler(commands=['photo_stats'])
def send_photo_stats(message):
    try:
        photos = get_channel_photos()
        if not photos:
            bot.reply_to(message, "❌ В канале не найдено фото")
            return
        
        # Сортируем по дате
        photos.sort(key=lambda x: x['date'])
        oldest = datetime.fromtimestamp(photos[0]['date']).strftime('%d.%m.%Y')
        newest = datetime.fromtimestamp(photos[-1]['date']).strftime('%d.%m.%Y')
        
        stats_text = f"""
📊 Статистика фото:

• Всего фото: {len(photos)}
• Самое старое: {oldest}
• Самое новое: {newest}
• Последнее обновление: {datetime.fromtimestamp(last_update_time).strftime('%d.%m.%Y %H:%M')}

Используйте /random_photo для получения случайного фото!
"""
        bot.reply_to(message, stats_text)
        
    except Exception as e:
        logging.error(f"Ошибка в команде photo_stats: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при получении статистики")

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

# Функция для авто-постинга (если нужно)
def auto_post_random_photo(chat_id, interval_hours=24):
    """
    Функция для автоматической отправки случайных фото с интервалом
    """
    while True:
        try:
            post_random_photo(chat_id, "🔄 Автоматическое обновление: случайное фото из канала!")
            time.sleep(interval_hours * 3600)  # Ждем указанное количество часов
        except Exception as e:
            logging.error(f"Ошибка в авто-постинге: {e}")
            time.sleep(3600)  # Ждем 1 час при ошибке

# Запуск бота
if __name__ == "__main__":
    logging.info("Бот запущен...")
    
    # Предварительная загрузка фото при старте
    logging.info("Загружаем фото из канала...")
    get_channel_photos()
    
    # Если нужно запустить авто-постинг в определенный чат, раскомментируйте:
    # import threading
    # auto_thread = threading.Thread(target=auto_post_random_photo, args=("@your_channel", 24))
    # auto_thread.daemon = True
    # auto_thread.start()
    
    bot.infinity_polling()
