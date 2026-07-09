"""
Heurísticas clássicas de roteamento para comparativo com o AG.

Implementa: rota aleatória, vizinho mais próximo e greedy por prioridade.
"""

import random
from typing import Dict, List, Tuple

import genetic_algorithm as ga
from genetic_algorithm import (
    Alocacao,
    Cidade,
    IndividuoVRP,
    calculate_distance,
    calcular_distancia_operacao,
    gerar_alocacao_aleatoria,
)


def rota_aleatoria(
    cities: List[Cidade],
    num_veiculos: int = ga.NUM_VEICULOS,
    seed: int = None,
) -> Tuple[List[Cidade], Alocacao]:
    """Ordem e alocação completamente aleatórias."""
    if seed is not None:
        random.seed(seed)
    path = random.sample(cities, len(cities))
    alocacao = gerar_alocacao_aleatoria(cities, num_veiculos)
    return path, alocacao


def _alocar_greedy_carga(
    path: List[Cidade],
    num_veiculos: int,
    demands: Dict[Cidade, int],
    capacidade: float,
) -> Alocacao:
    """Atribui cidades ao veículo com menor carga acumulada."""
    cargas = [0.0] * num_veiculos
    alocacao: Alocacao = {}

    for cidade in path:
        demanda = demands.get(cidade, 0)
        veiculo = min(range(num_veiculos), key=lambda v: cargas[v])
        alocacao[cidade] = veiculo
        cargas[veiculo] += demanda

    return ga.reparar_alocacao(alocacao, path, num_veiculos)


def nearest_neighbor(
    cities: List[Cidade],
    depot: Cidade = ga.DEPOT,
    num_veiculos: int = ga.NUM_VEICULOS,
    demands: Dict[Cidade, int] = None,
    capacidade: float = ga.CAPACIDADE_VEICULO,
) -> Tuple[List[Cidade], Alocacao]:
    """
    Constrói ordem de visita pelo vizinho mais próximo a partir do depósito.
    Aloca cidades aos veículos por balanceamento de carga.
    """
    if demands is None:
        demands = ga.city_demands

    path: List[Cidade] = []
    nao_visitadas = set(cities)
    atual = depot

    while nao_visitadas:
        proxima = min(
            nao_visitadas,
            key=lambda c: calculate_distance(atual, c),
        )
        path.append(proxima)
        nao_visitadas.remove(proxima)
        atual = proxima

    alocacao = _alocar_greedy_carga(
        path, num_veiculos, demands, capacidade
    )
    return path, alocacao


def greedy_prioridade(
    cities: List[Cidade],
    priorities: Dict[Cidade, int] = None,
    num_veiculos: int = ga.NUM_VEICULOS,
    demands: Dict[Cidade, int] = None,
    capacidade: float = ga.CAPACIDADE_VEICULO,
) -> Tuple[List[Cidade], Alocacao]:
    """
    Ordena cidades por prioridade decrescente (críticos primeiro).
    Aloca por balanceamento de carga entre veículos.
    """
    if priorities is None:
        priorities = ga.city_priorities
    if demands is None:
        demands = ga.city_demands

    path = sorted(cities, key=lambda c: -priorities.get(c, 1))
    alocacao = _alocar_greedy_carga(
        path, num_veiculos, demands, capacidade
    )
    return path, alocacao


def avaliar_solucao(
    path: List[Cidade],
    alocacao: Alocacao,
    num_veiculos: int = ga.NUM_VEICULOS,
) -> Dict:
    """Calcula distância, fitness e viabilidade de uma solução."""
    distancia = calcular_distancia_operacao(path, alocacao, num_veiculos)
    fitness = ga.calculate_fitness(path, alocacao, num_veiculos)
    restricoes = ga.avaliar_restricoes_veiculos(
        path, alocacao, num_veiculos
    )
    viavel = all(r["viavel"] for r in restricoes)

    return {
        "distancia": distancia,
        "fitness": fitness,
        "viavel": viavel,
        "restricoes": restricoes,
    }


def nome_metodo(metodo: str) -> str:
    nomes = {
        "ag": "Algoritmo Genético",
        "aleatoria": "Rota Aleatória",
        "nearest_neighbor": "Vizinho Mais Próximo",
        "greedy_prioridade": "Greedy por Prioridade",
        "otimo": "Ótimo (força bruta)",
    }
    return nomes.get(metodo, metodo)
