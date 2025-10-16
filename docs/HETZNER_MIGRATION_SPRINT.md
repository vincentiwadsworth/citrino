#  Sprint: Migración Citrino a Producción - Hetzner Cloud

**Documento de referencia para futuro deployment en producción**

---

##  Resumen Ejecutivo

### Objetivo del Sprint
Migrar Citrino desde desarrollo local a producción en Hetzner Cloud CPX11, manteniendo la arquitectura actual basada en PostgreSQL + PostGIS y todos los motores de recomendación ya desarrollados.

### Estado Actual del Proyecto
-  **ETL completado**: Datos migrados desde fuentes originales a PostgreSQL + PostGIS
-  **Motores de recomendación**: Funcionando con consultas nativas PostGIS
-  **API REST**: Flask con endpoints optimizados para base de datos relacional
-  **Chatbot UI**: Integrado y funcionando con datos estructurados
-  **Producción**: Requiere deployment en VPS para acceso externo

### Arquitectura a Desplegar
```
Hetzner Cloud CPX11 (€5.09/mes)
 Ubuntu 22.04 LTS
 PostgreSQL 15 + PostGIS 3.3
    Tabla: propiedades (1,588 registros)
    Tabla: servicios (4,777 registros)
    Índices GIST para consultas geoespaciales
 Python 3.11 + Flask 2.3.3
    recommendation_engine.py
    recommendation_engine_postgis.py (con PostGIS)
    property_catalog.py
    chatbot_completions.py
 Nginx (Reverse Proxy + SSL)
 Gunicorn (WSGI Server)
 Let's Encrypt (SSL gratuito)
```

---

##  Requerimientos del Sistema en Producción

### Recursos del Servidor (Hetzner CPX11)
- **CPU**: 2 vCPUs dedicados
- **RAM**: 2 GB (suficiente para arquitectura actual)
- **Storage**: 40 GB NVMe SSD
- **Tráfico**: 1 TB/mes incluido

### Consumo Estimado de Recursos
```
PostgreSQL + PostGIS:     ~400-600 MB
Python Flask + Gunicorn:  ~200-300 MB
Nginx + Sistema operativo: ~200-300 MB
Cache y queries activas:  ~200-400 MB
Total estimado:           1.0-1.6 GB 
```

### Software Requerido
- **PostgreSQL 15** con extensión **PostGIS 3.3**
- **Python 3.11** con dependencias del proyecto
- **Nginx** para reverse proxy y serving estático
- **Gunicorn** como WSGI server
- **Let's Encrypt** para SSL/TLS

---

##  Estructura del Deployment

### Directorios en Producción
```
/home/citrino/
 citrino/                    # Código fuente
    api/
       server.py
    src/
       recommendation_engine.py
       recommendation_engine_postgis.py
       property_catalog.py
       llm_integration.py
    requirements.txt
    .env                    # Variables de entorno
 database/
    backups/                # Backups automáticos
    logs/                   # Logs PostgreSQL
 nginx/
    nginx.conf              # Configuración Nginx
    ssl/                    # Certificados SSL
 scripts/
     deploy.sh               # Script de deployment
     backup.sh               # Backup automático
     monitor.sh              # Monitoreo básico
```

### Configuración de Base de Datos
```sql
-- Base de datos: citrino_prod
-- Extensiones requeridas:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Tablas principales existentes:
-- - propiedades (con coordenadas GEOGRAPHY)
-- - servicios (con coordenadas GEOGRAPHY)
-- - agentes (normalizada)

-- Índices existentes:
-- - idx_propiedades_coordenadas (GIST)
-- - idx_servicios_coordenadas (GIST)
-- - idx_propiedades_zona_precio_tipo (B-Tree)
```

---

##  Plan de Sprint (8 Commits Estructurados)

### **Commit 1: Preparación del Entorno**
- Crear branch `feature/hetzner-production`
- Configurar estructura de directorios para producción
- Crear scripts de setup inicial
- Documentación de requerimientos del servidor

### **Commit 2: Configuración de Infraestructura**
- Script Terraform para aprovisionar CPX11
- Configuración de seguridad básica (SSH keys, firewall)
- Setup de networking y dominio
- Configuración de backups automáticos

### **Commit 3: Setup Base de Datos**
- Instalación PostgreSQL 15 + PostGIS 3.3
- Migración de datos desde desarrollo local
- Configuración de índices optimizados
- Script de backup y restore

