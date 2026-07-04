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
# VRP — frota e restrições operacionais
# =============================================================================

NUM_VEICULOS = 4
CAPACIDADE_VEICULO = 40
DISTANCIA_MAXIMA_VEICULO = 900
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

# Demanda e prioridade geradas por cidade (intervalo inclusivo)
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
PLOT_X_OFFSET = 450
PLOT_UPDATE_EVERY = 5


def obter_cidades() -> List[Cidade]:
    """Retorna a lista de cidades conforme N_CIDADES e MODO_CIDADES."""
    if MODO_CIDADES == "aleatorio":
        random.seed(SEED)
        return [
            (
                random.randint(RANDOM_X_MIN, RANDOM_X_MAX),
                random.randint(RANDOM_Y_MIN, RANDOM_Y_MAX),
            )
            for _ in range(N_CIDADES)
        ]

    if N_CIDADES not in DEFAULT_PROBLEMS:
        disponiveis = sorted(DEFAULT_PROBLEMS.keys())
        raise ValueError(
            f"N_CIDADES={N_CIDADES} inválido no modo 'fixo'. "
            f"Opções: {disponiveis}. "
            f"Ou defina MODO_CIDADES='aleatorio'."
        )

    return DEFAULT_PROBLEMS[N_CIDADES].copy()
