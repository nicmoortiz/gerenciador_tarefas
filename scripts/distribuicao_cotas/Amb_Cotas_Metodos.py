from dotenv import load_dotenv
import logging
import os
import sys
import urllib

import pandas as pd
from sqlalchemy import create_engine, text


CAMINHO_ENV = r"C:\Configs\Variaveis\.env"
CAMINHO_LOG = r"C:\Configs\Logs"
DRIVER_SQL_SERVER = "ODBC Driver 17 for SQL Server"

nome_script = os.path.splitext(os.path.basename(sys.argv[0]))[0]
ARQUIVO_LOG = f"log_{nome_script}.txt"

os.makedirs(CAMINHO_LOG, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(CAMINHO_LOG, ARQUIVO_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv(CAMINHO_ENV)


def CriarConexao(servidor, banco, usuario, senha):
    parametros = (
        f"DRIVER={{{DRIVER_SQL_SERVER}}};"
        f"SERVER={servidor};"
        f"DATABASE={banco};"
        f"UID={usuario};"
        f"PWD={senha}"
    )
    mecanismo = create_engine(
        "mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametros)
    )
    return mecanismo.connect()


def CriarConexaoProducao():
    return CriarConexao(
        os.getenv("servidorProducao"),
        os.getenv("bancoProducao"),
        os.getenv("usuarioProducao"),
        os.getenv("senhaProducao"),
    )


def CriarConexaoMRA():
    return CriarConexao(
        os.getenv("servidorMRA"),
        os.getenv("bancoMRA"),
        os.getenv("usuarioMRA"),
        os.getenv("senhaMRA"),
    )


def IncluirDados(dataframe, tabela, conexao):
    try:
        logger.info(f"Iniciou o processo de inclusao dos registros na tabela {tabela}.")
        dataframe.to_sql(
            name=tabela,
            con=conexao,
            if_exists="append",
            index=False,
            chunksize=1000,
        )
        if hasattr(conexao, "commit"):
            conexao.commit()
        logger.info(f"Finalizou o processo de inclusao dos registros na tabela {tabela}.")
    except Exception:
        logger.exception(f"Erro no processo de inclusao dos registros na tabela {tabela}.")
        raise


def ApagarDados(tabela, conexao, condicao=""):
    try:
        logger.info(f"Iniciou o processo de exclusao dos registros na tabela {tabela}.")
        sql = f"DELETE FROM {tabela}"
        if condicao.strip():
            sql += f" WHERE {condicao}"
        with conexao.begin():
            conexao.execute(text(sql))
        logger.info(f"Finalizou o processo de exclusao dos registros na tabela {tabela}.")
    except Exception:
        logger.exception(f"Erro no processo de exclusao dos registros na tabela {tabela}.")
        raise


def ExtrairDados(conexao, comando):
    try:
        logger.info("Iniciou o processo de extracao dos dados.")
        dfExtracao = pd.read_sql_query(comando, conexao)
        logger.info(
            "Finalizou o processo de extracao dos dados. "
            f"Total de registros extraidos: {len(dfExtracao)}."
        )
        return dfExtracao
    except Exception:
        logger.exception("Erro no processo de extracao dos dados.")
        raise


conexaoProducao = CriarConexaoProducao()
conexaoMRA = CriarConexaoMRA()
