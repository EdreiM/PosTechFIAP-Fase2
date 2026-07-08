"""
Dados de apoio para os testes — um único lugar para cenários reutilizáveis.

Dois tipos de dado (não confundir):

1. MODO FIXO DO SISTEMA (função configurar_cenario_fixo)
   - Espelha a opção "fixo" da janela de configuração.
   - Nomes, kits e prioridades vêm de tabelas em dados_hospitalares.py.
   - A seed NÃO altera esses valores — ideal para testes reprodutíveis.

2. TEXTOS SIMULADOS (CENARIO_CHAT_*, CENARIO_REGRESSAO_18)
   - Copiam o formato de saída do tsp.py (texto_veiculos, rotas).
   - Servem para testar chat/IA sem rodar simulação + Pygame.
   - Não precisam bater com uma execução ao vivo — só com o formato esperado.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import genetic_algorithm as ga
from config import DEFAULT_PROBLEMS
from dados_hospitalares import configurar_cenario

Cidade = Tuple[float, float]

# ---------------------------------------------------------------------------
# AG mínimo (4 pontos em quadrado — testes rápidos de VRP)
# ---------------------------------------------------------------------------

CIDADES_AG_MINI: List[Cidade] = [(0, 0), (10, 0), (10, 10), (0, 10)]


def configurar_dados_ag_mini() -> None:
    """Preenche prioridades/demandas para CIDADES_AG_MINI."""
    ga.city_priorities.clear()
    ga.city_demands.clear()
    ga.city_names.clear()
    ga.city_types.clear()
    for cidade in CIDADES_AG_MINI:
        ga.city_priorities[cidade] = 5
        ga.city_demands[cidade] = 10


def configurar_cenario_fixo(n_entregas: int, seed: int = 42) -> List[Cidade]:
    """
    Monta o cenário hospitalar no modo fixo (como na demo com seed 42).

    n_entregas: 5, 10, 12 ou 15 (valores disponíveis em DEFAULT_PROBLEMS).
    Retorna a lista de coordenadas já registrada em genetic_algorithm.
    """
    cities = DEFAULT_PROBLEMS[n_entregas].copy()
    configurar_cenario(cities, seed=seed, n_cidades=n_entregas, modo="fixo")
    return cities


# ---------------------------------------------------------------------------
# Chat — veículo 3 (5 paradas, foco em prioridade p10 vs última parada p4)
# ---------------------------------------------------------------------------

CHAT_V3_VEICULOS = (
    "Veículo 3 | 5 entregas | carga 79/80 | distância 831/1500 | status: ok\n"
)

CHAT_V3_ROTAS = """
Rotas por veículo (Hospital Central → paradas → Hospital Central):

Veículo 3 (5 paradas):
  1ª parada: Unidade Domiciliar 11 [CRITICO] (10 prioridade, 12 kits)
  2ª parada: Unidade de Hemodiálise 5 [CRITICO] (8 prioridade, 10 kits)
  3ª parada: Home Care 10 [CRITICO] (9 prioridade, 8 kits)
  4ª parada: Unidade Pediátrica 18 [INSUMO] (1 prioridade, 20 kits)
  5ª parada: Unidade de Hemodiálise 15 [REGULAR] (4 prioridade, 14 kits)
  Última parada do veículo 3: Unidade de Hemodiálise 15 [REGULAR]
"""


# ---------------------------------------------------------------------------
# Chat — veículo 2 (3 paradas — perguntas de carga e "quantas de cada?")
# ---------------------------------------------------------------------------

CHAT_V2_VEICULOS = (
    "Veículo 2 | 3 entregas | carga 34/40 | distância 520/1500 | "
    "status: operacionalmente viável\n"
)

CHAT_V2_ROTAS = """
Rotas por veículo (Hospital Central → paradas → Hospital Central):

Veículo 2 (3 paradas):
  1ª parada: Farmácia Central [CRITICO] (8 prioridade, 8 kits)
  2ª parada: UTI Norte [CRITICO] (10 prioridade, 12 kits)
  3ª parada: Lab. Análises Clínicas [REGULAR] (7 prioridade, 14 kits)
  Última parada do veículo 2: Lab. Análises Clínicas [REGULAR]
