import telebot
import io
import threading
import os
from flask import Flask
from huggingface_hub import InferenceClient
from deep_translator import GoogleTranslator
from ddgs import DDGS

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8773199317:AAFIct_VqfoJ7yYxO-bR9bXLcKYjmlhS-ms'
HF_TOKEN = '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'

bot = telebot.TeleBot(BOT_TOKEN)
client = InferenceClient(token=HF_TOKEN)

# --- FLASK СЕРВЕР (Keep Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "HastAI Core is Running!"

def run_flask():
    # Render передает порт в переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def translate_to_en(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text

# --- ОБРАБОТЧИКИ КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f" привет, **{user_name}**! 👋\n"
        "─── **HASTAI CORE v3.6** ───\n\n"
        "🛰 **STATUS:** `System Online` (Flask Protected)\n"
        "📡 **NETWORK:** `Secure Connection Established`\n"
        "🛠 **ORG:** `TRIO & LogicWare`\n\n"
        "**ДОСТУПНЫЕ МОДУЛИ:**\n"
        "───\n"
        "🔍 `/sr` — **Global Search**\n"
        "🧠 `/ai` — **Neural Assistant**\n"
        "🎨 `/ig` — **Visual Engine**\n"
        "📝 `/tr` — **Translate Unit**\n"
        "───\n\n"
        "⚠️ **Console:** `Ready for input...`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['sr'])
def search_internet(message):
    query = message.text.replace('/sr', '').strip()
    if not query:
        bot.reply_to(message, "Что ищем?")
        return
    msg = bot.reply_to(message, "🔍 Ищу в глобальной сети...")
    try:
        results_text = f"🌐 **Результаты по запросу:** `{query}`\n\n"
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, region='wt-wt', safesearch='off', max_results=5))
            if search_results:
                for i, r in enumerate(search_results, 1):
                    title = r.get('title', 'Без названия')
                    href = r.get('href', '#')
                    body = r.get('body', 'Описание отсутствует')[:150] + "..."
                    results_text += f"{i}. [{title}]({href})\n_{body}_\n\n"
            else:
                results_text = "❌ Ничего не найдено."
        bot.edit_message_text(results_text, message.chat.id, msg.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка поиска: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(commands=['ai'])
def chat_ai(message):
    prompt = message.text.replace('/ai', '').strip()
    if not prompt: return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            max_tokens=800
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка ИИ: {e}")

@bot.message_handler(commands=['ig'])
def generate_image(message):
    prompt_ru = message.text.replace('/ig', '').strip()
    if not prompt_ru: return
    msg = bot.reply_to(message, "🎨 Генерирую...")
    prompt_en = translate_to_en(prompt_ru)
    try:
        image = client.text_to_image(prompt_en, model="stabilityai/stable-diffusion-xl-base-1.0")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        bot.send_photo(message.chat.id, img_byte_arr.getvalue(), caption=f"🖼 {prompt_ru}")
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка фото: {e}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    # 1. Запускаем Flask в отдельном потоке, чтобы он не мешал боту
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # 2. Запускаем бота
    print("HastAI Core v3.6 + Flask Server запущен!")
    bot.polling(none_stop=True)
