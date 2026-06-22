######################################################################################################################################################
## Bibliotecas #######################################################################################################################################
######################################################################################################################################################
import funcoes as fcn 
import pandas as pd
from datetime import datetime
######################################################################################################################################################
## Parâmetros ######################################################################################################################################
######################################################################################################################################################
caminho_parametros = r"C:\Projetos\Python\Funcoes\.env"
caminho_log = r"C:\Projetos\Python\log"
logger = fcn.configurar_log(caminho_log)
fcn.carregar_env(caminho_parametros)
engine_mraDev = fcn.criar_engine_por_env("LIBIADEV_MRA")
conexao_mraDev = engine_mraDev.connect()
engine_Producao = fcn.criar_engine_por_env("PRODUCAO")
conexao_Producao = engine_Producao.connect()
######################################################################################################################################################
## Comandos SQL ######################################################################################################################################
######################################################################################################################################################
recurso_paciente_fila = '''SELECT 
                            DISTINCT
                            CAST(DATA_ENTRADA AS date) DATA_ENTRADA, 
                            CODIGO_PACIENTE,
                            NOME_PACIENTE,
                            CODIGO_GRUPO,
                            NOME_GRUPO,
                            CODIGO_SUBGRUPO, 
                            NOME_SUBGRUPO,
                            CODIGO_RECURSO,
                            NOME_RECURSO,
                            (CASE
                                WHEN TIPO = 'E' THEN 'EXAME'
                                ELSE 'CONSULTA'
                            END) CATEGORIA_ATENDIMENTO
                        FROM 
                            TB_TEMPO_CUIDAR_ATUALIZADA
                        '''
######################################################################################################################################################
## Inteligência ######################################################################################################################################
######################################################################################################################################################
def dividir_lista(lista,tamanho=1000):
    for i in range(0,len(lista),tamanho):
        yield lista[i:i + tamanho]
