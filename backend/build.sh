#!/usr/bin/env bash
# Detiene el despliegue inmediatamente si algún comando falla
set -o errexit

# Instala todas las dependencias de Python definidas en requirements.txt
pip install -r requirements.txt

# Empaqueta los archivos estáticos (CSS/JS de DRF y Admin) para servirlos con WhiteNoise
python manage.py collectstatic --no-input

# Crea y actualiza las tablas en la base de datos PostgreSQL de Render
python manage.py migrate

# Carga datos iniciales y sincroniza APIs externas (|| true evita fallos si ya existen datos en redeploys)
python manage.py seed_data || true
python manage.py run_sync || true
python manage.py seed_tipo_cambio || true
python manage.py seed_riesgo_historico || true
python manage.py calcular_riesgo || true
python manage.py seed_portafolios || true
