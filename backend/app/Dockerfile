FROM python:3.10-slim

WORKDIR /app
COPY app/requirements.txt .

RUN pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
