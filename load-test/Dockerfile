FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY load_test.py .
COPY application_scenario.py .

RUN mkdir -p /config

ENTRYPOINT ["python", "load_test.py"]
