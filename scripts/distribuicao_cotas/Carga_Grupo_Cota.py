from Amb_Cotas_Metodos import ApagarDados, ExtrairDados, IncluirDados, conexaoMRA, conexaoProducao, logger
############################################################################################################################################
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_GRUPO_COTA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_GRUPO_COTA.")
    #Para atender aos relatorios tempo de cuidar que serao criados só preciso do ano de 2026.    
    comando = f'''
                SELECT 
                    'E' TIPO,
                    GRUPO_COTA.ID_GRUPO_COTA,
                    GRUPO_COTA.NOME_GRUPO_COTA,
                    ASSOCIACAO_EXAME.ID_EXAME CODIGO_RECURSO,
                    GRUPO_COTA.COD_UNIDADE
                FROM 
                    AMB_ASSOCIACAO ASSOCIACAO
                INNER JOIN AMB_ASSOCIACAO_EXAME ASSOCIACAO_EXAME ON ASSOCIACAO_EXAME.ID_ASSOCIACAO = ASSOCIACAO.ID_ASSOCIACAO
                INNER JOIN AMB_GRUPO_COTA GRUPO_COTA ON ASSOCIACAO.ID_GRUPO_COTA = GRUPO_COTA.ID_GRUPO_COTA
                WHERE GRUPO_COTA.FLG_ATIVO = 'S'
                AND ASSOCIACAO.FLG_ATIVO = 'S'
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_GRUPO_COTA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_GRUPO_COTA.")      