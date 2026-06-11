import pyautogui
import time
import pygetwindow as gw
import threading
import keyboard
import tkinter as tk
from tkinter import ttk, font as tkfont
from datetime import datetime

# ──────────────────────────────────────────────
#  CONFIGURAÇÕES DOS SLOTS (inalteradas)
# ──────────────────────────────────────────────
x_inicial = 1248
y_inicial = 495
espaco_x  = 33
espaco_y  = 31
posicoes  = [(x_inicial + c * espaco_x, y_inicial + l * espaco_y)
             for l in range(8) for c in range(8)]

delay_click   = 0.001
delay_posicao = 0.001
rodando       = False
tempo_ciclo   = 3600

# ──────────────────────────────────────────────
#  PALETA DE CORES
# ──────────────────────────────────────────────
BG        = "#0d0d14"
BG_PANEL  = "#12121e"
BG_INPUT  = "#1a1a2e"
PURPLE    = "#9b59f7"
PURPLE_DK = "#6c3abf"
PURPLE_LT = "#c084fc"
ACCENT    = "#e040fb"
TEXT      = "#e2e0f0"
TEXT_DIM  = "#6b6880"
GREEN     = "#39ff87"
RED       = "#ff4f6b"
YELLOW    = "#f7c948"
BORDER    = "#2a2640"

# ──────────────────────────────────────────────
#  ROOT
# ──────────────────────────────────────────────
root = tk.Tk()
root.title("MU COSMIC BOT")
root.geometry("480x680")
root.resizable(False, False)
root.configure(bg=BG)

MONO    = tkfont.Font(family="Consolas", size=10)
MONO_B  = tkfont.Font(family="Consolas", size=10, weight="bold")
TITLE_F = tkfont.Font(family="Consolas", size=14, weight="bold")
SMALL_F = tkfont.Font(family="Consolas", size=9)
BIG_F   = tkfont.Font(family="Consolas", size=20, weight="bold")

# ──────────────────────────────────────────────
#  HEADER
# ──────────────────────────────────────────────
header = tk.Frame(root, bg=BG_PANEL, height=56)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(header, text="◈ MU COSMIC BOT", font=TITLE_F,
         fg=PURPLE_LT, bg=BG_PANEL, padx=16).pack(side="left", pady=12)