"""


# ---------------------------------------------------------------------------
# Regressão — snapshot de demo com 18 entregas (modo aleatório, cap. 80)
# Usado em TestRegressaoBugsUsuario para bugs encontrados em teste manual.
# Nota: V4 com 81/80 no snapshot original é cenário PRÉ-priorização (autonomia);
#       testes de capacidade usam linha já corrigida (60/80).
# ---------------------------------------------------------------------------

REGRESSAO_18_VEICULOS = (
    "Veículo 1 | 4 entregas | carga 71/80 | distância 571/1500 | status: operacionalmente viável\n"
    "Veículo 2 | 4 entregas | carga 63/80 | distância 776/1500 | status: operacionalmente viável\n"
    "Veículo 3 | 5 entregas | carga 79/80 | distância 831/1500 | status: operacionalmente viável\n"
    "Veículo 4 | 5 entregas | carga 81/80 | distância 728/1500 | status: com restrição\n"
)

REGRESSAO_18_ROTAS = """
Rotas por veículo (Hospital Central → paradas → Hospital Central):

Veículo 3 (5 paradas):
  1ª parada: Unidade Domiciliar 11 [CRITICO] (10 prioridade, 12 kits)
  2ª parada: Unidade de Hemodiálise 5 [CRITICO] (8 prioridade, 10 kits)
  3ª parada: Home Care 10 [CRITICO] (9 prioridade, 8 kits)
  4ª parada: Unidade Pediátrica 18 [INSUMO] (1 prioridade, 20 kits)
  5ª parada: Unidade de Hemodiálise 15 [REGULAR] (4 prioridade, 14 kits)
  Última parada do veículo 3: Unidade de Hemodiálise 15 [REGULAR]

Veículo 4 (5 paradas):
  1ª parada: Unidade Domiciliar 1 [CRITICO] (9 prioridade, 10 kits)
  2ª parada: Posto de Saúde 2 [REGULAR] (5 prioridade, 16 kits)
  3ª parada: Ambulatório de Especialidades 16 [REGULAR] (6 prioridade, 18 kits)
  4ª parada: Centro de Cardiologia 9 [REGULAR] (5 prioridade, 16 kits)
  5ª parada: Posto de Saúde 12 [INSUMO] (3 prioridade, 22 kits)
  Última parada do veículo 4: Posto de Saúde 12 [INSUMO]
"""

REGRESSAO_18_VEICULO_4_POS_PRIORIZACAO = (
    "Veículo 4 | 3 entregas | carga 60/80 | distância 728/1500 | "
    "status: operacionalmente viável\n"
)


def kwargs_groq_conteudo_18_entregas() -> Dict:
    """Parâmetros para gerar_conteudo_completo no cenário de 18 entregas."""
    return dict(
        fitness_inicial=6914.0,
        fitness_final=2905.56,
        fitness_final_prioridade=4859.0,
        melhoria_fitness=39.54,
        melhoria_distancia=44.14,
        fitness_target_solution=float("nan"),
        diferenca_benchmark=float("nan"),
        top10_prioridades=[10, 9, 9, 8, 7, 6, 5, 4, 3, 2],
        geracao_convergencia=646,
        prioridade_10=1,
        prioridade_9_10=5,
        media_top10=7.9,
        total_cidades=18,
        num_veiculos=4,
        distancia_aleatoria=6914.0,
        texto_veiculos=REGRESSAO_18_VEICULOS,
        texto_rotas_detalhado=REGRESSAO_18_ROTAS,
        texto_resumo_semanal="Projeção semanal — 18 entregas × 5 dias",
        capacidade_veiculo=80,
        distancia_maxima_veiculo=1500,
    )


def kwargs_fallback_analise_18_entregas() -> Dict:
    """Subconjunto para _fallback_analisar (cenário 18 entregas, ótimo N/A)."""
    k = kwargs_groq_conteudo_18_entregas()
    for chave in (
        "top10_prioridades",
        "texto_veiculos",
        "texto_rotas_detalhado",
        "texto_resumo_semanal",
        "capacidade_veiculo",
        "distancia_maxima_veiculo",
    ):
        k.pop(chave)
    return k
