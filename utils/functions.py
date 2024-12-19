import re
import os
import requests
import openai
import fitz  # PyMuPDF
from PIL import Image
import easyocr
import io

import config

#Função para baixar os arquivos PDF da query
def download_pdf(link_pdf, nf_id):
    pdf_folder = './assets/pdf'
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
    #Caminho para salvar o PDF
    pdf_path = os.path.join(pdf_folder, f'invoice_{nf_id}.pdf')
    #Baixa o PDF
    response = requests.get(link_pdf)
    if response.status_code == 200:
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        return pdf_path
    else:
        print(f"Erro ao baixar o PDF: {response.status_code}")
        return None

#Função para excluir os arquivos PDF no final do processo
def delete_pdf_files():
    pdf_folder = './assets/pdf'
    #Verifica se a pasta existe e exclui todos os arquivos
    if os.path.exists(pdf_folder): 
        for file in os.listdir(pdf_folder):
            file_path = os.path.join(pdf_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

#funcao para extrair o texto do PDF e caso o PDF seja em outro formato, como imagem, usa o OCR para extrair o texto
def extract_text_from_pdf(file_path):
    try:
        # Primeira tentativa: tentar extrair texto diretamente do PDF
        with fitz.open(file_path) as pdf:
            text = ""
            page = pdf[0]
            extracted_text = page.get_text("text")
            if extracted_text.strip():  # Se o texto extraído não estiver vazio
                text += extracted_text
                if text.strip() and len(text.strip()) >= 250:
                    print("Texto extraído com sucesso:")
                    print(text)  # Para debug
                    return text.strip()
        
    except Exception as e:
        print(f"Erro ao extrair texto do PDF com fitz: {e}")

    # Se a extração com fitz falhar ou não encontrar texto, tenta usar OCR
    print("Tentando extrair texto via OCR")

    try:
        with fitz.open(file_path) as pdf:
            reader = easyocr.Reader(['pt', 'en'])  # Idiomas suportados
            text = ""
            for page_number in range(len(pdf)):
                page = pdf[page_number]
                # Renderiza como uma imagem
                pix = page.get_pixmap(dpi=300)  # Aumenta a resolução para melhorar o OCR
                image_data = pix.tobytes(output="png")

                # Pré-processamento da imagem (escala de cinza e limiarização)
                image = Image.open(io.BytesIO(image_data))
                image = image.convert('L')  # Converte para escala de cinza
                threshold = 150
                image = image.point(lambda p: p > threshold and 255)

                # Converte a imagem para um buffer de bytes
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                buf.seek(0)

                # Aplica OCR na imagem processada
                result = reader.readtext(buf.read(), detail=0)
                text += "\n".join(result) + "\n"

            if text.strip():
                print("Texto extraído via OCR:")
                print(text)  # Para debug
                return text.strip()
            else:
                print("Nenhum texto foi extraído via OCR.")
                return "Nenhum texto pode ser extraído."
        
    except Exception as e:
        print(f"Erro ao extrair texto via OCR: {e}")
        return "Nenhum texto pode ser extraído."

#Função para extrair os dados da nota fiscal por meio do OpenAI
def extract_data_with_openai(pdf_text):
    #Chave da API, na config.py
    openai.api_key = config.OPENAI_API_KEY

    #Prompt pro GPT
    prompt = f"""
        Você faz parte da equipe financeira de uma empresa. Sua tarefa é extrair dados específicos de notas fiscais fornecidas como texto, convertidas a partir de PDFs. As informações necessárias e o formato de saída são os seguintes:

Informações a Extrair:
CNPJ do Tomador de Serviço: Nas notas, voce pode encontrar mais de um cnpj, então extraia o do "Tomador de Serviço" como um número de CNPJ válido (exemplo: 00.000.000/0001-00).
Número da Nota Fiscal: Extraia o número da nota fiscal, algumas notas, além do numero possuem um codigo com letras, porém, quero somente o numero da nota.
Valor da Nota Fiscal: Extraia como um número decimal (exemplo: 1500.00), Em algumas notas pode vir como valor do serviço ou valor total do serviço.
Formato de Saída:
Retorne as informações extraídas no seguinte formato JSON:

{{
  "cnpj": "CNPJ extraído do tomador de serviço ou prestador do serviço",
  "num_nf": "Número da Nota Fiscal extraído",
  "valor": "Valor da Nota Fiscal extraído"
}}
Instruções:
Certifique-se de que as informações sejam corretamente extraídas e formatadas.
Se algum dos dados obrigatórios estiver ausente, utilize 0 como valor.
Valide que os dados estejam de acordo com os formatos especificados:
CNPJ: Certifique-se de que esteja em um formato válido de CNPJ.
Valor da Nota Fiscal: Certifique-se de que esteja no formato decimal.
Extraia todas as ocorrências dos dados caso sejam repetidos no texto.
Notas Adicionais:
A precisão e a completude na extração dos dados são críticas.

Texto:
{pdf_text}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant specialized in data extraction."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,  #Mais baixo para respostas mais focadas
            max_tokens=100    #Maximo de tokens que ele pode devolver
        )

        #Analisa a resposta
        response_content = response['choices'][0]['message']['content']
        print(response_content) #Serve para ver a resposta do GPT, também pra debugar
        
        #Inicializa o dicionario de dados
        data = {
            "cnpj": None,
            "num_nf": None,
            "valor": None
        }

        #Processa a resposta e extrai os valores
        lines = response_content.split('\n')
        for line in lines:
            if "cnpj" in line:
                data["cnpj"] = line.split(":")[1].strip()  #Remove espaços antes e depois
            elif "num_nf" in line:
                data["num_nf"] = line.split(":")[1].strip()
                data["num_nf"] = data["num_nf"].replace('"', '').replace(' ', '').replace(',', '').lstrip('0')  #Remove espaços, aspas, virgulas e zeros iniciais
            elif "valor" in line:
                value_str = line.split(":")[1].strip()
                value_str = value_str.replace('"', '').replace(' ', '').replace(',', '.')
                try:
                    #Garante que o valor tenha duas casas decimais (EX: 1500.00)
                    value_float = float(value_str)
                    data["valor"] = "{:.2f}".format(value_float)  #Formatar para duas casas decimais
                    #Armazena também como float para necessidades futuras
                    data["valor_float"] = value_float
                except ValueError:
                    data["valor"] = None  #Se o valor não estiver formatado corretamente
                    print("Exceção inserida")

        return data
    
    except Exception as e:
        print("Erro com a comunicação da API:", str(e))
        return {
            "cnpj": "0",
            "num_nf": "0",
            "valor": "0"
        }

#função para formatar o CNPJ
def format_cnpj(cnpj):
    #Para evitar problemas de comparação é necessario esse processo, pois no banco o cnpj pode vir formatado ou nao
    cnpj = re.sub(r'\D', '', cnpj)  #\D Remove tudo q não é numero
    #Verifica se tem 14 digitos 
    if len(cnpj) == 14:
        #Retorna o CNPJ no formato XX.XXX.XXX/XXXX-XX
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj  #Se não tiver 14 digitos, retorna o cnpj original

def compare_extracted_data(pdf_text, house_cnpj, invoice_number, proposal_value):

    # Extrai, formata e compara os dados extraídos do texto do PDF com os dados fornecidos.

    # Extrai os dados do PDF
    extracted_data = extract_data_with_openai(pdf_text)
    extracted_invoice_number = extracted_data.get("num_nf") or "0"
    extracted_cnpj = extracted_data.get("cnpj") or "0"  # Valor padrão caso não exista
    print(extracted_cnpj, extracted_data.get("cnpj") or "0")
    extracted_proposal_value = extracted_data.get("valor") or 0 

    # Formata os CNPJs para comparação
    formatted_house_cnpj = format_cnpj(house_cnpj)
    formatted_extracted_cnpj = format_cnpj(extracted_cnpj)

    # Logs para debug
    print(f"Query CNPJ: {formatted_house_cnpj} | ChatGPT CNPJ: {formatted_extracted_cnpj}")
    print(f"Query Invoice Number: {invoice_number} | ChatGPT Invoice Number: {extracted_invoice_number}")
    print(f"Query Proposal Value: {proposal_value} | ChatGPT Proposal Value: {extracted_proposal_value}")

    # Compara os dados
    if (formatted_extracted_cnpj.strip() == formatted_house_cnpj.strip() and
        extracted_invoice_number.strip() == invoice_number.strip() and
        float(extracted_proposal_value) == float(proposal_value)):
        return True, {
            "cnpj": formatted_extracted_cnpj,
            "num_nf": extracted_invoice_number,
            "valor": extracted_proposal_value,
        }

    # Retorna False e os dados extraídos em caso de divergência
    return False, {
            "cnpj": formatted_extracted_cnpj,
            "num_nf": extracted_invoice_number,
            "valor": extracted_proposal_value,
        }

#Função para validar os dados
def validate_data(link_pdf, house_cnpj, invoice_number, proposal_value):
    #Valida os dados extraídos de um PDF contra os dados fornecidos.
    #Tenta validar duas vezes antes de falhar.
    pdf_path = download_pdf(link_pdf, invoice_number)
    if not pdf_path:
        print("Erro: Caminho do PDF inválido ou não acessível.")
        return False, {"cnpj": "N/A", "num_nf": "N/A", "valor": "N/A"}

    pdf_text = extract_text_from_pdf(pdf_path)

    # Primeira tentativa de validação
    print("Validação em andamento...")
    is_valid, data = compare_extracted_data(pdf_text, house_cnpj, invoice_number, proposal_value)
    #print(f"Revalidação - CNPJ: {data['cnpj']}, NF: {data['num_nf']}, Valor: {data['valor']}")
    if is_valid:
        return True, data

    # Segunda tentativa de validação
    print("Revalidação em andamento...")
    is_valid, data = compare_extracted_data(pdf_text, house_cnpj, invoice_number, proposal_value)
    #print(f"Revalidação - CNPJ: {data['cnpj']}, NF: {data['num_nf']}, Valor: {data['valor']}")
    if is_valid:
        return True, data
    
    # Terceira tentativa de validação
    print("Segunda Revalidação em andamento...")
    is_valid, data = compare_extracted_data(pdf_text, house_cnpj, invoice_number, proposal_value)
    #print(f"Revalidação - CNPJ: {data['cnpj']}, NF: {data['num_nf']}, Valor: {data['valor']}")
    if is_valid:
        return True, data

    # Falha após duas tentativas
    print("Validação falhou após duas tentativas.")
    #print(f"Revalidação - CNPJ: {data['cnpj']}, NF: {data['num_nf']}, Valor: {data['valor']}")
    return False, data

#Função para inserir os resultados no banco por meio do EPM
processed_ids = set()

def insert_epm(tid, fid, nf_id, data):
    # Verifique se o tid está presente e é válido
    if not tid or tid == "tid invalido":
        print("Erro: tid inválido.")
        return

    # Verificar se já foi processado
    if nf_id in processed_ids:
        print("Este registro já foi processado. Ignorando...")
        return  # Ignorar se já foi processado

    # Adicionar a combinação (tid, fid) ao conjunto
    processed_ids.add(nf_id)

    # Seu login do EPM
    login_data = {
        "username": config.LOGIN_USERNAME, # Email, da config.py
        "password": config.LOGIN_PASSWORD, # Senha
        "loginSource": 1,
    }

    try:
        # Realizando o login para obter o ticket
        login_response = requests.post(
            'https://apps.eshows.com.br/eshows/Security/Login',
            json=login_data
        ).json()

        # Verificando se o login foi bem-sucedido
        if 'data' not in login_response:
            print(f"Erro no login: {login_response.get('error', 'Desconhecido')}")
            return

        ticket = login_response['data']['auth_ticket']

        headersEPM = {'Content-Type': 'application/json', 'auth': ticket}

        data3 = {
            "tid": tid,
            "fid": fid,
            "data": data,
            "type": 1,
        }

        # Realizando a requisição para salvar os dados
        create_response = requests.post(
            "https://apps.eshows.com.br/eshows/Integration/Save",
            headers=headersEPM,
            json=data3
        ).json()

        if "error" in create_response:
            print(f"Erro ao adicionar dados: {create_response['error']}")
        else:
            print('Adição realizada com sucesso')

    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição HTTP: {e}")
    except Exception as e:
        print(f"Erro desconhecido: {str(e)}")