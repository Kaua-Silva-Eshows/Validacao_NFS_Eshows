from utils.functions import *  
from data.querys import nfs_query
import tkinter as tk
from tkinter import scrolledtext

def display_results(results):
    #Cria uma janela de visualização simples
    window = tk.Tk()
    window.title("Resultados da Validação")
    window.geometry("600x500")  #Ajuste do tamanho da janela
    
    #Quantidade de Frames para a area rolavel
    text_frame = tk.Frame(window)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))  # Controls top and bottom margin of text area

    #Cria a area de texto rolavel
    results_text = scrolledtext.ScrolledText(text_frame, width=80, height=20, font=("Arial", 12))
    results_text.pack(fill=tk.BOTH, expand=True)

    #Insere os resultados na area de texto
    for result in results:
        results_text.insert(tk.END, result + "\n")

    #Desabilita edição, então a area de texto se torna apenas para leitura
    results_text.config(state=tk.DISABLED)

    #Função para atualizar os resultados, basicamente roda o codigo de novo, para não ter que fechar e rodar
    def update_results():
        window.destroy()
        
        delete_pdf_files()
        updated_results = process_invoices()  # Reprocess the invoices
        display_results(updated_results)
        

    #Cria um botão de "Atualizar"
    button_frame = tk.Frame(window)
    button_frame.pack(pady=(5, 10))  #Distancia do botão para a margem de cima

    #Botão de atualizar
    update_button = tk.Button(button_frame, text="Update", command=update_results)
    update_button.pack()

    window.mainloop()

def process_invoices():
    invoice_data = nfs_query()  #Pega os resultados do banco
    
    if invoice_data.empty:
        print("Nenhuma Fatura Encontrada.")
        return []

    results = []  # List to store results

    for invoice in invoice_data.itertuples(index=False):
        nf_id = invoice.NF_ID
        house_cnpj = invoice.CNPJ_Casa
        invoice_number = invoice.Num_NF
        proposal_value = invoice.Valor_Proposta
        pdf_link = invoice.Link
        #Antes de subir o valor pro banco é necessario dividir por 100, pois ao subir para o banco ele mutiplica por 100.
        #Provavelmente alguma configuração do Banco
        bank_value = proposal_value / 100 

        # Validate the PDF data
        if validate_data(pdf_link, house_cnpj, invoice_number, proposal_value) == True:
            insert_epm("VF9JTkZPU19OT1RBU19GSVNDQUlTOjE2NTUwNg==", 258,  
       {
            "FK_NOTA_FISCAL": nf_id,
            "NUMERO_ROBO": invoice_number,
            "CNPJ_TOMADOR": house_cnpj,
            "VALOR_SERVICO": bank_value,
        })
            results.append(f"{nf_id}: Certo")
        else:
            insert_epm("VF9JTkZPU19OT1RBU19GSVNDQUlTOjE2NTUwNg==", 258,  
       {
            "FK_NOTA_FISCAL": nf_id,
            "NUMERO_ROBO": invoice_number,
            "CNPJ_TOMADOR": house_cnpj,
            "VALOR_SERVICO": bank_value,
        })
            results.append(f"{nf_id}: Conferir")

    return results

initial_results = process_invoices()  #Coleta os dados iniciais
display_results(initial_results) #Exibe os resultados na interface
delete_pdf_files() #Limpa os arquivos PDF