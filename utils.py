from dotenv import load_dotenv
import logging
import os
import urllib

import pandas as pd
from sqlalchemy import create_engine, text


# Valores padrão — usados como fallback se o banco não estiver disponível
CAMINHO_LOG = r"C:\Configs\Logs"
DRIVER_SQL_SERVER = "ODBC Driver 17 for SQL Server"

load_dotenv(r"C:\Configs\Variaveis\.env")


def _config(chave, padrao):
    """Busca uma configuração no banco; retorna o padrão se não encontrar."""
    try:
        from agendador.models import Configuracao
        return Configuracao.get(chave, padrao)
    except Exception:
        return padrao


def configurar_logging(nome_script: str) -> logging.Logger:
    """
    Configura e retorna um logger para o script informado.
    Grava no banco (LogEvento) se o Django estiver disponível,
    caso contrário grava em arquivo .txt.

    Uso:
        from utils import configurar_logging
        logger = configurar_logging("meu_script")
        logger.info("Iniciando...")
    """
    logger = logging.getLogger(nome_script)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )

    try:
        from agendador.log_handler import DBLogHandler
        handler = DBLogHandler(nome_script)
    except Exception:
        caminho = _config('CAMINHO_LOG', CAMINHO_LOG)
        os.makedirs(caminho, exist_ok=True)
        handler = logging.FileHandler(
            os.path.join(caminho, f"log_{nome_script}.txt"),
            encoding="utf-8",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = logging.getLogger(__name__)


# ── Conexões ───────────────────────────────────────────────────────────────────

def CriarConexao(servidor, banco, usuario, senha):
    driver = _config('DRIVER_SQL_SERVER', DRIVER_SQL_SERVER)
    parametros = (
        f"DRIVER={{{driver}}};"
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


# ── Operações de dados ─────────────────────────────────────────────────────────

def IncluirDados(dataframe, tabela, conexao):
    try:
        logger.info(f"Iniciou inclusao na tabela {tabela}.")
        dataframe.to_sql(
            name=tabela,
            con=conexao,
            if_exists="append",
            index=False,
            chunksize=1000,
        )
        if hasattr(conexao, "commit"):
            conexao.commit()
        logger.info(f"Finalizou inclusao na tabela {tabela}.")
    except Exception:
        logger.exception(f"Erro na inclusao na tabela {tabela}.")
        raise


def ApagarDados(tabela, conexao, condicao="", parametros=None):
    """
    condicao: cláusula WHERE sem a palavra WHERE. Use :param para parâmetros.
              Ex: condicao="id = :id", parametros={"id": 42}
    """
    try:
        logger.info(f"Iniciou exclusao na tabela {tabela}.")
        sql = f"DELETE FROM {tabela}"
        if condicao.strip():
            sql += f" WHERE {condicao}"
        with conexao.begin():
            conexao.execute(text(sql), parametros or {})
        logger.info(f"Finalizou exclusao na tabela {tabela}.")
    except Exception:
        logger.exception(f"Erro na exclusao na tabela {tabela}.")
        raise


def ExtrairDados(conexao, comando):
    try:
        logger.info("Iniciou extracao dos dados.")
        df = pd.read_sql_query(comando, conexao)
        logger.info(f"Finalizou extracao. Total de registros: {len(df)}.")
        return df
    except Exception:
        logger.exception("Erro na extracao dos dados.")
        raise
