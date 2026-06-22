import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
import paramiko

#################################################################################################################################################
# CONFIGURAÇÕES GERAIS
#################################################################################################################################################
CAMINHO_CONFIGURACAO = r"C:\Configs\Variaveis\.env"
CAMINHO_LOG = r"C:\Configs\Logs"
NOME_SCRIPT = os.path.splitext(os.path.basename(sys.argv[0]))[0]
ARQUIVO_LOG = f"log_{NOME_SCRIPT}.txt"

#################################################################################################################################################
# CONFIGURAÇÃO DO LOG
#################################################################################################################################################
os.makedirs(CAMINHO_LOG, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(CAMINHO_LOG, ARQUIVO_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

logger = logging.getLogger(__name__)

#################################################################################################################################################
# CARREGAMENTO DAS CONFIGURAÇÕES
#################################################################################################################################################
load_dotenv(CAMINHO_CONFIGURACAO)

servidor = os.getenv("ftp_actionline_servidor")
usuario = os.getenv("ftp_actionline_usuario")
senha = os.getenv("ftp_actionline_senha")
porta = os.getenv("ftp_actionline_porta")

caminho_ftp_cancelamento = os.getenv("ftp_cancelamento")
caminho_local_cancelamento = os.getenv("actionline_cancelamentos")

#################################################################################################################################################
# FUNÇÕES
#################################################################################################################################################
def garantir_pasta(caminho):
    os.makedirs(caminho, exist_ok=True)

def obter_arquivos_locais_com_info(pasta):
    garantir_pasta(pasta)

    arquivos_locais = {}

    for nome_arquivo in os.listdir(pasta):
        caminho_completo = os.path.join(pasta, nome_arquivo)

        if os.path.isfile(caminho_completo):
            arquivos_locais[nome_arquivo] = {
                "data_modificacao": os.path.getmtime(caminho_completo),
                "tamanho": os.path.getsize(caminho_completo)
            }

    return arquivos_locais

def buscar_arquivos_novos_ou_atualizados():
    transport = None
    sftp = None

    try:
        logger.info("Iniciando conexão com o SFTP.")
        garantir_pasta(caminho_local_cancelamento)

        transport = paramiko.Transport((servidor, int(porta)))
        transport.connect(username=usuario, password=senha)

        sftp = paramiko.SFTPClient.from_transport(transport)

        arquivos_ftp = sftp.listdir_attr(caminho_ftp_cancelamento)
        arquivos_locais = obter_arquivos_locais_com_info(caminho_local_cancelamento)

        logger.info(f"Total de arquivos encontrados no FTP: {len(arquivos_ftp)}")
        logger.info(f"Total de arquivos encontrados localmente: {len(arquivos_locais)}")

        for arquivo_ftp in arquivos_ftp:
            nome_arquivo = arquivo_ftp.filename

            if not nome_arquivo.lower().endswith(".xlsx"):
                continue

            caminho_remoto = f"{caminho_ftp_cancelamento}/{nome_arquivo}"
            caminho_local = os.path.join(caminho_local_cancelamento, nome_arquivo)

            data_ftp = arquivo_ftp.st_mtime
            tamanho_ftp = arquivo_ftp.st_size

            info_local = arquivos_locais.get(nome_arquivo)

            baixar = False

            if info_local is None:
                baixar = True
                motivo = "arquivo novo"

            elif tamanho_ftp != info_local["tamanho"]:
                baixar = True
                motivo = "tamanho diferente"

            elif data_ftp > info_local["data_modificacao"]:
                baixar = True
                motivo = "arquivo mais novo no FTP"

            else:
                motivo = "arquivo local já atualizado"

            if baixar:
                data_ftp_formatada = datetime.fromtimestamp(data_ftp).strftime("%d/%m/%Y %H:%M:%S")
                tamanho_ftp_kb = round(tamanho_ftp / 1024, 2)

                print(f"Baixando: {nome_arquivo} | Motivo: {motivo} | Data FTP: {data_ftp_formatada} | Tamanho FTP: {tamanho_ftp_kb} KB")
                logger.info(f"Baixando arquivo {nome_arquivo} | Motivo: {motivo} | Data FTP: {data_ftp_formatada} | Tamanho FTP: {tamanho_ftp_kb} KB")

                sftp.get(caminho_remoto, caminho_local)

            else:
                print(f"Pulando: {nome_arquivo} | Motivo: {motivo}")
                logger.info(f"Pulando arquivo {nome_arquivo} | Motivo: {motivo}")

        print("Processo finalizado com sucesso.")
        logger.info("Processo finalizado com sucesso.")

    except Exception as e:
        print(f"Ocorreu o seguinte erro: {e}")
        logger.exception("Erro ao buscar arquivos no SFTP.")

    finally:
        if sftp:
            sftp.close()

        if transport:
            transport.close()

#################################################################################################################################################
# EXECUÇÃO INICIAL
#################################################################################################################################################
if __name__ == "__main__":
    buscar_arquivos_novos_ou_atualizados()
