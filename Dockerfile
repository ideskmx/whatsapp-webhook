FROM python:3.11-slim

# Evita que Python bufferice la salida para ver los logs en tiempo real
ENV PYTHONUNBUFFERED=True
WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY main.py .

# Cloud Run inyecta automáticamente la variable de entorno $PORT (por defecto 8080)
# Se ejecuta Gunicorn apuntando al objeto app dentro de main.py
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
