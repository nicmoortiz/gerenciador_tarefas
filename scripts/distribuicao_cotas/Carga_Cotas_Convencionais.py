from Amb_Cotas_Metodos import ApagarDados, ExtrairDados, IncluirDados, conexaoMRA, conexaoProducao, logger
############################################################################################################################################
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_DISTRIBUICAO_COTAS",conexaoMRA,"FERRAMENTA = 'CONVENCIONAL'")    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_DISTRIBUICAO_COTAS.")
    comando = f'''
                SELECT
                    'CONVENCIONAL'							FERRAMENTA,
                    'CONSULTA'								TIPO,

                    COTA.REF_MES							MES,
                    COTA.REF_ANO							ANO,

                    RECURSO.ID_ESPECIALIDADE				CODIGO_RECURSO,
                    UPPER(RECURSO.NOME_ESPECIALIDADE)		NOME_RECURSO,

                    COTA.COD_UNIDADE						CODIGO_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA				NOME_UNIDADE,

                    UNIDADE_ARVORE.COD_UNIDADE				CODIGO_UNIDADE_ARVORE,
                    UNIDADE_ARVORE.UNIDADE_FANTASIA			NOME_UNIDADE_ARVORE,

                    UNIDADE_ARVORE_TOPO.COD_UNIDADE			CODIGO_UNIDADE_TOPO,
                    UNIDADE_ARVORE_TOPO.UNIDADE_FANTASIA	NOME_UNIDADE_TOPO,

                    UNIDADE_ARVORE_PAI.COD_UNIDADE			CODIGO_UNIDADE_PAI,
                    UNIDADE_ARVORE_PAI.UNIDADE_FANTASIA		NOME_UNIDADE_PAI,
                    DRS_PAI.SIGLA_DRS						DRS_PAI,

                    COTA.COTA_CONSULTA_VALOR				COTA_VALOR,
                    COTA.COTA_CONSULTA_TOTAL				COTA_TOTAL,
                    COTA.COTA_CONSULTA_SALDO				COTA_SALDO,

                    --IDS
                    COTA.ID_COTA_CONSULTA					ID_COTA,
                    COTA.ID_ARVORE							CODIGO_ARVORE,
                    COTA.ID_ARVORE_TOPO						CODIGO_ARVORE_TOPO,
                    COTA.ID_ARVORE_PAI						CODIGO_ARVORE_PAI,
	                ARVORE.FLG_AGENDA						FLG_AGENDA
                FROM 
                    AMB_COTA_CONSULTA COTA
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE				ON UNIDADE.COD_UNIDADE				= COTA.COD_UNIDADE
                LEFT JOIN AMB_ESPECIALIDADE		RECURSO				ON RECURSO.ID_ESPECIALIDADE			= COTA.ID_ESPECIALIDADE

                LEFT JOIN AMB_ARVORE			ARVORE				ON ARVORE.ID_ARVORE					= COTA.ID_ARVORE
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE		ON UNIDADE_ARVORE.COD_UNIDADE		= ARVORE.COD_UNIDADE

                LEFT JOIN AMB_ARVORE			ARVORE_TOPO			ON ARVORE_TOPO.ID_ARVORE			= COTA.ID_ARVORE_TOPO
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE_TOPO	ON UNIDADE_ARVORE_TOPO.COD_UNIDADE	= ARVORE_TOPO.COD_UNIDADE

                LEFT JOIN AMB_ARVORE			ARVORE_PAI			ON ARVORE_PAI.ID_ARVORE				= COTA.ID_ARVORE_PAI
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE_PAI	ON UNIDADE_ARVORE_PAI.COD_UNIDADE	= ARVORE_PAI.COD_UNIDADE
                LEFT JOIN AMB_DRS				DRS_PAI				ON UNIDADE_ARVORE_PAI.COD_DRS		= DRS_PAI.COD_DRS
                WHERE	COTA.REF_ANO >= YEAR(GETDATE())  
                AND     COTA.REF_MES >= 1
                                
                UNION ALL
                                
                                
                SELECT 
                    'CONVENCIONAL'							FERRAMENTA,
                    'EXAME'									TIPO,

                    COTA.REF_MES							MES,
                    COTA.REF_ANO							ANO,

                    RECURSO.ID_GRUPO_COTA					CODIGO_RECURSO,
                    UPPER(RECURSO.NOME_GRUPO_COTA)			NOME_RECURSO,

                    COTA.COD_UNIDADE						CODIGO_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA				NOME_UNIDADE,

                    UNIDADE_ARVORE.COD_UNIDADE				CODIGO_UNIDADE_ARVORE,
                    UNIDADE_ARVORE.UNIDADE_FANTASIA			NOME_UNIDADE_ARVORE,

                    UNIDADE_ARVORE_TOPO.COD_UNIDADE			CODIGO_UNIDADE_TOPO,
                    UNIDADE_ARVORE_TOPO.UNIDADE_FANTASIA	NOME_UNIDADE_TOPO,

                    UNIDADE_ARVORE_PAI.COD_UNIDADE			CODIGO_UNIDADE_PAI,
                    UNIDADE_ARVORE_PAI.UNIDADE_FANTASIA		NOME_UNIDADE_PAI,
                    DRS_PAI.SIGLA_DRS						DRS_PAI,

                    COTA.COTA_EXAME_VALOR					COTA_VALOR,
                    COTA.COTA_EXAME_TOTAL					COTA_TOTAL,
                    COTA.COTA_EXAME_SALDO					COTA_SALDO,

                    --IDS
                    COTA.ID_COTA_EXAME						ID_COTA,
                    COTA.ID_ARVORE							CODIGO_ARVORE,
                    COTA.ID_ARVORE_TOPO						CODIGO_ARVORE_TOPO,
                    COTA.ID_ARVORE_PAI						CODIGO_ARVORE_PAI,
	                ARVORE.FLG_AGENDA						FLG_AGENDA
                FROM 
                    AMB_COTA_EXAME				COTA
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE				ON UNIDADE.COD_UNIDADE				= COTA.COD_UNIDADE
                LEFT JOIN AMB_GRUPO_COTA		RECURSO				ON RECURSO.ID_GRUPO_COTA			= COTA.ID_GRUPO_COTA

                LEFT JOIN AMB_ARVORE			ARVORE				ON ARVORE.ID_ARVORE					= COTA.ID_ARVORE
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE		ON UNIDADE_ARVORE.COD_UNIDADE		= ARVORE.COD_UNIDADE

                LEFT JOIN AMB_ARVORE			ARVORE_TOPO			ON ARVORE_TOPO.ID_ARVORE			= COTA.ID_ARVORE_TOPO
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE_TOPO	ON UNIDADE_ARVORE_TOPO.COD_UNIDADE	= ARVORE_TOPO.COD_UNIDADE

                LEFT JOIN AMB_ARVORE			ARVORE_PAI			ON ARVORE_PAI.ID_ARVORE				= COTA.ID_ARVORE_PAI
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE_PAI	ON UNIDADE_ARVORE_PAI.COD_UNIDADE	= ARVORE_PAI.COD_UNIDADE
                LEFT JOIN AMB_DRS				DRS_PAI				ON UNIDADE_ARVORE_PAI.COD_DRS		= DRS_PAI.COD_DRS

                WHERE	COTA.REF_ANO >= YEAR(GETDATE())  
                AND     COTA.REF_MES >= 1      
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_DISTRIBUICAO_COTAS",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_DISTRIBUICAO_COTAS.")      