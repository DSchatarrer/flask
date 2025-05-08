# Usa la imagen base de Python 3.8.20
FROM python:3.8.20-slim

# Instala dependencias del sistema (libgtk y OpenCV)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgtk-3-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia requirements.txt e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código
COPY . .

# Expone el puerto
EXPOSE 8080

# Ejecuta la app
CMD ["python", "src/app.py"]
