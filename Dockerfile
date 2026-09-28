FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "if [ \"$DEBUG\" = \"True\" ]; then uv run python -m src.main; else uv run gunicorn -w 1 --threads 4 --timeout 60 -b 0.0.0.0:5000 src.main:app; fi"]