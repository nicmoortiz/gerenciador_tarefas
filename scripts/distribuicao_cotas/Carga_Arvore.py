from Amb_Cotas_Metodos import ApagarDados, ExtrairDados, IncluirDados, conexaoMRA, conexaoProducao, logger
############################################################################################################################################
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_ARVORE",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_ARVORE.")
    #Para atender aos relatorios tempo de cuidar que serao criados só preciso do ano de 2026.    
    comando = f'''
                SELECT 
                    'CONVENCIONAL'                                                      FERRAMENTA,
                    ARVORE.ID_ARVORE_TOPO,
                    ARVORE.ID_ARVORE_PAI												ID_ARVORE_PAI,
                    DRS_TOPO.COD_DRS															CODIGO_DRS,
                    DRS_TOPO.SIGLA_DRS														SIGLA_DRS,
                    DRS_TOPO.NOME_DRS														NOME_DRS,
                    UNIDADE_TOPO.COD_UNIDADE											CODIGO_UNIDADE_ARVORE,
                    UNIDADE_TOPO.UNIDADE_FANTASIA										NOME_UNIDADE_ARVORE,
                    ARVORE.ID_ARVORE													ID_ARVORE,
                    UNIDADE.COD_UNIDADE													CODIGO_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA											NOME_UNIDADE,
                    ARVORE.FLG_ATIVO													ATIVO,
                    ARVORE.FLG_AGENDA													AGENDA
                FROM 
                    AMB_ARVORE ARVORE
                LEFT JOIN ADMAMB_ADM_UNIDADE		UNIDADE			ON UNIDADE.COD_UNIDADE			= ARVORE.COD_UNIDADE
                LEFT JOIN AMB_ARVORE 				ARVORE_TOPO		ON ARVORE_TOPO.ID_ARVORE		= ARVORE.ID_ARVORE_TOPO
                LEFT JOIN ADMAMB_ADM_UNIDADE		UNIDADE_TOPO	ON UNIDADE_TOPO.COD_UNIDADE		= ARVORE_TOPO.COD_UNIDADE
                LEFT JOIN AMB_DRS					DRS_TOPO		ON DRS_TOPO.COD_DRS				= UNIDADE_TOPO.COD_DRS
                UNION ALL 
                SELECT
                    'REGULADA'                                                          FERRAMENTA,
                    ARVORE.ID_ARVORE_REGULACAO                                          ID_ARVORE_TOPO,
                    ARVORE.ID_ARVORE_REGULACAO											ID_ARVORE_PAI,
                    DRS_TOPO.COD_DRS													CODIGO_DRS,
                    DRS_TOPO.SIGLA_DRS													SIGLA_DRS,
                    DRS_TOPO.NOME_DRS													NOME_DRS,
                    UNIDADE_TOPO.COD_UNIDADE											CODIGO_UNIDADE_ARVORE,
                    UNIDADE_TOPO.UNIDADE_FANTASIA										NOME_UNIDADE_ARVORE,
                    ARVORE.ID_ARVORE_REGULACAO											ID_ARVORE,
                    UNIDADE.COD_UNIDADE													CODIGO_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA											NOME_UNIDADE,
                    ARVORE.FLG_ATIVO													ATIVO,
                    ARVORE.FLG_AGENDA													AGENDA
                FROM Amb_arvore_regulacao ARVORE
                LEFT JOIN ADMAMB_ADM_UNIDADE		UNIDADE			ON UNIDADE.COD_UNIDADE			= ARVORE.COD_UNIDADE
                LEFT JOIN ADMAMB_ADM_UNIDADE		UNIDADE_TOPO	ON UNIDADE_TOPO.COD_UNIDADE		= ARVORE.COD_UNIDADE_TOPO
                LEFT JOIN AMB_DRS					DRS_TOPO		ON DRS_TOPO.COD_DRS				= UNIDADE_TOPO.COD_DRS                
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_ARVORE",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_ARVORE.")      