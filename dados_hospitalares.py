"""
Dados hospitalares: nomes de unidades, tipos de entrega e configuração do cenário.

Centraliza a geração de prioridades, demandas, nomes e tipos para tsp.py,
benchmark_comparativo.py e experimentos_ag.py.

Unidade de carga: 1 kit de medicamentos (caixa/kits fechados pela farmácia).
"""

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import genetic_algorithm as ga
from config import SEED, UNIDADE_MEDIDA_ABREV, Cidade

# Tipos de entrega e faixas associadas
TIPOS_ENTREGA = {
    "CRITICO": {
        "descricao": "Medicamentos críticos / urgência clínica",
        "prioridade_min": 8,
        "prioridade_max": 10,
        "demanda_min": 5,
        "demanda_max": 15,
    },
    "REGULAR": {
        "descricao": "Medicamentos regulares / tratamento contínuo",
        "prioridade_min": 4,
        "prioridade_max": 7,
        "demanda_min": 10,
        "demanda_max": 25,
    },
    "INSUMO": {
        "descricao": "Insumos hospitalares / material de apoio",
        "prioridade_min": 1,
        "prioridade_max": 3,
        "demanda_min": 15,
        "demanda_max": 30,
    },
}

# Nomes fixos por quantidade de cidades (modo "fixo" em config.py)
NOMES_POR_TAMANHO: Dict[int, List[str]] = {
    5: [
        "UTI Norte",
        "Home Care Zona Sul",
        "Farmácia Central",
        "Ambulatório Leste",
        "Lab. Análises Clínicas",
    ],
    10: [
        "UTI Norte",
        "Home Care Zona Sul",
        "Farmácia Central",
        "Ambulatório Leste",
        "Lab. Análises Clínicas",
        "Centro Cirúrgico",
        "Pronto-Socorro",
        "Unidade Domiciliar Oeste",
        "Oncologia Day Clinic",
        "Centro de Diálise",
    ],
    12: [
        "UTI Norte",
        "Home Care Zona Sul",
        "Farmácia Central",
        "Ambulatório Leste",
        "Lab. Análises Clínicas",
        "Centro Cirúrgico",
        "Pronto-Socorro",
        "Unidade Domiciliar Oeste",
        "Oncologia Day Clinic",
        "Centro de Diálise",
        "Maternidade",
        "Centro de Imagem",
    ],
    15: [
        "UTI Norte",
        "Home Care Zona Sul",
        "Farmácia Central",
        "Ambulatório Leste",
        "Lab. Análises Clínicas",
        "Centro Cirúrgico",
        "Pronto-Socorro",
        "Unidade Domiciliar Oeste",
        "Oncologia Day Clinic",
        "Centro de Diálise",
        "Maternidade",
        "Centro de Imagem",
        "Pediatria",
        "Cardiologia Ambulatorial",
        "Reabilitação Física",
    ],
}

# Tipos pré-definidos por índice (reprodutível no modo fixo)
TIPOS_POR_TAMANHO: Dict[int, List[str]] = {
    5: ["CRITICO", "CRITICO", "REGULAR", "REGULAR", "INSUMO"],
    10: [
        "CRITICO", "CRITICO", "CRITICO",
        "REGULAR", "REGULAR", "REGULAR", "REGULAR",
        "INSUMO", "INSUMO", "INSUMO",
    ],
    12: [
        "CRITICO", "CRITICO", "CRITICO",
        "REGULAR", "REGULAR", "REGULAR", "REGULAR", "REGULAR",
        "INSUMO", "INSUMO", "INSUMO", "INSUMO",
    ],
    15: [
        "CRITICO", "CRITICO", "CRITICO", "CRITICO",
        "REGULAR", "REGULAR", "REGULAR", "REGULAR", "REGULAR", "REGULAR",
        "INSUMO", "INSUMO", "INSUMO", "INSUMO", "INSUMO",
    ],
}

# Demandas fixas (kits) e prioridades fixas por índice — modo "fixo" (reprodutível)
DEMANDAS_FIXAS_POR_TAMANHO: Dict[int, List[int]] = {
    5: [12, 8, 18, 15, 28],
    10: [12, 10, 8, 20, 18, 16, 14, 30, 26, 22],
    12: [12, 10, 8, 20, 18, 16, 14, 12, 30, 26, 24, 22],
    15: [
        12, 10, 8, 14, 20, 18, 16, 14, 12, 10,
        30, 28, 26, 24, 22,
    ],
}

