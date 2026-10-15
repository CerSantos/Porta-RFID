import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from flask import Flask, request, jsonify
from datetime import datetime
import threading

IDS_AUTORIZADOS = []
STATUS_USUARIOS = {
    "31AC1CAA": "dentro",
    "00C12C1F": "fora"
}
app = Flask(__name__)

ip_esp = {
    "entrada": "192.168.0.206",
    "saida": "192.168.0.207"
}

cont = 0
log_display = None
usuario_logado = None
root = None
user_entry = None
password_entry = None  
btn_acessar = None

ARQUIVO_CONFIG = "data/config.json"

#--- CLASSES ---
class Usuario:
    def __init__(self, username, password, nivel_acesso):
        self.username = username
        self.password = password
        self.nivel_acesso = nivel_acesso  # 'admin' ou 'visualizador'

    def conferir_credenciais(self, user_digitado, senha_digitada):
        return self.username == user_digitado and self.password == senha_digitada

# Banco de dados em memória
BANCO_DE_USUARIOS = []

# --- LÓGICA DE CONFIGURAÇÃO ---
def salvar_config(ip_entrada, ip_saida, novo_user, novo_password):
    global ip_esp, BANCO_DE_USUARIOS, usuario_logado

    if not ip_entrada or not ip_saida or not novo_user or not novo_password:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos.")
        return
    
    ip_esp = {"entrada": ip_entrada, "saida": ip_saida}
    
    # Atualiza o usuário logado dentro da lista geral
    for u in BANCO_DE_USUARIOS:
        if usuario_logado and u.username == usuario_logado.username:
            u.username = novo_user
            u.password = novo_password
            break
    
    if usuario_logado:
        usuario_logado.username = novo_user
        usuario_logado.password = novo_password

    salvar_no_arquivo()
    messagebox.showinfo("Sucesso", "Dados atualizados!")
    
# --- PERSISTÊNCIA DE DADOS ---
def carregar_config():
    global ip_esp, BANCO_DE_USUARIOS, IDS_AUTORIZADOS, STATUS_USUARIOS
    
    usuario_default = Usuario("admin", "123", "admin")
    
    # Garante que a pasta 'data' exista
    if not os.path.exists("data"):
        os.makedirs("data")

    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)
                ip_esp = dados.get("esp32", ip_esp)
                lista = dados.get("lista_usuarios", [])
                
                BANCO_DE_USUARIOS = []
                for u in lista:
                    if u.get("username") and u.get("password") and u.get("nivel_acesso"):
                        BANCO_DE_USUARIOS.append(
                            Usuario(u["username"], u["password"], u["nivel_acesso"])
                        )
                if not BANCO_DE_USUARIOS:
                    BANCO_DE_USUARIOS = [usuario_default]   

                IDS_AUTORIZADOS = dados.get("IDS_AUTORIZADOS", [])
                STATUS_USUARIOS = dados.get("STATUS_USUARIOS", {})
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            BANCO_DE_USUARIOS = [usuario_default]
    else:
        BANCO_DE_USUARIOS = [usuario_default]
        IDS_AUTORIZADOS = []
        salvar_no_arquivo()

def salvar_no_arquivo():
    global ip_esp, BANCO_DE_USUARIOS, IDS_AUTORIZADOS, STATUS_USUARIOS

    dados = {}
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r") as f:
                dados = json.load(f)
        except:
            dados = {}

    dados["esp32"] = ip_esp
    dados["lista_usuarios"] = [
        {
            "username": u.username,
            "password": u.password,
            "nivel_acesso": u.nivel_acesso
        }
        for u in BANCO_DE_USUARIOS
    ]
    dados["IDS_AUTORIZADOS"] = IDS_AUTORIZADOS
    dados["STATUS_USUARIOS"] = STATUS_USUARIOS

    try:
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump(dados, f, indent=4)
        print("Configuração sincronizada no arquivo JSON.")
    except Exception as e:
        print(f"Erro ao salvar: {e}")

def validar_login(user, password):
    global usuario_logado
    for u in BANCO_DE_USUARIOS:
        if u.conferir_credenciais(user, password):
            usuario_logado = u
            return True
    return False

def verificar_uid(uid):
    uid = uid.strip().upper()
    for item in IDS_AUTORIZADOS:
        if uid == item["uid"].strip().upper():
            return True, item["nome"]
    return False, None

