import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from flask import Flask, request, jsonify
from datetime import datetime
import threading

# --- CONFIGURAÇÕES ---
IDS_AUTORIZADOS = ["31AC1CAA", "00C12C1F"]
app = Flask(__name__)
ARQUIVO_CONFIG = "config.json"

# Variáveis globais
ip_esp = "192.168.0.206"
BANCO_DE_USUARIOS = []
usuario_logado = None
log_display = None
cont = 0

class Usuario:
    def __init__(self, username, password, nivel_acesso):
        self.username = username
        self.password = password
        self.nivel_acesso = nivel_acesso

    def conferir_credenciais(self, user_digitado, senha_digitada):
        return self.username == user_digitado and self.password == senha_digitada

# --- PERSISTÊNCIA ---
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
            BANCO_DE_USUARIOS = [usuario_default]
    else:
        BANCO_DE_USUARIOS = [usuario_default]

def salvar_config(novo_ip, novo_user, novo_password, config_window):
    global ip_esp, usuario_logado
    if not novo_ip or not novo_user or not novo_password:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos.")
        return

    # Atualiza na lista global
    for u in BANCO_DE_USUARIOS:
        if u.username == usuario_logado.username:
            u.username = novo_user
            u.password = novo_password
            break
    
    ip_esp = novo_ip
    usuario_logado.username = novo_user
    usuario_logado.password = novo_password

    # Salva no arquivo
    lista_json = [{"u": u.username, "s": u.password, "n": u.nivel_acesso} for u in BANCO_DE_USUARIOS]
    try:
        with open(ARQUIVO_CONFIG, "w") as f:
            json.dump({"ip": ip_esp, "lista_usuarios": lista_json}, f, indent=4)
        messagebox.showinfo("Sucesso", "Configurações atualizadas!")
        config_window.destroy() # Fecha a janela de config após salvar
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar: {e}")

# --- INTERFACES ---
def entrada(user_entry, password_entry, root, btn_acessar):
    global cont, usuario_logado
    u_dig = user_entry.get()
    s_dig = password_entry.get()

    for u in BANCO_DE_USUARIOS:
        if u.conferir_credenciais(u_dig, s_dig):
            usuario_logado = u
            messagebox.showinfo("Sucesso", f"Bem-vindo, {u.username}!")
            root.destroy()
            tela_principal()
            return

    cont += 1
    if cont >= 3:
        btn_acessar.config(state="disabled")
        messagebox.showerror("Bloqueado", "Muitas tentativas. Aguarde 30s.")
        root.after(30000, lambda: btn_acessar.config(state="normal"))
        cont = 0
    else:
        messagebox.showwarning("Erro", f"Credenciais inválidas. Tentativa {cont}/3")

def janela():
    root = tk.Tk()
    root.title("RFID Access Control")
    root.geometry("400x350")
    
    ttk.Label(root, text="Login do Sistema", font=("Arial", 14, "bold")).pack(pady=20)
    
    user_entry = ttk.Entry(root, width=30)
    user_entry.insert(0, "Usuário")
    user_entry.pack(pady=5)
    
    pass_entry = ttk.Entry(root, width=30, show="*")
    pass_entry.pack(pady=5)
    
    btn = ttk.Button(root, text="Acessar")
    btn.config(command=lambda: entrada(user_entry, pass_entry, root, btn))
    btn.pack(pady=20)
    
    root.mainloop()

def tela_principal():
    global log_display
    main_window = tk.Tk()
    main_window.title(f"Painel RFID - {usuario_logado.username}")
    main_window.geometry("700x500")

    ttk.Button(main_window, text="Configurações", command=configurações).pack(pady=10)
    
    log_display = scrolledtext.ScrolledText(main_window, width=80, height=20)
    log_display.pack(padx=20, pady=10)
    log_display.insert(tk.END, "Aguardando logs do ESP32...\n")
    
    main_window.mainloop()

def configurações():
    config_window = tk.Toplevel()
    config_window.title("Ajustes de Conexão")
    
    ttk.Label(config_window, text="IP do ESP32:").pack(pady=5)
    ip_ent = ttk.Entry(config_window)
    ip_ent.insert(0, ip_esp)
    ip_ent.pack()

    ttk.Label(config_window, text="Alterar Usuário:").pack(pady=5)
    u_ent = ttk.Entry(config_window)
    u_ent.insert(0, usuario_logado.username)
    u_ent.pack()

    ttk.Label(config_window, text="Alterar Senha:").pack(pady=5)
    p_ent = ttk.Entry(config_window, show="*")
    p_ent.insert(0, usuario_logado.password)
    p_ent.pack()

    ttk.Button(config_window, text="Salvar", 
               command=lambda: salvar_config(ip_ent.get(), u_ent.get(), p_ent.get(), config_window)).pack(pady=20)

# --- FLASK ---
@app.route('/log', methods=['POST'])
def receber_log():
    dados = request.json
    uid = dados.get("uid", "N/A")
    horario = datetime.now().strftime("%H:%M:%S")
    
    status = "LIBERADO" if uid in IDS_AUTORIZADOS else "NEGADO"
    msg = f"[{horario}] {status}: {uid}\n"

    if log_display:
        log_display.after(0, lambda: log_display.insert(tk.END, msg))
        log_display.after(0, lambda: log_display.see(tk.END))
    
    return jsonify({"status": status.lower()}), 200

if __name__ == "__main__":
    carregar_config()
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    janela()
