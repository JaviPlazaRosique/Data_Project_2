FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", ":5000", "--workers", "1", "--threads", "8", "--timeout", "0", "main:server"]