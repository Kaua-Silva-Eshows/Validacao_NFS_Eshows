# Projeto de Validação de Notas Fiscais

Este projeto tem como objetivo validar notas fiscais a partir de um banco de dados e fornecer feedback sobre a validade de cada nota. Ele também processa as notas fiscais de acordo com as regras definidas, gera relatórios e sobe os dados validados no banco de dados. A interface gráfica, desenvolvida com Tkinter, exibe os resultados da validação para interação do usuário.


## Índice

1. [Funcionalidades](#funcionalidades)
2. [Requisitos](#requisitos)
3. [Como Usar](#como-usar)
4. [Consulta de validação](#consulta-de-validacao)
4. [Como Funciona](#como-funciona)

## Funcionalidades

- **Conexão com Banco de Dados MySQL**: O sistema se conecta a um banco de dados MySQL para buscar informações sobre as notas fiscais.
- **Validação de Notas Fiscais**: Através de uma função de validação personalizada, o sistema verifica a conformidade das notas fiscais com base em dados como CNPJ, número da nota fiscal e valores de proposta.
- **Interface Gráfica**: A interface gráfica usa a biblioteca Tkinter para exibir os resultados da validação e permite a atualização dos resultados em tempo real.
- **Integração com OpenAI**: A API do OpenAI é usada para algumas funcionalidades adicionais no processo de validação.

## Requisitos

Para rodar este projeto, você precisa ter o Python 3.x instalado, juntamente com as seguintes dependências:

- `mysql-connector-python`
- `tkinter`
- `openai`
- Outras...

Você pode instalar as dependências necessárias com o comando:

```bash
pip install -r requirements.txt
```

## Como Usar
1- Configuração: Antes de rodar o projeto, crie o arquivo config.py na raiz do projeto com as credenciais do banco de dados e da API, conforme mostrado abaixo:

Exemplo de config.py:
```bash
DB_HOST = 'your-db-host'
DB_PORT = 'your-db-port'
DB_DATABASE = 'your-db-name'
DB_USER = 'your-db-username'
DB_PASSWORD = 'your-db-password'

# Dados de login
LOGIN_USERNAME = 'your-username'
LOGIN_PASSWORD = 'your-password'

# Chave da API do OpenAI
OPENAI_API_KEY = 'your-openai-api-key'
```
2- Rodar o Projeto: Execute o script principal main.py para iniciar o processo de validação de notas fiscais:

```bash
python main.py
```

3- Exibição dos Resultados: Após rodar o script, uma janela gráfica será aberta mostrando os resultados da validação das notas fiscais. Você pode atualizar os resultados clicando no botão "Atualizar". Além disso, os dados validados serão automaticamente inseridos ou atualizados no banco de dados.

## Consulta de validação
```sql
SELECT

TNF.ID AS 'NF_ID',
TA.NOME AS 'Artista',
TNF.NUMERO_NOTA_FISCAL AS 'Num_NF',
INF.NUMERO_ROBO AS 'Num_NF_IA',

CASE
    WHEN TC.CNPJ NOT LIKE '%\.%' 
      AND TC.CNPJ NOT LIKE '%/%' 
      AND TC.CNPJ NOT LIKE '%-%' 
    THEN CONCAT(
        SUBSTRING(TC.CNPJ, 1, 2), '.', 
        SUBSTRING(TC.CNPJ, 3, 3), '.', 
        SUBSTRING(TC.CNPJ, 6, 3), '/', 
        SUBSTRING(TC.CNPJ, 9, 4), '-', 
        SUBSTRING(TC.CNPJ, 13, 2)
    )
    ELSE TC.CNPJ
END AS 'CNPJ_Casa',

INF.CNPJ_TOMADOR AS 'CNPJ_Casa_IA',
TP.VALOR_BRUTO AS 'Valor Proposta',
INF.VALOR_SERVICO AS 'Valor_Liquido_IA',

CASE 
    WHEN TNF.NUMERO_NOTA_FISCAL = INF.NUMERO_ROBO 
         AND (
             (TC.CNPJ NOT LIKE '%\.%' 
              	AND TC.CNPJ NOT LIKE '%/%' 
              	AND TC.CNPJ NOT LIKE '%-%' 
             AND CONCAT(
                 SUBSTRING(TC.CNPJ, 1, 2), '.', 
                 SUBSTRING(TC.CNPJ, 3, 3), '.', 
                 SUBSTRING(TC.CNPJ, 6, 3), '/', 
                 SUBSTRING(TC.CNPJ, 9, 4), '-', 
                 SUBSTRING(TC.CNPJ, 13, 2)
             ) = INF.CNPJ_TOMADOR)
             OR 
             (TC.CNPJ = INF.CNPJ_TOMADOR)
         )
         AND TP.VALOR_BRUTO = INF.VALOR_SERVICO
    THEN '1'
    ELSE '0'
END AS 'VALIDAÇÃO',

EF.FILENAME AS 'Link'

FROM T_PROPOSTAS TP 
LEFT JOIN T_PROPOSTA_NOTA_FISCAL PNF ON (PNF.FK_PROPOSTA = TP.ID)
LEFT JOIN T_NOTAS_FISCAIS TNF ON (PNF.FK_NOTA = TNF.ID AND TNF.FK_STATUS_NF)
LEFT JOIN EPM_FILES EF ON (TNF.ID = EF.TABLE_ID)
LEFT JOIN T_ATRACOES TA ON (TNF.FK_ATRACAO = TA.ID)
LEFT JOIN T_COMPANIES TC ON (TP.FK_CONTRANTE = TC.ID)
LEFT JOIN T_CONFERENCIA_NOTA_FISCAL TCNF ON (TNF.FK_STATUS_NF = TCNF.ID)
LEFT JOIN T_INFOS_NOTAS_FISCAIS INF ON INF.FK_NOTA_FISCAL = TNF.ID
WHERE DATE_FORMAT(INF.LAST_UPDATE, '%Y/%m/%d') = CURDATE()

GROUP BY TNF.ID
```

- A consulta SQL é responsável por recuperar e verificar os dados das notas fiscais a partir do banco de dados. Ela realiza as seguintes verificações:

- Verificação de Conformidade dos Dados: A consulta verifica se os dados das notas fiscais, como o número da nota (NUMERO_NOTA_FISCAL), CNPJ do contratante (CNPJ_Casa) e os valores da proposta (VALOR_BRUTO), estão em conformidade com os dados extraídos e validados pelo sistema.

- Validação da Nota Fiscal: Ela retorna uma coluna chamada VALIDAÇÃO, que é preenchida com '1' para as notas fiscais que passaram nas verificações e com '0' para as que falharam. Isso é feito comparando o número da nota fiscal e o CNPJ do contratante com os valores armazenados na tabela de informações da nota fiscal, e validando se os valores correspondem entre as propostas e os serviços.

- Somente Dados Corretos: A consulta serve para filtrar apenas os dados que foram validados como corretos pelo código. Portanto, os registros com a coluna VALIDAÇÃO igual a '1' indicam que as informações estão consistentes e foram aprovadas pela lógica de validação definida no sistema.

- Resultados de Arquivo: A consulta também recupera o arquivo correspondente à nota fiscal, com a coluna Link fornecendo o caminho para o arquivo relacionado.

## Como Funciona
Conexão com o Banco de Dados: O código se conecta ao banco de dados MySQL utilizando as credenciais configuradas no arquivo config.py.

Processamento das Notas Fiscais: A função processar_notas_fiscais consulta o banco de dados e recupera as notas fiscais. Para cada nota, o sistema valida os dados (como CNPJ, número da nota e valor de proposta) e insere os resultados em uma lista.

Interface Gráfica: A interface gráfica exibe os resultados da validação das notas fiscais em uma área de texto rolável. Os resultados podem ser atualizados clicando no botão "Atualizar", que recarrega as notas fiscais e exibe os novos resultados.

API do OpenAI: A API do OpenAI é chamada para algumas funcionalidades adicionais de validação. Certifique-se de configurar sua chave de API corretamente no arquivo config.py.

Armazenamento no Banco de Dados: Após o processamento, os dados validados e os resultados da verificação (como o status de validação) são inseridos em uma tabela no banco de dados, permitindo o acompanhamento e a auditoria dos resultados.