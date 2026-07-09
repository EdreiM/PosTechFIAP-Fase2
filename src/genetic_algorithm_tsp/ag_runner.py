"""
Execução do Algoritmo Genético sem interface gráfica.

Usado por benchmark_comparativo.py, experimentos_ag.py e tsp.py.
"""

import random
import time
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

import genetic_algorithm as ga
from genetic_algorithm import (
    Alocacao,
    Cidade,
    IndividuoVRP,
    calculate_fitness_individuo,
    calcular_distancia_operacao,
    crossover_vrp,
    generate_random_population,
    mutate_individuo,
    sort_population,
)


def executar_ag(
    cities_locations: List[Cidade],
    population_size: int,
    n_generations: int,
    mutation_probability: float,
    limite_sem_melhora: int,
    seed: int = 42,
    num_veiculos: int = ga.NUM_VEICULOS,
    verbose: bool = False,
    callback: Optional[Callable[[int, IndividuoVRP, float], bool]] = None,
) -> Dict:
    """
    Executa o AG completo e retorna métricas da melhor solução encontrada.

    callback(generation, best_individual, best_fitness) é chamado a cada geração.
    Se retornar False, a execução é interrompida (usado pelo Pygame).
    """
    random.seed(seed)
    np.random.seed(seed)

    population = generate_random_population(
        cities_locations, population_size, num_veiculos
    )

    best_fitness_values: List[float] = []
    best_solutions: List[IndividuoVRP] = []
    melhor_fitness_global = float("inf")
    geracoes_sem_melhora = 0
    fitness_inicial = None
    distancia_inicial = None
    geracao_convergencia = None

    inicio = time.perf_counter()

    for generation in range(1, n_generations + 1):
        population_fitness = [
            calculate_fitness_individuo(ind, num_veiculos) for ind in population
        ]
        population, population_fitness = sort_population(
            population, population_fitness
        )

        best_fitness = population_fitness[0]
        best_individual = population[0]

        if best_fitness < melhor_fitness_global:
            melhor_fitness_global = best_fitness
            geracoes_sem_melhora = 0
        else:
            geracoes_sem_melhora += 1

        if fitness_inicial is None:
            fitness_inicial = best_fitness
            best_path, best_aloc = best_individual
            distancia_inicial = calcular_distancia_operacao(
                best_path, best_aloc, num_veiculos
            )

        best_fitness_values.append(best_fitness)
        best_solutions.append(best_individual)

        if callback:
            continuar = callback(generation, best_individual, best_fitness)
            if continuar is False:
                geracao_convergencia = generation
                break

        if verbose and generation % 50 == 0:
            print(
                f"  Geração {generation}: fitness={best_fitness:.2f} | "
                f"sem melhora={geracoes_sem_melhora}"
            )

        if geracoes_sem_melhora >= limite_sem_melhora:
            geracao_convergencia = generation
            if verbose:
                print(f"  Convergência na geração {generation}")
            break

        new_population = [population[0]]
        probability = 1 / np.array(population_fitness)

        while len(new_population) < population_size:
            parent1, parent2 = random.choices(
                population, weights=probability, k=2
            )
            child = crossover_vrp(parent1, parent2, num_veiculos)
            child = mutate_individuo(child, mutation_probability, num_veiculos)
            new_population.append(child)

        population = new_population

    tempo_segundos = time.perf_counter() - inicio

    if geracao_convergencia is None:
        geracao_convergencia = len(best_fitness_values)

    best_path, best_alocacao = best_solutions[-1]
    fitness_final_prioridade = best_fitness_values[-1]
    fitness_final = calcular_distancia_operacao(
        best_path, best_alocacao, num_veiculos
    )

    melhoria_fitness = (
        (fitness_inicial - fitness_final_prioridade) / fitness_inicial * 100
        if fitness_inicial
        else 0.0
    )
    melhoria_distancia = (
        (distancia_inicial - fitness_final) / distancia_inicial * 100
        if distancia_inicial
        else 0.0
    )

    return {
        "path": best_path,
        "alocacao": best_alocacao,
        "fitness_final": fitness_final,
        "fitness_final_prioridade": fitness_final_prioridade,
        "fitness_inicial": fitness_inicial,
        "distancia_inicial": distancia_inicial,
        "melhoria_fitness_pct": melhoria_fitness,
        "melhoria_distancia_pct": melhoria_distancia,
        "geracao_convergencia": geracao_convergencia,
        "geracoes_executadas": len(best_fitness_values),
        "best_fitness_values": best_fitness_values,
        "tempo_segundos": tempo_segundos,
    }
