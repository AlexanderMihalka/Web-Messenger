FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
# Один воркер навмисно: реєстр WebSocket-з'єднань і rate-limiter живуть у пам'яті процесу
# (app/websocket/manager.py, app/core/rate_limit.py). З кількома воркерами кожен мав би
# свій окремий реєстр, і push-повідомлення не долітали б до сокета на іншому воркері.
# Горизонтальне масштабування вимагало б винести обидва стани в Redis — свідомо поза
# межами цього навчального проєкту (детальніше — у README, розділ "Відомі обмеження").
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
