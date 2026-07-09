import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Dict, List, Optional, Set, Tuple

from draw_functions import (
    indices_veiculos_ociosos,
    montar_legenda_veiculos,
    posicoes_marcadores_veiculos_ociosos,
)
from metricas_benchmark import (
    MetricasComparativoMetodos,
    montar_bloco_analise_metricas,
)

Cidade = Tuple[float, float]

CORES_VEICULOS = [
    "#2563eb",  # V1
    "#dc2626",  # V2
    "#16a34a",  # V3
    "#9333ea",  # V4
    "#ea580c",  # V5
    "#0891b2",  # V6
    "#be185d",  # V7
    "#64748b",  # V8
]
NOMES_CORES_VEICULOS = [
    "V1 azul", "V2 vermelho", "V3 verde", "V4 roxo",
    "V5 laranja", "V6 ciano", "V7 rosa", "V8 cinza",
]

CHAT_TAG_POR_AUTOR = {
    "Você": "chat_usuario",
    "Assistente": "chat_assistente",
    "Sistema": "chat_sistema",
}


def _configurar_tags_chat(historico: scrolledtext.ScrolledText) -> None:
    """Destaca apenas o nome do autor na aba Chat."""
    historico.tag_configure(
        "chat_usuario",
        foreground="#1e40af",
        font=("Segoe UI", 10, "bold"),
    )
    historico.tag_configure(
        "chat_assistente",
        foreground="#166534",
        font=("Segoe UI", 10, "bold"),
    )
    historico.tag_configure(
        "chat_sistema",
        foreground="#64748b",
        font=("Segoe UI", 10, "italic"),
    )


def _metricas_legacy_para_bloco(
    fitness_final: float,
    distancia_aleatoria: float,
    fitness_target_solution: float,
    diferenca_benchmark: float,
    geracao_convergencia: int,
    motivo_otimo_omitido: str = "",
    total_entregas: int = 0,
    num_veiculos: int = 0,
) -> MetricasComparativoMetodos:
    """Compatibilidade quando só distâncias parciais são passadas."""
    return MetricasComparativoMetodos(
        fitness_inicial=float("nan"),
        distancia_inicial=float("nan"),
        fitness_final=fitness_final,
        fitness_final_prioridade=float("nan"),
        melhoria_fitness_pct=float("nan"),
        melhoria_distancia_pct=float("nan"),
        geracao_convergencia=geracao_convergencia,
        distancia_aleatoria=distancia_aleatoria,
        distancia_vizinho_proximo=float("nan"),
        distancia_greedy_prioridade=float("nan"),
        fitness_target_solution=fitness_target_solution,
        diferenca_benchmark_pct=diferenca_benchmark,
        num_veiculos=num_veiculos,
        total_entregas=total_entregas,
        motivo_otimo_omitido=motivo_otimo_omitido,
    )


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


def _estilo_no_mapa(
    cidade: Cidade,
    ordem_visita: Dict[Cidade, int],
    remanescentes: Set[Cidade],
    city_priorities: Dict[Cidade, int],
    city_types: Optional[Dict[Cidade, str]] = None,
) -> Dict:
    """Estilo visual de um nó no mapa (função pura, testável sem Tkinter)."""
    if cidade in remanescentes or cidade not in ordem_visita:
        return {
            "fill": "#94a3b8",
            "outline": "#64748b",
            "label": "—",
            "raio": 10,
            "text_color": "white",
            "no_hospital": True,
        }

    prioridade = city_priorities.get(cidade, 1)
    tipo = (city_types or {}).get(cidade, "")
    if prioridade >= 9 or tipo == "CRITICO":
        fill = "#b91c1c"
        outline = "#7f1d1d"
    elif tipo == "INSUMO":
        fill = "#f97316"
        outline = "#7f1d1d"
    else:
        fill = "#ef4444"
        outline = "#7f1d1d"

    return {
        "fill": fill,
        "outline": outline,
        "label": str(ordem_visita[cidade]),
        "raio": 12,
        "text_color": "white",
        "no_hospital": False,
    }