PRIORIDADES_FIXAS_POR_TAMANHO: Dict[int, List[int]] = {
    5: [10, 9, 6, 5, 2],
    10: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    12: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 3, 2],
    15: [10, 9, 8, 10, 7, 6, 5, 4, 3, 2, 3, 2, 1, 3, 2],
}

NOMES_ALEATORIOS = [
    "Unidade Domiciliar",
    "Posto de Saúde",
    "Clínica Especializada",
    "Centro de Reabilitação",
    "Unidade de Hemodiálise",
    "Ambulatório de Especialidades",
    "Centro de Oncologia",
    "Unidade Pediátrica",
    "Centro de Cardiologia",
    "Home Care",
]


def prioridade_para_tipo(prioridade: int) -> str:
    """Infere o tipo de entrega a partir da prioridade numérica."""
    if prioridade >= 8:
        return "CRITICO"
    if prioridade >= 4:
        return "REGULAR"
    return "INSUMO"


def _gerar_valores_por_tipo(tipo: str, rng: random.Random) -> Tuple[int, int]:
    cfg = TIPOS_ENTREGA[tipo]
    prioridade = rng.randint(cfg["prioridade_min"], cfg["prioridade_max"])
    demanda = rng.randint(cfg["demanda_min"], cfg["demanda_max"])
    return prioridade, demanda


def _escolher_tipo_aleatorio(rng: random.Random) -> str:
    return rng.choices(
        ["CRITICO", "REGULAR", "INSUMO"],
        weights=[0.25, 0.45, 0.30],
        k=1,
    )[0]


@dataclass
class EntregaInfo:
    cidade: Cidade
    nome: str
    tipo: str
    prioridade: int
    demanda: int


def _dados_entrega_fixa(indice: int, n: int) -> Tuple[str, str, int, int]:
    nome = NOMES_POR_TAMANHO[n][indice]
    tipo = TIPOS_POR_TAMANHO[n][indice]
    demanda = DEMANDAS_FIXAS_POR_TAMANHO[n][indice]
    prioridade = PRIORIDADES_FIXAS_POR_TAMANHO[n][indice]
    return nome, tipo, prioridade, demanda


def montar_entregas(
    cities: List[Cidade],
    seed: int = SEED,
    n_cidades: Optional[int] = None,
    modo: str = "fixo",
) -> List[EntregaInfo]:
    """Monta lista de entregas sem alterar genetic_algorithm (preview ou carga)."""
    rng = random.Random(seed)
    n = n_cidades or len(cities)
    entregas: List[EntregaInfo] = []

    if modo == "fixo" and n in NOMES_POR_TAMANHO:
        for i, cidade in enumerate(cities):
            nome, tipo, prioridade, demanda = _dados_entrega_fixa(i, n)
            entregas.append(
                EntregaInfo(cidade, nome, tipo, prioridade, demanda)
            )
        return entregas

    nomes = [
        f"{NOMES_ALEATORIOS[i % len(NOMES_ALEATORIOS)]} {i + 1}"
        for i in range(len(cities))
    ]
    for i, cidade in enumerate(cities):
        tipo = _escolher_tipo_aleatorio(rng)
        prioridade, demanda = _gerar_valores_por_tipo(tipo, rng)
        nome = nomes[i]
        entregas.append(
            EntregaInfo(cidade, nome, tipo, prioridade, demanda)
        )

    return entregas


def aplicar_entregas(entregas: List[EntregaInfo]) -> List[Cidade]:
    """Preenche genetic_algorithm a partir de entregas montadas ou CSV."""
    ga.city_priorities.clear()
    ga.city_demands.clear()
    ga.city_names.clear()
    ga.city_types.clear()

    cities: List[Cidade] = []
    for entrega in entregas:
        cities.append(entrega.cidade)
        ga.city_names[entrega.cidade] = entrega.nome
        ga.city_types[entrega.cidade] = entrega.tipo
        ga.city_priorities[entrega.cidade] = entrega.prioridade
        ga.city_demands[entrega.cidade] = entrega.demanda

    return cities


def carga_total_dia(entregas: List[EntregaInfo]) -> int:
    return sum(e.demanda for e in entregas)


