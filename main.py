from whatsapp_sender import enviar_mensagem_whatsapp
from db_utils import (
    enviar_email_resumo,
    buscar_beneficiarios_pendentes,
    marcar_integracao_concluida,
    registrar_log_erro,
    registrar_log_sucesso,
    registrar_log_integracao
)
from api_utils import criar_beneficiario, atualizar_beneficiario
from db_utils import registrar_status
import logging
import traceback
import datetime

# Configuração de logging
logging.basicConfig(
    filename='logs/integracao.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def json_serial(obj):
    """Converte objetos datetime e date para string ISO 8601"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.strftime("%Y-%m-%dT%H:%M:%S")
    raise TypeError(f"Tipo {type(obj)} não é serializável para JSON.")

def limpar_logs():
    """Apaga os logs antigos antes de iniciar um novo processamento"""
    arquivos_logs = ["logs/integracao.log", "logs/sucesso.log", "logs/erros.log"]
    for arquivo in arquivos_logs:
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write("")
            logging.info(f"🧹 {arquivo} limpo com sucesso.")
        except Exception as e:
            logging.error(f"❌ Erro ao limpar {arquivo}: {e}")

def tratar_resposta(cpf, carteira, response, tipo, beneficiario):
    """Trata resposta da API e realiza log conforme sucesso ou erro"""

    if response is not None:
        try:
            data = response.json()
        except Exception:
            data = {}

        logging.info(f"📥 Resposta da API: {response.status_code} - {data}")

        if response.status_code in [200, 201] or data.get("Sucesso") is True:
            # Verifica se é inativação com DT_RESCISAO
            if tipo == "U" and "DT_RESCISAO" in beneficiario:
                dt_rescisao = beneficiario["DT_RESCISAO"]
                if dt_rescisao:
                    if isinstance(dt_rescisao, datetime.datetime):
                        dt_rescisao = dt_rescisao.date()

                    if dt_rescisao < datetime.datetime.now().date():
                        registrar_log_sucesso(cpf, carteira, f"⚠️ Inativado. DT_RESCISAO: {dt_rescisao}")
                        return "inativado"

            registrar_log_sucesso(cpf, carteira, "✅ Beneficiário integrado com sucesso.")
            return "sucesso"
        else:
            registrar_log_erro(cpf, carteira, f"❌ Erro API: {response.text}")
    else:
        registrar_log_erro(cpf, carteira, "❌ Sem resposta da API.")

    return "erro"

def processar_beneficiarios():
    """Processa os beneficiários pendentes no PostgreSQL."""

    limpar_logs()
    logging.info("🧹 Logs anteriores apagados. Iniciando novo processamento...")
    logging.info("🚀 Iniciando processamento dos beneficiários...")

    beneficiarios = buscar_beneficiarios_pendentes()
    total_beneficiarios = len(beneficiarios)

    if not beneficiarios:
        logging.warning("⚠️ Nenhum beneficiário encontrado para processar.")
        return

    logging.info(f"🔍 {total_beneficiarios} registros pendentes encontrados para integração.")
    print(f"🔍 {total_beneficiarios} registros pendentes encontrados para integração.")

    # Contadores
    novos = 0
    atualizados = 0
    inativados = 0
    erros = 0
    erros_cpfs = []
    cpfs_integrados = []

    try:
        for idx, beneficiario in enumerate(beneficiarios, start=1):
            cpf = beneficiario.get("CPF", "DESCONHECIDO")
            carteira = beneficiario.get("CARTEIRA", "DESCONHECIDO")
            tipo_operacao = beneficiario.get("TIPO_OPERACAO", "")

            # ✅ Mostra progresso no terminal a cada 100 registros
            if idx % 100 == 0 or idx == 1:
                print(f"📦 Processando registro {idx}/{total_beneficiarios}...")

            logging.info(f"🔍 Verificando beneficiário CPF: {cpf}, Carteira: {carteira}...")
            registrar_log_integracao(cpf, carteira, "INFO",
                                     f"Verificando beneficiário CPF: {cpf}, Carteira: {carteira}...")

            # Chamada de API conforme operação
            if tipo_operacao == "N":
                logging.info(f"➕ Criando novo beneficiário CPF: {cpf}...")
                registrar_log_integracao(cpf, carteira, "INFO", f"Criando novo beneficiário CPF: {cpf}...")
                response = criar_beneficiario(beneficiario)
                resultado = tratar_resposta(cpf, carteira, response, "N", beneficiario)

            elif tipo_operacao == "U":
                logging.info(f"🔄 Atualizando beneficiário CPF: {cpf}...")
                registrar_log_integracao(cpf, carteira, "INFO", f"Atualizando beneficiário CPF: {cpf}...")
                response = atualizar_beneficiario(beneficiario)
                resultado = tratar_resposta(cpf, carteira, response, "U", beneficiario)

            else:
                registrar_log_erro(cpf, carteira, f"❌ Operação desconhecida: {tipo_operacao}")
                erros += 1
                continue

            # Atualiza contadores com base no retorno
            if resultado == "sucesso":
                cpfs_integrados.append((cpf, carteira))
                if tipo_operacao == "N":
                    novos += 1
                else:
                    atualizados += 1
            elif resultado == "inativado":
                cpfs_integrados.append((cpf, carteira))
                inativados += 1
            else:
                erros += 1
                erros_cpfs.append(cpf)

    except Exception as e:
        logging.error(f"❌ Erro crítico durante a execução: {e}")
        traceback_str = traceback.format_exc()

        cpf = locals().get("cpf", "DESCONHECIDO")
        carteira = locals().get("carteira", "DESCONHECIDO")

        registrar_log_erro(cpf, carteira, f"❌ Erro crítico: {traceback_str}")
        registrar_log_erro(cpf, carteira, str(e))
        registrar_log_integracao(cpf, carteira, "ERRO", "Erro inesperado durante a integração.")
        erros += 1

    finally:
        # Atualiza integração no banco
        if cpfs_integrados:
            marcar_integracao_concluida(cpfs_integrados, "Sucesso")

        # Envia e-mail resumo
        enviar_email_resumo(novos, atualizados, inativados, erros)

        # Envia WhatsApp (se desejar, descomente)
        # enviar_mensagem_whatsapp(novos, atualizados, inativados, erros)

        logging.info("🏁 Processamento finalizado.")
        print("🏁 Processamento finalizado.")

if __name__ == "__main__":
    inicio = datetime.datetime.now()
    registrar_status("api_integracao", "executando", "Início da integração com a API", inicio=inicio)

    try:
        processar_beneficiarios()
        fim = datetime.datetime.now()
        registrar_status("api_integracao", "sucesso", "Processamento finalizado com sucesso", inicio, fim)

    except Exception as e:
        fim = datetime.datetime.now()
        registrar_status("api_integracao", "erro", str(e), inicio, fim)