def _desenhar_rota(
    canvas,
    cities_locations,
    best_solution,
    city_priorities,
    rotas_veiculos=None,
    depot=None,
    city_names=None,
    city_types=None,
    remanescentes=None,
):
    canvas.delete("all")

    if not cities_locations:
        return

    if best_solution is None:
        best_solution = []

    remanescentes_set: Set[Cidade] = set(remanescentes or [])

    if rotas_veiculos is None:
        rotas_veiculos = [best_solution] if best_solution else []

    largura = canvas.winfo_width() or 700
    altura = canvas.winfo_height() or 400

    todos_pontos = list(cities_locations)
    if depot is not None:
        todos_pontos = todos_pontos + [depot]

    xs = [c[0] for c in todos_pontos]
    ys = [c[1] for c in todos_pontos]
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
    if depot is not None:
        coords[depot] = projeta(depot)

    ordem_visita = {
        cidade: indice + 1
        for indice, cidade in enumerate(best_solution)
    }

    cores_veiculos = CORES_VEICULOS

    for indice_veiculo, rota in enumerate(rotas_veiculos):
        if not rota:
            continue

        cor = cores_veiculos[indice_veiculo % len(cores_veiculos)]
        pontos = [coords[c] for c in rota]

        if depot is not None:
            depot_coord = coords[depot]
            canvas.create_line(
                depot_coord[0], depot_coord[1],
                pontos[0][0], pontos[0][1],
                fill=cor, width=2,
            )
            canvas.create_line(
                pontos[-1][0], pontos[-1][1],
                depot_coord[0], depot_coord[1],
                fill=cor, width=2,
            )

        for pos in range(len(pontos) - 1):
            x1, y1 = pontos[pos]
            x2, y2 = pontos[pos + 1]
            canvas.create_line(x1, y1, x2, y2, fill=cor, width=2)

    if depot is not None:
        dx, dy = coords[depot]
        ociosos = indices_veiculos_ociosos(rotas_veiculos)
        posicoes = posicoes_marcadores_veiculos_ociosos((dx, dy), len(ociosos))
        for pos, indice_veiculo in zip(posicoes, ociosos):
            mx, my = pos
            cor = cores_veiculos[indice_veiculo % len(cores_veiculos)]
            raio_m = 9
            canvas.create_oval(
                mx - raio_m, my - raio_m, mx + raio_m, my + raio_m,
                fill=cor, outline="#cbd5e1", width=1,
            )
            canvas.create_text(
                mx, my, text=f"V{indice_veiculo + 1}", fill="white",
                font=("Segoe UI", 7, "bold"),
            )

        raio_depot = 16
        canvas.create_oval(
            dx - raio_depot, dy - raio_depot,
            dx + raio_depot, dy + raio_depot,
            fill="#166534", outline="#14532d", width=2,
        )
        canvas.create_text(
            dx, dy, text="H", fill="white",
            font=("Segoe UI", 10, "bold"),
        )

    for cidade in cities_locations:
        x, y = coords[cidade]
        estilo = _estilo_no_mapa(
            cidade,
            ordem_visita,
            remanescentes_set,
            city_priorities,
            city_types,
        )
        raio = estilo["raio"]

        canvas.create_oval(
            x - raio, y - raio, x + raio, y + raio,
            fill=estilo["fill"],
            outline=estilo["outline"],
            width=2 if estilo["no_hospital"] else 1,
            dash=(3, 2) if estilo["no_hospital"] else (),
        )

        canvas.create_text(
            x, y,
            text=estilo["label"],
            fill=estilo["text_color"],
            font=("Segoe UI", 8 if estilo["no_hospital"] else 9, "bold"),
        )


