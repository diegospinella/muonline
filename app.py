import pyautogui
import time
import pygetwindow as gw
import threading
import keyboard
import tkinter as tk
from tkinter import ttk, font as tkfont
from datetime import datetime
import cv2
import numpy as np
from PIL import ImageGrab

pyautogui.FAILSAFE = False   # evita crash se mouse for ao canto da tela


# ──────────────────────────────────────────────
#  CONFIGURAÇÕES DOS SLOTS
# ──────────────────────────────────────────────
x_inicial = 1248
y_inicial = 495
espaco_x  = 33
espaco_y  = 31
posicoes  = [(x_inicial + c * espaco_x, y_inicial + l * espaco_y)
             for l in range(8) for c in range(8)]

delay_click   = 0.0
delay_posicao = 0.0
rodando       = False
tempo_ciclo   = 3600

# ──────────────────────────────────────────────
#  ESTATÍSTICAS GLOBAIS
# ──────────────────────────────────────────────
total_geral        = 0          # cliques desde o INICIAR
hora_inicio_bot    = None       # datetime do INICIAR

# Snapshots: {segundos: cliques_naquele_momento}
INTERVALOS_SEG = [1800, 3600, 5400, 7200, 10800, 14400, 18000, 21600, 25200, 28800]
INTERVALOS_ROT = ["30min","1h","1h30","2h","3h","4h","5h","6h","7h","8h"]
snapshots       = {}   # seg -> total registrado
snapshot_labels = {}   # seg -> tk.Label (referência para atualizar)

# ──────────────────────────────────────────────
#  DETECÇÃO DE ITEM NO SLOT
# ──────────────────────────────────────────────
SLOT_SAMPLE    = 10
SAT_PX_MIN     = 30
BRILHO_PX_MIN  = 35
PIXELS_MIN     = 4

def slot_tem_item(cx, cy):
    try:
        img = ImageGrab.grab(bbox=(cx - SLOT_SAMPLE, cy - SLOT_SAMPLE,
                                   cx + SLOT_SAMPLE, cy + SLOT_SAMPLE))
        hsv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)
        sat    = hsv[:, :, 1]
        brilho = hsv[:, :, 2]
        mask   = (sat >= SAT_PX_MIN) & (brilho >= BRILHO_PX_MIN)
        return int(np.sum(mask)) >= PIXELS_MIN
    except Exception:
        return True


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
root.geometry("480x900")
root.resizable(False, False)
root.configure(bg=BG)

MONO    = tkfont.Font(family="Consolas", size=10)
MONO_B  = tkfont.Font(family="Consolas", size=10, weight="bold")
TITLE_F = tkfont.Font(family="Consolas", size=14, weight="bold")
SMALL_F = tkfont.Font(family="Consolas", size=9)
TINY_F  = tkfont.Font(family="Consolas", size=8)
BIG_F   = tkfont.Font(family="Consolas", size=20, weight="bold")
MED_F   = tkfont.Font(family="Consolas", size=11, weight="bold")

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
ctrl = tk.Frame(root, bg=BG_PANEL, padx=18, pady=10)
ctrl.pack(fill="x")

def sec(parent, txt):
    tk.Label(parent, text=txt, font=MONO_B, fg=PURPLE,
             bg=BG_PANEL, anchor="w").pack(fill="x", pady=(8, 2))

# — Janelas —
sec(ctrl, "JANELAS DETECTADAS")
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
sec(ctrl, "TEMPO DE CICLO")

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

opcoes_ordenadas = dict(sorted(OPCOES_CICLO.items(), key=lambda x: x[1]))
primeira_opcao = next(iter(opcoes_ordenadas.keys()))
ciclo_var = tk.StringVar(value=primeira_opcao)

