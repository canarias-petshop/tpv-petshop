FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema operativo necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos y las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto al contenedor
COPY . .

# Exponer el puerto que usa Streamlit
EXPOSE 8501

COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Comando para comprobar que el contenedor está funcionando bien
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Streamlit + cron nocturno KPIs (23:05 Canarias)
ENTRYPOINT ["/entrypoint.sh"]