### **Commit 4: Configuración Python + Flask**
- Instalación Python 3.11 y dependencias
- Configuración variables de entorno
- Setup Gunicorn con workers optimizados
- Testing de conectividad a base de datos

### **Commit 5: Configuración Nginx + SSL**
- Instalación y configuración Nginx
- Configuración reverse proxy a Gunicorn
- Instalación certificado Let's Encrypt
- Optimización serving estático

### **Commit 6: Deployment de Aplicación**
- Deploy de código fuente completo
- Configuración health checks
- Testing de endpoints principales
- Validación de motores de recomendación

### **Commit 7: Monitoreo y Logging**
- Configuración logs estructurados
- Setup monitoreo básico (Uptime Kuma)
- Alertas por email
- Scripts de mantenimiento automático

### **Commit 8: Documentación y Handover**
- Documentación completa de producción
- Guía de troubleshooting
- Procedimientos de backup/restore
- Checklist de verificación final

---

##  Scripts Clave de Deployment

### Script de Deploy Principal
```bash
#!/bin/bash
# deploy.sh - Deployment completo de Citrino

# Variables
APP_DIR="/home/citrino/citrino"
BACKUP_DIR="/home/citrino/database/backups"
NGINX_CONF="/home/citrino/nginx/nginx.conf"

# 1. Backup actual
./scripts/backup.sh

# 2. Actualizar código
cd $APP_DIR
git pull origin main
pip install -r requirements.txt

# 3. Restart servicios
systemctl restart gunicorn
systemctl reload nginx

# 4. Health check
curl -f http://localhost:5001/api/health || exit 1

echo " Deployment completado exitosamente"
```

### Script de Backup Automático
```bash
#!/bin/bash
# backup.sh - Backup de base de datos

DB_NAME="citrino_prod"
BACKUP_FILE="$BACKUP_DIR/citrino_$(date +%Y%m%d_%H%M%S).sql"

pg_dump $DB_NAME > $BACKUP_FILE
gzip $BACKUP_FILE

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo " Backup completado: $BACKUP_FILE.gz"
```

---

##  Variables de Entorno de Producción

### .env Configuration
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=citrino_prod
DB_USER=citrino_user
DB_PASSWORD=secure_password_here

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
PORT=5001

# LLM Integration
ZAI_API_KEY=your_zai_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
LLM_PROVIDER=zai

# External Services
DOMAIN=citrino.yourdomain.com
SSL_EMAIL=admin@yourdomain.com
```

### Configuración Gunicorn
```python
# gunicorn.conf.py
bind = "127.0.0.1:5001"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

---

##  Configuración PostgreSQL Optimizada

### postgresql.conf (2GB RAM)
```ini
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 50
listen_addresses = 'localhost'

# WAL settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query optimization
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Queries PostGIS Optimizadas
```sql
-- Query de ejemplo: propiedades cerca de servicios
WITH params AS (
    SELECT -17.783 AS lat, -63.182 AS lng, 2000 AS radio_metros
)
SELECT p.*,
       ST_Distance(p.coordenadas, ST_MakePoint(-63.182, -17.783)::geography) as distancia
FROM propiedades p
WHERE ST_DWithin(
    p.coordenadas,
    ST_MakePoint(-63.182, -17.783)::geography,
    (SELECT radio_metros FROM params)
)
ORDER BY distancia
LIMIT 10;
```

---

##  Configuración de Seguridad

### Firewall Rules
```bash
# Permitir SSH (puerto 22)
ufw allow 22

# Permitir HTTP/HTTPS
ufw allow 80
ufw allow 443

# Denegar todo lo demás
ufw default deny incoming
ufw default allow outgoing
ufw enable
```

### SSL con Let's Encrypt
```bash
# Obtener certificado
certbot --nginx -d citrino.yourdomain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

---

##  Monitoreo y Mantenimiento

### Health Checks
```bash
# Verificar estado de servicios
systemctl status postgresql
systemctl status gunicorn
systemctl status nginx

# Health check de API
curl -f http://localhost:5001/api/health

# Verificar uso de recursos
htop
df -h
free -h
```

### Logs Importantes
```bash
# Logs de aplicación
tail -f /var/log/gunicorn/error.log

# Logs de PostgreSQL
tail -f /var/log/postgresql/postgresql-15-main.log

# Logs de Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

##  Procedimientos de Deployment

### Deployment Inicial (Setup)
```bash
# 1. Crear servidor en Hetzner Cloud
# 2. Configurar SSH keys
# 3. Clonar repositorio
git clone https://github.com/user/citrino.git

