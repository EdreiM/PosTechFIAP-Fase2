import math

from groq_utils import chamar_llm


def _fallback_relatorio(
    fitness_final,
    melhoria_distancia,
    diferenca_benchmark,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    texto_veiculos,
    total_cidades,
    num_veiculos,
    distancia_aleatoria,
    fitness_target_solution,
    texto_remanescentes="",
):
    diff_otimo = (
        f"{diferenca_benchmark:.2f}%"
        if not math.isnan(diferenca_benchmark)
        else "N/A"
    )
    otimo = (
        f"{fitness_target_solution:.0f} km"
        if not math.isnan(fitness_target_solution)
        else "N/A"
    )

    return f"""1. Resumo
Operação diária concluída: {total_cidades} entregas com {num_veiculos} veículos.
Distância total: {fitness_final:.0f} km.

2. Eficiência da rota
Melhoria de distância vs. início do AG: {melhoria_distancia:.1f}%.
Comparativo: AG {fitness_final:.0f} km | Aleatória {distancia_aleatoria:.0f} km | Ótimo {otimo}.

3. Capacidade dos veículos
{texto_veiculos}

4. Autonomia dos veículos
Ver distância por veículo acima (limite configurado na simulação).

5. Prioridades atendidas
{prioridade_10} entregas prioridade 10; {prioridade_9_10} com prioridade 9–10.
Média nas 10 primeiras posições: {media_top10:.1f}.
Diferença para ótimo VRP: {diff_otimo}.

6. Kits remanescentes no hospital
{texto_remanescentes if texto_remanescentes.strip() else "Nenhum kit remanescente — frota absorveu toda a demanda."}

7. Recomendações
Informar unidades com kits pendentes no hospital; avaliar reforço de frota se remanescentes forem críticos.
Relatório gerado localmente — IA Groq indisponível no momento.
"""


def gerar_relatorio_operacional(
    fitness_final,
    melhoria_distancia,
    diferenca_benchmark,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    texto_veiculos,
    total_cidades,
    num_veiculos,
    distancia_aleatoria,
    fitness_target_solution,
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
Você é um analista logístico hospitalar.

Gere um RELATÓRIO OPERACIONAL DIÁRIO de fechamento da operação de entregas.

Dados gerais:

Total de cidades: {total_cidades}
Veículos em operação: {num_veiculos}
Distância total da operação: {fitness_final:.2f}
Melhoria da distância vs início: {melhoria_distancia:.2f}%
Comparativo VRP -> AG: {fitness_final:.2f} | Aleatória: {distancia_aleatoria:.2f} | Ótimo: {otimo_txt}
Diferença para ótimo VRP: {diff_txt}
Cidades com prioridade 10: {prioridade_10}
Cidades com prioridade 9 ou 10: {prioridade_9_10}
Média das prioridades (10 primeiras posições): {media_top10:.2f}

Status por veículo (avalie CADA veículo individualmente):

{texto_veiculos}

Gere exatamente estas seções:

1. Resumo
2. Eficiência da rota
3. Capacidade dos veículos
4. Autonomia dos veículos
5. Prioridades atendidas
6. Recomendações (melhorias no processo para o próximo dia/semana)

Regras:
- Máximo 300 palavras no total.
- Avalie capacidade e autonomia POR VEÍCULO, não pelo total da operação.
- Na seção Recomendações, sugira melhorias práticas (ex.: redistribuir cidades críticas, usar mais veículos, ajustar peso de prioridade).
- Linguagem operacional e direta.
- NÃO liste todas as cidades.
- NÃO repita análise de convergência ou benchmark longo.
- NÃO use linguagem acadêmica.
"""

    return chamar_llm(
        prompt,
        lambda: _fallback_relatorio(
            fitness_final,
            melhoria_distancia,
            diferenca_benchmark,
            prioridade_10,
            prioridade_9_10,
            media_top10,
            texto_veiculos,
            total_cidades,
            num_veiculos,
            distancia_aleatoria,
            fitness_target_solution,
        ),
    )
