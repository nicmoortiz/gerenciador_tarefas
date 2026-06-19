from Amb_Cotas_Metodos import ApagarDados, ExtrairDados, IncluirDados, conexaoMRA, conexaoProducao, logger
############################################################################################################################################
if __name__ == "__main__":

    logger.info(f"--> INICIOU ROTINA ApagarDados.")
    ApagarDados("TB_CONSOLIDADO_COTA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA ApagarDados.")  
    logger.info(f"--> INICIOU ROTINA DE CARGA - TB_CONSOLIDADO_COTA.")
    comando = f'''
                    WITH
                        DISTRIBUICAO_COTAS_EXECUTANTE AS (
                                                            SELECT 
                                                                COTA.FERRAMENTA, 
                                                                COTA.TIPO, 
                                                                ARVORE.CODIGO_UNIDADE,
                                                                ARVORE.NOME_UNIDADE, 
                                                                COTA.MES,
                                                                COTA.ANO,
                                                                COTA.CODIGO_ARVORE_TOPO, 
                                                                COTA.CODIGO_RECURSO, 
                                                                COTA.NOME_RECURSO,  
                                                                SUM(COTA_TOTAL) COTA_TOTAL
                                                            FROM TB_DISTRIBUICAO_COTAS COTA 
                                                            LEFT JOIN TB_ARVORE ARVORE ON ARVORE.ID_ARVORE = COTA.CODIGO_ARVORE_TOPO AND ARVORE.FERRAMENTA = COTA.FERRAMENTA
                                                            WHERE COTA.CODIGO_ARVORE_PAI = COTA.CODIGO_ARVORE_TOPO
                                                            AND COTA.CODIGO_UNIDADE <> 0
                                                            GROUP BY COTA.FERRAMENTA, 
                                                                COTA.TIPO, 
                                                                ARVORE.CODIGO_UNIDADE,
                                                                ARVORE.NOME_UNIDADE, 
                                                                COTA.MES,
                                                                COTA.ANO,
                                                                COTA.CODIGO_ARVORE_TOPO, 
                                                                COTA.CODIGO_RECURSO, 
                                                                COTA.NOME_RECURSO),
                        AGENDA_EXECUTANTE AS (
                                                SELECT 
                                                    AGENDA.MES,
                                                    AGENDA.ANO,
                                                    AGENDA.TIPO,
                                                    AGENDA.CODIGO_RECURSO,
                                                    AGENDA.CODIGO_EXECUTANTE,
                                                    MIN(AGENDA.IDADE_INICIAL) IDADE_INICIAL, 
                                                    MIN(IDADE_FINAL) IDADE_FINAL,
                                                    SUM(AGENDA.OFERTA) OFERTA,
                                                    SUM(AGENDA.AGENDAMENTO_BLOQUEADO)AGENDAMENTO_BLOQUEADO,
                                                    SUM(AGENDA.AGENDAMENTO_BOLSAO)AGENDAMENTO_BOLSAO,
                                                    SUM(AGENDA.AGENDAMENTO_NAO_DISTRIBUIDO)AGENDAMENTO_NAO_DISTRIBUIDO,
                                                    SUM(AGENDA.AGENDAMENTO_POR_COTA)AGENDAMENTO_POR_COTA,
                                                    SUM(AGENDA.AGENDAMENTO_TOTAL)AGENDAMENTO_TOTAL
                                                FROM 
                                                    TB_RESUMO_AGENDAMENTO AGENDA
                                                GROUP BY 	
                                                    AGENDA.MES,
                                                    AGENDA.ANO,
                                                    AGENDA.TIPO,
                                                    AGENDA.CODIGO_RECURSO,
                                                    AGENDA.CODIGO_EXECUTANTE
                                            ),
                        DADOS_COTAS AS  (
                                            SELECT 
                                                COTA.*,
                                                AGENDA.IDADE_INICIAL,
                                                AGENDA.IDADE_FINAL,
                                                AGENDA.OFERTA,
                                                AGENDA.AGENDAMENTO_BLOQUEADO,
                                                AGENDA.AGENDAMENTO_BOLSAO,
                                                AGENDA.AGENDAMENTO_NAO_DISTRIBUIDO,
                                                AGENDA.AGENDAMENTO_POR_COTA,
                                                AGENDA.AGENDAMENTO_TOTAL
                                            FROM 
                                                DISTRIBUICAO_COTAS_EXECUTANTE COTA
                                            LEFT JOIN AGENDA_EXECUTANTE AGENDA ON AGENDA.MES = COTA.MES AND AGENDA.ANO = COTA.ANO AND AGENDA.TIPO = COTA.TIPO AND AGENDA.CODIGO_RECURSO = COTA.CODIGO_RECURSO AND AGENDA.CODIGO_EXECUTANTE = COTA.CODIGO_UNIDADE
                                        ),
                        DADOS_FINAIS AS (
                                            SELECT 
                                                FERRAMENTA,
                                                TIPO,
                                                ANO,
                                                MES,
                                                CODIGO_RECURSO,
                                                NOME_RECURSO,
                                                UNIDADE.CODIGO_DRS,
                                                UNIDADE.NOME_DRS,
                                                DADOS_COTAS.CODIGO_UNIDADE CODIGO_UNIDADE_REFERENCIA,
                                                DADOS_COTAS.NOME_UNIDADE UNIDADE_REFERENCIA, 
                                                IDADE_INICIAL,
                                                IDADE_FINAL,
                                                COTA_TOTAL COTA,
                                                OFERTA,
                                                AGENDAMENTO_BLOQUEADO,
                                                AGENDAMENTO_BOLSAO,
                                                AGENDAMENTO_NAO_DISTRIBUIDO,
                                                AGENDAMENTO_POR_COTA,
                                                AGENDAMENTO_TOTAL
                                            FROM 
                                                DADOS_COTAS
                                            LEFT JOIN TB_TEMPO_CUIDAR_UNIDADE UNIDADE ON UNIDADE.CODIGO_UNIDADE = DADOS_COTAS.CODIGO_UNIDADE)
                    SELECT 
                        * 
                    FROM 
                        DADOS_FINAIS
                    ORDER BY DADOS_FINAIS.FERRAMENTA, DADOS_FINAIS.TIPO, DADOS_FINAIS.UNIDADE_REFERENCIA, DADOS_FINAIS.MES, DADOS_FINAIS.NOME_RECURSO
               '''    
    dfDados = ExtrairDados(conexaoMRA,comando)
    IncluirDados(dfDados,"TB_CONSOLIDADO_COTA",conexaoMRA)    
    logger.info(f"--> FINALIZOU ROTINA DE CARGA - TB_CONSOLIDADO_COTA.")      