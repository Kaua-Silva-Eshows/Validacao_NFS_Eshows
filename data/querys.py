from data.dbconnect import get_dataframe_from_query
def nfs_query():
    return get_dataframe_from_query("""
   WITH CTE_DADOS AS (
    SELECT
        TP.FK_FECHAMENTO AS 'Fechamento',
        TP.ID AS 'PROPOSTA',
        TNF.ID AS 'NF_ID',
        CASE WHEN TP.ADIANTAMENTO = 1 THEN 'sim' ELSE 'nao' END AS 'Antecipacao',
        TC.NAME AS 'Casa',
        TC.CNPJ AS 'CNPJ_Casa',
        TA.NOME AS 'Artista',
        TNF.NUMERO_NOTA_FISCAL AS 'Num_NF',
        EF.FILENAME AS 'Link',
        SUM(TP.VALOR_BRUTO) AS 'Valor_Total',
        SUM(TP.VALOR_BRUTO) AS 'Valor_Proposta',
        TCNF.STATUS_NF AS 'Status_NF',
        TNF2.ID AS ID_NOTA_FISCAL,
        CONCAT("https://admin.eshows.com.br/proposta/", P2.ID) AS ID_PROPOSTA,
        TNF2.CREATED_AT,
        EF2.FILENAME,
        COUNT(*) OVER (PARTITION BY TP.ID) AS CNT
    FROM T_PROPOSTAS TP 
    LEFT JOIN T_PROPOSTA_NOTA_FISCAL PNF ON (PNF.FK_PROPOSTA = TP.ID)
    LEFT JOIN T_NOTAS_FISCAIS TNF ON (PNF.FK_NOTA = TNF.ID AND TNF.FK_STATUS_NF = 100)
    LEFT JOIN T_FECHAMANETOS TF ON (TP.FK_FECHAMENTO = TF.ID)
    LEFT JOIN EPM_FILES EF ON (TNF.ID = EF.TABLE_ID)
    LEFT JOIN T_ATRACOES TA ON (TNF.FK_ATRACAO = TA.ID)
    LEFT JOIN T_COMPANIES TC ON (TP.FK_CONTRANTE = TC.ID)
    LEFT JOIN T_CONFERENCIA_NOTA_FISCAL TCNF ON (TNF.FK_STATUS_NF = TCNF.ID)
    LEFT JOIN T_CONFERENCIA_NOTA_FISCAL_ROBO TCNFR ON (TNF.FK_STATUS_NF_ROBO = TCNFR.ID)
    LEFT JOIN T_NOTAS_FISCAIS TNF2 ON (TNF2.FK_ATRACAO = TP.FK_CONTRATADO AND TNF2.NUMERO_NOTA_FISCAL = TNF.NUMERO_NOTA_FISCAL AND TNF2.ID != TNF.ID AND TNF2.FK_STATUS_NF != 102)
    LEFT JOIN T_PROPOSTAS P2 ON (P2.FK_NOTA_FISCAL = TNF2.ID)
    LEFT JOIN EPM_FILES EF2 ON (TNF2.ID = EF2.TABLE_ID AND EF2.TABLE_NAME = "T_NOTAS_FISCAIS")
    LEFT JOIN T_INFOS_NOTAS_FISCAIS INF ON (INF.FK_NOTA_FISCAL = TNF.ID)
    WHERE EF.TABLE_NAME = 'T_NOTAS_FISCAIS'
      AND TCNF.STATUS_NF = "Pendente"
      AND TC.ID NOT IN (102)
      AND INF.ID IS NULL
    GROUP BY 
        TNF.NUMERO_NOTA_FISCAL, 
        TC.CNPJ, 
        TP.FK_FECHAMENTO, 
        TNF.ID, 
        TP.ADIANTAMENTO, 
        TC.NAME, 
        TA.NOME, 
        EF.FILENAME, 
        TCNF.STATUS_NF, 
        TNF2.ID, 
        P2.ID, 
        TNF2.CREATED_AT, 
        EF2.FILENAME
)
SELECT *
FROM CTE_DADOS
WHERE CNT = 1                                                                             
""")
