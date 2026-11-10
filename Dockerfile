FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# /data doit être un volume persistant : il contient la base et les images.
ENV NOEL_DATABASE_URL=sqlite:////data/app.db \
    NOEL_MEDIA_DIR=/data/media \
    NOEL_SECURE_COOKIES=true
VOLUME /data
EXPOSE 8000

# NOEL_SECRET_KEY doit être défini dans les variables d'environnement de l'hébergeur.
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
