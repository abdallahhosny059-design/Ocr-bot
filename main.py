import discord
from discord.ext import commands
import requests
import os
from openai import OpenAI

# ====== ENV ======
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")

# تحذيرات لو المتغيرات مش موجودة
if not TOKEN:
    print("⚠️ تحذير: DISCORD_TOKEN غير موجود، البوت مش هيقدر يتصل بالديسكورد")
if not OPENAI_API_KEY:
    print("⚠️ تحذير: OPENAI_API_KEY غير موجود، الترجمة مش هتشتغل")
if not OCR_API_KEY:
    print("⚠️ تحذير: OCR_API_KEY غير موجود، استخراج النص مش هيشتغل")

# ====== OPENAI CLIENT ======
client_ai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ====== DISCORD ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== OCR SPACE ======
def extract_text_from_image(image_url):
    if not OCR_API_KEY:
        return None

    try:
        img = requests.get(image_url, timeout=20)
        ocr = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": img.content},
            data={
                "apikey": OCR_API_KEY,
                "language": "eng"  # افتراضي للإنجليزي
            },
            timeout=30
        )
        result = ocr.json()
        if result.get("IsErroredOnProcessing"):
            print("OCR SPACE ERROR:", result.get("ErrorMessage"))
            return None

        parsed = result.get("ParsedResults")
        if not parsed or len(parsed) == 0:
            return None

        return parsed[0].get("ParsedText", "").strip()
    except Exception as e:
        print("OCR EXCEPTION:", e)
        return None

# ====== READY ======
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ====== MESSAGE HANDLER ======
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

        extracted_text = extract_text_from_image(attachment.url)
        if not extracted_text:
            await message.channel.send("❌ لم يتم استخراج أي نص أو حدث خطأ في OCR.")
            continue

        if not client_ai:
            await message.channel.send("⚠️ مفتاح OpenAI مش موجود، الترجمة مش هتشتغل.")
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

# ====== RUN ======
if TOKEN:
    bot.run(TOKEN)
else:
    print("⚠️ البوت لن يبدأ لأن DISCORD_TOKEN غير موجود")
