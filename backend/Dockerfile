FROM python:3.10-slim

WORKDIR /app/foodgram

RUN apt-get update && apt-get install -y postgresql-client && apt-get clean

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000