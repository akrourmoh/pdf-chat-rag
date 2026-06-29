# ── Backend image for the PDF Chat API ───────────────────────────────────────
FROM python:3.13-slim

# Keep Python output unbuffered and skip writing .pyc files (cleaner logs/images).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# The API listens on this port inside the container.
EXPOSE 8000

# Start the API. Uses $PORT if the platform provides one (e.g. Render), else 8000.
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
