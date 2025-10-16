# Dockerfile PostgreSQL + PostGIS UTF-8 Nativo
# Ubuntu 22.04 + PostgreSQL 15 + PostGIS 3.3 - Sin problemas de encoding Windows

FROM ubuntu:22.04

# Establecer locale UTF-8 español nativo desde el inicio
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES:es
ENV LC_ALL=es_ES.UTF-8

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar PostgreSQL 14 + PostGIS + herramientas de migración
RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-contrib \
    postgresql-14-postgis-3 \
    postgresql-14-postgis-3-scripts \
    postgis \
    wget \
    curl \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar cliente PostgreSQL Python nativo (sin wrappers)
RUN pip3 install psycopg2-binary pandas sqlalchemy openpyxl

# Exponer puerto PostgreSQL
EXPOSE 5432

# Usar el método estándar de Docker para PostgreSQL
COPY init-db.sh /docker-entrypoint-initdb.d/init-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Configurar PostgreSQL para aceptar conexiones remotas
RUN echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/14/main/pg_hba.conf && \
    echo "listen_addresses = '*'" >> /etc/postgresql/14/main/postgresql.conf

# Comando de inicio PostgreSQL
CMD ["/usr/lib/postgresql/14/bin/postgres"]