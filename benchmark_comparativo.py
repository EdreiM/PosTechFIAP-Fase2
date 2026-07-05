"""
Comparativo de desempenho: AG vs heurísticas clássicas.

Executar: python benchmark_comparativo.py
Saída: results/benchmark_comparativo.txt (+ CSV)
"""

import csv
import math
import os
import time

import genetic_algorithm as ga
from ag_runner import executar_ag
from config import (
    CAPACIDADE_VEICULO,
    LIMITE_CIDADES_BENCHMARK,
    LIMITE_SEM_MELHORA,
    MODO_CIDADES,
    MUTATION_PROBABILITY,
    N_CIDADES,
    N_GENERATIONS,
    NUM_VEICULOS,
    POPULATION_SIZE,
    SEED,
    obter_cidades,
)
from dados_hospitalares import configurar_cenario, resumo_tipos
from genetic_algorithm import calcular_solucao_otima_vrp
from heuristics import (
    avaliar_solucao,
    greedy_prioridade,
    nearest_neighbor,
    nome_metodo,
    rota_aleatoria,
)

RESULTS_DIR = "results"


def configurar_dados(cities):
    configurar_cenario(cities, seed=SEED, n_cidades=N_CIDADES, modo=MODO_CIDADES)


def executar_metodo(nome, func, *args, **kwargs):
    inicio = time.perf_counter()
    path, alocacao = func(*args, **kwargs)
    tempo = time.perf_counter() - inicio
    metricas = avaliar_solucao(path, alocacao)
    metricas["tempo_segundos"] = tempo
    metricas["metodo"] = nome
    return metricas


def executar_ag_benchmark(cities):
    configurar_dados(cities)
    resultado = executar_ag(
        cities,
        population_size=POPULATION_SIZE,
        n_generations=N_GENERATIONS,
        mutation_probability=MUTATION_PROBABILITY,
        limite_sem_melhora=LIMITE_SEM_MELHORA,
        seed=SEED,
        num_veiculos=NUM_VEICULOS,
        verbose=False,
    )
    metricas = avaliar_solucao(resultado["path"], resultado["alocacao"])
    metricas["tempo_segundos"] = resultado["tempo_segundos"]
    metricas["metodo"] = "ag"
    metricas["geracao_convergencia"] = resultado["geracao_convergencia"]
    return metricas


def executar_otimo(cities):
    inicio = time.perf_counter()
    otimo = calcular_solucao_otima_vrp(
        cities, NUM_VEICULOS, LIMITE_CIDADES_BENCHMARK
    )
    tempo = time.perf_counter() - inicio

    if math.isnan(otimo):
        return None

    return {
        "metodo": "otimo",
        "distancia": otimo,
        "fitness": otimo,
        "viavel": True,
        "tempo_segundos": tempo,
        "geracao_convergencia": "-",
    }


def formatar_linha(r):
    viavel = "Sim" if r.get("viavel") else "Não"
    conv = r.get("geracao_convergencia", "-")
    return (
        f"{nome_metodo(r['metodo']):<28} | "
        f"Dist: {r['distancia']:>8.2f} | "
        f"Fitness: {r['fitness']:>8.2f} | "
        f"Viável: {viavel:<3} | "
        f"Tempo: {r['tempo_segundos']:>6.2f}s | "
        f"Conv: {conv}"
    )


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    cities = obter_cidades()
    configurar_dados(cities)

    print("=" * 70)
    print("BENCHMARK COMPARATIVO — AG vs Heurísticas")
    print("=" * 70)
    print(f"Cidades: {len(cities)} | Veículos: {NUM_VEICULOS} | "
          f"Capacidade: {CAPACIDADE_VEICULO} | Seed: {SEED}")
    print(f"Depósito hospitalar: {ga.DEPOT}")
    contagem = resumo_tipos(cities)
    print(
        f"Tipos: CRITICO={contagem['CRITICO']} | "
        f"REGULAR={contagem['REGULAR']} | "
        f"INSUMO={contagem['INSUMO']}"
    )
    print("-" * 70)

    resultados = []

    print("\nExecutando Algoritmo Genético...")
    resultados.append(executar_ag_benchmark(cities))

    print("Executando Rota Aleatória...")
    resultados.append(
        executar_metodo(
            "aleatoria",
            rota_aleatoria,
            cities,
            NUM_VEICULOS,
            SEED,
        )
    )

    print("Executando Vizinho Mais Próximo...")
    resultados.append(
        executar_metodo(
            "nearest_neighbor",
            nearest_neighbor,
            cities,
            ga.DEPOT,
            NUM_VEICULOS,
            ga.city_demands,
            CAPACIDADE_VEICULO,
        )
    )

    print("Executando Greedy por Prioridade...")
    resultados.append(
        executar_metodo(
            "greedy_prioridade",
            greedy_prioridade,
            cities,
            ga.city_priorities,
            NUM_VEICULOS,
            ga.city_demands,
            CAPACIDADE_VEICULO,
        )
    )

    print("Calculando Ótimo (força bruta)...")
    otimo = executar_otimo(cities)
    if otimo:
        resultados.append(otimo)
    else:
        print(
            f"  Ótimo omitido: mais de {LIMITE_CIDADES_BENCHMARK} cidades."
        )

    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)

    linhas_txt = []
    for r in resultados:
        linha = formatar_linha(r)
        print(linha)
        linhas_txt.append(linha)

    melhor = min(resultados, key=lambda r: r["distancia"])
    print("-" * 70)
    print(f"Melhor distância: {nome_metodo(melhor['metodo'])} "
          f"({melhor['distancia']:.2f})")

    ag = next(r for r in resultados if r["metodo"] == "ag")
    aleatoria = next(r for r in resultados if r["metodo"] == "aleatoria")
    economia = aleatoria["distancia"] - ag["distancia"]
    print(f"Economia AG vs Aleatória: {economia:.2f} "
          f"({economia / aleatoria['distancia'] * 100:.1f}%)")

    txt_path = os.path.join(RESULTS_DIR, "benchmark_comparativo.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("BENCHMARK COMPARATIVO — AG vs Heurísticas\n")
        f.write("=" * 70 + "\n")
        f.write(f"Cidades: {len(cities)} | Veículos: {NUM_VEICULOS}\n")
        f.write(f"Depósito: {ga.DEPOT}\n\n")
        for linha in linhas_txt:
            f.write(linha + "\n")
        f.write(f"\nMelhor: {nome_metodo(melhor['metodo'])} "
                f"({melhor['distancia']:.2f})\n")
        f.write(f"Economia AG vs Aleatória: {economia:.2f}\n")

    csv_path = os.path.join(RESULTS_DIR, "benchmark_comparativo.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "metodo", "distancia", "fitness", "viavel",
                "tempo_segundos", "geracao_convergencia",
            ],
        )
        writer.writeheader()
        for r in resultados:
            writer.writerow({
                "metodo": r["metodo"],
                "distancia": f"{r['distancia']:.2f}",
                "fitness": f"{r['fitness']:.2f}",
                "viavel": r.get("viavel", False),
                "tempo_segundos": f"{r['tempo_segundos']:.2f}",
                "geracao_convergencia": r.get("geracao_convergencia", ""),
            })

    print(f"\nResultados salvos em {txt_path} e {csv_path}")


if __name__ == "__main__":
    main()
