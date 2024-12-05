import mysql.connector
import pandas as pd
import config

def get_mysql_connection():
    # Definir diretamente as credenciais de conexão
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        database=config.DB_DATABASE,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )    
    return conn

def execute_query(query):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
        
        cursor.execute(query)
        
        # Verifique se cursor.description não é None
        if cursor.description is None:
            print("Descrição do cursor é None")
            return None, None

        # Obter nomes das colunas
        column_names = [col[0] for col in cursor.description]
        
        # Obter resultados
        result = cursor.fetchall()
        
        if not result:
            print("Nenhuma linha retornada pela consulta.")
        
        cursor.close()
        conn.close()
        return result, column_names
    except Exception as e:
        print(f"Erro ao executar a consulta: {e}")
        return None, None
    finally:
        cursor.close()
        conn.close()

def get_dataframe_from_query(consulta):
    result, column_names = execute_query(consulta)
    if result is None or column_names is None:
        return pd.DataFrame() 
    return pd.DataFrame(result, columns=column_names)