#----------------------------------------------------------------------------------------------------------------------------------------------------#
def buscaAgendamentoPorAno(conexao,pacientes,ano, logger=None):
    data_inicio = f"{ano}-01-01"
    data_fim = f"{ano + 1}-01-01"

    lista_df = []

    logger.info(f"Buscando agendamentos entre {data_inicio} e {data_fim}")

    for lote in dividir_lista(pacientes, 5000):
        pacientes_sql = ",".join(map(str, lote))

        sql = f"""                
                SELECT 
                    'CONSULTA' CATEGORIA_ATENDIMENTO,
                    CONSULTA.ID_AGE_CONSULTA_HOR CODIGO_HORARIO,
                    CONSULTA.COD_PACIENTE CODIGO_PACIENTE,
                    (CASE 
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN 'Em Aberto' 
                        WHEN CONSULTA.DATA_AGENDA < CAST(GETDATE() AS DATE) THEN 'Histórico'
                    END) LINHA_TEMPO,
                    CONSULTA.DATA_AGENDA,
                    CONSULTA.HOR_INI HORARIO,
                    EXECUTANTE.UNIDADE_FANTASIA UNIDADE_EXECUTANTE,
                    ESPECIALIDADE.ID_ESPECIALIDADE CODIGO_RECURSO,
                    UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE) NOME_RECURSO,
                    GRUPO.ID_GRUPO CODIGO_GRUPO,
                    UPPER(GRUPO.NOME_GRUPO) NOME_GRUPO,                    
                    SUBGRUPO.ID_SUBGRUPO CODIGO_SUBGRUPO,
                    UPPER(SUBGRUPO.NOME_SUBGRUPO) NOME_SUBGRUPO,
                    CID.SUBCATEG CID,
                    CONSULTA.COD_UNIDADE_SOLICITANTE,
                    CONSULTA.COD_UNIDADE_EXECUTANTE,
                    (CASE
                        WHEN CONSULTA.TIPO = 'R' THEN 'Retorno'
                        WHEN CONSULTA.COD_UNIDADE_SOLICITANTE = CONSULTA.COD_UNIDADE_EXECUTANTE AND CONSULTA.TIPO = 'P' THEN 'Interconsulta'
                        WHEN CONSULTA.COD_UNIDADE_SOLICITANTE <> CONSULTA.COD_UNIDADE_EXECUTANTE AND CONSULTA.TIPO = 'P' THEN '1ª Consulta'
                        ELSE CONSULTA.TIPO
                    END) TIPO,
                    (CASE
                        WHEN CONSULTA.STATUS = 'A' THEN 'Ausente'
                        WHEN CONSULTA.STATUS = 'D' THEN 'Desistente'
                        WHEN CONSULTA.STATUS = 'I' THEN 'Dispensado'
                        WHEN CONSULTA.STATUS = 'P' THEN 'Presente'
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN'Sem recepção (Agenda Futura)'
                        ELSE 'Sem recepção'
                    END) RECEPCAO,
                    CONSULTA.DT_ULTIMA_ATUALIZ DATA_ULTIMA_ATUALIZACAO,
                    NULL						TIPO_LOG,
                    NULL						CODIGO_MOTIVO  
                FROM 
                    AMB_AGE_CONSULTA_HOR CONSULTA 
                LEFT JOIN AMB_PROTOCOLO CID ON CID.ID_PROTOCOLO = CONSULTA.ID_PROTOCOLO
                LEFT JOIN ADMAMB_ADM_UNIDADE EXECUTANTE ON EXECUTANTE.COD_UNIDADE = CONSULTA.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_ESPECIALIDADE ESPECIALIDADE ON ESPECIALIDADE.ID_ESPECIALIDADE = CONSULTA.ID_ESPECIALIDADE
                LEFT JOIN AMB_SUBGRUPO SUBGRUPO ON SUBGRUPO.ID_SUBGRUPO = ESPECIALIDADE.ID_SUBGRUPO
                LEFT JOIN AMB_GRUPO GRUPO ON SUBGRUPO.ID_GRUPO = GRUPO.ID_GRUPO AND GRUPO.TIPO_GRUPO = 'C' AND GRUPO.FLG_ATIVO = 'S' 
                WHERE CONSULTA.COD_PACIENTE IN ({pacientes_sql})
                AND CONSULTA.DATA_AGENDA >= '{data_inicio}'
                AND CONSULTA.DATA_AGENDA < '{data_fim}'

                UNION

                SELECT 
                    'CONSULTA' CATEGORIA_ATENDIMENTO,
                    CONSULTA.ID_AGE_CONSULTA_HOR CODIGO_HORARIO,
                    CONSULTA.COD_PACIENTE CODIGO_PACIENTE,
                    'Cancelamentos' LINHA_TEMPO,
                    CONSULTA.DATA_AGENDA,
                    CONSULTA.HOR_INI HORARIO,
                    EXECUTANTE.UNIDADE_FANTASIA UNIDADE_EXECUTANTE,
                    ESPECIALIDADE.ID_ESPECIALIDADE CODIGO_RECURSO,
                    UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE) NOME_RECURSO,
                    GRUPO.ID_GRUPO CODIGO_GRUPO,
                    UPPER(GRUPO.NOME_GRUPO) NOME_GRUPO,                          
                    SUBGRUPO.ID_SUBGRUPO CODIGO_SUBGRUPO,
                    UPPER(SUBGRUPO.NOME_SUBGRUPO) NOME_SUBGRUPO,
                    CID.SUBCATEG CID,
                    CONSULTA.COD_UNIDADE_SOLICITANTE,
                    CONSULTA.COD_UNIDADE_EXECUTANTE,
                    (CASE
                        WHEN CONSULTA.TIPO = 'R' THEN 'Retorno'
                        WHEN CONSULTA.COD_UNIDADE_SOLICITANTE = CONSULTA.COD_UNIDADE_EXECUTANTE AND CONSULTA.TIPO = 'P' THEN 'Interconsulta'
                        WHEN CONSULTA.COD_UNIDADE_SOLICITANTE <> CONSULTA.COD_UNIDADE_EXECUTANTE AND CONSULTA.TIPO = 'P' THEN '1ª Consulta'
                        ELSE CONSULTA.TIPO
                    END) TIPO,
                    (CASE
                        WHEN CONSULTA.STATUS = 'A' THEN 'Ausente'
                        WHEN CONSULTA.STATUS = 'D' THEN 'Desistente'
                        WHEN CONSULTA.STATUS = 'I' THEN 'Dispensado'
                        WHEN CONSULTA.STATUS = 'P' THEN 'Presente'
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN'Sem recepção (Agenda Futura)'
                        ELSE 'Sem recepção'
                    END) RECEPCAO,
                    CONSULTA.DATA_ACAO DATA_ULTIMA_ATUALIZACAO,
                    CONSULTA.TIPO_LOG						TIPO_LOG,
                    CONSULTA.ID_MOTIVO						CODIGO_MOTIVO  
                FROM 
                    AMB_LOG_CONSULTA CONSULTA 
                LEFT JOIN AMB_PROTOCOLO CID ON CID.ID_PROTOCOLO = CONSULTA.ID_PROTOCOLO
                LEFT JOIN ADMAMB_ADM_UNIDADE EXECUTANTE ON EXECUTANTE.COD_UNIDADE = CONSULTA.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_ESPECIALIDADE ESPECIALIDADE ON ESPECIALIDADE.ID_ESPECIALIDADE = CONSULTA.ID_ESPECIALIDADE
                LEFT JOIN AMB_SUBGRUPO SUBGRUPO ON SUBGRUPO.ID_SUBGRUPO = ESPECIALIDADE.ID_SUBGRUPO
                LEFT JOIN AMB_GRUPO GRUPO ON SUBGRUPO.ID_GRUPO = GRUPO.ID_GRUPO AND GRUPO.TIPO_GRUPO = 'C' AND GRUPO.FLG_ATIVO = 'S'
                WHERE CONSULTA.TIPO_LOG IN ('C','P')
                AND CONSULTA.COD_PACIENTE IN ({pacientes_sql})
                AND CONSULTA.DATA_AGENDA >= '{data_inicio}'
                AND CONSULTA.DATA_AGENDA < '{data_fim}'

                UNION 

                --> Agendas de Exame -- Histórico
                SELECT 
                    'EXAME' CATEGORIA_ATENDIMENTO,
                    CONSULTA.ID_AGE_EXAME_HOR CODIGO_HORARIO,
                    CONSULTA.COD_PACIENTE CODIGO_PACIENTE,
                    (CASE 
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN 'Em Aberto' 
                        WHEN CONSULTA.DATA_AGENDA < CAST(GETDATE() AS DATE) THEN 'Histórico'
                    END) LINHA_TEMPO,
                    CONSULTA.DATA_AGENDA,
                    CONSULTA.HOR_INI HORARIO,
                    EXECUTANTE.UNIDADE_FANTASIA UNIDADE_EXECUTANTE,
                    ESPECIALIDADE.ID_EXAME CODIGO_RECURSO,
                    UPPER(ESPECIALIDADE.NOME_EXAME) NOME_RECURSO,
                    GRUPO.ID_GRUPO CODIGO_GRUPO,
                    UPPER(GRUPO.NOME_GRUPO) NOME_GRUPO,                          
                    SUBGRUPO.ID_SUBGRUPO CODIGO_SUBGRUPO,
                    UPPER(SUBGRUPO.NOME_SUBGRUPO) NOME_SUBGRUPO,
                    NULL CID,
                    CONSULTA.COD_UNIDADE_SOLICITANTE,
                    CONSULTA.COD_UNIDADE_EXECUTANTE,
                    null TIPO,
                    (CASE
                        WHEN CONSULTA.STATUS = 'A' THEN 'Ausente'
                        WHEN CONSULTA.STATUS = 'D' THEN 'Desistente'
                        WHEN CONSULTA.STATUS = 'I' THEN 'Dispensado'
                        WHEN CONSULTA.STATUS = 'P' THEN 'Presente'
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN'Sem recepção (Agenda Futura)'
                        ELSE 'Sem recepção'
                    END) RECEPCAO,
                    CONSULTA.DT_ULTIMA_ATUALIZ DATA_ULTIMA_ATUALIZACAO,
                    NULL						TIPO_LOG,
                    NULL						CODIGO_MOTIVO  
                FROM 
                    AMB_AGE_EXAME_HOR CONSULTA 
                LEFT JOIN ADMAMB_ADM_UNIDADE EXECUTANTE ON EXECUTANTE.COD_UNIDADE = CONSULTA.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_EXAME1 ESPECIALIDADE ON ESPECIALIDADE.ID_EXAME = CONSULTA.ID_EXAME
                LEFT JOIN AMB_SUBGRUPO SUBGRUPO ON SUBGRUPO.ID_SUBGRUPO = ESPECIALIDADE.ID_SUBGRUPO
                LEFT JOIN AMB_GRUPO GRUPO ON SUBGRUPO.ID_GRUPO = GRUPO.ID_GRUPO AND GRUPO.TIPO_GRUPO = 'E' AND GRUPO.FLG_ATIVO = 'S'
                WHERE CONSULTA.COD_PACIENTE IN ({pacientes_sql})
                AND CONSULTA.DATA_AGENDA >= '{data_inicio}'
                AND CONSULTA.DATA_AGENDA < '{data_fim}'

                UNION

                SELECT 
                    'EXAME' CATEGORIA_ATENDIMENTO,
                    CONSULTA.ID_AGE_EXAME_HOR CODIGO_HORARIO,
                    CONSULTA.COD_PACIENTE CODIGO_PACIENTE,
                    'Cancelamentos' LINHA_TEMPO,
                    CONSULTA.DATA_AGENDA,
                    CONSULTA.HOR_INI HORARIO,
                    EXECUTANTE.UNIDADE_FANTASIA UNIDADE_EXECUTANTE,
                    ESPECIALIDADE.ID_EXAME CODIGO_RECURSO,
                    UPPER(ESPECIALIDADE.NOME_EXAME) NOME_RECURSO,
                    GRUPO.ID_GRUPO CODIGO_GRUPO,
                    UPPER(GRUPO.NOME_GRUPO) NOME_GRUPO,                          
                    SUBGRUPO.ID_SUBGRUPO CODIGO_SUBGRUPO,
                    UPPER(SUBGRUPO.NOME_SUBGRUPO) NOME_SUBGRUPO,
                    NULL CID,
                    CONSULTA.COD_UNIDADE_SOLICITANTE,
                    CONSULTA.COD_UNIDADE_EXECUTANTE,
                    NULL TIPO,
                    (CASE
                        WHEN CONSULTA.STATUS = 'A' THEN 'Ausente'
                        WHEN CONSULTA.STATUS = 'D' THEN 'Desistente'
                        WHEN CONSULTA.STATUS = 'I' THEN 'Dispensado'
                        WHEN CONSULTA.STATUS = 'P' THEN 'Presente'
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN'Sem recepção (Agenda Futura)'
                        ELSE 'Sem recepção'
                    END) RECEPCAO,
                    CONSULTA.DATA_ACAO DATA_ULTIMA_ATUALIZACAO,
                    CONSULTA.TIPO_LOG						TIPO_LOG,
                    CONSULTA.ID_MOTIVO						CODIGO_MOTIVO  
                FROM 
                    AMB_LOG_EXAME CONSULTA 
                LEFT JOIN ADMAMB_ADM_UNIDADE EXECUTANTE ON EXECUTANTE.COD_UNIDADE = CONSULTA.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_EXAME1 ESPECIALIDADE ON ESPECIALIDADE.ID_EXAME = CONSULTA.ID_EXAME
                LEFT JOIN AMB_SUBGRUPO SUBGRUPO ON SUBGRUPO.ID_SUBGRUPO = ESPECIALIDADE.ID_SUBGRUPO
                LEFT JOIN AMB_GRUPO GRUPO ON SUBGRUPO.ID_GRUPO = GRUPO.ID_GRUPO AND GRUPO.TIPO_GRUPO = 'E' AND GRUPO.FLG_ATIVO = 'S'
                WHERE CONSULTA.TIPO_LOG IN ('C','P')
                AND CONSULTA.COD_PACIENTE IN ({pacientes_sql})
                AND CONSULTA.DATA_AGENDA >= '{data_inicio}'
                AND CONSULTA.DATA_AGENDA < '{data_fim}'       
                     
        """

        df_temp = fcn.extrair_dados(conexao, sql, logger)

        if df_temp.empty:
            logger.info(f"Não retornou nenhum dado.")
            
        if not df_temp.empty:
            lista_df.append(df_temp)        
            fcn.incluir_dados(df_temp,'TB_HISTORICO_AGENDAMENTOS',conexao_mraDev)

    if lista_df:
        return pd.concat(lista_df, ignore_index=True)

    return pd.DataFrame()             
