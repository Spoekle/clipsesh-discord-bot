FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY bot.py .
COPY config.py .

RUN mkdir downloads

CMD ["python", "bot.py"]