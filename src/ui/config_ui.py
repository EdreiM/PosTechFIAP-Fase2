"""
Janela de configuração da simulação (Tkinter).

Abre antes do Pygame para o usuário escolher cenário, frota e restrições
sem editar config.py. Exibe resumo de pedidos antes de iniciar.
"""

import random
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from config import (
    CAPACIDADE_VEICULO,
    CIDADES_FIXAS_DISPONIVEIS,
    DISTANCIA_MAXIMA_VEICULO,
    LIMITE_CIDADES_BENCHMARK,
    MODO_CIDADES,
    N_CIDADES,
    NUM_VEICULOS,
    OPCOES_AUTONOMIA,
    OPCOES_CAPACIDADE,
    SEED,
    UNIDADE_MEDIDA,
    obter_cidades,
)
from dados_hospitalares import (
    EntregaInfo,
    avaliar_viabilidade_frota,
    montar_entregas,
    parse_pedidos_csv,
)

# Limites informados na UI para o benchmark de solução ótima (força bruta)
MAX_VEICULOS_SOLUCAO_OTIMA = 6


def avisos_benchmark_solucao_otima(
    num_veiculos: int,
    n_entregas: int,
    limite_entregas: int = LIMITE_CIDADES_BENCHMARK,
) -> List[str]:
    """Mensagens quando o cálculo ótimo por força bruta será omitido."""
    avisos: List[str] = []
    if num_veiculos > MAX_VEICULOS_SOLUCAO_OTIMA:
        avisos.append(
            f"Mais de {MAX_VEICULOS_SOLUCAO_OTIMA} veículos ({num_veiculos}): "
            "a solução ótima (força bruta) não será calculada."
        )
    if n_entregas >= limite_entregas:
        avisos.append(
            f"{n_entregas} entregas (≥ {limite_entregas}): "
            "o cálculo ótimo não será realizado devido a limitações computacionais."
        )
    return avisos


def texto_painel_benchmark_solucao_otima(
    num_veiculos: int,
    n_entregas: Optional[int],
) -> tuple[str, str]:
    """Retorna (texto, cor_hex) para o painel de aviso do benchmark."""
    if n_entregas is None:
        return (
            "Solução ótima: informe entregas (ou importe CSV) para ver se o "
            "benchmark por força bruta será calculado.",
            "#64748b",
        )
    avisos = avisos_benchmark_solucao_otima(num_veiculos, n_entregas)
    if avisos:
        return ("⚠ " + "\n⚠ ".join(avisos), "#b45309")
    return (
        "Solução ótima (força bruta) será calculada para comparar com o AG.",
        "#166534",
    )


@dataclass
class ParametrosSimulacao:
    n_cidades: int
    modo_cidades: str
    num_veiculos: int
    seed: int
    capacidade_veiculo: int
    distancia_maxima_veiculo: int
    arquivo_csv: Optional[str] = None

    @classmethod
    def padrao(cls) -> "ParametrosSimulacao":
        return cls(
            n_cidades=N_CIDADES,
            modo_cidades=MODO_CIDADES,
            num_veiculos=NUM_VEICULOS,
            seed=SEED,
            capacidade_veiculo=CAPACIDADE_VEICULO,
            distancia_maxima_veiculo=DISTANCIA_MAXIMA_VEICULO,
            arquivo_csv=None,
        )


def _montar_entregas_preview(params: ParametrosSimulacao) -> List[EntregaInfo]:
    if params.arquivo_csv:
        return parse_pedidos_csv(params.arquivo_csv)

    cities = obter_cidades(
        params.n_cidades,
        params.modo_cidades,
        params.seed,
    )
    return montar_entregas(
        cities,
        seed=params.seed,
        n_cidades=params.n_cidades,
        modo=params.modo_cidades,
    )


