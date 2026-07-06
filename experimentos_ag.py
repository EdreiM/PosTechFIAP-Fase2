"""
Três experimentos com configurações diferentes do Algoritmo Genético.

Executar: python experimentos_ag.py
Saída: results/experimentos_ag.txt + results/experimentos_convergencia.png
"""

import os

import matplotlib
import matplotlib.pyplot as plt

import genetic_algorithm as ga
from ag_runner import executar_ag
from config import (
    EXPERIMENTOS_AG,
    LIMITE_SEM_MELHORA,
    MODO_CIDADES,
    N_CIDADES,
    NUM_VEICULOS,
    SEED,
    obter_cidades,
)
from dados_hospitalares import configurar_cenario, resumo_tipos

matplotlib.use("Agg")

RESULTS_DIR = "results"


def configurar_dados(cities):
    configurar_cenario(cities, seed=SEED, n_cidades=N_CIDADES, modo=MODO_CIDADES)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    cities = obter_cidades()
    configurar_dados(cities)

    print("=" * 70)
    print("EXPERIMENTOS DO ALGORITMO GENÉTICO")
    print("=" * 70)
    print(f"Cidades: {len(cities)} | Veículos: {NUM_VEICULOS} | Seed: {SEED}")
    print(f"Depósito hospitalar: {ga.DEPOT}")
    contagem = resumo_tipos(cities)
    print(
        f"Tipos: CRITICO={contagem['CRITICO']} | "
        f"REGULAR={contagem['REGULAR']} | "
        f"INSUMO={contagem['INSUMO']}"
    )
    print("-" * 70)

    resultados = []
    linhas_txt = []

    for exp in EXPERIMENTOS_AG:
        print(f"\n>>> Experimento {exp['nome']}")
        print(f"    População: {exp['population_size']} | "
              f"Mutação: {exp['mutation_probability']} | "
              f"Gerações: {exp['n_generations']}")

        resultado = executar_ag(
            cities,
            population_size=exp["population_size"],
            n_generations=exp["n_generations"],
            mutation_probability=exp["mutation_probability"],
            limite_sem_melhora=LIMITE_SEM_MELHORA,
            seed=SEED,
            num_veiculos=NUM_VEICULOS,
            verbose=True,
        )

        resultado["nome"] = exp["nome"]
        resultados.append(resultado)

        linha = (
            f"{exp['nome']:<18} | "
            f"Pop: {exp['population_size']:>3} | "
            f"Mut: {exp['mutation_probability']:.1f} | "
            f"Dist: {resultado['fitness_final']:>8.2f} | "
            f"Conv: {resultado['geracao_convergencia']:>4} | "
            f"Tempo: {resultado['tempo_segundos']:>5.1f}s"
        )
        print(f"    {linha}")
        linhas_txt.append(linha)

    melhor = min(resultados, key=lambda r: r["fitness_final"])

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    for linha in linhas_txt:
        print(linha)
    print("-" * 70)
    print(f"Melhor experimento: {melhor['nome']} "
          f"(distância {melhor['fitness_final']:.2f})")

    fig, ax = plt.subplots(figsize=(10, 6))
    cores = ["#2563eb", "#dc2626", "#16a34a"]

    for i, r in enumerate(resultados):
        ax.plot(
            range(1, len(r["best_fitness_values"]) + 1),
            r["best_fitness_values"],
            label=r["nome"],
            color=cores[i % len(cores)],
            linewidth=2,
        )

    ax.set_xlabel("Geração")
    ax.set_ylabel("Fitness (distância + restrições)")
    ax.set_title(
        f"Convergência do AG — {len(cities)} cidades, "
        f"{NUM_VEICULOS} veículos"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    png_path = os.path.join(RESULTS_DIR, "experimentos_convergencia.png")
    plt.savefig(png_path, dpi=150)
    plt.close()
    print(f"\nGráfico salvo em {png_path}")

    txt_path = os.path.join(RESULTS_DIR, "experimentos_ag.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("EXPERIMENTOS DO ALGORITMO GENÉTICO\n")
        f.write("=" * 70 + "\n")
        f.write(f"Cidades: {len(cities)} | Veículos: {NUM_VEICULOS}\n")
        f.write(f"Depósito: {ga.DEPOT}\n\n")
        for linha in linhas_txt:
            f.write(linha + "\n")
        f.write(f"\nMelhor: {melhor['nome']} ({melhor['fitness_final']:.2f})\n")

    print(f"Resultados salvos em {txt_path}")


if __name__ == "__main__":
    main()
