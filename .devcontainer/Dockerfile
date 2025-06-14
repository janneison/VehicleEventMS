# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.10-bookworm

# Actualiza paquetes e instala algunas dependencias del sistema
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    libpq-dev # Para psycopg2/asyncpg, necesario para la conexión a PostgreSQL

# Instala dependencias de Python
COPY requirements.txt requirements-dev.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements-dev.txt

# Copia la configuración de pre-commit
COPY .pre-commit-config.yaml /root/.pre-commit-config.yaml

# Instala los hooks de pre-commit dentro del contenedor
RUN pre-commit install --install-hooks

# (Opcional) Configura la zona horaria si es crítica para tu aplicación o pruebas
# Por ejemplo, para Barranquilla, Atlantico, Colombia (UTC-5)
ENV TZ=America/Bogota
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Configura variables de entorno para que devcontainer.json pueda usarlas
# (Esto es un ejemplo, las vars sensibles deben ir en .env o secrets)
ENV PYTHONUNBUFFERED=1

# Configuración de usuario por defecto (vscode)
# Esta imagen base ya lo maneja por defecto, pero es bueno saberlo.
# Si cambias el usuario, asegúrate de que tiene los permisos adecuados para /workspaces.