# syntax=docker/dockerfile:1.4
# Usa una imagen base oficial de Python.
# La versión "slim-buster" es más pequeña que la estándar y viene con menos librerías extra.
# Puedes considerar "slim-bookworm" si prefieres la versión más reciente de Debian.
FROM python:3.10-slim-buster

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para las librerías de Python.
# 'build-essential' es para compilar dependencias C.
# 'libpq-dev' es crucial para 'asyncpg' (el driver de PostgreSQL que usa SQLAlchemy).
# '--no-install-recommends' y 'rm -rf /var/lib/apt/lists/*' ayudan a mantener la imagen pequeña.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia solo el archivo de requerimientos de producción y luego instálalos.
# Esto aprovecha el caché de Docker: si los requerimientos no cambian, este paso no se vuelve a ejecutar.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación al directorio de trabajo.
# Esto se hace después de la instalación de dependencias para asegurar que los cambios en el código
# no invaliden el caché de la capa de instalación de dependencias.
COPY . .

# Configura variables de entorno para la aplicación.
# PYTHONUNBUFFERED=1 asegura que los logs de Python se muestren en tiempo real en Docker.
# PYTHONPATH asegura que Python encuentre tus módulos internos correctamente.
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expone el puerto en el que correrá tu aplicación FastAPI.
# Esto no publica el puerto automáticamente, solo lo declara.
EXPOSE 8000

# Comando para ejecutar la aplicación cuando el contenedor se inicie.
# Ejecutamos uvicorn directamente, apuntando a tu aplicación FastAPI dentro del paquete 'app'.
# '0.0.0.0' hace que la aplicación sea accesible desde fuera del contenedor.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]