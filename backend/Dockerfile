FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system flowka && adduser --system --ingroup flowka flowka

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY app ./app

USER flowka

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
