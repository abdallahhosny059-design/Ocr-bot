import discord
from discord.ext import commands
import requests
import os
from io import BytesIO
from PIL import Image
import pytesseract
from openai import OpenAI

# ====== ENV VARIABLES ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing")

# ====== OPENAI CLIENT ======
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ====== DISCORD BOT ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== OCR FUNCTION ======
def extract_text_from_image(image_url):
    response = requests.get(image_url, timeout=20)
    img = Image.open(BytesIO(response.content))
    # دعم الإنجليزية والكورية واليابانية
    text = pytesseract.image_to_string(img, lang='eng+kor+jpn')
    return text.strip()

# ====== READY EVENT ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ====== MESSAGE EVENT ======
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not message.attachments:
        return

    for attachment in message.attachments:
        if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")):
            continue

        await message.channel.send("📖 جارٍ استخراج النص...")

        try:
            extracted_text = extract_text_from_image(attachment.url)
        except Exception as e:
            print("OCR ERROR:", e)
            await message.channel.send("❌ حدث خطأ أثناء استخراج النص.")
            continue

        if not extracted_text:
            await message.channel.send("❌ لم يتم العثور على نص.")
            continue

        await message.channel.send("🧠 جارٍ التعريب الأدبي...")

        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """هذا نص من إحدى المانهوا. أرجو ترجمته إلى العربية الفصحى الرفيعة مع اعتماد تعريب أدبي محكم (Localization) يصوغ المعنى بروح النص، ويحافظ على دلالته كاملة دون زيادة أو نقصان.

تعليمات التعريب:

لا تُنقل الكلمات أو الألقاب حرفيًا. اختر أقرب معنى عربي حسب سياق الحوار والقصة.
الأسماء الشخصية تُترك كما هي دون تغيير.
لا تضف أو تحذف أي حدث أو معنى.
حافظ على أسلوب، نبرة، وشخصية كل شخصية كما في النص الأصلي.
راقب الإملاء، النحو، علامات الترقيم، والهمزات بدقة.
اجعل الحوار يبدو طبيعيًا وكأنه مكتوب أصلًا بالعربية، مع الحفاظ على شعور النص وروحه.
المرجو إخراج الترجمة فقط، خالية من الشروح والتعليقات."""
                    },
                    {"role": "user", "content": extracted_text}
                ]
            )

            translated_text = response.choices[0].message.content
            await message.channel.send(translated_text)

        except Exception as e:
            print("OPENAI ERROR:", e)
            await message.channel.send("❌ حدث خطأ أثناء الترجمة.")

    await bot.process_commands(message)

# ====== RUN BOT ======
bot.run(DISCORD_TOKEN)
