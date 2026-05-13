FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app/ ./app/

EXPOSE 8890

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8890", "--reload"]