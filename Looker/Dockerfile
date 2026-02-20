# Base Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgeos-dev \
    libproj-dev \
 && rm -rf /var/lib/apt/lists/*

# Copia solo requirements.txt primero
COPY requirements.txt .

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código
COPY main.py .

# Expone puerto 8080 para Cloud Run
EXPOSE 8080

# Comando de inicio
CMD ["python","main.py"]