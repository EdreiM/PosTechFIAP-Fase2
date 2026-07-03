import threading
import tkinter as tk
from tkinter import scrolledtext, ttk


def _criar_aba_texto(notebook, titulo, conteudo):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text=titulo)
    texto = scrolledtext.ScrolledText(
        frame, wrap=tk.WORD, font=("Segoe UI", 10)
    )
    texto.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    texto.insert(tk.END, conteudo)
    texto.config(state=tk.DISABLED)
    return frame


def _desenhar_rota(canvas, cities_locations, best_solution, city_priorities, rotas_veiculos=None):
    canvas.delete("all")

    if not cities_locations or not best_solution:
        return

    if rotas_veiculos is None:
        rotas_veiculos = [best_solution]

    largura = canvas.winfo_width() or 700
    altura = canvas.winfo_height() or 400

    xs = [c[0] for c in cities_locations]
    ys = [c[1] for c in cities_locations]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    margem = 50

    faixa_x = max_x - min_x or 1
    faixa_y = max_y - min_y or 1
    escala = min(
        (largura - 2 * margem) / faixa_x,
        (altura - 2 * margem) / faixa_y,
    )

    offset_x = (largura - faixa_x * escala) / 2
    offset_y = (altura - faixa_y * escala) / 2

    def projeta(cidade):
        x = offset_x + (cidade[0] - min_x) * escala
        y = offset_y + (cidade[1] - min_y) * escala
        return x, y

    coords = {cidade: projeta(cidade) for cidade in cities_locations}
    ordem_visita = {
        cidade: indice + 1
        for indice, cidade in enumerate(best_solution)
    }

    cores_veiculos = ["#2563eb", "#dc2626", "#16a34a", "#9333ea"]

    for indice_veiculo, rota in enumerate(rotas_veiculos):
        if not rota:
            continue

        cor = cores_veiculos[indice_veiculo % len(cores_veiculos)]
        pontos = [coords[c] for c in rota]

        for pos in range(len(pontos)):
            x1, y1 = pontos[pos]
            x2, y2 = pontos[(pos + 1) % len(pontos)]
            canvas.create_line(x1, y1, x2, y2, fill=cor, width=2)

    for cidade in cities_locations:
        x, y = coords[cidade]
        prioridade = city_priorities.get(cidade, 1)
        cor = "#b91c1c" if prioridade >= 9 else "#ef4444"
        raio = 12

        canvas.create_oval(
            x - raio, y - raio, x + raio, y + raio,
            fill=cor, outline="#7f1d1d", width=1,
        )

        ordem = ordem_visita[cidade]
        canvas.create_text(
            x, y,
            text=str(ordem),
            fill="white",
            font=("Segoe UI", 9, "bold"),
        )


