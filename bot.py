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
        
        # Для простоты будем использовать фиксированный набор file_id фото
        # В реальном приложении вам нужно будет получить эти ID другим способом
        
        # Временное решение: можно вручную добавить несколько file_id фото
        # которые бот уже получил из канала
        
        if not photos:
            # Если список пуст, попробуем получить информацию о канале
            try:
                chat = bot.get_chat(CHANNEL_USERNAME)
                logging.info(f"Информация о канале: {chat.title}")
            except Exception as e:
                logging.error(f"Не удалось получить информацию о канале: {e}")
        
        channel_photos = photos
        last_update_time = current_time
        logging.info(f"Загружено {len(channel_photos)} фото из канала")
        return photos
        
    except Exception as e:
        logging.error(f"Ошибка при получении фото из канала: {e}")
        return channel_photos

def get_random_photo():
    """
    Функция для получения случайного фото
    Временное решение - используем заранее подготовленные фото
    """
    # Временный список фото для демонстрации
    # ЗАМЕНИТЕ эти file_id на реальные из вашего канала
    demo_photos = [
        # Добавьте сюда реальные file_id фото из вашего канала
        # Пример: "AgACAgIAAxkBAAIB..."
    ]
    
    if demo_photos:
        return {'file_id': random.choice(demo_photos)}
    
    return None

def manual_add_photo(message):
    """
    Функция для ручного добавления фото в базу
    """
    global channel_photos
    
    if message.photo:
        largest_photo = max(message.photo, key=lambda p: p.file_size)
        photo_data = {
            'file_id': largest_photo.file_id,
            'message_id': message.message_id,
            'date': message.date
        }
        channel_photos.append(photo_data)
        logging.info(f"Добавлено новое фото в базу. Всего фото: {len(channel_photos)}")
        return photo_data
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        photo_data = {
            'file_id': message.document.file_id,
            'message_id': message.message_id,
            'date': message.date,
            'is_document': True
        }
        channel_photos.append(photo_data)
        logging.info(f"Добавлен новый документ-фото в базу. Всего фото: {len(channel_photos)}")
        return photo_data
    
    return None

def post_random_photo(chat_id, caption=None):
    """
    Функция для отправки случайного фото в указанный чат
    """
    try:
        photo_data = get_random_photo()
        if not photo_data:
            # Если нет фото в базе, предложим способ добавления
            bot.send_message(
                chat_id, 
                "📷 Фото еще не добавлены в базу.\n\n"
                "Чтобы добавить фото, просто отправьте его в этот чат с подписью '/add_photo'"
            )
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
/random_photo - случайное фото
/add_photo - добавить фото в базу (ответом на фото)
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
/random_photo - получить случайное фото
/add_photo - добавить новое фото в базу
/photo_stats - показать статистику по фото
"""
    bot.reply_to(message, help_text)

# Обработчик команды /random_photo
@bot.message_handler(commands=['random_photo'])
def send_random_photo(message):
    try:
        # Показываем, что бот загружает фото
        bot.send_chat_action(message.chat.id, 'upload_photo')
        
        # Отправляем случайное фото
        caption = "📸 Случайное фото!"
        post_random_photo(message.chat.id, caption)
        
    except Exception as e:
        logging.error(f"Ошибка в команде random_photo: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при получении фото")

# Обработчик команды /add_photo
@bot.message_handler(commands=['add_photo'])
def handle_add_photo_command(message):
    bot.reply_to(message, "📷 Отправьте фото в ответ на это сообщение, и я добавлю его в базу для случайной отправки!")

# Обработчик команды /photo_stats
@bot.message_handler(commands=['photo_stats'])
def send_photo_stats(message):
    try:
        photos = channel_photos
        
        if not photos:
            bot.reply_to(message, "❌ В базе пока нет фото. Используйте /add_photo чтобы добавить фото!")
            return
        
        # Сортируем по дате
        photos.sort(key=lambda x: x['date'])
        oldest = datetime.fromtimestamp(photos[0]['date']).strftime('%d.%m.%Y %H:%M')
        newest = datetime.fromtimestamp(photos[-1]['date']).strftime('%d.%m.%Y %H:%M')
        
        stats_text = f"""
📊 Статистика фото:

• Всего фото в базе: {len(photos)}
• Самое старое: {oldest}
• Самое новое: {newest}
• Последнее обновление: {datetime.fromtimestamp(last_update_time).strftime('%d.%m.%Y %H:%M')}

Используйте /random_photo для получения случайного фото!
"""
        bot.reply_to(message, stats_text)
        
    except Exception as e:
        logging.error(f"Ошибка в команде photo_stats: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при получении статистики")

# Обработчик фото
@bot.message_handler(content_types=['photo', 'document'])
def handle_photos(message):
    try:
        # Проверяем, является ли сообщение ответом на команду /add_photo
        if message.reply_to_message and message.reply_to_message.text and '/add_photo' in message.reply_to_message.text:
            photo_data = manual_add_photo(message)
            if photo_data:
                bot.reply_to(message, "✅ Фото успешно добавлено в базу!")
            else:
                bot.reply_to(message, "❌ Не удалось добавить фото. Убедитесь, что отправлено изображение.")
        
        # Если фото отправлено без команды, предлагаем добавить его
        elif message.photo or (message.document and message.document.mime_type and message.document.mime_type.startswith('image/')):
            bot.reply_to(
                message,
                "📷 Вижу, что вы отправили фото!\n\n"
                "Хотите добавить его в базу для случайной отправки?\n"
                "Ответьте на это сообщение командой /add_photo"
            )
            
    except Exception as e:
        logging.error(f"Ошибка при обработке фото: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке фото")

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
    
    # Предварительная загрузка фото при старте
    logging.info("Инициализация базы фото...")
    get_channel_photos()
    
    bot.infinity_polling()