style = ttk.Style()
style.theme_use("clam")
style.configure("Dark.TMenubutton",
    background=BG_INPUT, foreground=TEXT,
    font=("Consolas", 10), relief="flat",
    borderwidth=1, arrowcolor=PURPLE_LT,
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
        label = f"{tempo_ciclo}s (TESTE)"
    elif tempo_ciclo < 3600:
        label = f"{tempo_ciclo//60:02d} min"
    else:
        horas   = tempo_ciclo // 3600
        minutos = (tempo_ciclo % 3600) // 60
        label   = f"{horas:02d}h {minutos:02d}min"
    log(f"Ciclo definido: {label}", "warn" if tempo_ciclo < 60 else "info")

btn_aplicar = tk.Button(
    dropdown_row, text="Aplicar", font=SMALL_F,
    fg=BG, bg=PURPLE_DK, activebackground=PURPLE, activeforeground=BG,
    relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
    command=aplicar_ciclo,
)
btn_aplicar.pack(side="left", padx=(8, 0))

# — Sensibilidade —
sec(ctrl, "SENSIBILIDADE DE DETECÇÃO")
sens_row = tk.Frame(ctrl, bg=BG_PANEL)
sens_row.pack(fill="x", pady=(0, 2))

tk.Label(sens_row, text="Pixels mín.:", font=MONO, fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")

sens_var = tk.IntVar(value=PIXELS_MIN)
sens_spin = tk.Spinbox(
    sens_row, from_=1, to=40, textvariable=sens_var,
    width=4, font=MONO, bg=BG_INPUT, fg=TEXT,
    buttonbackground=BG_INPUT, relief="flat",
    highlightthickness=1, highlightbackground=BORDER,
    insertbackground=PURPLE,
)
sens_spin.pack(side="left", padx=(8, 0))
tk.Label(sens_row, text="  (padrão = 4, menor = mais sensível)", font=SMALL_F,
         fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")

def aplicar_sensibilidade():
    global PIXELS_MIN
    PIXELS_MIN = sens_var.get()
    log(f"Pixels mín. = {PIXELS_MIN}", "info")

btn_sens = tk.Button(
    sens_row, text="OK", font=SMALL_F,
    fg=BG, bg=PURPLE_DK, activebackground=PURPLE, activeforeground=BG,
    relief="flat", bd=0, padx=8, pady=4, cursor="hand2",
    command=aplicar_sensibilidade,
)
btn_sens.pack(side="left", padx=(8, 0))

# — Countdown —
sec(ctrl, "PRÓXIMO CICLO")
countdown_row = tk.Frame(ctrl, bg=BG_PANEL)
countdown_row.pack(fill="x")

countdown_label = tk.Label(countdown_row, text="--:--", font=BIG_F,
                            fg=PURPLE_LT, bg=BG_PANEL)
countdown_label.pack(side="left")

ciclo_geral_label = tk.Label(countdown_row, text="  ciclo #0", font=SMALL_F,
                              fg=TEXT_DIM, bg=BG_PANEL)
ciclo_geral_label.pack(side="left", padx=(8, 0))

# — Total geral ao vivo —
total_label = tk.Label(countdown_row, text="  ✦ 0 joias", font=MONO_B,
                       fg=YELLOW, bg=BG_PANEL)
total_label.pack(side="right", padx=(0, 4))

tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

# ──────────────────────────────────────────────
#  PAINEL DE ESTATÍSTICAS POR TEMPO
# ──────────────────────────────────────────────
stats_frame = tk.Frame(root, bg=BG_PANEL, padx=18, pady=8)
stats_frame.pack(fill="x")

tk.Label(stats_frame, text="JOIAS RESGATADAS POR INTERVALO", font=MONO_B,
         fg=PURPLE, bg=BG_PANEL, anchor="w").pack(fill="x", pady=(0, 6))

# Grid 2 colunas × 5 linhas
grid = tk.Frame(stats_frame, bg=BG_PANEL)
grid.pack(fill="x")

for i, (seg, rot) in enumerate(zip(INTERVALOS_SEG, INTERVALOS_ROT)):
    col = i % 2
    row = i // 2

    cell = tk.Frame(grid, bg=BG_INPUT, padx=8, pady=4)
    cell.grid(row=row, column=col, padx=(0 if col else 0, 6), pady=2, sticky="ew")
    grid.columnconfigure(col, weight=1)

    tk.Label(cell, text=rot, font=TINY_F, fg=TEXT_DIM, bg=BG_INPUT,
             anchor="w").pack(side="left")

    lbl = tk.Label(cell, text="—", font=MED_F, fg=TEXT_DIM, bg=BG_INPUT,
                   anchor="e")
    lbl.pack(side="right")
    snapshot_labels[seg] = lbl

def reset_stats():
    """Zera estatísticas ao iniciar o bot."""
    global total_geral, hora_inicio_bot, snapshots
    total_geral     = 0
    hora_inicio_bot = datetime.now()
    snapshots       = {}
    total_label.config(text="  ✦ 0 joias")
    for lbl in snapshot_labels.values():
        lbl.config(text="—", fg=TEXT_DIM)

def registrar_snapshot():
    """
    Chamado após cada ciclo. Verifica se algum intervalo
    de tempo foi atingido e registra o total acumulado.
    """
    if hora_inicio_bot is None:
        return
    elapsed = (datetime.now() - hora_inicio_bot).total_seconds()
    for seg in INTERVALOS_SEG:
        if seg not in snapshots and elapsed >= seg:
            snapshots[seg] = total_geral
            rot = INTERVALOS_ROT[INTERVALOS_SEG.index(seg)]
            lbl = snapshot_labels[seg]
            lbl.config(text=str(total_geral), fg=GREEN)
            log(f"  📊 {rot}: {total_geral} joias resgatadas", "warn")

tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

# ──────────────────────────────────────────────
#  BOTÕES DE AÇÃO
# ──────────────────────────────────────────────
btn_bar = tk.Frame(root, bg=BG_PANEL, padx=18, pady=10)
btn_bar.pack(fill="x")

def small_btn(parent, text, color, cmd):
    b = tk.Button(
        parent, text=text, font=MONO_B,
        fg=BG, bg=color,
        activebackground=TEXT, activeforeground=BG,
        relief="flat", bd=0, padx=14, pady=6,
        cursor="hand2", command=cmd,
    )
    b.pack(side="left", padx=(0, 8))
    return b

def on_iniciar():
    if not rodando:
        reset_stats()
        aplicar_ciclo()
        log("Iniciando bot...", "info")
        atualizar_janelas_label()
        threading.Thread(target=iniciar_bot, daemon=True).start()

def on_parar():
    parar_bot()

small_btn(btn_bar, "▶ INICIAR", GREEN,  on_iniciar)
small_btn(btn_bar, "■ PARAR",   RED,    on_parar)
small_btn(btn_bar, "⟳ SCAN",   PURPLE, atualizar_janelas_label)

tk.Label(btn_bar, text="  Parar: Ctrl+-", font=SMALL_F,
         fg=TEXT_DIM, bg=BG_PANEL).pack(side="left", padx=(4, 0))

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
#  LÓGICA DO BOT
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
    global rodando, total_geral
    ciclo_geral = 0

    while rodando:
        cliques_ciclo = 0   # total deste ciclo específico

        for win in janelas:
            if not rodando:
                return

            ativou = False
            for _ in range(3):
                try:
                    win.activate()
                    time.sleep(0.03)
                    ativou = True
                    break
                except Exception:
                    time.sleep(0.1)

            if not ativou:
                log(f"Não conseguiu ativar: {win.title}", "err")
                continue

            # Garante foco real antes de clicar no helper
            time.sleep(0.3)
            try: win.activate()
            except: pass
            time.sleep(0.3)

            # Clica no MU Helper com mouseDown/mouseUp (mais físico que click)
            pyautogui.moveTo(751, 160)
            time.sleep(0.1)
            pyautogui.mouseDown(button='left')
            time.sleep(0.05)
            pyautogui.mouseUp(button='left')
            time.sleep(1.2)
            pyautogui.moveTo(751, 160)
            time.sleep(0.1)
            pyautogui.mouseDown(button='left')
            time.sleep(0.05)
            pyautogui.mouseUp(button='left')
            time.sleep(0.5)

            log(f"Varrendo: {win.title}", "info")

            slots_clicados = 0
            slots_pulados  = 0

            for pos in posicoes:
                if not rodando:
                    return
                if slot_tem_item(pos[0], pos[1]):
                    pyautogui.keyDown('ctrl')
                    pyautogui.click(pos[0], pos[1], button='right')
                    pyautogui.click(pos[0], pos[1], button='right')
                    pyautogui.keyUp('ctrl')
                    time.sleep(delay_click)
                    slots_clicados += 1
                else:
                    slots_pulados += 1

            log(f"  ✔ {slots_clicados} slot(s) clicado(s) / {slots_pulados} vazio(s)", "ok")
            cliques_ciclo += slots_clicados
            time.sleep(delay_posicao)

        # — Atualiza totais —
        ciclo_geral  += 1
        total_geral  += cliques_ciclo

        ciclo_geral_label.config(text=f"  ciclo #{ciclo_geral}")
        total_label.config(text=f"  ✦ {total_geral} joias")

        log(f"=== Ciclo {ciclo_geral}: {cliques_ciclo} joias  |  Total: {total_geral} ===", "cycle")

        # Verifica snapshots de intervalo
        registrar_snapshot()

        t = threading.Thread(target=timer_regressivo, args=(tempo_ciclo,), daemon=True)
        t.start()
        while t.is_alive():
            t.join(timeout=0.5)
            if not rodando:
                break

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
    if rodando:
        rodando = False
        log(f"Bot parado. Total da sessão: {total_geral} joias.", "warn")
        root.after(0, lambda: set_status(False))

def _hotkey_parar():
    if rodando:
        parar_bot()

keyboard.add_hotkey("ctrl+-", _hotkey_parar, suppress=False)

# ──────────────────────────────────────────────
#  INIT
# ──────────────────────────────────────────────
log("Pronto. Selecione o ciclo e clique INICIAR.", "info")
log("Tecla [Ctrl + -] para cancelar o bot.", "dim")
log(f"Detecção: {PIXELS_MIN} pixel(s) colorido(s) por slot.", "dim")
atualizar_janelas_label()

root.mainloop()