tk.Label(header, text="by Diego Spinella", font=SMALL_F,
         fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")

status_dot = tk.Label(header, text="● PARADO", font=MONO_B,
                      fg=RED, bg=BG_PANEL, padx=16)
status_dot.pack(side="right", pady=12)

tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

# ──────────────────────────────────────────────
#  PAINEL DE CONTROLE
# ──────────────────────────────────────────────
ctrl = tk.Frame(root, bg=BG_PANEL, padx=18, pady=14)
ctrl.pack(fill="x")

def sec(txt):
    tk.Label(ctrl, text=txt, font=MONO_B, fg=PURPLE,
             bg=BG_PANEL, anchor="w").pack(fill="x", pady=(10, 3))

# — Janelas —
sec("JANELAS DETECTADAS")
win_label = tk.Label(ctrl, text="—", font=MONO, fg=TEXT_DIM,
                     bg=BG_PANEL, anchor="w", justify="left")
win_label.pack(fill="x")

def atualizar_janelas_label():
    janelas = [w for w in gw.getAllWindows() if "Mu Cosmic" in w.title]
    if janelas:
        win_label.config(text=f"{len(janelas)} janela(s) detectada(s)", fg=GREEN)
    else:
        win_label.config(text="Nenhuma janela encontrada", fg=TEXT_DIM)

# — Ciclo (dropdown) —
sec("TEMPO DE CICLO")

OPCOES_CICLO = {
    "10 segundos (teste)": 10,
    "1 minuto":            60,
    "10 minutos":          600,
    "20 minutos":          1200,
    "30 minutos":          1800,
    "40 minutos":          2400,
    "50 minutos":          3000,
    "1 hora":              3600,
    "1h 30min":            5400,
    "2 horas":             7200,
}

# Ordena as opções pelo valor (segundos)
opcoes_ordenadas = dict(sorted(OPCOES_CICLO.items(), key=lambda x: x[1]))

# Valor inicial agora é o menor tempo (10 segundos)
primeira_opcao = next(iter(opcoes_ordenadas.keys()))
ciclo_var = tk.StringVar(value=primeira_opcao)

# Estilo do OptionMenu
style = ttk.Style()
style.theme_use("clam")
style.configure("Dark.TMenubutton",
    background=BG_INPUT, foreground=TEXT,
    font=("Consolas", 10),
    relief="flat",
    borderwidth=1,
    arrowcolor=PURPLE_LT,
)
style.map("Dark.TMenubutton",
    background=[("active", PURPLE_DK)],
    foreground=[("active", TEXT)],
)

dropdown_row = tk.Frame(ctrl, bg=BG_PANEL)
dropdown_row.pack(fill="x", pady=(0, 2))

dropdown = ttk.OptionMenu(dropdown_row, ciclo_var, primeira_opcao, *opcoes_ordenadas.keys())
dropdown.configure(style="Dark.TMenubutton", width=22)
dropdown["menu"].configure(bg=BG_INPUT, fg=TEXT, activebackground=PURPLE_DK,
                            activeforeground=TEXT, font=("Consolas", 10),
                            relief="flat", bd=0)
dropdown.pack(side="left")

def aplicar_ciclo():
    global tempo_ciclo
    tempo_ciclo = opcoes_ordenadas[ciclo_var.get()]

    if tempo_ciclo < 60:
        # Menos de 1 minuto → mostra em segundos
        label = f"{tempo_ciclo}s (TESTE)"
    elif tempo_ciclo < 3600:
        # Menos de 1 hora → mostra em minutos
        label = f"{tempo_ciclo//60:02d} min"
    else:
        # 1 hora ou mais → mostra em horas e minutos com zeros à esquerda
        horas = tempo_ciclo // 3600
        minutos = (tempo_ciclo % 3600) // 60
        label = f"{horas:02d}h {minutos:02d}min"

    log(f"Ciclo: {label}", "warn" if tempo_ciclo < 60 else "info")


btn_aplicar = tk.Button(
    dropdown_row, text="Aplicar", font=SMALL_F,
    fg=BG, bg=PURPLE_DK, activebackground=PURPLE, activeforeground=BG,
    relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
    command=aplicar_ciclo,
)
btn_aplicar.pack(side="left", padx=(8, 0))

# — Countdown —
sec("PRÓXIMO CICLO")
countdown_row = tk.Frame(ctrl, bg=BG_PANEL)
countdown_row.pack(fill="x")

countdown_label = tk.Label(countdown_row, text="--:--", font=BIG_F,
                            fg=PURPLE_LT, bg=BG_PANEL)
countdown_label.pack(side="left")

ciclo_geral_label = tk.Label(countdown_row, text="  ciclo #0", font=SMALL_F,
                              fg=TEXT_DIM, bg=BG_PANEL)
ciclo_geral_label.pack(side="left", padx=(8, 0))

tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

# ──────────────────────────────────────────────
#  BOTÕES DE AÇÃO (compactos)
# ──────────────────────────────────────────────
btn_bar = tk.Frame(root, bg=BG_PANEL, padx=18, pady=10)
btn_bar.pack(fill="x")

def small_btn(parent, text, color, cmd):
    b = tk.Button(
        parent, text=text, font=MONO_B,
        fg=BG, bg=color,
        activebackground=TEXT, activeforeground=BG,
        relief="flat", bd=0,
        padx=14, pady=6,
        cursor="hand2", command=cmd,
    )
    b.pack(side="left", padx=(0, 8))
    return b

def on_iniciar():
    if not rodando:
        aplicar_ciclo()
        log("Iniciando bot...", "info")
        atualizar_janelas_label()
        threading.Thread(target=iniciar_bot, daemon=True).start()

def on_parar():
    parar_bot()

small_btn(btn_bar, "▶ INICIAR", GREEN,  on_iniciar)
small_btn(btn_bar, "■ PARAR",   RED,    on_parar)
small_btn(btn_bar, "⟳ SCAN",   PURPLE, atualizar_janelas_label)

tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

# ──────────────────────────────────────────────
#  LOG
# ──────────────────────────────────────────────
log_frame = tk.Frame(root, bg=BG, padx=12, pady=8)
log_frame.pack(fill="both", expand=True)

tk.Label(log_frame, text="LOG", font=MONO_B, fg=PURPLE, bg=BG, anchor="w").pack(fill="x")

log_wrap = tk.Frame(log_frame, bg=BG)
log_wrap.pack(fill="both", expand=True, pady=(4, 0))

log_box = tk.Text(
    log_wrap,
    bg=BG_INPUT, fg=TEXT, font=MONO,
    bd=0, highlightthickness=1,
    highlightbackground=BORDER, highlightcolor=PURPLE_DK,
    insertbackground=PURPLE,
    wrap="word", state="disabled", relief="flat",
)
log_box.pack(side="left", fill="both", expand=True)

sb = tk.Scrollbar(log_wrap, command=log_box.yview, bg=BG_PANEL,
                  troughcolor=BG, activebackground=PURPLE_DK, relief="flat", width=8)
sb.pack(side="right", fill="y")
log_box.configure(yscrollcommand=sb.set)

log_box.tag_configure("ok",    foreground=GREEN)
log_box.tag_configure("err",   foreground=RED)
log_box.tag_configure("warn",  foreground=YELLOW)
log_box.tag_configure("info",  foreground=PURPLE_LT)
log_box.tag_configure("dim",   foreground=TEXT_DIM)
log_box.tag_configure("cycle", foreground=ACCENT)

def log(msg, tag="normal"):
    ts = datetime.now().strftime("%H:%M:%S")
    log_box.configure(state="normal")
    log_box.insert("end", f"[{ts}] ", "dim")
    log_box.insert("end", msg + "\n", tag)
    log_box.configure(state="disabled")
    log_box.see("end")

# ──────────────────────────────────────────────
#  LÓGICA DO BOT (inalterada)
# ──────────────────────────────────────────────
def set_status(running):
    if running:
        status_dot.config(text="● RODANDO", fg=GREEN)
    else:
        status_dot.config(text="● PARADO",  fg=RED)

def posicionar_janelas(janelas):
    for win in janelas:
        try:
            win.moveTo(483, 121)
            log(f"Posicionada: {win.title}", "ok")
        except Exception as e:
            log(f"Erro ao mover {win.title}: {e}", "err")

def timer_regressivo(segundos):
    fim = time.time() + segundos
    while rodando and time.time() < fim:
        restante = int(fim - time.time())
        m, s = restante // 60, restante % 60
        countdown_label.config(text=f"{m:02d}:{s:02d}")
        time.sleep(0.2)
    countdown_label.config(text="--:--")
    if rodando:
        log("Iniciando novo ciclo...", "cycle")

def rodar_bot(janelas):
    global rodando
    ciclo_geral = 0
    ciclos_por_janela = {w.title: 0 for w in janelas}

    while rodando:
        for win in janelas:
            if not rodando:
                return
            try:
                win.activate()
                time.sleep(0.01)
                log(f"Ativando: {win.title}", "info")
            except Exception:
                continue

            for pos in posicoes:
                if not rodando:
                    return
                pyautogui.keyDown('ctrl')
                pyautogui.click(pos[0], pos[1], button='right')
                pyautogui.click(pos[0], pos[1], button='right')
                pyautogui.keyUp('ctrl')
                time.sleep(delay_click)

            ciclos_por_janela[win.title] += 1
            time.sleep(delay_posicao)

        ciclo_geral += 1
        ciclo_geral_label.config(text=f"  ciclo #{ciclo_geral}")
        log(f"=== Ciclo {ciclo_geral} completo ===", "cycle")

        t = threading.Thread(target=timer_regressivo, args=(tempo_ciclo,), daemon=True)
        t.start()
        t.join()

def iniciar_bot():
    global rodando
    rodando = True
    root.after(0, lambda: set_status(True))
    janelas = [w for w in gw.getAllWindows() if "Mu Cosmic" in w.title]
    if not janelas:
        log("Nenhuma janela 'Mu Cosmic' encontrada!", "err")
        rodando = False
        root.after(0, lambda: set_status(False))
        return
    posicionar_janelas(janelas)
    rodar_bot(janelas)
    root.after(0, lambda: set_status(False))
    log("Bot encerrado.", "warn")

def parar_bot():
    global rodando
    rodando = False
    log("Bot cancelado pelo usuário.", "warn")
    root.after(0, lambda: set_status(False))

def monitorar_cancelamento():
    while True:
        if keyboard.is_pressed("2") and rodando:
            parar_bot()
        time.sleep(0.1)

threading.Thread(target=monitorar_cancelamento, daemon=True).start()

# ──────────────────────────────────────────────
#  INIT
# ──────────────────────────────────────────────
log("Pronto. Selecione o ciclo e clique INICIAR.", "info")
log("Tecla [2] cancela o bot a qualquer momento.", "dim")
atualizar_janelas_label()

root.mainloop()