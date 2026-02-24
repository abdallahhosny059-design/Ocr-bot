import discord
import requests
import os
from openai import OpenAI

# ====== ENV VARIABLES ======
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OCR_API_KEY = os.getenv("OCR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing")

if not OCR_API_KEY:
    raise ValueError("OCR_API_KEY is missing")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing")

# ====== OPENAI CLIENT ======
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ====== DISCORD ======
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ====== PROMPT ======
def literary_prompt(text):
    return f"""
هذا نصٌّ  من إحدى المانهوا. أرجو ترجمته إلى العربية الفصحى الرفيعة مع اعتماد تعريب أدبي محكم (Localization) يصوغ المعنى بروح النص، ويحافظ على دلالته كاملة دون زيادة أو نقصان.

تعليمات التعريب:

لا تُنقل الكلمات أو الألقاب حرفيًا. اختر أقرب معنى عربي حسب سياق الحوار والقصة.

الأسماء الشخصية تُترك كما هي دون تغيير.

لا تضف أو تحذف أي حدث أو معنى.

حافظ على أسلوب، نبرة، وشخصية كل شخصية كما في النص الأصلي.

راقب الإملاء، النحو، علامات الترقيم، والهمزات بدقة.

اجعل الحوار يبدو طبيعيًا وكأنه مكتوب أصلًا بالعربية، مع الحفاظ على شعور النص وروحه.

المرجو إخراج الترجمة فقط، خالية من الشروح والتعليقات.

النص:
{text}
"""

# ====== READY ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ====== MESSAGE ======
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not message.attachments:
        return

    for attachment in message.attachments:
        if not attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
            continue

        await message.channel.send("📖 جارٍ استخراج النص...")

        try:
            img = requests.get(attachment.url, timeout=20)

            ocr = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": img.content},
                data={
                    "apikey": OCR_API_KEY,
                    "language": "kor"
                },
                timeout=30
            )

            result = ocr.json()

            if "ParsedResults" not in result:
                await message.channel.send("❌ فشل استخراج النص.")
                return

            raw_text = result["ParsedResults"][0]["ParsedText"]

            if not raw_text.strip():
                await message.channel.send("⚠️ لم يتم العثور على نص.")
                return

        except Exception as e:
            await message.channel.send("❌ حدث خطأ أثناء OCR.")
            print("OCR ERROR:", e)
            return

        await message.channel.send("🧠 جارٍ التعريب الأدبي...")

        try:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": literary_prompt(raw_text)}]
            )

            translated = response.choices[0].message.content

        except Exception as e:
            await message.channel.send("❌ حدث خطأ أثناء الترجمة.")
            print("OPENAI ERROR:", e)
            return

        bubbles = [b.strip() for b in translated.split("\n") if b.strip()]

        formatted = ""
        for i, bubble in enumerate(bubbles, start=1):
            formatted += f"【فقاعة {i}】\n{bubble}\n\n"

        await message.channel.send(formatted)


# ====== RUN ======
bot.run(DISCORD_TOKEN)