# 4. Ejecutar script de setup
./scripts/setup.sh

# 5. Migrar base de datos
./scripts/migrate_db.sh

# 6. Configurar SSL
./scripts/setup_ssl.sh

# 7. Iniciar servicios
systemctl start postgresql gunicorn nginx
```

### Updates de Producción
```bash
# 1. Backup actual
./scripts/backup.sh

# 2. Pull cambios
git pull origin main

# 3. Actualizar dependencias
pip install -r requirements.txt

# 4. Restart servicios
systemctl restart gunicorn
systemctl reload nginx

# 5. Verificar deployment
./scripts/health_check.sh
```

---

##  Checklist de Verificación Final

###  Pre-Deployment
- [ ] Servidor CPX11 creado y configurado
- [ ] PostgreSQL + PostGIS instalado
- [ ] Datos migrados y validados
- [ ] Variables de entorno configuradas
- [ ] SSL certificado instalado
- [ ] Firewall configurado
- [ ] Backups automáticos activados

###  Post-Deployment
- [ ] API responde correctamente
- [ ] Motores de recomendación funcionan
- [ ] Chatbot UI operativo
- [ ] Consultas geoespaciales rápidas (<100ms)
- [ ] Monitoreo funcionando
- [ ] Logs configurados
- [ ] Documentación completa

###  Rendimiento
- [ ] Tiempo de respuesta <200ms
- [ ] Uso RAM <80%
- [ ] Uso CPU <50%
- [ ] Espacio disco <70%
- [ ] Queries usando índices PostGIS
- [ ] SSL funcionando correctamente

---

##  Procedimientos de Emergency

### Rollback Automático
```bash
# Si deployment falla:
./scripts/rollback.sh

# Rollback manual:
systemctl stop gunicorn
git checkout HEAD~1
pip install -r requirements.txt
systemctl start gunicorn
```

### Recovery de Base de Datos
```bash
# Restaurar desde backup
gunzip -c /path/to/backup.sql.gz | psql citrino_prod

# Verificar integridad
./scripts/validate_db.sh
```

---

##  Costos Estimados Mensuales

### Hetzner Cloud CPX11
- **Servidor**: €5.09/mes
- **Backup opcional**: €1.59/mes
- **Tráfico extra**: €0.01/GB (después de 1TB)
- **Dominio**: ~€10/año
- **Total estimado**: €7-10/mes

### Costos Anuales
- **Infraestructura**: €85-120/año
- **Dominio**: €10/año
- **Total**: ~€100-130/año

---

##  Referencias y Documentación

### Enlaces Útiles
- [Hetzner Cloud Docs](https://docs.hetzner.com/cloud)
- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [PostGIS 3.3 Documentation](https://postgis.net/docs/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)

### Comandos Rápidos
```bash
# Reiniciar servicios
systemctl restart postgresql gunicorn nginx

# Ver logs
journalctl -u gunicorn -f

# Backup rápido
pg_dump citrino_prod | gzip > backup_$(date +%Y%m%d).sql.gz

# Health check
curl -I https://citrino.yourdomain.com/api/health
```

---

##  Próximos Pasos Futuros

### Mejoras Post-Deployment
- Configurar CDN para assets estáticos
- Implementar cache Redis
- Setup de monitoreo avanzado (Prometheus + Grafana)
- Configurar CI/CD automático
- Implementar escala horizontal (load balancer)

### Monitoreo Avanzado
- Alertas personalizadas
- Dashboard de métricas
- Backup automático a cloud storage
- Logs centralizados
- Performance monitoring

---

**Documento creado**: 2025-10-15
**Autoría**: Claude Code Assistant
**Estado**: Plan de referencia para futuro deployment
**Versión**: v1.0 (basada en arquitectura actual PostgreSQL + PostGIS)

---

### NOTA IMPORTANTE
Este documento asume que:
1. **ETL ya completado**: Datos en PostgreSQL + PostGIS
2. **Motores funcionando**: Usando consultas nativas PostGIS
3. **Sin procesamiento JSON**: Archivos JSON ya migrados a BD
4. **API desarrollada**: Endpoints listos para producción
5. **Desarrollo local completo**: Solo requiere deployment

**NO incluye**:
-  Procesamiento de archivos JSON
-  Scripts ETL
-  Migración desde archivos planos
-  Setup de motores desde cero

El objetivo es un deployment puro de producción.