def abrir_dashboard(
    best_solution,
    cities_locations,
    city_priorities,
    analise,
    relatorio,
    relatorio_semanal,
    instrucoes,
    texto_veiculos,
    fitness_final,
    responder_pergunta_fn,
    rotas_veiculos=None,
    depot=None,
    city_names=None,
    city_types=None,
    num_veiculos=None,
    remanescentes=None,
    houve_corte_capacidade=False,
    metricas_comparativo: Optional[MetricasComparativoMetodos] = None,
    distancia_aleatoria=float("nan"),
    fitness_target_solution=float("nan"),
    diferenca_benchmark=float("nan"),
    geracao_convergencia=0,
    total_entregas=0,
    motivo_otimo_omitido="",
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
    cabecalho.pack(pady=(12, 10))

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
            depot,
            city_names,
            city_types,
            remanescentes=remanescentes,
        )

    canvas.bind("<Configure>", redesenhar)
    root.after(100, redesenhar)

    legenda_veiculos = montar_legenda_veiculos(
        rotas_veiculos or [], NOMES_CORES_VEICULOS
    )
    n_entregues = len(best_solution) if best_solution else 0
    n_pedidos = len(cities_locations)
    legenda_partes = [
        f"H = Hospital",
        f"Número = ordem global ({n_entregues}/{n_pedidos} entregas)",
        legenda_veiculos,
        "Marcador colorido perto do H = veículo ocioso (sem rota)",
        "Vermelho escuro = CRITICO",
        "Laranja = INSUMO",
    ]
    if houve_corte_capacidade or (remanescentes and len(remanescentes) > 0):
        legenda_partes.append("Cinza tracejado = aguardando no hospital")
    legenda = ttk.Label(
        aba_rota,
        text="  |  ".join(legenda_partes),
        font=("Segoe UI", 9),
        wraplength=860,
        justify=tk.CENTER,
    )
    legenda.pack(pady=(0, 8))

    _criar_aba_texto(notebook, "Veículos", texto_veiculos)

    bloco_benchmark = montar_bloco_analise_metricas(
        metricas_comparativo
        if metricas_comparativo is not None
        else _metricas_legacy_para_bloco(
            fitness_final=fitness_final,
            distancia_aleatoria=distancia_aleatoria,
            fitness_target_solution=fitness_target_solution,
            diferenca_benchmark=diferenca_benchmark,
            geracao_convergencia=geracao_convergencia,
            motivo_otimo_omitido=motivo_otimo_omitido,
            total_entregas=total_entregas,
            num_veiculos=num_veiculos or 0,
        )
    )
    conteudo_analise = (
        f"{bloco_benchmark}\n\n{'─' * 40}\n\n"
        f"INTERPRETAÇÃO (IA)\n\n{analise}"
    )
    _criar_aba_texto(notebook, "Análise", conteudo_analise)
    _criar_aba_texto(notebook, "Relatório Diário", relatorio)
    _criar_aba_texto(notebook, "Relatório Semanal", relatorio_semanal)
    _criar_aba_texto(notebook, "Guia Motoristas", instrucoes)

    aba_chat = ttk.Frame(notebook)
    notebook.add(aba_chat, text="Chat")

    historico = scrolledtext.ScrolledText(
        aba_chat, wrap=tk.WORD, font=("Segoe UI", 10), state=tk.DISABLED
    )
    historico.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))
    _configurar_tags_chat(historico)

    frame_entrada = ttk.Frame(aba_chat)
    frame_entrada.pack(fill=tk.X, padx=8, pady=(0, 8))

    entrada = ttk.Entry(frame_entrada, font=("Segoe UI", 10))
    entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

    btn_enviar = ttk.Button(frame_entrada, text="Enviar")
    btn_enviar.pack(side=tk.RIGHT)

    processando = {"ativo": False}
    historico_turnos: list[tuple[str, str]] = []

    def adicionar_mensagem(autor, mensagem):
        tag_autor = CHAT_TAG_POR_AUTOR.get(autor, "chat_sistema")
        historico.config(state=tk.NORMAL)
        historico.insert(tk.END, "\n")
        historico.insert(tk.END, autor, tag_autor)
        historico.insert(tk.END, f": {mensagem}\n")
        historico.see(tk.END)
        historico.config(state=tk.DISABLED)

    adicionar_mensagem(
        "Sistema",
        "Olá! Pergunte o que precisar sobre rotas, veículos, kits ou a operação de hoje.",
    )

    def ao_receber_resposta(pergunta, resposta):
        historico_turnos.append((pergunta, resposta))
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
        historico_envio = list(historico_turnos)

        def worker():
            try:
                resposta = responder_pergunta_fn(pergunta, historico_envio)
            except Exception as erro:
                resposta = f"Erro ao consultar IA: {erro}"
            root.after(0, lambda: ao_receber_resposta(pergunta, resposta))

        threading.Thread(target=worker, daemon=True).start()

    btn_enviar.config(command=enviar)
    entrada.bind("<Return>", lambda _evento: enviar())

    ttk.Button(root, text="Fechar", command=root.destroy).pack(pady=10)

    notebook.select(0)
    entrada.focus_set()
    root.mainloop()