def avaliar_viabilidade_frota(
    entregas: List[EntregaInfo],
    num_veiculos: int,
    capacidade_veiculo: int,
) -> Dict:
    """
    Verifica se a frota pode carregar todos os kits (limite teórico).

    Retorna dict com viavel, carga_total, capacidade_frota, deficit, mensagem.
    """
    total = carga_total_dia(entregas)
    capacidade_frota = num_veiculos * capacidade_veiculo
    viavel = total <= capacidade_frota
    deficit = max(0, total - capacidade_frota)
    min_veiculos = max(1, (total + capacidade_veiculo - 1) // capacidade_veiculo)

    if viavel:
        mensagem = (
            f"Carga total ({total} kits) cabe na frota "
            f"({num_veiculos} × {capacidade_veiculo} = {capacidade_frota} kits)."
        )
    else:
        mensagem = (
            f"Carga total ({total} kits) excede a frota "
            f"({num_veiculos} × {capacidade_veiculo} = {capacidade_frota} kits). "
            f"Faltam {deficit} kits de capacidade. "
            f"Sugestão: ≥ {min_veiculos} veículos ou capacidade ≥ "
            f"{(total + num_veiculos - 1) // num_veiculos} kits/veículo."
        )

    return {
        "viavel": viavel,
        "carga_total": total,
        "capacidade_frota": capacidade_frota,
        "deficit": deficit,
        "min_veiculos_carga": min_veiculos,
        "mensagem": mensagem,
    }


def resumo_pedidos_dia(entregas: List[EntregaInfo]) -> List[Dict]:
    """Linhas para tabela: unidade | tipo | kits | prioridade."""
    return [
        {
            "unidade": e.nome,
            "tipo": e.tipo,
            "demanda": e.demanda,
            "prioridade": e.prioridade,
        }
        for e in entregas
    ]


def formatar_resumo_pedidos(
    entregas: List[EntregaInfo],
    capacidade_veiculo: int,
    num_veiculos: int,
) -> str:
    total = carga_total_dia(entregas)
    linhas = [
        f"{'Unidade':<32} {'Tipo':<8} {'Kits':>5} {'Prior.':>6}",
        "-" * 55,
    ]
    for e in entregas:
        linhas.append(
            f"{e.nome:<32} {e.tipo:<8} {e.demanda:>5} {e.prioridade:>6}"
        )
    linhas.extend([
        "-" * 55,
        f"Carga total do dia: {total} {UNIDADE_MEDIDA_ABREV}",
        f"Capacidade por veículo: {capacidade_veiculo} {UNIDADE_MEDIDA_ABREV}",
        f"Veículos disponíveis: {num_veiculos}",
        f"Capacidade total da frota: {num_veiculos * capacidade_veiculo} {UNIDADE_MEDIDA_ABREV}",
        f"Carga média por veículo (referência): {total / max(num_veiculos, 1):.1f} {UNIDADE_MEDIDA_ABREV}",
    ])
    viab = avaliar_viabilidade_frota(entregas, num_veiculos, capacidade_veiculo)
    linhas.append(viab["mensagem"])
    return "\n".join(linhas)


def parse_pedidos_csv(caminho: str) -> List[EntregaInfo]:
    """Lê CSV de pedidos sem alterar genetic_algorithm (preview)."""
    path = Path(caminho)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho}")

    entregas: List[EntregaInfo] = []
    with path.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        campos = {c.strip().lower() for c in (leitor.fieldnames or [])}
        obrigatorios = {"nome", "tipo", "demanda_kits", "prioridade", "x", "y"}
        faltando = obrigatorios - campos
        if faltando:
            raise ValueError(
                f"CSV incompleto. Colunas faltando: {sorted(faltando)}. "
                f"Esperado: {', '.join(sorted(obrigatorios))}"
            )

        for linha, row in enumerate(leitor, start=2):
            tipo = row["tipo"].strip().upper()
            if tipo not in TIPOS_ENTREGA:
                raise ValueError(
                    f"Linha {linha}: tipo '{tipo}' inválido. "
                    f"Use CRITICO, REGULAR ou INSUMO."
                )
            try:
                demanda = int(row["demanda_kits"])
                prioridade = int(row["prioridade"])
                x = float(row["x"])
                y = float(row["y"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Linha {linha}: demanda_kits, prioridade, x e y devem ser numéricos."
                ) from exc

            if demanda < 1:
                raise ValueError(f"Linha {linha}: demanda_kits deve ser >= 1.")

            entregas.append(
                EntregaInfo(
                    cidade=(x, y),
                    nome=row["nome"].strip(),
                    tipo=tipo,
                    prioridade=prioridade,
                    demanda=demanda,
                )
            )

    if not entregas:
        raise ValueError("CSV sem linhas de pedido.")

    return entregas


def carregar_pedidos_csv(caminho: str) -> List[Cidade]:
    """
    Carrega pedidos de CSV e preenche genetic_algorithm.

    Colunas obrigatórias: nome, tipo, demanda_kits, prioridade, x, y
    """
    return aplicar_entregas(parse_pedidos_csv(caminho))


def configurar_cenario(
    cities: List[Cidade],
    seed: int = SEED,
    n_cidades: Optional[int] = None,
    modo: str = "fixo",
) -> None:
    """
    Preenche city_priorities, city_demands, city_names e city_types em genetic_algorithm.

    Modo fixo: nomes, tipos, demandas e prioridades pré-definidos (reprodutível).
    Modo aleatório: gera nomes e sorteia demanda/prioridade por tipo (usa seed).
    """
    entregas = montar_entregas(cities, seed, n_cidades, modo)
    aplicar_entregas(entregas)


def obter_nome(cidade: Cidade) -> str:
    return ga.city_names.get(cidade, "Unidade não identificada")


def obter_tipo(cidade: Cidade) -> str:
    return ga.city_types.get(cidade, prioridade_para_tipo(
        ga.city_priorities.get(cidade, 5)
    ))


def formatar_entrega(cidade: Cidade, ordem: int = None) -> str:
    nome = obter_nome(cidade)
    tipo = obter_tipo(cidade)
    prioridade = ga.city_priorities.get(cidade, 0)
    demanda = ga.city_demands.get(cidade, 0)
    prefixo = f"{ordem}. " if ordem is not None else ""
    return (
        f"{prefixo}{nome} [{tipo}] "
        f"({prioridade} prioridade, {demanda} {UNIDADE_MEDIDA_ABREV})"
    )


def resumo_tipos(cities: List[Cidade]) -> Dict[str, int]:
    contagem = {"CRITICO": 0, "REGULAR": 0, "INSUMO": 0}
    for cidade in cities:
        tipo = obter_tipo(cidade)
        contagem[tipo] = contagem.get(tipo, 0) + 1
    return contagem


def listar_entregas(cities: List[Cidade]) -> str:
    linhas = []
    for i, cidade in enumerate(cities, start=1):
        linhas.append(formatar_entrega(cidade, ordem=i))
    return "\n".join(linhas)


def montar_rotas_por_veiculo(
    rotas_veiculos: List[List[Cidade]],
) -> str:
    """Ordem completa de paradas por veículo (para chat e relatórios)."""
    linhas = [
        "Rotas por veículo (Hospital Central → paradas → Hospital Central):",
        "",
    ]

    for indice, rota in enumerate(rotas_veiculos, start=1):
        if not rota:
            linhas.append(f"Veículo {indice}: sem entregas")
            linhas.append("")
            continue

        linhas.append(f"Veículo {indice} ({len(rota)} paradas):")
        for pos, cidade in enumerate(rota, start=1):
            linhas.append(
                f"  {pos}ª parada: {formatar_entrega(cidade)}"
            )
        linhas.append(
            f"  Última parada do veículo {indice}: "
            f"{obter_nome(rota[-1])} [{obter_tipo(rota[-1])}]"
        )
        linhas.append("")

    return "\n".join(linhas)


def montar_ordem_global(
    best_path: List[Cidade],
    best_alocacao: Dict[Cidade, int],
) -> str:
    """Ordem global de visita e última entrega da operação."""
    if not best_path:
        return "Nenhuma entrega na rota."

    linhas = [
        "Ordem global de entrega (sequência otimizada pelo AG):",
        "",
    ]

    for ordem, cidade in enumerate(best_path, start=1):
        veiculo = best_alocacao[cidade] + 1
        linhas.append(
            f"  {ordem}. {obter_nome(cidade)} [{obter_tipo(cidade)}] "
            f"→ Veículo {veiculo}"
        )

    ultima = best_path[-1]
    primeira = best_path[0]
    linhas.extend([
        "",
        f"Primeira entrega global: {obter_nome(primeira)} [{obter_tipo(primeira)}] "
        f"(Veículo {best_alocacao[primeira] + 1})",
        f"Última entrega global: {obter_nome(ultima)} [{obter_tipo(ultima)}] "
        f"(Veículo {best_alocacao[ultima] + 1})",
    ])

    return "\n".join(linhas)
