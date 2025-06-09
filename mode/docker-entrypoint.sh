#!/bin/bash
set -e

# Carrega o .env manualmente
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -d '\n')
fi

echo "[INFO] Aguarde, verificando conexão com o PostgreSQL..."

# Verifica se todas as variáveis necessárias estão presentes
for var in DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME; do
  if [ -z "${!var}" ]; then
    echo "[ERRO] Variável $var não está definida."
    exit 1
  fi
done

# Loop de verificação da conexão
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL ainda não está pronto. Aguardando..."
  sleep 2
done

echo "[INFO] PostgreSQL está acessível. Iniciando criação das tabelas..."

# Executa o script SQL de criação de tabelas
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f sql/init.sql

echo "[INFO] Tabelas criadas com sucesso. Iniciando aplicação Flask..."

# Inicia o Gunicorn
exec gunicorn -b 0.0.0.0:5001 app:app
