#!/bin/bash
set -e

echo "[INFO] Aguardando conexão com PostgreSQL em $DB_HOST..."

until PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL não disponível. Aguardando..."
  sleep 2
done

echo "[INFO] PostgreSQL pronto. Executando sql/init.sql..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f /app/sql/init.sql

echo "[INFO] Tabelas criadas. Iniciando Gunicorn..."
exec gunicorn -b 0.0.0.0:5001 app:app
