FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/* \
    && tr -d '\000' < requirements.txt > /tmp/requirements.clean.txt \
    && pip install --no-cache-dir -r /tmp/requirements.clean.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_DEBUG=1

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
