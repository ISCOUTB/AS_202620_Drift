# API FastAPI de DRIFT. Dos etapas para que la imagen final no lleve herramientas de compilación.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS dependencias
COPY requirements.txt .
RUN pip install --prefix=/instalado -r requirements.txt

FROM base
COPY --from=dependencias /instalado /usr/local
COPY . .
RUN useradd --uid 10001 --no-create-home app
USER app
EXPOSE 8000
# La API se publica bajo /api con Strip Path: --root-path hace que /api/docs funcione.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--root-path", "/api", "--proxy-headers", "--forwarded-allow-ips", "*"]
