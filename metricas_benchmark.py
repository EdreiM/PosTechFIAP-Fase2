"""
Métricas comparativas entre métodos de roteamento (AG, heurísticas, ótimo).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from config import DEPOT, LIMITE_CIDADES_BENCHMARK
from genetic_algorithm import Cidade, calcular_distancia_operacao
from heuristics import greedy_prioridade, nearest_neighbor


def motivo_omissao_benchmark(
    num_veiculos: int,
    total_entregas: int,
    limite_cidades: int = LIMITE_CIDADES_BENCHMARK,
    fitness_target_solution: float = float("nan"),
) -> str:
    """Motivo textual quando o ótimo VRP não foi calculado; vazio se calculado."""
    if not math.isnan(fitness_target_solution):
        return ""
    if num_veiculos > total_entregas:
        return (
            f"{num_veiculos} veículos para {total_entregas} entregas "
            f"(requer veículos ≤ entregas)"
        )
    if total_entregas >= limite_cidades:
        return (
            f"{total_entregas} entregas (≥ {limite_cidades}): "
            "limitações computacionais (força bruta omitida)"
        )
    return "condições do cenário não permitem cálculo exato"


def _economia_vs_ag(dist_referencia: float, dist_ag: float) -> Tuple[float, float]:
    economia_km = max(dist_referencia - dist_ag, 0.0)
    economia_pct = (economia_km / dist_referencia * 100) if dist_referencia > 0 else 0.0
    return economia_km, economia_pct


def calcular_distancias_heuristicas(
    cities: List[Cidade],
    num_veiculos: int,
    depot: Cidade = DEPOT,
) -> Tuple[float, float]:
    """Retorna (vizinho_mais_proximo, greedy_prioridade) em km."""
    path_nn, aloc_nn = nearest_neighbor(cities, depot, num_veiculos)
    dist_nn = calcular_distancia_operacao(path_nn, aloc_nn, num_veiculos)
    path_gr, aloc_gr = greedy_prioridade(cities, num_veiculos=num_veiculos)
    dist_gr = calcular_distancia_operacao(path_gr, aloc_gr, num_veiculos)
    return dist_nn, dist_gr


@dataclass
class MetricasComparativoMetodos:
    """Métricas disponíveis após execução do AG e benchmarks auxiliares."""

    fitness_inicial: float
    distancia_inicial: float
    fitness_final: float
    fitness_final_prioridade: float
    melhoria_fitness_pct: float
    melhoria_distancia_pct: float
    geracao_convergencia: int
    distancia_aleatoria: float
    distancia_vizinho_proximo: float
    distancia_greedy_prioridade: float
    fitness_target_solution: float
    diferenca_benchmark_pct: float
    num_veiculos: int
    total_entregas: int
    motivo_otimo_omitido: str = ""

    @property
    def otimo_calculado(self) -> bool:
        return not math.isnan(self.fitness_target_solution)


def montar_bloco_analise_metricas(metricas: MetricasComparativoMetodos) -> str:
    """Bloco determinístico com todas as métricas para a aba Análise."""
    m = metricas
    linhas = [
        "MÉTRICAS DO ALGORITMO GENÉTICO",
        "─" * 40,
        f"Fitness inicial (distância + penalidades): {m.fitness_inicial:.2f}",
        f"Distância inicial (população):            {m.distancia_inicial:.2f} km",
        f"Fitness final (distância + penalidades):  {m.fitness_final_prioridade:.2f}",
        f"Distância final da operação (AG):         {m.fitness_final:.2f} km",
        f"Melhoria de fitness:                      {m.melhoria_fitness_pct:.2f}%",
        f"Melhoria de distância:                    {m.melhoria_distancia_pct:.2f}%",
        f"Geração de convergência:                    {m.geracao_convergencia}",
        "",
        "COMPARATIVO DE MÉTODOS (distância em km)",
        "─" * 40,
        f"{'Método':<32} {'Distância':>10}",
        f"{'AG (solução final)':<32} {m.fitness_final:>10.2f}",
    ]

    metodos_ref = [
        ("Rota aleatória", m.distancia_aleatoria),
        ("Vizinho mais próximo", m.distancia_vizinho_proximo),
        ("Greedy por prioridade", m.distancia_greedy_prioridade),
    ]
    for nome, dist in metodos_ref:
        if not math.isnan(dist):
            linhas.append(f"{nome:<32} {dist:>10.2f}")

    if m.otimo_calculado:
        linhas.append(
            f"{'Ótimo VRP (força bruta)':<32} {m.fitness_target_solution:>10.2f}"
        )
    else:
        linhas.append(f"{'Ótimo VRP (força bruta)':<32} {'N/A':>10}")

    linhas.extend(["", "ANÁLISE RELATIVA (referência vs AG)", "─" * 40])

    for nome, dist in metodos_ref:
        if not math.isnan(dist) and dist > 0:
            km, pct = _economia_vs_ag(dist, m.fitness_final)
            linhas.append(f"Economia vs {nome:<22} {km:>6.0f} km ({pct:.1f}%)")

    if m.otimo_calculado and not math.isnan(m.diferenca_benchmark_pct):
        linhas.append(f"Diferença AG vs ótimo:              {m.diferenca_benchmark_pct:>6.2f}%")
    elif m.motivo_otimo_omitido:
        linhas.append(f"Ótimo omitido: {m.motivo_otimo_omitido}")
        linhas.append(
            "Nota: omissão do ótimo não indica falha do AG — "
            "compare com as heurísticas acima."
        )

    linhas.extend([
        "",
        f"Frota: {m.num_veiculos} veículos | Entregas: {m.total_entregas}",
    ])

    return "\n".join(linhas)