#----------------------------------------------------------------------------------------------------------------------------------------------------#
def buscaAgendamentoPorAnoTransferenciaOutros(conexao,pacientes,ano, logger=None):
    data_inicio = f"{ano}-01-01"
    data_fim = f"{ano + 1}-01-01"

    lista_df = []

    logger.info(f"Buscando agendamentos entre {data_inicio} e {data_fim}")

    for lote in dividir_lista(pacientes, 5000):
        pacientes_sql = ",".join(map(str, lote))

        sql = f"""                
                SELECT 
                    'CONSULTA' CATEGORIA_ATENDIMENTO,
                    CONSULTA.ID_AGE_CONSULTA_HOR CODIGO_HORARIO,
                    CONSULTA.COD_PACIENTE CODIGO_PACIENTE,
                    'Transferência ou Outros' LINHA_TEMPO,
                    CONSULTA.DATA_AGENDA,
                    CONSULTA.HOR_INI HORARIO,
                    EXECUTANTE.UNIDADE_FANTASIA UNIDADE_EXECUTANTE,
                    ESPECIALIDADE.ID_ESPECIALIDADE CODIGO_RECURSO,
                    UPPER(ESPECIALIDADE.NOME_ESPECIALIDADE) NOME_RECURSO,
                    GRUPO.ID_GRUPO CODIGO_GRUPO,
                    UPPER(GRUPO.NOME_GRUPO) NOME_GRUPO,                          
                    SUBGRUPO.ID_SUBGRUPO CODIGO_SUBGRUPO,
                    UPPER(SUBGRUPO.NOME_SUBGRUPO) NOME_SUBGRUPO,
                    CID.SUBCATEG CID,
                    CONSULTA.COD_UNIDADE_SOLICITANTE,
                    CONSULTA.COD_UNIDADE_EXECUTANTE,
                    (CASE
                        WHEN CONSULTA.TIPO = 'R' THEN 'Retorno'
                        WHEN CONSULTA.COD_UNIDADE_SOLICITANTE = CONSULTA.COD_UNIDADE_EXECUTANTE AND CONSULTA.TIPO = 'P' THEN 'Interconsulta'
                        WHEN CONSULTA.COD_UNIDADE_SOLICITANTE <> CONSULTA.COD_UNIDADE_EXECUTANTE AND CONSULTA.TIPO = 'P' THEN '1ª Consulta'
                        ELSE CONSULTA.TIPO
                    END) TIPO,
                    (CASE
                        WHEN CONSULTA.STATUS = 'A' THEN 'Ausente'
                        WHEN CONSULTA.STATUS = 'D' THEN 'Desistente'
                        WHEN CONSULTA.STATUS = 'I' THEN 'Dispensado'
                        WHEN CONSULTA.STATUS = 'P' THEN 'Presente'
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN'Sem recepção (Agenda Futura)'
                        ELSE 'Sem recepção'
                    END) RECEPCAO,
                    CONSULTA.DATA_ACAO DATA_ULTIMA_ATUALIZACAO,
                    CONSULTA.TIPO_LOG						TIPO_LOG,
                    CONSULTA.ID_MOTIVO						CODIGO_MOTIVO  
                FROM 
                    AMB_LOG_CONSULTA CONSULTA 
                LEFT JOIN AMB_PROTOCOLO CID ON CID.ID_PROTOCOLO = CONSULTA.ID_PROTOCOLO
                LEFT JOIN ADMAMB_ADM_UNIDADE EXECUTANTE ON EXECUTANTE.COD_UNIDADE = CONSULTA.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_ESPECIALIDADE ESPECIALIDADE ON ESPECIALIDADE.ID_ESPECIALIDADE = CONSULTA.ID_ESPECIALIDADE
                LEFT JOIN AMB_SUBGRUPO SUBGRUPO ON SUBGRUPO.ID_SUBGRUPO = ESPECIALIDADE.ID_SUBGRUPO
                LEFT JOIN AMB_GRUPO GRUPO ON SUBGRUPO.ID_GRUPO = GRUPO.ID_GRUPO AND GRUPO.TIPO_GRUPO = 'C' AND GRUPO.FLG_ATIVO = 'S'
                WHERE (CONSULTA.TIPO_LOG = 'T' OR CONSULTA.TIPO_LOG IS NULL)
                AND CONSULTA.COD_PACIENTE IN ({pacientes_sql})
                AND CONSULTA.DATA_AGENDA >= '{data_inicio}'
                AND CONSULTA.DATA_AGENDA < '{data_fim}'

                UNION 

                SELECT 
                    'EXAME' CATEGORIA_ATENDIMENTO,
                    CONSULTA.ID_AGE_EXAME_HOR CODIGO_HORARIO,
                    CONSULTA.COD_PACIENTE CODIGO_PACIENTE,
                    'Transferência ou Outros' LINHA_TEMPO,
                    CONSULTA.DATA_AGENDA,
                    CONSULTA.HOR_INI HORARIO,
                    EXECUTANTE.UNIDADE_FANTASIA UNIDADE_EXECUTANTE,
                    ESPECIALIDADE.ID_EXAME CODIGO_RECURSO,
                    UPPER(ESPECIALIDADE.NOME_EXAME) NOME_RECURSO,
                    GRUPO.ID_GRUPO CODIGO_GRUPO,
                    UPPER(GRUPO.NOME_GRUPO) NOME_GRUPO,                          
                    SUBGRUPO.ID_SUBGRUPO CODIGO_SUBGRUPO,
                    UPPER(SUBGRUPO.NOME_SUBGRUPO) NOME_SUBGRUPO,
                    NULL CID,
                    CONSULTA.COD_UNIDADE_SOLICITANTE,
                    CONSULTA.COD_UNIDADE_EXECUTANTE,
                    NULL TIPO,
                    (CASE
                        WHEN CONSULTA.STATUS = 'A' THEN 'Ausente'
                        WHEN CONSULTA.STATUS = 'D' THEN 'Desistente'
                        WHEN CONSULTA.STATUS = 'I' THEN 'Dispensado'
                        WHEN CONSULTA.STATUS = 'P' THEN 'Presente'
                        WHEN CONSULTA.DATA_AGENDA >= CAST(GETDATE() AS DATE) THEN'Sem recepção (Agenda Futura)'
                        ELSE 'Sem recepção'
                    END) RECEPCAO,
                    CONSULTA.DATA_ACAO DATA_ULTIMA_ATUALIZACAO,
                    CONSULTA.TIPO_LOG						TIPO_LOG,
                    CONSULTA.ID_MOTIVO						CODIGO_MOTIVO  
                FROM 
                    AMB_LOG_EXAME CONSULTA 
                LEFT JOIN ADMAMB_ADM_UNIDADE EXECUTANTE ON EXECUTANTE.COD_UNIDADE = CONSULTA.COD_UNIDADE_EXECUTANTE
                LEFT JOIN AMB_EXAME1 ESPECIALIDADE ON ESPECIALIDADE.ID_EXAME = CONSULTA.ID_EXAME
                LEFT JOIN AMB_SUBGRUPO SUBGRUPO ON SUBGRUPO.ID_SUBGRUPO = ESPECIALIDADE.ID_SUBGRUPO
                LEFT JOIN AMB_GRUPO GRUPO ON SUBGRUPO.ID_GRUPO = GRUPO.ID_GRUPO AND GRUPO.TIPO_GRUPO = 'E' AND GRUPO.FLG_ATIVO = 'S'
                WHERE (CONSULTA.TIPO_LOG = 'T' OR CONSULTA.TIPO_LOG IS NULL)
                AND CONSULTA.COD_PACIENTE IN ({pacientes_sql})
                AND CONSULTA.DATA_AGENDA >= '{data_inicio}'
                AND CONSULTA.DATA_AGENDA < '{data_fim}'       
                     
        """

        df_temp = fcn.extrair_dados(conexao, sql, logger)

        if df_temp.empty:
            logger.info(f"Não retornou nenhum dado.")
            
        if not df_temp.empty:
            lista_df.append(df_temp)        
            fcn.incluir_dados(df_temp,'TB_HISTORICO_AGENDAMENTOS',conexao_mraDev)

    if lista_df:
        return pd.concat(lista_df, ignore_index=True)

    return pd.DataFrame()             
