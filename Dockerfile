FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && pip uninstall -y pinecone-plugin-inference || true

COPY . .

EXPOSE 5000

# Simple: run the dev server for ease of testing
CMD ["python", "app.py"]

