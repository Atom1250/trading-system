FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    RUN_MODE=console

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["/app/docker-entrypoint.sh"]
