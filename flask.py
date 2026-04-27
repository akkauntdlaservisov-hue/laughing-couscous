import telebot
import io
from huggingface_hub import InferenceClient
from deep_translator import GoogleTranslator
from ddgs import DDGS # Наш новый движок поиска

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8773199317:AAFIct_VqfoJ7yYxO-bR9bXLcKYjmlhS-ms'
HF_TOKEN = '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'

bot = telebot.TeleBot(BOT_TOKEN)
client = InferenceClient(token=HF_TOKEN)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def translate_to_en(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text

# --- ОБРАБОТЧИКИ КОМАНД ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Узнаем имя пользователя для персонализации
    user_name = message.from_user.first_name
    
    welcome_text = (
        f" привет, **{user_name}**! 👋\n"
        "─── **HASTAI CORE v3.5** ───\n\n"
        "🛰 **STATUS:** `System Online`\n"
        "📡 **NETWORK:** `Secure Connection Established`\n"
        "🛠 **ORG:** `TRIO & LogicWare`\n\n"
        "**ДОСТУПНЫЕ МОДУЛИ:**\n"
        "───\n"
        "🔍 `/sr` — **Global Search**\n"
        "   _Поиск по документации и сети_\n\n"
        "🧠 `/ai` — **Neural Assistant**\n"
        "   _Llama 3: Код, логика, DuckOS_\n\n"
        "🎨 `/ig` — **Visual Engine**\n"
        "   _SDXL: Генератор UI и концептов_\n\n"
        "📝 `/tr` — **Translate Unit**\n"
        "   _RU ↔ EN Технический перевод_\n"
        "───\n\n"
        "⚠️ **Console:** `Ready for input...`"
    )
    
    bot.reply_to(message, welcome_text, parse_mode="Markdown")
# 1. НОВАЯ ФУНКЦИЯ: ПОИСК В СЕТИ
@bot.message_handler(commands=['sr'])
def search_internet(message):
    query = message.text.replace('/s', '').strip()
    if not query:
        bot.reply_to(message, "Что ищем? Напиши например: /s как работает ассемблер")
        return

    msg = bot.reply_to(message, "🔍 Ищу в глобальной сети...")
    
    try:
        results_text = f"🌐 **Результаты по запросу:** `{query}`\n\n"
        
        # Настройка DDGS для более стабильного поиска
        with DDGS() as ddgs:
            # region='wt-wt' — это поиск по всему миру
            # safesearch='off' — чтобы ничего не скрывал
            search_results = list(ddgs.text(query, region='wt-wt', safesearch='off', max_results=5))
            
            if search_results:
                for i, r in enumerate(search_results, 1):
                    title = r.get('title', 'Без названия')
                    href = r.get('href', '#')
                    body = r.get('body', 'Описание отсутствует')[:150] + "..."
                    results_text += f"{i}. [{title}]({href})\n_{body}_\n\n"
            else:
                results_text = "❌ Интернет молчит. Попробуй сократить запрос до 2-3 слов."
        
        bot.edit_message_text(results_text, message.chat.id, msg.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    
    except Exception as e:
        # Если ошибка в библиотеке, бот скажет об этом
        bot.edit_message_text(f"❌ Ошибка движка: {str(e)}", message.chat.id, msg.message_id)
# 2. ТЕКСТОВЫЙ ИИ (Llama 3)
@bot.message_handler(commands=['ai'])
def chat_ai(message):
    prompt = message.text.replace('/ai', '').strip()
    if not prompt: return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            max_tokens=800 # Увеличил лимит для длинных кодов
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка ИИ: {e}")

# 3. КАРТИНКИ (SDXL - это работает всегда)
@bot.message_handler(commands=['ig'])
def generate_image(message):
    prompt_ru = message.text.replace('/img', '').strip()
    if not prompt_ru: return
    prompt_en = translate_to_en(prompt_ru)
    try:
        image = client.text_to_image(prompt_en, model="stabilityai/stable-diffusion-xl-base-1.0")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        bot.send_photo(message.chat.id, img_byte_arr.getvalue(), caption=f"🖼 {prompt_ru}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка фото: {e}")

# ЗАПУСК
print("HastSearch Bot запущен и готов к работе!")
bot.polling(none_stop=True)