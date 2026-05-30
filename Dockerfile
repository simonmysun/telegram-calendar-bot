FROM python:3.12-alpine3.20 AS base

WORKDIR /app/

COPY requirements.txt .
RUN pip install -q -r requirements.txt

# ---- test stage ----
FROM base AS test

COPY requirements-test.txt .
RUN pip install -q -r requirements-test.txt

COPY . .

CMD ["python", "-m", "pytest", "tests/", "-v"]

# ---- production stage ----
FROM base AS production

COPY . .

CMD ["python", "bot.py"]
