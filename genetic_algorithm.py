

import random
import math
import copy
import itertools
from typing import Dict, List, Tuple

from config import (
    CAPACIDADE_VEICULO as _CAPACIDADE_PADRAO,
    DEFAULT_PROBLEMS,
    DEPOT,
    DISTANCIA_MAXIMA_VEICULO as _AUTONOMIA_PADRAO,
    NUM_VEICULOS,
    PENALIDADE_AUTONOMIA,
    PENALIDADE_CARGA,
    PENALIDADE_VEICULO_VAZIO,
    PESO_PRIORIDADE,
)

default_problems = DEFAULT_PROBLEMS

# Atualizável em runtime (janela de configuração do tsp.py)
CAPACIDADE_VEICULO = _CAPACIDADE_PADRAO
DISTANCIA_MAXIMA_VEICULO = _AUTONOMIA_PADRAO


def aplicar_parametros_frota(
    capacidade: int = None,
    autonomia: int = None,
) -> None:
    """Define capacidade (kits) e autonomia (km) da frota para esta execução."""
    global CAPACIDADE_VEICULO, DISTANCIA_MAXIMA_VEICULO
    if capacidade is not None:
        CAPACIDADE_VEICULO = capacidade
    if autonomia is not None:
        DISTANCIA_MAXIMA_VEICULO = autonomia

city_priorities = {}
city_demands = {}
city_names = {}
city_types = {}

Cidade = Tuple[float, float]
Alocacao = Dict[Cidade, int]
IndividuoVRP = Tuple[List[Cidade], Alocacao]


def gerar_alocacao_aleatoria(
    cities: List[Cidade],
    num_veiculos: int = NUM_VEICULOS,
) -> Alocacao:
    """Atribui cada cidade a um veículo; garante ao menos 1 cidade por veículo."""
    n = len(cities)
    embaralhadas = cities.copy()
    random.shuffle(embaralhadas)

    alocacao: Alocacao = {}
    for veiculo in range(min(num_veiculos, n)):
        alocacao[embaralhadas[veiculo]] = veiculo

    for cidade in embaralhadas[num_veiculos:]:
        alocacao[cidade] = random.randint(0, num_veiculos - 1)

    return alocacao


def reparar_alocacao(
    alocacao: Alocacao,
    path: List[Cidade],
    num_veiculos: int = NUM_VEICULOS,
) -> Alocacao:
    """Garante índices válidos e ao menos uma cidade por veículo."""
    alocacao = alocacao.copy()

    for cidade in path:
        if cidade not in alocacao:
            alocacao[cidade] = random.randint(0, num_veiculos - 1)
        elif alocacao[cidade] < 0 or alocacao[cidade] >= num_veiculos:
            alocacao[cidade] = random.randint(0, num_veiculos - 1)

    usados = set(alocacao[c] for c in path)

    for veiculo in range(num_veiculos):
        if veiculo not in usados:
            cidade = random.choice(path)
            alocacao[cidade] = veiculo
            usados.add(veiculo)

    return alocacao


def dividir_rota_em_veiculos(
    path: List[Cidade],
    alocacao: Alocacao = None,
    num_veiculos: int = NUM_VEICULOS,
) -> List[List[Cidade]]:
    """
    Monta rotas por veículo.
    Ordem de visita em cada veículo = ordem em que aparecem em path.
    """
    rotas = [[] for _ in range(num_veiculos)]

    if alocacao is None:
        for indice, cidade in enumerate(path):
            rotas[indice % num_veiculos].append(cidade)
        return rotas

    alocacao = reparar_alocacao(alocacao, path, num_veiculos)

    for cidade in path:
        rotas[alocacao[cidade]].append(cidade)

    return rotas


def calcular_distancia_operacao(
    path: List[Cidade],
    alocacao: Alocacao = None,
    num_veiculos: int = NUM_VEICULOS,
) -> float:
    rotas = dividir_rota_em_veiculos(path, alocacao, num_veiculos)

    return sum(
        calculate_distance_only(rota)
        for rota in rotas
        if rota
    )