def is_admin():
    return usuario_logado and usuario_logado.nivel_acesso == "admin"

# --- INTERFACES ---
def entrada():
    global cont, user_entry, password_entry, root
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
    global cont, btn_acessar
    cont = 0
    if btn_acessar:
        btn_acessar.config(state="normal")
    messagebox.showinfo("Info", "Acesso liberado para novas tentativas.")

def janela():
    global root, password_entry, btn_acessar, user_entry

    root = tk.Tk()
    root.title("Controle de Acesso RFID - ESP32")
    root.geometry("600x400+500+230") 
    root.resizable(False, False)
    
    main_frame = ttk.Frame(root, padding="10") 
    main_frame.pack(fill="both", expand=True)
    
    label = ttk.Label(main_frame, text="Bem-vindo ao Controle de Acesso RFID", font=("Arial", 16))
    label.pack(pady=20)

    ttk.Label(main_frame, text="Digite o usuário:").pack(pady=5)
    user_entry = ttk.Entry(main_frame, width=30)
    user_entry.pack(pady=5)
    
    ttk.Label(main_frame, text="Senha:").pack(pady=5)
    password_entry = ttk.Entry(main_frame, width=30, show="*")
    password_entry.pack(pady=5)
    password_entry.bind('<Return>', lambda e: entrada()) 
    
    btn_acessar = ttk.Button(main_frame, text="Entrar", command=entrada)
    btn_acessar.pack(pady=20)

    root.mainloop() 

def tela_principal():
    global log_display
    main_window = tk.Tk()
    main_window.title(f"Painel de Controle ESP32 - Operador: {usuario_logado.username}")
    main_window.geometry("800x600+400+130")

    label = ttk.Label(main_window, text="Logs do Sistema RFID", font=("Arial", 14, "bold"))
    label.pack(pady=10)

    acesso_config_btn = ttk.Button(main_window, text="Configurações de Conexão", command=configurações)
    acesso_config_btn.pack(pady=5)

    log_display = scrolledtext.ScrolledText(main_window, width=80, height=20)
    log_display.pack(padx=20, pady=20)
    
    log_display.insert(tk.END, "Servidor Online. Aguardando passagens de cartões...\n")
    
    if is_admin():
        ttk.Button(main_window, text="Gerenciar IDs", command=janela_ids).pack(pady=5)
    
    main_window.mainloop()

def configurações():
    config_window = tk.Toplevel()
    config_window.title("Configurações do Sistema")
    config_window.geometry("400x450+500+230")

    ttk.Label(config_window, text="Configurações", font=("Arial", 14, "bold")).pack(pady=10)

    ttk.Label(config_window, text="IP ESP Entrada:").pack(pady=5)
    ip_entrada_entry = ttk.Entry(config_window, width=30)
    ip_entrada_entry.insert(0, ip_esp["entrada"])
    ip_entrada_entry.pack(pady=5)

    ttk.Label(config_window, text="IP ESP Saída:").pack(pady=5)
    ip_saida_entry = ttk.Entry(config_window, width=30)
    ip_saida_entry.insert(0, ip_esp["saida"])
    ip_saida_entry.pack(pady=5)

    ttk.Label(config_window, text="Alterar Usuário:").pack(pady=5)
    user_cfg_entry = ttk.Entry(config_window, width=30)
    user_cfg_entry.insert(0, usuario_logado.username if usuario_logado else "admin")
    user_cfg_entry.pack(pady=5)

    ttk.Label(config_window, text="Alterar Senha:").pack(pady=5)
    pass_cfg_entry = ttk.Entry(config_window, width=30, show="*")
    pass_cfg_entry.insert(0, usuario_logado.password if usuario_logado else "123")
    pass_cfg_entry.pack(pady=5)

    def salvar_e_fechar():
        salvar_config(
            ip_entrada_entry.get(),
            ip_saida_entry.get(),
            user_cfg_entry.get(),
            pass_cfg_entry.get()
        )   
        config_window.destroy()

    ttk.Button(config_window, text="Salvar", command=salvar_e_fechar).pack(pady=20)
    