######################################################################################################################################################

######################################################################################################################################################
# Achar os agendamentos dos pacientes da fila tempo de cuidar ########################################################################################
######################################################################################################################################################

def ExtraindoAgendando():
    dfRecursoPacienteFila = fcn.extrair_dados(conexao_mraDev,recurso_paciente_fila,logger)

    pacientes = (dfRecursoPacienteFila["CODIGO_PACIENTE"].dropna().astype(int).unique().tolist())

    ano_atual = datetime.now().year

    lista_agendas = []

    for ano in range(2009, ano_atual + 1):
        
        if logger:
            logger.info(f"Buscando agendamentos do ano {ano}")      

        df_ano = buscaAgendamentoPorAno(
            conexao=conexao_Producao,
            pacientes=pacientes,
            ano=ano,
            logger=logger
        )

    '''
        if not df_ano.empty:
            lista_agendas.append(df_ano)

    dfAgendamentosTempoCuidar = (
        pd.concat(lista_agendas, ignore_index=True)
        if lista_agendas
        else pd.DataFrame()
    )

    df_fila = dfRecursoPacienteFila.copy()
    df_agenda = dfAgendamentosTempoCuidar.copy()

    df_fila["DATA_ENTRADA"] = pd.to_datetime(df_fila["DATA_ENTRADA"])
    df_agenda["DATA_AGENDA"] = pd.to_datetime(df_agenda["DATA_AGENDA"])

    df_fila["CODIGO_PACIENTE"] = pd.to_numeric(df_fila["CODIGO_PACIENTE"], errors="coerce")
    df_agenda["CODIGO_PACIENTE"] = pd.to_numeric(df_agenda["CODIGO_PACIENTE"], errors="coerce")

    df_base = df_fila.merge(
        df_agenda,
        on=["CODIGO_PACIENTE", "CATEGORIA_ATENDIMENTO"],
        how="left",
        suffixes=("_FILA", "_AGENDA")
    )

    df_resultado = df_base[
        (df_base["DATA_AGENDA"] >= df_base["DATA_ENTRADA"]) &
        (
            (df_base["CODIGO_SUBGRUPO_FILA"] == df_base["CODIGO_SUBGRUPO_AGENDA"]) |
            (df_base["CODIGO_RECURSO_FILA"] == df_base["CODIGO_RECURSO_AGENDA"])
        )
    ].copy()


    print(df_resultado)
    fcn.incluir_dados(df_resultado,'TB_TESTE',conexao_mraDev)
    '''