def _confirmar_resumo_pedidos(
    parent: tk.Tk,
    entregas: List[EntregaInfo],
    params: ParametrosSimulacao,
) -> bool:
    """Diálogo modal com tabela de pedidos. Retorna True se o usuário confirmar."""
    dialogo = tk.Toplevel(parent)
    dialogo.title("Resumo dos pedidos do dia")
    dialogo.geometry("720x560")
    dialogo.resizable(True, True)
    dialogo.transient(parent)
    dialogo.grab_set()

    frame = ttk.Frame(dialogo, padding=12)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frame,
        text="Confira os pedidos antes de iniciar a otimização",
        font=("Segoe UI", 11, "bold"),
    ).pack(anchor=tk.W, pady=(0, 4))

    ttk.Label(
        frame,
        text=(
            f"Unidade de carga: 1 {UNIDADE_MEDIDA}  |  "
            f"Frota: {params.num_veiculos} veículos  |  "
            f"{params.capacidade_veiculo} kits/veículo  |  "
            f"{params.distancia_maxima_veiculo} km autonomia"
        ),
        font=("Segoe UI", 9),
    ).pack(anchor=tk.W, pady=(0, 8))

    tabela_frame = ttk.Frame(frame)
    tabela_frame.pack(fill=tk.BOTH, expand=True)

    colunas = ("unidade", "tipo", "kits", "prioridade")
    tabela = ttk.Treeview(
        tabela_frame, columns=colunas, show="headings", height=min(len(entregas), 10)
    )
    tabela.heading("unidade", text="Unidade")
    tabela.heading("tipo", text="Tipo")
    tabela.heading("kits", text="Kits")
    tabela.heading("prioridade", text="Prioridade")
    tabela.column("unidade", width=280)
    tabela.column("tipo", width=80)
    tabela.column("kits", width=60, anchor=tk.E)
    tabela.column("prioridade", width=80, anchor=tk.E)

    for entrega in entregas:
        tabela.insert(
            "",
            tk.END,
            values=(
                entrega.nome,
                entrega.tipo,
                entrega.demanda,
                entrega.prioridade,
            ),
        )

    scroll = ttk.Scrollbar(tabela_frame, orient=tk.VERTICAL, command=tabela.yview)
    tabela.configure(yscrollcommand=scroll.set)
    tabela.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    viabilidade = avaliar_viabilidade_frota(
        entregas, params.num_veiculos, params.capacidade_veiculo
    )
    total = sum(e.demanda for e in entregas)
    capacidade_frota = params.num_veiculos * params.capacidade_veiculo

    resumo_frame = ttk.LabelFrame(frame, text="Resumo da frota", padding=8)
    resumo_frame.pack(fill=tk.X, pady=(10, 0))

    linhas_resumo = [
        f"Carga total do dia: {total} kits",
        f"Capacidade por veículo: {params.capacidade_veiculo} kits",
        f"Autonomia por veículo: {params.distancia_maxima_veiculo} km",
        f"Veículos disponíveis: {params.num_veiculos}",
        f"Capacidade total da frota: {capacidade_frota} kits",
        f"Carga média por veículo (referência): {total / max(params.num_veiculos, 1):.1f} kits",
        viabilidade["mensagem"],
    ]
    excedentes = params.num_veiculos - len(entregas)
    if excedentes > 0:
        linhas_resumo.append(
            f"Aviso: {excedentes} veículo(s) excedente(s) permanecerão no hospital "
            f"(sem rota nesta execução)."
        )
    for aviso in avisos_benchmark_solucao_otima(
        params.num_veiculos, len(entregas)
    ):
        linhas_resumo.append(f"Benchmark ótimo: {aviso}")
    ttk.Label(
        resumo_frame,
        text="\n".join(linhas_resumo),
        font=("Consolas", 9),
        justify=tk.LEFT,
        wraplength=680,
    ).pack(anchor=tk.W, fill=tk.X)

    if not viabilidade["viavel"]:
        ttk.Label(
            dialogo,
            text=(
                "⚠ Frota insuficiente para a carga total — o AG roda normalmente. "
                "Entregas de menor prioridade permanecerão no hospital."
            ),
            font=("Segoe UI", 9),
            foreground="#b45309",
            wraplength=680,
        ).pack(anchor=tk.W, padx=12, pady=(0, 4))

    confirmado = {"ok": False}

    def confirmar():
        confirmado["ok"] = True
        dialogo.destroy()

    def voltar():
        dialogo.destroy()

    botoes = ttk.Frame(dialogo, padding=(12, 0, 12, 12))
    botoes.pack(fill=tk.X)
    ttk.Button(botoes, text="Confirmar e iniciar", command=confirmar).pack(
        side=tk.LEFT, padx=(0, 8)
    )
    ttk.Button(botoes, text="Voltar", command=voltar).pack(side=tk.LEFT)

    dialogo.wait_window()
    return confirmado["ok"]