def avaliar_restricoes_veiculos(
    path: List[Cidade],
    alocacao: Alocacao = None,
    num_veiculos: int = NUM_VEICULOS,
):
    rotas = dividir_rota_em_veiculos(path, alocacao, num_veiculos)
    resumo = []

    for indice, rota in enumerate(rotas, start=1):
        carga = sum(city_demands.get(cidade, 0) for cidade in rota)
        distancia = calculate_distance_only(rota) if rota else 0
        capacidade_ok = carga <= CAPACIDADE_VEICULO
        autonomia_ok = distancia <= DISTANCIA_MAXIMA_VEICULO

        resumo.append({
            "veiculo": indice,
            "cidades": len(rota),
            "carga": carga,
            "distancia": distancia,
            "capacidade_ok": capacidade_ok,
            "autonomia_ok": autonomia_ok,
            "viavel": capacidade_ok and autonomia_ok,
        })

    return resumo


def melhor_alocacao_exaustiva(
    path: List[Cidade],
    num_veiculos: int = NUM_VEICULOS,
) -> Tuple[float, Alocacao]:
    """Encontra a melhor alocação para uma ordem fixa de cidades."""
    n = len(path)
    melhor_dist = float("inf")
    melhor_alocacao: Alocacao = {}

    for atribuicoes in itertools.product(range(num_veiculos), repeat=n):
        if len(set(atribuicoes)) < num_veiculos:
            continue

        alocacao = {path[i]: atribuicoes[i] for i in range(n)}
        distancia = calcular_distancia_operacao(path, alocacao, num_veiculos)

        if distancia < melhor_dist:
            melhor_dist = distancia
            melhor_alocacao = alocacao

    return melhor_dist, melhor_alocacao


def calcular_solucao_otima_vrp(
    cities_locations: List[Cidade],
    num_veiculos: int = NUM_VEICULOS,
    limite_cidades: int = 7,
) -> float:
    """
    Força bruta com ordem + alocação real.
    Viável apenas com poucas cidades (n <= 7).
    """
    n = len(cities_locations)
    if n > limite_cidades:
        return float("nan")

    melhor = float("inf")
    for permutacao in itertools.permutations(cities_locations):
        path = list(permutacao)
        distancia, _ = melhor_alocacao_exaustiva(path, num_veiculos)
        if distancia < melhor:
            melhor = distancia

    return melhor


def criar_individuo_aleatorio(
    cities_location: List[Cidade],
    num_veiculos: int = NUM_VEICULOS,
) -> IndividuoVRP:
    path = random.sample(cities_location, len(cities_location))
    alocacao = gerar_alocacao_aleatoria(cities_location, num_veiculos)
    return path, alocacao


def generate_random_population(
    cities_location: List[Cidade],
    population_size: int,
    num_veiculos: int = NUM_VEICULOS,
) -> List[IndividuoVRP]:
    return [
        criar_individuo_aleatorio(cities_location, num_veiculos)
        for _ in range(population_size)
    ]


def calculate_distance(point1: Cidade, point2: Cidade) -> float:
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def calculate_distance_only(
    path: List[Cidade],
    depot: Cidade = DEPOT,
) -> float:
    """
    Distância de uma rota de veículo.
    Com depósito: depot → cidades → depot (VRP realista).
    Sem depósito (depot=None): ciclo fechado entre as cidades (legado).
    """
    if not path:
        return 0.0

    if depot is None:
        distance = 0.0
        for i in range(len(path)):
            distance += calculate_distance(path[i], path[(i + 1) % len(path)])
        return distance

    distance = calculate_distance(depot, path[0])
    for i in range(len(path) - 1):
        distance += calculate_distance(path[i], path[i + 1])
    distance += calculate_distance(path[-1], depot)
    return distance