def agendamentoPorAno():
    try:
        ano_atual = datetime.now().year
        for ano_fila in range(2009, ano_atual + 1):
            logger.info(f"Buscando fila do ano {ano_fila}")   
            print(f"Ano da fila: {ano_fila}")
            recurso_paciente_fila_ano = f'''
                                        WITH 
                                        DADOS_PACIENTE AS (SELECT 
                                                            CODIGO_PACIENTE, 
                                                            MIN(ANO_ENTRADA) ANO_ENTRADA 
                                                        FROM TB_TEMPO_CUIDAR_ATUALIZADA 
                                                        GROUP BY CODIGO_PACIENTE)                                            
                                            SELECT CODIGO_PACIENTE FROM DADOS_PACIENTE WHERE ANO_ENTRADA = {ano_fila}
                                    '''   
            dfRecursoPacienteFila = fcn.extrair_dados(conexao_mraDev,recurso_paciente_fila_ano,logger)

            pacientes = (dfRecursoPacienteFila["CODIGO_PACIENTE"].dropna().astype(int).unique().tolist()) 

            for ano in range(ano_fila, ano_atual + 1):
                print(f"Buscando agendamentos do ano {ano}")
                if logger:
                    logger.info(f"Buscando agendamentos do ano {ano}")      

                buscaAgendamentoPorAno(conexao=conexao_Producao,pacientes=pacientes,ano=ano,logger=logger)      
                buscaAgendamentoPorAnoTransferenciaOutros(conexao=conexao_Producao,pacientes=pacientes,ano=ano,logger=logger)                  
    except Exception as e:
        logger.info(f"Erro : {e}")
        print(f"Erro : {e}")

if __name__ == "__main__":        
    agendamentoPorAno()