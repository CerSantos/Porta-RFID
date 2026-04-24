import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from flask import Flask, request, jsonify
from datetime import datetime
import threading

IDS_AUTORIZADOS = ["31AC1CAA", "00C12C1F"]

app = Flask(__name__)

ip_esp = "192.168.0.206"
usuario = "admin"
senha = "123"
ip = ip_esp
user = usuario
password = senha

cont = 0
log_display = None

ARQUIVO_CONFIG = "config.json"

# --- LÓGICA DE CONFIGURAÇÃO ---
def salvar_config(novo_ip, novo_user, novo_password):
    global ip_esp, usuario, senha, ip, user, password   

    # Validação simples para não salvar campos vazios
    if not novo_ip or not novo_user or not novo_password:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos.")
        return
    
    if novo_password != senha:
        confirmar = messagebox.askyesno("Confirmar Alteração","Você tem certeza que deseja alterar a senha de acesso?")
        if not confirmar:
            return
    
    ip_esp = ip = novo_ip
    usuario = user = novo_user
    senha = password = novo_password
    salvar_no_arquivo(ip, user, password)

    
    messagebox.showinfo("Configurações Salvas", "Os dados foram gravados permanentemente.")

# --- PERSISTÊNCIA DE DADOS ---
def carregar_config():
    global ip_esp, usuario, senha
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r") as f:
            dados = json.load(f)
            ip_esp = dados.get("ip", "192.168.0.206")
            usuario = dados.get("usuario", "admin")
            senha = dados.get("senha", "123")
    else:
        ip_esp, usuario, senha = "192.168.0.206", "admin", "123" # Valores padrão se o arquivo não existir

def salvar_no_arquivo(ip, user, password):
    dados_existentes = {}
     # 1. Tenta ler o que já está no arquivo para não apagar o Wi-Fi
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados_existentes = json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo: {e}")

    dados_existentes.update({
        "ip": ip,
        "usuario": user,
        "senha": password
    })

    # 3. Salva de volta
    try:
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados_existentes, f, indent=4)
        print("Configurações atualizadas sem apagar os dados do ESP32.")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

# --- INTERFACES ---
def entrada():
    global cont
    try:
        digitado = password_entry.get()
        if digitado == senha:
            messagebox.showinfo("Acesso Permitido", "Bem-vindo! Acesso concedido.")
            root.destroy()
            tela_principal() 
            cont = 0
        else:
            cont += 1
            restantes = 3 - cont
            if cont >= 3:
                messagebox.showerror("Bloqueado", "Número máximo de tentativas atingido. Aguarde 30s.")
                btn_acessar.config(state="disabled")
                root.after(30000, liberar_acesso) # Espera 30s sem travar a janela
            else:
                messagebox.showwarning("Negado", f"Senha incorreta. Você tem mais {restantes} tentativas.")
                password_entry.delete(0, tk.END)
                
    except Exception as e:
        print(f"Erro ao verificar credenciais, {e}")
            
def liberar_acesso():
    global cont
    cont = 0
    btn_acessar.config(state="normal")
    messagebox.showinfo("Info", "Acesso liberado para novas tentativas.")

def janela():
    global root, password_entry, btn_acessar

    root = tk.Tk()
    root.title("Controle de Acesso RFID - ESP32")
    root.geometry("600x400+500+230") #Configurações da janela
    root.resizable(False, False)
    main_frame = ttk.Frame(root, padding="10") # Frame principal
    main_frame.pack(fill="both", expand=True)
    
    label = ttk.Label(main_frame, text="Bem-vindo ao Controle de Acesso RFID", font=("Arial", 16))
    label.pack(pady=20)

    ttk.Label(main_frame, text="Digite a senha para acessar os logs:").pack(pady=10)
    ttk.Label(main_frame, text="Senha:").pack(pady=5)
    password_entry = ttk.Entry(main_frame, width=30, show="*")
    password_entry.pack(pady=5)
    password_entry.bind('<Return>', lambda e: entrada()) # Permite dar Enter
    
    btn_acessar = ttk.Button(main_frame, text="Entrar", command=entrada)
    btn_acessar.pack(pady=20)

    root.mainloop() 

def tela_principal():
    global log_display
    main_window = tk.Tk()
    main_window.title("Painel de Controle ESP32")
    main_window.geometry("800x600+400+130")

    label = ttk.Label(main_window, text="Logs do Sistema RFID", font=("Arial", 14, "bold"))
    label.pack(pady=10)

    acesso_config_btn = ttk.Button(main_window, text="Configurações de Conexão", command=configurações)
    acesso_config_btn.pack(pady=5)

    log_display = scrolledtext.ScrolledText(main_window, width=80, height=20)
    log_display.pack(padx=20, pady=20)
    
    log_display.insert(tk.END, "Conectado ao ESP32...\nAguardando dados...\n")
    
    main_window.mainloop()

def configurações():
    config_window = tk.Toplevel()
    config_window.title("Configuraçõe")
    config_window.geometry("400x300+500+230")

    ttk.Label(config_window, text="Configurações", font=("Arial", 14, "bold")).pack(pady=10)

    ttk.Label(config_window, text="IP da ESP32:").pack(pady=5)
    ip_entry = ttk.Entry(config_window, width=30)
    ip_entry.insert(0, ip_esp)
    ip_entry.pack(pady=5)

    ttk.Label(config_window, text="Usuário:").pack(pady=5)
    user_entry = ttk.Entry(config_window, width=30)
    user_entry.insert(0, usuario)
    user_entry.pack(pady=5)

    ttk.Label(config_window, text="Senha:").pack(pady=5)
    pass_entry = ttk.Entry(config_window, width=30, show="*")
    pass_entry.insert(0, senha)
    pass_entry.pack(pady=5)

    ttk.Button(config_window, text="Salvar", command=lambda: salvar_config(ip_entry.get(), user_entry.get(), pass_entry.get())).pack(pady=20)
    
#---CONFIGURAÇÕES DO SERVIDOR FLASK---
@app.route('/log', methods=['POST'])
def receber_log():
    global log_display
    dados = request.json
    uid = dados.get("uid")
    horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
   # Verifica se a UID recebida está na nossa lista
    if uid in IDS_AUTORIZADOS:
        status = "autorizado"
        msg_tela = f"[{horario}] ACESSO LIBERADO: {uid}\n"
    else:
        status = "negado"
        msg_tela = f"[{horario}] ACESSO NEGADO: {uid}\n"

    # Atualiza a interface
    if log_display:
        log_display.after(0, lambda: log_display.insert(tk.END, msg_tela))
        log_display.after(0, lambda: log_display.see(tk.END))
        print(f"Log recebido e enviado para tela: {uid}") # Aparece no console do VSCode/PyCharm
    else:
        print(f"Erro: log_display ainda não foi iniciado. UID: {uid}")


    print(msg_tela.strip())
    return jsonify({"status": status}), 200

def iniciar_servidor():
    app.run(host='0.0.0.0', port=5000,debug=False, use_reloader=False)

if __name__ == "__main__":
    carregar_config()
    threading.Thread(target=iniciar_servidor, daemon=True).start()
    janela()