FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Copia e instala dependências do sistema
RUN apt-get update && apt-get install -y \
    unzip \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências do Python
COPY requirements.txt .
COPY .env .env
RUN pip install --no-cache-dir -r requirements.txt

# Copia o Oracle Instant Client (ajuste conforme sua estrutura)
COPY mode/instantclient-basiclite-linux.x64-21.12.0.0.0dbru.el9.zip /tmp/
RUN unzip /tmp/instantclient-basiclite-linux.x64-21.12.0.0.0dbru.el9.zip -d /opt/oracle \
    && rm /tmp/instantclient-basiclite-linux.x64-21.12.0.0.0dbru.el9.zip \
    && echo /opt/oracle/instantclient_21_12 > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_12

# Copia todo o código
COPY . .

# Copia o script de entrada customizado
COPY mode/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Define o entrypoint
ENTRYPOINT ["/entrypoint.sh"]