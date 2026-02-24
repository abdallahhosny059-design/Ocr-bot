FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-kor \
    tesseract-ocr-jpn \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
