from dotenv import load_dotenv
import os
import urllib
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
import sys
from dateutil.relativedelta import relativedelta
from datetime import timedelta
############################################################################################################################################ 
CAMINHO_ENV = r"C:\Configs\Variaveis\.env"
CAMINHO_LOG = r"C:\Configs\Logs"
nome_script = os.path.splitext(os.path.basename(sys.argv[0]))[0]
ARQUIVO_LOG = f"log_{nome_script}.txt"
############################################################################################################################################ 
os.makedirs(CAMINHO_LOG, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(CAMINHO_LOG, ARQUIVO_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)
load_dotenv(CAMINHO_ENV)
############################################################################################################################################ 
### Produção ###
############################################################################################################################################ 
servidorDUO 			= os.getenv("servidorProducao")
bancoDUO    			= os.getenv("bancoProducao")
usuarioDUO  			= os.getenv("usuarioProducao")
senhaDUO    			= os.getenv("senhaProducao")
parametros_bdProducao 	= ("DRIVER={" + "ODBC Driver 17 for SQL Server" + "};SERVER=" + servidorDUO + ";DATABASE=" + bancoDUO+ ";UID=" + usuarioDUO + ";PWD=" + senhaDUO)        
mecanismoProducao 		= create_engine("mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametros_bdProducao)) 
conexaoProducao 		= mecanismoProducao.connect()
############################################################################################################################################ 
### Desenvolvimento ###
############################################################################################################################################ 
servidorMRA 	= os.getenv("servidorMRA")
bancoMRA    	= os.getenv("bancoMRA")
usuarioMRA  	= os.getenv("usuarioMRA")
senhaMRA    	= os.getenv("senhaMRA")
parametrosMRA	= ("DRIVER={" + "ODBC Driver 17 for SQL Server" + "};SERVER=" + servidorMRA + ";DATABASE=" + bancoMRA  + ";UID=" + usuarioMRA  + ";PWD=" + senhaMRA)        
mecanismoMRA  	= create_engine("mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(parametrosMRA)) 
conexaoMRA   	= mecanismoMRA.connect() 
############################################################################################################################################ 
def IncluirDados(dataframe,tabela,conexao):
    try:
        logger.info(f"Iniciou o processo de inclusão dos registros na tabela {tabela}.")
        dataframe.to_sql(name=tabela, con=conexao, if_exists='append', index=False, chunksize =1000) 
        logger.info(f"Finalizou o processo de inclusão dos registros na tabela {tabela}.")
    except Exception as e:
        logger.exception(f"Erro no processo de inclusão dos registros na tabela {tabela}. ")
        raise    
############################################################################################################################################
def ApagarDados(tabela, conexao, condicao=""):
    try:
        logger.info(f"Iniciou o processo de exclusão dos registros na tabela {tabela}.")
        sql = f"DELETE FROM {tabela}"
        if condicao.strip():
            sql += f" WHERE {condicao}"
        with conexao.begin():
            conexao.execute(text(sql))
        logger.info(f"Finalizou o processo de exclusão dos registros na tabela {tabela}.")        
    except Exception:
        logger.exception(f"Erro no processo de extração dos dados.")
        raise      
############################################################################################################################################    
def ExtrairDados(conexao, comando):
    try:
        logger.info(f"Iniciou o processo de extração dos dados.")
        dfExtracao = pd.read_sql_query(comando, conexao)
        logger.info(f"Finalizou o processo de extração dos dados. Total de registros extraídos: {len(dfExtracao)}.")
        return dfExtracao        
    except Exception:
        logger.exception(f"Erro no processo de extração dos dados.")
        raise
############################################################################################################################################
def executar_periodos(ano_inicio, mes_inicio, dia_inicio, ano_fim, mes_fim, dia_fim, numero_dias):
    data_atual = datetime(ano_inicio, mes_inicio, dia_inicio)
    data_limite = datetime(ano_fim, mes_fim, dia_fim)    
    while data_atual <= data_limite:
        data_inicial = data_atual
        data_final = data_atual + relativedelta(days=numero_dias)
        data_final = data_final - timedelta(seconds=1)
        logger.info(f"Data Inicial: {data_inicial} | Data Final:{data_final}")
        print(f"Data Inicial: {data_inicial} | Data Final:{data_final}")
        logger.info(f"--> INICIOU ROTINA ApagarDados - TB_HORARIOS.")
        ApagarDados("TB_PACIENTES",conexaoMRA,f" DATA_AGENDAMENTO BETWEEN '{data_inicial}' AND '{data_final}'")    
        logger.info(f"--> FINALIZOU ROTINA ApagarDados.")         
        Rotina(data_inicial, data_final)
        data_atual = data_atual + relativedelta(days=numero_dias)   
############################################################################################################################################
def Rotina(codigo_paciente):  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_PACIENTES.") 
    comando = f'''
                SELECT 
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.COD_PACIENTE)), ''), 'null')) AS CODIGO,
                    PACIENTE.NOME,
                    PACIENTE.NOME_SOCIAL,
                    PACIENTE.SEXO,
                    TRY_CONVERT(DATE, PACIENTE.DT_NASCIMENTO, 103) AS DATA_NASCIMENTO,
                    PACIENTE.NACIONALIDADE,
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.CD_RACA)), ''), 'null')) AS CD_RACA,
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.COD_ETNIA)), ''), 'null')) AS COD_ETNIA,
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.ID_ESTADO_CIVIL)), ''), 'null')) AS ID_ESTADO_CIVIL,
                    PACIENTE.RG,
                    PACIENTE.CPF,
                    PACIENTE.NOME_MAE,
                    PACIENTE.NOME_PAI,
                    PACIENTE.ENDERECO,
                    PACIENTE.ENDERECO_NUMERO,
                    PACIENTE.ENDERECO_COMPLEMENTO,
                    PACIENTE.BAIRRO,
                    PACIENTE.MUNICIPIO,
                    PACIENTE.UF,
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.CODMUNGEST)), ''), 'null')) AS CODMUNGEST,
                    PACIENTE.CEP,
                    PACIENTE.TEL_RES_DDD,
                    PACIENTE.TEL_RES,
                    PACIENTE.TEL_CELULAR_DDD,
                    PACIENTE.TEL_CELULAR,
                    PACIENTE.TEL_COM_DDD,
                    PACIENTE.TEL_COM,
                    PACIENTE.TEL_COM_RAMAL,
                    PACIENTE.EMAIL,
                    PACIENTE.CONTATO_NOME,
                    PACIENTE.CONTATO_TEL_DDD,
                    PACIENTE.CONTATO_TEL,
                    TRY_CONVERT(DATE, PACIENTE.DT_CADASTRO, 103) AS DT_CADASTRO,
                    TRY_CONVERT(DATE, PACIENTE.DT_ULTIMA_ATUALIZ, 103) AS DT_ULTIMA_ATUALIZ,
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(RRAS.COD_RRAS)), ''), 'null')) AS RRAS,
                    TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(DRS.COD_DRS)), ''), 'null')) AS CODIGO_DRS,
                    DRS.NOME_DRS AS NOME_DRS,
                    DRS.SIGLA_DRS,
                    REPLACE(CIR.CIR, 'REGIAO DE SAUDE - ', '') AS NOME_REGIAO_SAUDE
                FROM SES_PACIENTE PACIENTE

                LEFT JOIN AMB_ADM_UNIDADE_REGIOES DRS_PACIENTE
                    ON TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.CODMUNGEST)), ''), 'null'))
                    = TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(DRS_PACIENTE.CODMUNGEST)), ''), 'null'))

                LEFT JOIN AMB_DRS DRS
                    ON TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(DRS_PACIENTE.COD_DRS)), ''), 'null'))
                    = TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(DRS.COD_DRS)), ''), 'null'))

                LEFT JOIN AMB_RRAS_MUNGEST RRAS
                    ON TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(PACIENTE.CODMUNGEST)), ''), 'null'))
                    = TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(RRAS.CODMUNGEST)), ''), 'null'))

                LEFT JOIN ADMAMB_ADM_UNIDADE_CIR CIR
                    ON TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(DRS.COD_DRS)), ''), 'null'))
                    = TRY_CONVERT(INT, NULLIF(NULLIF(LTRIM(RTRIM(CIR.COD_UNIDADE)), ''), 'null'))                  

                WHERE PACIENTE.COD_PACIENTE IN ({codigo_paciente})
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_PACIENTES",conexaoMRA)    
    conexaoMRA.commit()
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_PACIENTES.") 
def CadastrarPacientePorLote():
    logger.info(f": (Inicio) Processando rotina AtualizaFilaCDR :")    
    
    logger.info(f":: (Inicio) Trazendo Pacientes :::")
    comando = text("""SELECT DISTINCT	FILA.CODIGO_PACIENTE FROM TB_TEMPO_CUIDAR_ATUALIZADA FILA
                    WHERE ((CODIGO_STATUS  IN (0,11) AND FILA.ORIGEM = 'CDR') OR (CODIGO_STATUS = 3 AND FILA.ORIGEM = 'Regulação') OR (CODIGO_STATUS = 5 AND FILA.ORIGEM = 'Solicitações')) """)
    dfCodigos = ExtrairDados(conexaoMRA, comando)
    logger.info(f"Qtde Pacientes para cadastro: {len(dfCodigos)}")
    logger.info(f":: (Fim) Trazendo CODIGO_PACIENTE :::")

    if dfCodigos.empty:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Não foi encontrado nenhum código.")
        logger.info(f"--> Não foi encontrado nenhum código")
        return        

    logger.info(f":: (Inicio) Atualização da Fila TB_PACIENTES")
    lista_codigos = dfCodigos["CODIGO_PACIENTE"].tolist()
    tamanho_lote = 1000

    for i in range(0, len(lista_codigos), tamanho_lote):
        lote = lista_codigos[i:i + tamanho_lote]
        codigos_str = ','.join(map(str, lote))
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Inicio) Processando lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} filas TB_PACIENTES)")        
        comando = Rotina(codigos_str)          
        logger.info(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] "
            f"::: (Fim) do Processamento do lote {i//tamanho_lote + 1} de {len(lista_codigos)//tamanho_lote + 1} "
            f"({len(lote)} pacientes)")
        
    logger.info(f":: (Fim) Atualização da TB_PACIENTES")   

    logger.info(f": (Fim) Processando rotina AtualizaFilaCDR :")          
if __name__ == "__main__":
    ApagarDados('TB_PACIENTES', conexaoMRA, 'CODIGO IN (SELECT CODIGO_PACIENTE FROM TB_TEMPO_CUIDAR_ATUALIZADA)')
    CadastrarPacientePorLote()
