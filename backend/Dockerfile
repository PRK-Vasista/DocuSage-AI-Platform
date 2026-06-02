# Start from a clean, stable Python image
FROM python:3.10-slim
WORKDIR /app

# Install dependencies first (for faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, migrations, and automated tests
COPY app/ ./app/
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY tests/ ./tests/
COPY pytest.ini .
EXPOSE 8000

# Command to run the application (with hot-reloading for development)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
