FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .

ENV PORT=8080

CMD ["uv", "run", "python", "main.py"]
