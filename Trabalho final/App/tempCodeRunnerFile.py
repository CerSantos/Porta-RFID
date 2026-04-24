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
usuario_logado = None
root = None
user_entry = None
password_entry = None  
btn_acessar = None

ARQUIVO_CONFIG = "config.json"

#--- CLASSES ---
class Usuario:
    def __init__(self, username, password, nivel_acesso):
        self.username = username
        self.password = password
        self.nivel_acesso = nivel_acesso  # 'admin' ou 'visualizador'

    def conferir_credenciais(self, user_digitado, senha_digitada):
        #Retorna True se os dados coincidirem com este usuário específico.
        return self.username == user_digitado and self.password == senha_digitada

# Simulando um banco de dados de usuários
BANCO_DE_USUARIOS = []

# --- LÓGICA DE CONFIGURAÇÃO ---
def salvar_config(novo_ip, novo_user, novo_password):
    global ip_esp,BANCO_DE_USUARIOS  

    ip_esp = ip = novo_ip
    # Validação simples para não salvar campos vazios
    if not novo_ip or not novo_user or not novo_password:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos.")
        return
    
    for u in BANCO_DE_USUARIOS:
       if u.username == usuario_logado.username:  # Só atualiza o usuário logado
            u.username ==  novo_user
            u.password == novo_password
            break
    
    # Atualiza a sessão atual
    usuario_logado.username = novo_user
    usuario_logado.password = novo_password

    # Salva todos da lista de volta no arquivo
    salvar_no_arquivo(ip_esp, novo_user, novo_password)
    
    messagebox.showinfo("Sucesso", "Dados atualizados!")
    
# --- PERSISTÊNCIA DE DADOS ---
def carregar_config():
    global ip_esp, BANCO_DE_USUARIOS
    usuario_default = Usuario("admin", "123", "admin")
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)
                ip_esp = dados.get("ip", "192.168.0.206")
                lista = dados.get("lista_usuarios", [])
                if not lista:
                    BANCO_DE_USUARIOS = [usuario_default]
                else:
                    BANCO_DE_USUARIOS = [Usuario(u.get("u"), u.get("s"), u.get("n")) for u in lista]
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            BANCO_DE_USUARIOS = [usuario_default]
    else:
        BANCO_DE_USUARIOS = [usuario_default]

def salvar_no_arquivo(ip, user, password):
    global ip_esp, usuario_logado, BANCO_DE_USUARIOS

    # Prepara a lista de usuários para formato JSON
    lista_usuarios_json = []
    for u in BANCO_DE_USUARIOS:
        lista_usuarios_json.append({
            "u": u.username, 
            "s": u.password, 
            "n": u.nivel_acesso
        })

    ip_esp = ip
    usuario_logado.username = user
    usuario_logado.password = password

    dados_para_salvar = [{"u": u.username, "s": u.password, "n": u.nivel_acesso} for u in BANCO_DE_USUARIOS]
    try:
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump({"ip": ip_esp, "lista_usuarios": lista_usuarios_json}, f, indent=4)
        print("Arquivo de configuração atualizado.")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

def validar_login(user, password):
    global usuario_logado
    for u in BANCO_DE_USUARIOS:
        print(f"Tentando: {user} | No banco: {u.username} ({u.nivel_acesso})")
        if u.conferir_credenciais(user, password):
            usuario_logado = u
            return True
    return False

# --- INTERFACES ---
def entrada():
    global cont, user_entry, password_entry
    try:
        u_digitado = user_entry.get()
        s_digitada = password_entry.get()

        if validar_login(u_digitado, s_digitada):
            messagebox.showinfo("Acesso Permitido", f"Bem-vindo, {usuario_logado.username}!")
            root.destroy()
            tela_principal()
            cont = 0
        else:
            cont += 1
            if cont >= 3:
                btn_acessar.config(state="disabled")
                messagebox.showerror("Bloqueado", "Muitas tentativas. Aguarde 30s.")
                root.after(30000, liberar_acesso)
            else:
                messagebox.showwarning("Erro", f"Credenciais inválidas ({3 - cont} restantes).")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro no login: {e}")

def liberar_acesso():
    global cont
    cont = 0
    btn_acessar.config(state="normal")
    messagebox.showinfo("Info", "Acesso liberado para novas tentativas.")

def janela():
    global root, password_entry, btn_acessar, user_entry, user

    root = tk.Tk()
    root.title("Controle de Acesso RFID - ESP32")
    root.geometry("600x400+500+230") #Configurações da janela
    root.resizable(False, False)
    main_frame = ttk.Frame(root, padding="10") # Frame principal
    main_frame.pack(fill="both", expand=True)
    
    label = ttk.Label(main_frame, text="Bem-vindo ao Controle de Acesso RFID", font=("Arial", 16))
    label.pack(pady=20)

    ttk.Label(main_frame, text="Digite o usuário:").pack(pady=5)
    user_entry = ttk.Entry(main_frame, width=30)
    user_entry.pack(pady=5)
    
    ttk.Label(main_frame, text="Digite a senha para acessar os logs:").pack(pady=10)
    ttk.Label(main_frame, text="Senha:").pack(pady=5)
    password_entry = ttk.Entry(main_frame, width=30, show="*")
    password_entry.pack(pady=5)
    password_entry.bind('<Return>', lambda e: entrada()) # Permite dar Enter
    
    btn_acessar = ttk.Button(main_frame, text="Entrar", command=entrada)
    btn_acessar.pack(pady=20)

    root.mainloop() 

def tela_principal():
    global log_display, main_window
    main_window = tk.Tk()
    main_window.title(f"Painel de Controle ESP32, Logado como: {usuario_logado.username}")
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
    config_window.title("Configurações")
    config_window.geometry("400x300+500+230")

    ttk.Label(config_window, text="Configurações", font=("Arial", 14, "bold")).pack(pady=10)

    ttk.Label(config_window, text="IP da ESP32:").pack(pady=5)
    ip_entry = ttk.Entry(config_window, width=30)
    ip_entry.insert(0, ip_esp)
    ip_entry.pack(pady=5)

    ttk.Label(config_window, text="Usuário:").pack(pady=5)
    user_entry = ttk.Entry(config_window, width=30)
    user_entry.insert(0, usuario_logado.username)
    user_entry.pack(pady=5)

    ttk.Label(config_window, text="Senha:").pack(pady=5)
    pass_entry = ttk.Entry(config_window, width=30, show="*")
    pass_entry.insert(0, usuario_logado.password)
    pass_entry.pack(pady=5)

    ttk.Button(config_window, text="Salvar", command=lambda: salvar_config(ip_entry.get(), user_entry.get(), pass_entry.get(), main_window)).pack(pady=20)
    
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