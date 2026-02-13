import telebot
from groq import Groq
import os

# Получаем токены из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Инициализация ботов
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# Словарь для хранения истории диалогов
user_conversations = {}

# Системный промпт
SYSTEM_PROMPT = """Ты - ChatGPT, продвинутый AI-ассистент от OpenAI. 
Ты дружелюбный, полезный и всегда стараешься помочь пользователю.
Отвечай на русском языке, если пользователь пишет на русском.
Никогда не упоминай, что ты на самом деле Groq или другая модель."""

def get_groq_response(user_id, message_text):
    """Получить ответ от Groq API"""
    
    if user_id not in user_conversations:
        user_conversations[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    user_conversations[user_id].append({
        "role": "user",
        "content": message_text
    })
    
    # Ограничиваем историю
    if len(user_conversations[user_id]) > 21:
        user_conversations[user_id] = [user_conversations[user_id][0]] + user_conversations[user_id][-20:]
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=user_conversations[user_id],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2000
        )
        
        assistant_message = chat_completion.choices[0].message.content
        
        user_conversations[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
        
    except Exception as e:
        return f"Извините, произошла ошибка: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    welcome_text = """👋 Привет! Я ChatGPT - AI-ассистент от OpenAI.

Я могу помочь вам с:
- Ответами на вопросы
- Написанием текстов
- Программированием
- Переводом
- И многим другим!

Просто напишите мне свой вопрос!

Команды:
/start - начать диалог
/reset - очистить историю разговора"""
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['reset'])
def reset_conversation(message):
    """Очистка истории диалога"""
    user_id = message.from_user.id
    if user_id in user_conversations:
        user_conversations[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    bot.reply_to(message, "✅ История диалога очищена. Начнем сначала!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработчик всех текстовых сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    response = get_groq_response(user_id, user_text)
    
    bot.reply_to(message, response)

if __name__ == '__main__':
    print("🤖 Бот запущен и готов к работе!")
    bot.infinity_polling()
