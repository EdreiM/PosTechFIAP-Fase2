import math

from groq_utils import chamar_llm


def _fallback_analisar(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    melhoria_fitness,
    melhoria_distancia,
    fitness_target_solution,
    diferenca_benchmark,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    total_cidades,
    num_veiculos,
    distancia_aleatoria,
):
    otimo = (
        f"{fitness_target_solution:.2f} km"
        if not math.isnan(fitness_target_solution)
        else "N/A (muitas cidades para força bruta)"
    )
    diff_otimo = (
        f"{diferenca_benchmark:.2f}%"
        if not math.isnan(diferenca_benchmark)
        else "N/A"
    )
    economia_aleatoria = max(distancia_aleatoria - fitness_final, 0)

    if math.isnan(fitness_target_solution):
        nota_otimo = (
            "Ótimo VRP não calculado (problema grande demais para força bruta) — "
            "use a tabela comparativa acima (AG vs heurísticas)."
        )
    else:
        nota_otimo = (
            f"Referência ótima VRP: {otimo} (diferença: {diff_otimo})."
        )

    linha_economia = (
        f"Economia estimada vs. rota aleatória: {economia_aleatoria:.0f} km."
        if economia_aleatoria > 0
        else ""
    )

    return f"""1. Convergência
O AG estabilizou na geração {geracao_convergencia} (fitness {fitness_inicial:.0f} → {fitness_final_prioridade:.0f}, melhoria de {melhoria_fitness:.1f}%).

2. Prioridades clínicas
{prioridade_10} entregas com prioridade 10; {prioridade_9_10} com prioridade 9–10.
Média de prioridade nas 10 primeiras posições da rota: {media_top10:.1f}.

3. Conclusão
{total_cidades} entregas em {num_veiculos} veículos. {nota_otimo}
{linha_economia}
Interpretação gerada localmente — métricas numéricas na tabela acima.
"""


def analisar_resultado(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    melhoria_fitness,
    melhoria_distancia,
    fitness_target_solution,
    diferenca_benchmark,
    top10_prioridades,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    total_cidades,
    num_veiculos,
    distancia_aleatoria,
):
    otimo_txt = (
        f"{fitness_target_solution:.2f}"
        if not math.isnan(fitness_target_solution)
        else "N/A"
    )
    diff_txt = (
        f"{diferenca_benchmark:.2f}%"
        if not math.isnan(diferenca_benchmark)
        else "N/A"
    )

    prompt = f"""
Analise tecnicamente os resultados de um Algoritmo Genético aplicado ao VRP hospitalar.

Dados:

Fitness inicial: {fitness_inicial:.2f}
Fitness final (com prioridades e restrições): {fitness_final_prioridade:.2f}
Distância total da operação ({num_veiculos} veículos): {fitness_final:.2f}
Melhoria do fitness: {melhoria_fitness:.2f}%
Melhoria da distância: {melhoria_distancia:.2f}%
Solução ótima VRP (força bruta): {otimo_txt}
Diferença para o ótimo: {diff_txt}
Distância de rota aleatória: {distancia_aleatoria:.2f}
Geração de convergência: {geracao_convergencia}
Total de cidades: {total_cidades}
Veículos disponíveis: {num_veiculos}

Prioridades nas 10 primeiras posições: {top10_prioridades}
Média das prioridades (top 10): {media_top10:.2f}
Cidades com prioridade 10: {prioridade_10}
Cidades com prioridade 9 ou 10: {prioridade_9_10}

Parâmetros: população 100, gerações 1000, mutação 0.5.

Nota: o AG otimiza VRP com {num_veiculos} veículos, prioridades, capacidade e autonomia por veículo.

Gere uma análise técnica CURTA com exatamente estas seções:

1. Qualidade da solução
2. Convergência
3. Prioridades
4. Benchmark (compare AG vs rota aleatória vs ótimo VRP)
5. Conclusão

Regras:
- Máximo 250 palavras no total.
- Linguagem técnica e direta, sem tom acadêmico.
- NÃO liste cidades.
- NÃO gere plano de entrega.
- NÃO analise a rota completa cidade por cidade.
- Use apenas os dados fornecidos.
"""

    return chamar_llm(
        prompt,
        lambda: _fallback_analisar(
            fitness_inicial,
            fitness_final,
            fitness_final_prioridade,
            melhoria_fitness,
            melhoria_distancia,
            fitness_target_solution,
            diferenca_benchmark,
            geracao_convergencia,
            prioridade_10,
            prioridade_9_10,
            media_top10,
            total_cidades,
            num_veiculos,
            distancia_aleatoria,
        ),
    )
