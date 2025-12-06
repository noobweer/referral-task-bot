FROM python:3.11-slim

WORKDIR /app

COPY . /app/bot

COPY requirements.txt /app/bot/requirements.txt
RUN pip install --no-cache-dir -r /app/bot/requirements.txt

ENV PYTHONPATH=/app

CMD ["python", "bot/main.py"]