def calculate_fitness(
    path: List[Cidade],
    alocacao: Alocacao = None,
    num_veiculos: int = NUM_VEICULOS,
) -> float:
    rotas_veiculos = dividir_rota_em_veiculos(path, alocacao, num_veiculos)

    distance = sum(
        calculate_distance_only(rota)
        for rota in rotas_veiculos
        if rota
    )

    priority_penalty = 0
    for position, city in enumerate(path):
        prioridade = city_priorities.get(city, 1)
        priority_penalty += position * prioridade * PESO_PRIORIDADE

    load_penalty = 0
    autonomy_penalty = 0
    empty_penalty = 0

    for indice, rota in enumerate(rotas_veiculos):
        if not rota:
            empty_penalty += PENALIDADE_VEICULO_VAZIO
            continue

        carga = sum(city_demands.get(cidade, 0) for cidade in rota)
        if carga > CAPACIDADE_VEICULO:
            load_penalty += (carga - CAPACIDADE_VEICULO) * PENALIDADE_CARGA

        distancia_veiculo = calculate_distance_only(rota)
        if distancia_veiculo > DISTANCIA_MAXIMA_VEICULO:
            autonomy_penalty += (
                distancia_veiculo - DISTANCIA_MAXIMA_VEICULO
            ) * PENALIDADE_AUTONOMIA

    return (
        distance
        + priority_penalty
        + load_penalty
        + autonomy_penalty
        + empty_penalty
    )


def calculate_fitness_individuo(
    individuo: IndividuoVRP,
    num_veiculos: int = NUM_VEICULOS,
) -> float:
    path, alocacao = individuo
    return calculate_fitness(path, alocacao, num_veiculos)


def order_crossover(
    parent1: List[Cidade],
    parent2: List[Cidade],
) -> List[Cidade]:
    length = len(parent1)
    start_index = random.randint(0, length - 1)
    end_index = random.randint(start_index + 1, length)

    child = parent1[start_index:end_index]
    remaining_positions = [i for i in range(length) if i < start_index or i >= end_index]
    remaining_genes = [gene for gene in parent2 if gene not in child]

    for position, gene in zip(remaining_positions, remaining_genes):
        child.insert(position, gene)

    return child


def crossover_alocacao(
    alocacao1: Alocacao,
    alocacao2: Alocacao,
    path: List[Cidade],
    num_veiculos: int = NUM_VEICULOS,
) -> Alocacao:
    filho = {}
    for cidade in path:
        if random.random() < 0.5:
            filho[cidade] = alocacao1[cidade]
        else:
            filho[cidade] = alocacao2[cidade]

    return reparar_alocacao(filho, path, num_veiculos)


def crossover_vrp(
    parent1: IndividuoVRP,
    parent2: IndividuoVRP,
    num_veiculos: int = NUM_VEICULOS,
) -> IndividuoVRP:
    path1, aloc1 = parent1
    path2, aloc2 = parent2

    child_path = order_crossover(path1, path2)
    child_aloc = crossover_alocacao(aloc1, aloc2, child_path, num_veiculos)

    return child_path, child_aloc


def mutate_path(path: List[Cidade], mutation_probability: float) -> List[Cidade]:
    mutated = copy.deepcopy(path)

    if random.random() < mutation_probability and len(path) >= 2:
        index = random.randint(0, len(path) - 2)
        mutated[index], mutated[index + 1] = path[index + 1], path[index]

    return mutated


def mutate_alocacao(
    alocacao: Alocacao,
    path: List[Cidade],
    mutation_probability: float,
    num_veiculos: int = NUM_VEICULOS,
) -> Alocacao:
    alocacao = alocacao.copy()

    if random.random() < mutation_probability:
        cidade = random.choice(path)
        alocacao[cidade] = random.randint(0, num_veiculos - 1)
        alocacao = reparar_alocacao(alocacao, path, num_veiculos)

    return alocacao


def mutate_individuo(
    individuo: IndividuoVRP,
    mutation_probability: float,
    num_veiculos: int = NUM_VEICULOS,
) -> IndividuoVRP:
    path, alocacao = individuo
    path = mutate_path(path, mutation_probability)
    alocacao = mutate_alocacao(
        alocacao, path, mutation_probability, num_veiculos
    )
    return path, alocacao


def sort_population(
    population: List[IndividuoVRP],
    fitness: List[float],
) -> Tuple[List[IndividuoVRP], List[float]]:
    combined = list(zip(population, fitness))
    combined.sort(key=lambda x: x[1])
    sorted_population, sorted_fitness = zip(*combined)
    return list(sorted_population), list(sorted_fitness)
