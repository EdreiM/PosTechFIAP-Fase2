"""
Parâmetros centralizados do projeto.

Altere os valores abaixo para mudar o cenário sem editar tsp.py ou genetic_algorithm.py.
"""

import random
from typing import Dict, List, Tuple

Cidade = Tuple[float, float]

# =============================================================================
# PROBLEMA — quantidade e origem das cidades
# =============================================================================

N_CIDADES = 15

# "fixo"     → usa conjunto pré-definido (chaves em DEFAULT_PROBLEMS)
# "aleatorio" → gera N_CIDADES coordenadas aleatórias
MODO_CIDADES = "fixo"

SEED = 42

DEFAULT_PROBLEMS: Dict[int, List[Cidade]] = {
    5: [
        (733, 251), (706, 87), (546, 97), (562, 49), (576, 253),
    ],
    10: [
        (470, 169), (602, 202), (754, 239), (476, 233), (468, 301),
        (522, 29), (597, 171), (487, 325), (746, 232), (558, 136),
    ],
    12: [
        (728, 67), (560, 160), (602, 312), (712, 148), (535, 340),
        (720, 354), (568, 300), (629, 260), (539, 46), (634, 343),
        (491, 135), (768, 161),
    ],
    15: [
        (512, 317), (741, 72), (552, 50), (772, 346), (637, 12),
        (589, 131), (732, 165), (605, 15), (730, 38), (576, 216),
        (589, 381), (711, 387), (563, 228), (494, 22), (787, 288),
    ],
}

# Limites do canvas para MODO_CIDADES = "aleatorio"
RANDOM_X_MIN = 60
RANDOM_X_MAX = 790
RANDOM_Y_MIN = 10
RANDOM_Y_MAX = 390

# =============================================================================
# DEPÓSITO HOSPITALAR — ponto de saída/retorno de todos os veículos
# =============================================================================

DEPOT: Cidade = (400, 200)

# =============================================================================
# UNIDADE DE CARGA — documentação operacional
# =============================================================================
# Cada ponto de "demanda" representa um kit padrão de medicamentos/insumos
# (caixa térmica ou kit fechado pela farmácia hospitalar).
UNIDADE_MEDIDA = "kit de medicamentos"
UNIDADE_MEDIDA_ABREV = "kits"

# =============================================================================
# VRP — frota e restrições operacionais
# =============================================================================

NUM_VEICULOS = 4
CAPACIDADE_VEICULO = 40
DISTANCIA_MAXIMA_VEICULO = 1500

# Opções expostas na janela de configuração (tsp.py)
OPCOES_CAPACIDADE = [40, 60, 80]
OPCOES_AUTONOMIA = [1200, 1500, 2000]
PENALIDADE_CARGA = 100
PENALIDADE_AUTONOMIA = 50
PENALIDADE_VEICULO_VAZIO = 5000
PESO_PRIORIDADE = 5

# =============================================================================
# ALGORITMO GENÉTICO
# =============================================================================

POPULATION_SIZE = 100
N_GENERATIONS = 1000
MUTATION_PROBABILITY = 0.5
LIMITE_SEM_MELHORA = 100
LIMITE_CIDADES_BENCHMARK = 7

# Configurações para experimentos comparativos do AG (experimentos_ag.py)
EXPERIMENTOS_AG = [
    {
        "nome": "A - Padrão",
        "population_size": 100,
        "mutation_probability": 0.5,
        "n_generations": 1000,
    },
    {
        "nome": "B - Exploração",
        "population_size": 200,
        "mutation_probability": 0.7,
        "n_generations": 500,
    },
    {
        "nome": "C - Refino",
        "population_size": 50,
        "mutation_probability": 0.2,
        "n_generations": 2000,
    },
]

# Intervalos legados (modo aleatório usa TIPOS_ENTREGA em dados_hospitalares.py)
PRIORIDADE_MIN = 1
PRIORIDADE_MAX = 10
DEMANDA_MIN = 5
DEMANDA_MAX = 30

# =============================================================================
# INTERFACE (Pygame)
# =============================================================================

WIDTH = 800
HEIGHT = 400
NODE_RADIUS = 10
FPS = 30
PLOT_WIDTH = 400
MAP_X = 400
MAP_WIDTH = WIDTH - MAP_X
PLOT_UPDATE_EVERY = 5


def obter_cidades(
    n_cidades: int = None,
    modo: str = None,
    seed: int = None,
) -> List[Cidade]:
    """Retorna a lista de cidades conforme parâmetros (ou defaults de config)."""
    n = n_cidades if n_cidades is not None else N_CIDADES
    m = modo if modo is not None else MODO_CIDADES
    s = seed if seed is not None else SEED

    if m == "aleatorio":
        random.seed(s)
        return [
            (
                random.randint(RANDOM_X_MIN, RANDOM_X_MAX),
                random.randint(RANDOM_Y_MIN, RANDOM_Y_MAX),
            )
            for _ in range(n)
        ]

    if n not in DEFAULT_PROBLEMS:
        disponiveis = sorted(DEFAULT_PROBLEMS.keys())
        raise ValueError(
            f"N_CIDADES={n} inválido no modo 'fixo'. "
            f"Opções: {disponiveis}. "
            f"Ou use modo 'aleatorio'."
        )

    return DEFAULT_PROBLEMS[n].copy()


CIDADES_FIXAS_DISPONIVEIS = sorted(DEFAULT_PROBLEMS.keys())
