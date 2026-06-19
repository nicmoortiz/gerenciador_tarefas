from Amb_Cotas_Metodos import ApagarDados, ExtrairDados, IncluirDados, conexaoMRA, conexaoProducao, logger
############################################################################################################################################
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_DISTRIBUICAO_COTAS",conexaoMRA,"FERRAMENTA = 'REGULADA'")    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_DISTRIBUICAO_COTAS.")
    comando = f'''
                SELECT
                            
                    'REGULADA'								FERRAMENTA,
                    (CASE
                        WHEN COTA.COD_TIPO = 'C' THEN 
                            'CONSULTA'
                        ELSE
                            'EXAME'
                    END)									TIPO,

                    COTA.MES_COTA							MES,
                    COTA.ANO_COTA							ANO,

                    (CASE
                        WHEN COTA.COD_TIPO = 'C' THEN 
                            ESPECIALIDADE.ID_ESPECIALIDADE			
                        ELSE
                            GRUPO_COTA.ID_GRUPO_COTA	
                    END)									CODIGO_RECURSO,	

                    UPPER(CASE
                        WHEN COTA.COD_TIPO = 'C' THEN 
                            ESPECIALIDADE.NOME_ESPECIALIDADE			
                        ELSE
                            GRUPO_COTA.NOME_GRUPO_COTA
                    END)									NOME_RECURSO,		

                    COTA.COD_UNIDADE						CODIGO_UNIDADE,
                    UNIDADE.UNIDADE_FANTASIA				NOME_UNIDADE,

                    UNIDADE_ARVORE.COD_UNIDADE				CODIGO_UNIDADE_ARVORE,
                    UNIDADE_ARVORE.UNIDADE_FANTASIA			NOME_UNIDADE_ARVORE,

                    UNIDADE_ARVORE.COD_UNIDADE				CODIGO_UNIDADE_TOPO,
                    UNIDADE_ARVORE.UNIDADE_FANTASIA			NOME_UNIDADE_TOPO,

                    UNIDADE_ARVORE.COD_UNIDADE				CODIGO_UNIDADE_PAI,
                    UNIDADE_ARVORE.UNIDADE_FANTASIA			NOME_UNIDADE_PAI,
                    DRS_PAI.SIGLA_DRS						DRS_PAI,

                    CAST(COTA.VALOR_COTA AS VARCHAR(20)) 	COTA_VALOR,
                    COTA.VALOR_COTA							COTA_TOTAL,
                    COTA.VALOR_COTA							COTA_SALDO,

                    --IDS
                    COTA.ID_COTA							ID_COTA,
                    COTA.ID_ARVORE_TOPO						CODIGO_ARVORE,
                    COTA.ID_ARVORE_TOPO						CODIGO_ARVORE_TOPO,
                    COTA.ID_ARVORE_TOPO						CODIGO_ARVORE_PAI  ,
	                ARVORE.FLG_AGENDA						FLG_AGENDA             
                    
                FROM 
                    [Amb-Reg_cota] COTA
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE				ON UNIDADE.COD_UNIDADE				=	COTA.COD_UNIDADE
                LEFT JOIN AMB_ESPECIALIDADE		ESPECIALIDADE		ON ESPECIALIDADE.ID_ESPECIALIDADE	=	COTA.ID_ESP_EXAME AND COTA.COD_TIPO = 'C'
                LEFT JOIN AMB_GRUPO_COTA		GRUPO_COTA			ON GRUPO_COTA.ID_GRUPO_COTA			=	COTA.ID_ESP_EXAME AND COTA.COD_TIPO = 'E'

                LEFT JOIN Amb_arvore_regulacao	ARVORE				ON ARVORE.ID_ARVORE_REGULACAO		=	COTA.ID_ARVORE_TOPO		
                LEFT JOIN ADMAMB_ADM_UNIDADE	UNIDADE_ARVORE		ON UNIDADE_ARVORE.COD_UNIDADE		=	ARVORE.COD_UNIDADE
                LEFT JOIN AMB_DRS				DRS_PAI				ON UNIDADE_ARVORE.COD_DRS			=	DRS_PAI.COD_DRS

                WHERE	COTA.ANO_COTA >= YEAR(GETDATE()) 
                AND     COTA.MES_COTA >= 1              
               '''    
    dfSOLICITACAO = ExtrairDados(conexaoProducao,comando)
    IncluirDados(dfSOLICITACAO,"TB_DISTRIBUICAO_COTAS",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_DISTRIBUICAO_COTAS.")      