# api_utils.py
import json
import requests
import logging
from config.config import API_URL, API_TOKEN
from datetime import datetime, date
import time
import random  # ⬅️ Necessário para jitter no backoff

# Configuração de logging
logging.basicConfig(
    filename="logs/integracao.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def formatar_data(data):
    """Converte objeto datetime ou date para string no formato ISO 8601"""
    if isinstance(data, (datetime, date)):
        return data.strftime("%Y-%m-%dT%H:%M:%S")
    return data


def json_serial(obj):
    """Função para serializar objetos datetime e date em JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.strftime("%Y-%m-%dT%H:%M:%S")
    raise TypeError(f"Tipo {type(obj)} não é serializável para JSON.")


def construir_payload(beneficiario):
    """Monta o JSON de forma correta para envio à API"""

    payload = {
        "Nome": beneficiario["NOME"],
        "Cpf": f"{int(beneficiario['CPF']):011d}",  # ✅ CPF sempre com 11 dígitos
        "Nascimento": formatar_data(beneficiario["NASCIMENTO"]),
        "Sexo": beneficiario["GENERO"],
        "EstadoCivil": beneficiario["ESTADO_CIVIL"],
        "Cns": str(beneficiario["CNS"]),
        "Carteiras": [
            {
                "CnpjOperadora": str(beneficiario["OPERADORA"]),
                "Numero": beneficiario["CARTEIRA"],
                "Nome": beneficiario["NOME_CARTAO"],
                "Validade": formatar_data(beneficiario["VALIDADE"]),
                "Produto": beneficiario["PLANO"],
                "Ativa": "S" if beneficiario["CARTEIRA"] else "N",
            }
        ],
        "CompartilharComContratos": [
            {
                "Numero": "0228-000001"
            }
        ]
    }

    # ✅ Remove campos vazios para evitar problemas
    payload = {k: v for k, v in payload.items() if v}

    return payload

def enviar_requisicao(url, payload, metodo="POST", max_retentativas=3):
    """Envia requisição com retry, backoff e logging"""

    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json",
    }

    for tentativa in range(1, max_retentativas + 1):
        try:
            if metodo == "PUT":
                response = requests.put(url, headers=headers, json=payload, timeout=60)
            else:
                logging.info(f"📤 Enviando para a URL: {url}")
                logging.info(f"📤 Payload Enviado: {json.dumps(payload, indent=2, ensure_ascii=False)}")
                response = requests.post(url, headers=headers, json=payload, timeout=60)

            response.raise_for_status()

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text

            logging.info(f"📤 Payload Enviado: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            logging.info(f"📥 Resposta da API: {response.status_code} - {response_data}")

            time.sleep(0.1)  # Protege a API de sobrecarga
            return response

        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠️ Tentativa {tentativa}/{max_retentativas} falhou: {e}")

            if tentativa == max_retentativas:
                logging.error("❌ Falha permanente após várias tentativas.")
                with open("logs/falhas.csv", "a", encoding="utf-8") as f:
                    cpf = payload.get("Cpf", "N/A")
                    carteira = payload.get("Carteiras", [{}])[0].get("Numero", "N/A")
                    f.write(f"{cpf},{carteira},{datetime.now().isoformat()},\"{str(e)}\"\n")
                return None

            tempo_espera = min(60, (2 ** tentativa) + random.uniform(0, 1))
            logging.info(f"⏳ Aguardando {tempo_espera:.2f}s antes de nova tentativa...")
            time.sleep(tempo_espera)

    # Garantia de retorno em caso de falha inesperada fora do loop
    return None

def criar_beneficiario(beneficiario):
    """Cadastra um novo beneficiário na API"""
    url = f"{API_URL}/Contatos/PessoaFisica/Post"
    payload = construir_payload(beneficiario)
    return enviar_requisicao(url, payload, "POST")


def atualizar_beneficiario(beneficiario):
    """Atualiza um beneficiário existente na API"""

    if "DT_RESCISAO" in beneficiario and beneficiario["DT_RESCISAO"]:
        dt_rescisao = beneficiario["DT_RESCISAO"]

        if isinstance(dt_rescisao, str):
            try:
                dt_rescisao = datetime.fromisoformat(dt_rescisao)
            except ValueError:
                logging.warning(f"⚠️ DT_RESCISAO em formato inválido: {dt_rescisao}")
                dt_rescisao = None

        if dt_rescisao and dt_rescisao < datetime.now():
            logging.info(f"⚠️ Beneficiário CPF {beneficiario['CPF']} será INATIVADO.")
            # segue com o PUT

            logging.info(f"⚠️ Beneficiário CPF {beneficiario['CPF']} será INATIVADO.")
            url = f"{API_URL}/Contatos/InativarBeneficiario/Put"
            payload = {
                "NumeroCarteira": beneficiario["CARTEIRA"],
                "Data": formatar_data(beneficiario["DT_RESCISAO"]),
                "IdMotivo": 0,
                "ExcluirDasEquipes": 0,
                "FinalizarLinhasCuidado": 0,
                "CancelarTarefasAvulsas": 0,
                "CompartilharComContratos": [{"Numero": "0228-000001"}]
            }
            return enviar_requisicao(url, payload, "PUT")

    logging.info(f"🔄 Atualizando beneficiário CPF {beneficiario['CPF']}...")
    url = f"{API_URL}/Contatos/PessoaFisica/Post"
    payload = construir_payload(beneficiario)
    return enviar_requisicao(url, payload, "POST")