def abrir_configuracao() -> ParametrosSimulacao:
    """
    Exibe diálogo modal. Retorna parâmetros escolhidos ou padrão se fechar.
    """
    resultado = {"params": None}
    root = tk.Tk()
    root.title("TSP Logística — Configurar Simulação")
    root.geometry("520x620")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frame,
        text="Configurar cenário antes da simulação",
        font=("Segoe UI", 12, "bold"),
    ).pack(anchor=tk.W, pady=(0, 4))

    ttk.Label(
        frame,
        text=f"Carga medida em {UNIDADE_MEDIDA}.",
        font=("Segoe UI", 9),
        wraplength=480,
    ).pack(anchor=tk.W, pady=(0, 8))

    # --- CSV opcional ---
    var_usar_csv = tk.BooleanVar(value=False)
    var_csv_path = tk.StringVar(value="")

    frame_csv = ttk.LabelFrame(frame, text="Pedidos do dia (opcional)", padding=8)
    frame_csv.pack(fill=tk.X, pady=(0, 10))

    chk_csv = ttk.Checkbutton(
        frame_csv,
        text="Importar pedidos de arquivo CSV",
        variable=var_usar_csv,
    )
    chk_csv.pack(anchor=tk.W)

    frame_csv_linha = ttk.Frame(frame_csv)
    frame_csv_linha.pack(fill=tk.X, pady=(4, 0))

    entry_csv = ttk.Entry(frame_csv_linha, textvariable=var_csv_path, width=42)
    entry_csv.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def buscar_csv():
        from pathlib import Path

        caminho = filedialog.askopenfilename(
            title="Selecionar pedidos (CSV)",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialdir=str(Path(__file__).resolve().parents[2] / "exemplos"),
        )
        if caminho:
            var_csv_path.set(caminho)
            var_usar_csv.set(True)

    ttk.Button(frame_csv_linha, text="Procurar…", command=buscar_csv).pack(
        side=tk.LEFT, padx=(6, 0)
    )

    ttk.Label(
        frame_csv,
        text="Colunas: nome, tipo, demanda_kits, prioridade, x, y — ver exemplos/pedidos_exemplo.csv",
        font=("Segoe UI", 8),
        wraplength=460,
    ).pack(anchor=tk.W, pady=(4, 0))

    # --- Modo de cidades ---
    ttk.Label(frame, text="Modo de entregas:").pack(anchor=tk.W)
    var_modo = tk.StringVar(value=MODO_CIDADES)
    combo_modo = ttk.Combobox(
        frame,
        textvariable=var_modo,
        values=["fixo", "aleatorio"],
        state="readonly",
        width=20,
    )
    combo_modo.pack(anchor=tk.W, pady=(2, 8))

    ttk.Label(frame, text="Quantidade de entregas:").pack(anchor=tk.W)

    frame_cidades = ttk.Frame(frame)
    frame_cidades.pack(anchor=tk.W, pady=(2, 8))

    var_n_fixo = tk.StringVar(value=str(N_CIDADES))
    combo_n_fixo = ttk.Combobox(
        frame_cidades,
        textvariable=var_n_fixo,
        values=[str(n) for n in CIDADES_FIXAS_DISPONIVEIS],
        state="readonly",
        width=8,
    )
    combo_n_fixo.pack(side=tk.LEFT)

    var_n_aleatorio = tk.IntVar(value=N_CIDADES)
    spin_n_aleatorio = ttk.Spinbox(
        frame_cidades,
        from_=3,
        to=25,
        textvariable=var_n_aleatorio,
        width=6,
    )
    spin_n_aleatorio.pack(side=tk.LEFT, padx=(8, 0))

    ttk.Label(
        frame_cidades,
        text="(fixo: 5/10/12/15  |  aleatório: 3–25)",
        font=("Segoe UI", 8),
    ).pack(side=tk.LEFT, padx=(8, 0))

    # --- Veículos ---
    ttk.Label(frame, text="Quantidade de veículos:").pack(anchor=tk.W)
    var_veiculos = tk.IntVar(value=NUM_VEICULOS)
    spin_veiculos = ttk.Spinbox(
        frame,
        from_=2,
        to=8,
        textvariable=var_veiculos,
        width=6,
    )
    spin_veiculos.pack(anchor=tk.W, pady=(2, 8))

    frame_benchmark = ttk.LabelFrame(
        frame, text="Benchmark — solução ótima (força bruta)", padding=8
    )
    frame_benchmark.pack(fill=tk.X, pady=(0, 8))

    lbl_aviso_benchmark = ttk.Label(
        frame_benchmark,
        text="",
        font=("Segoe UI", 9),
        wraplength=460,
        justify=tk.LEFT,
    )
    lbl_aviso_benchmark.pack(anchor=tk.W, fill=tk.X)

    # --- Capacidade e autonomia ---
    frame_frota = ttk.LabelFrame(
        frame, text="Restrições da frota", padding=8
    )
    frame_frota.pack(fill=tk.X, pady=(0, 8))

    ttk.Label(
        frame_frota,
        text="Capacidade por veículo (kits):",
    ).grid(row=0, column=0, sticky=tk.W)
    var_capacidade = tk.StringVar(value=str(CAPACIDADE_VEICULO))
    combo_capacidade = ttk.Combobox(
        frame_frota,
        textvariable=var_capacidade,
        values=[str(v) for v in OPCOES_CAPACIDADE],
        state="readonly",
        width=8,
    )
    combo_capacidade.grid(row=0, column=1, sticky=tk.W, padx=(8, 0))

    ttk.Label(
        frame_frota,
        text="Autonomia por veículo (km):",
    ).grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
    var_autonomia = tk.StringVar(value=str(DISTANCIA_MAXIMA_VEICULO))
    combo_autonomia = ttk.Combobox(
        frame_frota,
        textvariable=var_autonomia,
        values=[str(v) for v in OPCOES_AUTONOMIA],
        state="readonly",
        width=8,
    )
    combo_autonomia.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=(6, 0))

    # --- Seed ---
    var_seed_aleatoria = tk.BooleanVar(value=False)
    chk_seed = ttk.Checkbutton(
        frame,
        text="Cenário diferente a cada execução (seed aleatória)",
        variable=var_seed_aleatoria,
    )
    chk_seed.pack(anchor=tk.W, pady=(0, 4))

    ttk.Label(
        frame,
        text=f"Seed fixa padrão: {SEED} (reprodutível para relatório e testes)",
        font=("Segoe UI", 8),
    ).pack(anchor=tk.W, pady=(0, 12))

    controles_modo = [
        combo_modo,
        combo_n_fixo,
        spin_n_aleatorio,
    ]

    def atualizar_modo(_evento=None):
        usar_csv = var_usar_csv.get()
        estado_csv = "disabled" if not usar_csv else "normal"
        entry_csv.config(state=estado_csv)

        if usar_csv:
            for w in controles_modo:
                w.config(state="disabled")
            atualizar_aviso_benchmark()
            return

        fixo = var_modo.get() == "fixo"
        combo_modo.config(state="readonly")
        combo_n_fixo.config(state="readonly" if fixo else "disabled")
        spin_n_aleatorio.config(state="normal" if not fixo else "disabled")
        atualizar_aviso_benchmark()

    def _entregas_efetivas_formulario() -> Optional[int]:
        if var_usar_csv.get():
            caminho = var_csv_path.get().strip()
            if not caminho:
                return None
            try:
                return len(parse_pedidos_csv(caminho))
            except (OSError, ValueError):
                return None
        if var_modo.get() == "fixo":
            try:
                return int(var_n_fixo.get())
            except (tk.TclError, ValueError):
                return None
        try:
            return int(var_n_aleatorio.get())
        except tk.TclError:
            return None

    def atualizar_aviso_benchmark(*_):
        try:
            num_v = int(var_veiculos.get())
        except tk.TclError:
            num_v = NUM_VEICULOS
        texto, cor = texto_painel_benchmark_solucao_otima(
            num_v, _entregas_efetivas_formulario()
        )
        lbl_aviso_benchmark.config(text=texto, foreground=cor)

    for var in (var_veiculos, var_n_fixo, var_n_aleatorio):
        var.trace_add("write", lambda *_: atualizar_aviso_benchmark())
    var_usar_csv.trace_add("write", lambda *_: atualizar_modo())
    var_csv_path.trace_add("write", lambda *_: atualizar_aviso_benchmark())
    combo_modo.bind("<<ComboboxSelected>>", atualizar_modo)

    atualizar_modo()

    def _ler_params_formulario() -> Optional[ParametrosSimulacao]:
        usar_csv = var_usar_csv.get()
        arquivo_csv = var_csv_path.get().strip() if usar_csv else None

        try:
            num_veiculos = int(var_veiculos.get())
            capacidade = int(var_capacidade.get())
            autonomia = int(var_autonomia.get())
        except tk.TclError:
            messagebox.showerror("Erro", "Verifique veículos, capacidade e autonomia.")
            return None

        if capacidade not in OPCOES_CAPACIDADE:
            messagebox.showerror(
                "Erro",
                f"Capacidade deve ser uma de: {OPCOES_CAPACIDADE}",
            )
            return None
        if autonomia not in OPCOES_AUTONOMIA:
            messagebox.showerror(
                "Erro",
                f"Autonomia deve ser uma de: {OPCOES_AUTONOMIA}",
            )
            return None

        if usar_csv:
            if not arquivo_csv:
                messagebox.showerror("Erro", "Selecione um arquivo CSV.")
                return None
            try:
                entregas_csv = parse_pedidos_csv(arquivo_csv)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Erro no CSV", str(exc))
                return None
            n_cidades = len(entregas_csv)
            modo = "csv"
        else:
            modo = var_modo.get()
            if modo == "fixo":
                try:
                    n_cidades = int(var_n_fixo.get())
                except (tk.TclError, ValueError):
                    messagebox.showerror("Erro", "Selecione a quantidade de entregas.")
                    return None
                if n_cidades not in CIDADES_FIXAS_DISPONIVEIS:
                    messagebox.showerror(
                        "Erro",
                        f"No modo fixo use: {CIDADES_FIXAS_DISPONIVEIS}",
                    )
                    return None
            else:
                try:
                    n_cidades = int(var_n_aleatorio.get())
                except tk.TclError:
                    messagebox.showerror("Erro", "Informe a quantidade de entregas.")
                    return None
                if not 3 <= n_cidades <= 25:
                    messagebox.showerror(
                        "Erro", "Use entre 3 e 25 entregas no modo aleatório."
                    )
                    return None

        if num_veiculos < 2:
            messagebox.showerror("Erro", "Use pelo menos 2 veículos.")
            return None

        seed = random.randint(1, 999_999) if var_seed_aleatoria.get() else SEED

        return ParametrosSimulacao(
            n_cidades=n_cidades,
            modo_cidades=modo,
            num_veiculos=num_veiculos,
            seed=seed,
            capacidade_veiculo=capacidade,
            distancia_maxima_veiculo=autonomia,
            arquivo_csv=arquivo_csv,
        )

    def validar_e_iniciar():
        params = _ler_params_formulario()
        if params is None:
            return

        try:
            entregas = _montar_entregas_preview(params)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Erro", str(exc))
            return

        if not _confirmar_resumo_pedidos(root, entregas, params):
            return

        resultado["params"] = params
        root.destroy()

    def cancelar():
        resultado["params"] = ParametrosSimulacao.padrao()
        root.destroy()

    frame_botoes = ttk.Frame(frame)
    frame_botoes.pack(fill=tk.X, pady=(8, 0))
    ttk.Button(
        frame_botoes, text="Iniciar simulação", command=validar_e_iniciar
    ).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(
        frame_botoes, text="Iniciar com padrão (config.py)", command=cancelar
    ).pack(side=tk.LEFT)

    root.protocol("WM_DELETE_WINDOW", cancelar)
    root.mainloop()

    return resultado["params"] or ParametrosSimulacao.padrao()
