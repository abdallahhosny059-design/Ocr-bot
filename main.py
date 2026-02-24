import discord
from discord.ext import commands
import requests
import os
import sys
from openai import OpenAI

sys.stdout.reconfigure(line_buffering=True)

# ====== ENV ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing")

if not OCR_API_KEY:
    raise ValueError("OCR_API_KEY is missing")

client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ====== DISCORD ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== READY ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ====== MESSAGE ======
@bot.event
async def on_message(message):
    print("MESSAGE RECEIVED")

    if message.author == bot.user:
        return

    if not message.attachments:
        return

    for attachment in message.attachments:

        await message.channel.send("📖 جارٍ استخراج النص...")

        try:
            img = requests.get(attachment.url, timeout=20)

            ocr = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": ("image.png", img.content)},
                data={
                    "apikey": OCR_API_KEY,
                    "language": "auto",
                    "isOverlayRequired": False
                },
                timeout=30
            )

            result = ocr.json()
            print("OCR RESULT:", result)

            if not result.get("ParsedResults"):
                await message.channel.send("❌ فشل استخراج النص.")
                return

            extracted_text = result["ParsedResults"][0]["ParsedText"].strip()

        except Exception as e:
            print("OCR ERROR:", e)
            await message.channel.send("❌ حدث خطأ أثناء استخراج النص.")
            return

        if not extracted_text:
            await message.channel.send("❌ لم يتم العثور على نص.")
            return

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

# ====== RUN ======
bot.run(DISCORD_TOKEN, log_handler=None)
