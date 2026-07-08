from groq_utils import chamar_llm


def _fallback_relatorio_semanal(texto_resumo_semanal):
    return f"""1. Projeção semanal (5 dias úteis)
{texto_resumo_semanal}

2. Tendências
Estimativa baseada em 1 dia otimizado replicado — não é histórico real de operação.

3. Recomendações estratégicas
Revisar alocação de entregas críticas e capacidade por veículo na próxima semana.
Status operacional diário: aba Veículos.
Relatório semanal gerado localmente — IA Groq indisponível no momento.
"""


def gerar_relatorio_semanal(
    texto_resumo_semanal,
    texto_veiculos,
    relatorio_diario,
):
    prompt = f"""
Você é um analista logístico hospitalar.

Gere um RELATÓRIO OPERACIONAL SEMANAL consolidado sobre entregas de medicamentos e insumos.

IMPORTANTE — natureza dos dados:
- Os números são uma PROJEÇÃO SEMANAL (1 dia de operação otimizada × 5 dias úteis).
- NÃO trate como histórico real de 5 dias distintos.
- Deixe claro no texto que é estimativa/projeção baseada na rota otimizada pelo AG.
- Todas as rotas partem e retornam ao depósito hospitalar (Hospital Central).
- Existem tipos de entrega: CRITICO (medicamentos críticos), REGULAR e INSUMO.

Dados consolidados da semana (projeção):

{texto_resumo_semanal}

Status por veículo (referência da operação diária):

{texto_veiculos}

Referência do fechamento diário mais recente:

{relatorio_diario}

Gere exatamente estas seções:

1. Resumo da semana (mencione que é projeção)
2. Eficiência acumulada das rotas
3. Economia de tempo e recursos
4. Padrões identificados (prioridades, tipos CRITICO/REGULAR/INSUMO, uso da frota)
5. Recomendações estratégicas (próxima semana)

Regras:
- Máximo 350 palavras no total.
- Foque em tendências, padrões e economia — não repita o relatório diário.
- Avalie capacidade e autonomia por veículo quando relevante.
- Mencione o depósito hospitalar e a distinção entre entregas críticas e insumos.
- Sugira melhorias de processo com base nos padrões (ex.: redistribuição, frota, prioridades).
- Linguagem operacional e direta.
- Use "entregas" ou "unidades hospitalares", não "cidades".
- NÃO liste todas as unidades.
- NÃO use linguagem acadêmica.
- NÃO afirme que houve 5 dias reais de operação — sempre deixe claro que é projeção.
"""

    return chamar_llm(
        prompt,
        lambda: _fallback_relatorio_semanal(texto_resumo_semanal),
    )
