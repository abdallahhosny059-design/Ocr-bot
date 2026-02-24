import discord
from discord.ext import commands
import requests
import os
from openai import OpenAI

# ====== ENV ======
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")

if not TOKEN:
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

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not message.attachments:
        return

    for attachment in message.attachments:

        # يقبل أي صورة
        if not attachment.content_type or not attachment.content_type.startswith("image"):
            continue

        await message.channel.send("📖 جارٍ استخراج النص...")

        try:
            # تحميل الصورة
            img_response = requests.get(attachment.url, timeout=20)

            # إرسالها للـ OCR
            ocr_response = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": ("image.png", img_response.content)},
                data={
                    "apikey": OCR_API_KEY,
                    "language": "eng",
                    "OCREngine": 2,
                    "scale": True
                },
                timeout=40
            )

            result = ocr_response.json()
            print("OCR RAW RESPONSE:", result)

            # لو فيه خطأ من OCR
            if result.get("IsErroredOnProcessing"):
                print("OCR ERROR MESSAGE:", result.get("ErrorMessage"))
                await message.channel.send("❌ فشل استخراج النص.")
                return

            if "ParsedResults" not in result:
                await message.channel.send("❌ فشل استخراج النص.")
                return

            extracted_text = result["ParsedResults"][0]["ParsedText"].strip()

        except Exception as e:
            print("OCR EXCEPTION:", e)
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

bot.run(TOKEN)