def abrir_dashboard(
    best_solution,
    cities_locations,
    city_priorities,
    analise,
    relatorio,
    instrucoes,
    texto_veiculos,
    texto_rota_resumo,
    best_fitness_values,
    fitness_final,
    responder_pergunta_fn,
    rotas_veiculos=None,
):
    root = tk.Tk()
    root.title("TSP Logística — Painel Operacional")
    root.geometry("920x680")
    root.minsize(720, 520)

    estilo = ttk.Style()
    if "vista" in estilo.theme_names():
        estilo.theme_use("vista")

    cabecalho = ttk.Label(
        root,
        text="Painel Operacional — Rotas Otimizadas",
        font=("Segoe UI", 14, "bold"),
    )
    cabecalho.pack(pady=(12, 4))

    resumo = ttk.Label(
        root,
        text=texto_rota_resumo.replace("\n", "   •   "),
        font=("Segoe UI", 9),
        wraplength=860,
        justify=tk.CENTER,
    )
    resumo.pack(pady=(0, 10), padx=12)

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

    aba_rota = ttk.Frame(notebook)
    notebook.add(aba_rota, text="Mapa da Rota")

    canvas = tk.Canvas(
        aba_rota,
        bg="white",
        highlightthickness=1,
        highlightbackground="#d1d5db",
    )
    canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def redesenhar(_evento=None):
        _desenhar_rota(
            canvas,
            cities_locations,
            best_solution,
            city_priorities,
            rotas_veiculos,
        )

    canvas.bind("<Configure>", redesenhar)
    root.after(100, redesenhar)

    legenda = ttk.Label(
        aba_rota,
        text=f"Distância total: {fitness_final:.2f}  |  "
             f"Número = ordem de visita  |  "
             f"Cores = rotas por veículo  |  "
             f"Vermelho escuro = prioridade 9-10",
        font=("Segoe UI", 9),
    )
    legenda.pack(pady=(0, 8))

    _criar_aba_texto(notebook, "Veículos", texto_veiculos)
    _criar_aba_texto(notebook, "Análise", analise)
    _criar_aba_texto(notebook, "Relatório", relatorio)
    _criar_aba_texto(notebook, "Instruções", instrucoes)

    aba_convergencia = ttk.Frame(notebook)
    notebook.add(aba_convergencia, text="Convergência")

    texto_convergencia = scrolledtext.ScrolledText(
        aba_convergencia, wrap=tk.WORD, font=("Segoe UI", 10)
    )
    texto_convergencia.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    linhas = [
        f"Geração {i + 1}: {valor:.2f}"
        for i, valor in enumerate(best_fitness_values)
    ]
    texto_convergencia.insert(
        tk.END,
        "Evolução do fitness (distância + prioridades):\n\n"
        + "\n".join(linhas),
    )
    texto_convergencia.config(state=tk.DISABLED)

    aba_chat = ttk.Frame(notebook)
    notebook.add(aba_chat, text="Chat")

    historico = scrolledtext.ScrolledText(
        aba_chat, wrap=tk.WORD, font=("Segoe UI", 10), state=tk.DISABLED
    )
    historico.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

    frame_entrada = ttk.Frame(aba_chat)
    frame_entrada.pack(fill=tk.X, padx=8, pady=(0, 8))

    entrada = ttk.Entry(frame_entrada, font=("Segoe UI", 10))
    entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

    btn_enviar = ttk.Button(frame_entrada, text="Enviar")
    btn_enviar.pack(side=tk.RIGHT)

    processando = {"ativo": False}

    def adicionar_mensagem(autor, mensagem):
        historico.config(state=tk.NORMAL)
        historico.insert(tk.END, f"\n{autor}:\n{mensagem}\n")
        historico.see(tk.END)
        historico.config(state=tk.DISABLED)

    adicionar_mensagem(
        "Sistema",
        "Pergunte sobre rotas, veículos, capacidade ou prioridades.\n"
        "Ex.: Qual veículo tem maior carga? A autonomia foi respeitada?",
    )

    def ao_receber_resposta(resposta):
        adicionar_mensagem("Assistente", resposta)
        processando["ativo"] = False
        btn_enviar.config(state=tk.NORMAL)
        entrada.focus_set()

    def enviar():
        if processando["ativo"]:
            return

        pergunta = entrada.get().strip()
        if not pergunta:
            return

        entrada.delete(0, tk.END)
        adicionar_mensagem("Você", pergunta)
        processando["ativo"] = True
        btn_enviar.config(state=tk.DISABLED)
        adicionar_mensagem("Sistema", "Consultando IA...")

        def worker():
            try:
                resposta = responder_pergunta_fn(pergunta)
            except Exception as erro:
                resposta = f"Erro ao consultar IA: {erro}"
            root.after(0, lambda: ao_receber_resposta(resposta))

        threading.Thread(target=worker, daemon=True).start()

    btn_enviar.config(command=enviar)
    entrada.bind("<Return>", lambda _evento: enviar())

    ttk.Button(root, text="Fechar", command=root.destroy).pack(pady=10)

    notebook.select(0)
    entrada.focus_set()
    root.mainloop()
