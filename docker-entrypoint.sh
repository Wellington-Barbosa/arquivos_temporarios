#!/bin/bash
set -e

# Carrega variáveis do .env manualmente
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "[INFO] Aguarde, verificando conexão com o PostgreSQL..."

# Aguarda até o PostgreSQL estar pronto
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL ainda não está pronto. Aguardando..."
  sleep 2
done

echo "[INFO] PostgreSQL está acessível. Iniciando criação das tabelas..."

# Executa o script SQL de criação de tabelas
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/init.sql

echo "[INFO] Tabelas criadas com sucesso. Iniciando aplicação Flask..."

# Inicia o Flask
exec gunicorn -b 0.0.0.0:5001 app:app
