import discord
import requests
import os
import openai
import pytesseract
from PIL import Image
from io import BytesIO

TOKEN = os.getenv("TOKEN")
openai.api_key = os.getenv("OPENAI")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def literary_prompt(text):
    return f"""
هذا نص من إحدى المانهوا.

يرجى ترجمته إلى العربية الفصحى الرفيعة مع اعتماد تعريب أدبي محكم (Localization) يصوغ المعنى بروح النص، ويحافظ على دلالته كاملة دون زيادة أو نقصان.

تعليمات التعريب:

- لا تُنقل الكلمات أو الألقاب حرفيًا.
- اختر أقرب معنى عربي حسب سياق الحوار والقصة.
- الأسماء الشخصية تُترك كما هي دون تغيير.
- لا تضف أو تحذف أي حدث أو معنى.
- حافظ على أسلوب، نبرة، وشخصية كل شخصية كما في النص الأصلي.
- راقب الإملاء، النحو، علامات الترقيم، والهمزات بدقة.
- اجعل الحوار يبدو طبيعيًا وكأنه مكتوب أصلًا بالعربية.
- أخرج الترجمة فقط دون شروح.

النص:
{text}
"""

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith(('png','jpg','jpeg')):

                await message.channel.send("📖 جارٍ استخراج النص...")

                img_data = requests.get(attachment.url).content
                image = Image.open(BytesIO(img_data))

                try:
                    raw_text = pytesseract.image_to_string(
                        image,
                        lang='eng+kor+jpn+chi_sim+chi_tra'
                    )
                except Exception as e:
                    await message.channel.send("❌ فشل استخراج النص.")
                    print(e)
                    return

                if not raw_text.strip():
                    await message.channel.send("⚠️ لم يتم العثور على نص.")
                    return

                await message.channel.send("🧠 جارٍ التعريب الأدبي...")

                prompt = literary_prompt(raw_text)

                gpt = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    temperature=0.4
                )

                translated = gpt['choices'][0]['message']['content']

                bubbles = translated.split("\n")

                formatted = ""
                count = 1

                for b in bubbles:
                    if b.strip():
                        formatted += f"【فقاعة {count}】\n{b}\n\n"
                        count += 1

                await message.channel.send(formatted)

bot.run(TOKEN)