def adicionar_id(uid, nome):
    if not is_admin():
        messagebox.showerror("Acesso negado", "Apenas administradores podem adicionar IDs.")
        return
    
    uid = uid.strip().upper()
    if not uid or not nome:
        messagebox.showwarning("Aviso", "Preencha o Nome e o UID.")
        return

    for item in IDS_AUTORIZADOS:
        if item["uid"] == uid:
            messagebox.showwarning("Aviso", "UID já cadastrado.")
            return

    IDS_AUTORIZADOS.append({"uid": uid, "nome": nome})
    salvar_no_arquivo()
    messagebox.showinfo("Sucesso", "ID adicionado com sucesso!") 

def remover_id(uid):
    if not is_admin():
        messagebox.showerror("Acesso negado", "Apenas administradores podem remover IDs.")
        return
    
    global IDS_AUTORIZADOS
    IDS_AUTORIZADOS = [i for i in IDS_AUTORIZADOS if i["uid"] != uid]
    salvar_no_arquivo()
    messagebox.showinfo("Sucesso", "ID removido!") 

def janela_ids():
    if not is_admin():
        messagebox.showerror("Acesso negado", "Apenas administradores.")
        return

    win = tk.Toplevel()
    win.title("Gerenciar IDs")
    win.geometry("400x450")

    listbox = tk.Listbox(win, width=50)
    listbox.pack(pady=10)

    def atualizar_lista():
        listbox.delete(0, tk.END)
        for item in IDS_AUTORIZADOS:
            listbox.insert(tk.END, f'{item["nome"]} - {item["uid"]}')

    atualizar_lista()

    tk.Label(win, text="Nome:").pack()
    nome_entry = tk.Entry(win, width=30)
    nome_entry.pack()

    tk.Label(win, text="UID (Tag RFID):").pack()
    uid_entry = tk.Entry(win, width=30)
    uid_entry.pack()

    def add():
        adicionar_id(uid_entry.get(), nome_entry.get())
        atualizar_lista()
        nome_entry.delete(0, tk.END)
        uid_entry.delete(0, tk.END)

    def remove():
        selecionado = listbox.get(tk.ACTIVE)
        if selecionado and " - " in selecionado:
            uid = selecionado.split(" - ")[1]
            remover_id(uid)
            atualizar_lista()

    tk.Button(win, text="Adicionar ID", command=add).pack(pady=5)
    tk.Button(win, text="Remover Selecionado", command=remove).pack(pady=5)

#---CONFIGURAÇÕES DO SERVIDOR FLASK---
@app.route('/log', methods=['POST'])
def receber_log():
    global log_display, STATUS_USUARIOS
    dados = request.json
    if not dados:
        return jsonify({"status": "error", "message": "Sem dados JSON"}), 400

    uid = dados.get("uid", "").strip().upper()
    porta = dados.get("porta", "").lower()
    horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    autorizado, nome = verificar_uid(uid)
    estado_atual = STATUS_USUARIOS.get(uid, "fora")

    if autorizado:
        if porta == "entrada":
            if estado_atual == "dentro":
                status = "negado"
                msg_tela = f"[{horario}] ACESSO NEGADO (ENTRADA): {nome} ({uid}) já está dentro.\n"
            else:
                STATUS_USUARIOS[uid] = "dentro"
                status = "autorizado"
                msg_tela = f"[{horario}] ACESSO PERMITIDO (ENTRADA): {nome} ({uid}) entrou.\n"
                salvar_no_arquivo()
        elif porta == "saida":
            if estado_atual == "fora":
                status = "negado"
                msg_tela = f"[{horario}] ACESSO NEGADO (SAÍDA): {nome} ({uid}) já está fora.\n"
            else:
                STATUS_USUARIOS[uid] = "fora"
                status = "autorizado"
                msg_tela = f"[{horario}] ACESSO PERMITIDO (SAÍDA): {nome} ({uid}) saiu.\n"
                salvar_no_arquivo()
        else:
            status = "negado"
            msg_tela = f"[{horario}] PORTA INVÁLIDA ({porta.upper()}): {nome} ({uid})\n"
    else:
        status = "negado"
        msg_tela = f"[{horario}] ACESSO NEGADO (NÃO CADASTRADO): {uid}\n"

    # Atualiza a interface de forma segura via thread principal
    if log_display:
        log_display.after(0, lambda m=msg_tela: log_display.insert(tk.END, m))
        log_display.after(0, lambda: log_display.see(tk.END))
    
    print(msg_tela.strip())
    return jsonify({"status": status}), 200

def iniciar_servidor():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    carregar_config()
    # Roda o Flask em Background
    threading.Thread(target=iniciar_servidor, daemon=True).start()
    janela()