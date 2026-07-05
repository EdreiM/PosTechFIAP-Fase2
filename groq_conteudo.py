"""Gera análise, relatórios e instruções em uma única chamada à Groq (economiza tokens)."""

import math
import re
from typing import Dict

from groq_analysis import _fallback_analisar
from groq_relatorio import _fallback_relatorio
from groq_relatorio_semanal import _fallback_relatorio_semanal
from groq_rotas import _fallback_instrucoes
from groq_contexto import bloco_contexto_para_prompt
from groq_utils import chamar_llm

_MARCADORES = (
    "ANALISE",
    "RELATORIO_DIARIO",
    "RELATORIO_SEMANAL",
    "INSTRUCOES",
)

# Linhas eco do prompt que a LLM às vezes repete dentro das seções
_ECO_SECAO = re.compile(
    r"^("
    r"Análise técnica.*|"
    r"Relatório operacional diário.*|"
    r"Relatório semanal PROJETADO.*|"
    r"Instruções para motoristas.*|"
    r"Relatório operacional diário \(máx\..*|"
    r"Relatório semanal PROJETADO \(máx\..*"
    r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _limpar_secao(texto: str) -> str:
    if not texto:
        return texto
    linhas = [ln for ln in texto.splitlines() if not _ECO_SECAO.match(ln.strip())]
    return "\n".join(linhas).strip()


def _parse_resposta_combinada(texto: str) -> Dict[str, str]:
    partes: Dict[str, str] = {}
    for indice, nome in enumerate(_MARCADORES):
        padrao = rf"===\s*{nome}\s*==="
        matches = list(re.finditer(padrao, texto, flags=re.IGNORECASE))
        if not matches:
            continue
        inicio = matches[-1].end()
        fim = len(texto)
        for proximo in _MARCADORES[indice + 1 :]:
            m = re.search(rf"===\s*{proximo}\s*===", texto[inicio:], flags=re.IGNORECASE)
            if m:
                fim = inicio + m.start()
                break
        conteudo = texto[inicio:fim].strip()
        if conteudo:
            partes[nome.lower()] = conteudo

    return {
        "analise": _limpar_secao(partes.get("analise", "")),
        "relatorio": _limpar_secao(partes.get("relatorio_diario", "")),
        "relatorio_semanal": _limpar_secao(partes.get("relatorio_semanal", "")),
        "instrucoes": _limpar_secao(partes.get("instrucoes", "")),
    }


def _fallback_completo(**kwargs) -> Dict[str, str]:
    analise = _fallback_analisar(
        kwargs["fitness_inicial"],
        kwargs["fitness_final"],
        kwargs["fitness_final_prioridade"],
        kwargs["melhoria_fitness"],
        kwargs["melhoria_distancia"],
        kwargs["fitness_target_solution"],
        kwargs["diferenca_benchmark"],
        kwargs["geracao_convergencia"],
        kwargs["prioridade_10"],
        kwargs["prioridade_9_10"],
        kwargs["media_top10"],
        kwargs["total_cidades"],
        kwargs["num_veiculos"],
        kwargs["distancia_aleatoria"],
    )
    relatorio = _fallback_relatorio(
        kwargs["fitness_final"],
        kwargs["melhoria_distancia"],
        kwargs["diferenca_benchmark"],
        kwargs["prioridade_10"],
        kwargs["prioridade_9_10"],
        kwargs["media_top10"],
        kwargs["texto_veiculos"],
        kwargs["total_cidades"],
        kwargs["num_veiculos"],
        kwargs["distancia_aleatoria"],
        kwargs["fitness_target_solution"],
    )
    relatorio_semanal = _fallback_relatorio_semanal(
        kwargs["texto_resumo_semanal"],
        kwargs["texto_veiculos"],
    )
    instrucoes = _fallback_instrucoes(
        kwargs["texto_veiculos"],
        kwargs["prioridade_10"],
        kwargs["prioridade_9_10"],
    )
    return {
        "analise": analise,
        "relatorio": relatorio,
        "relatorio_semanal": relatorio_semanal,
        "instrucoes": instrucoes,
    }


def gerar_conteudo_completo(
    *,
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
    texto_veiculos,
    texto_resumo_semanal,
    capacidade_veiculo,
    distancia_maxima_veiculo,
) -> Dict[str, str]:
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
    benchmark_nao_calculado = math.isnan(fitness_target_solution)
    nota_benchmark = (
        "Ótimo VRP NÃO foi calculado (mais de 7 entregas — limite da força bruta). "
        "Compare AG vs rota aleatória; NÃO diga que o AG falhou por causa do ótimo."
        if benchmark_nao_calculado
        else f"Ótimo VRP calculado: {otimo_txt} km (diferença: {diff_txt})."
    )

    kwargs = {
        "fitness_inicial": fitness_inicial,
        "fitness_final": fitness_final,
        "fitness_final_prioridade": fitness_final_prioridade,
        "melhoria_fitness": melhoria_fitness,
        "melhoria_distancia": melhoria_distancia,
        "fitness_target_solution": fitness_target_solution,
        "diferenca_benchmark": diferenca_benchmark,
        "geracao_convergencia": geracao_convergencia,
        "prioridade_10": prioridade_10,
        "prioridade_9_10": prioridade_9_10,
        "media_top10": media_top10,
        "total_cidades": total_cidades,
        "num_veiculos": num_veiculos,
        "distancia_aleatoria": distancia_aleatoria,
        "texto_veiculos": texto_veiculos,
        "texto_resumo_semanal": texto_resumo_semanal,
    }

    prompt = f"""
{bloco_contexto_para_prompt()}
Você é analista e coordenador de logística hospitalar (VRP com {num_veiculos} veículos).
Siga o CONTEXTO DO SISTEMA acima; use os limites de capacidade/autonomia informados abaixo.

Dados da operação:
- Fitness inicial: {fitness_inicial:.0f} | final: {fitness_final_prioridade:.0f} | distância: {fitness_final:.0f} km
- Melhoria fitness: {melhoria_fitness:.1f}% | distância: {melhoria_distancia:.1f}%
- Ótimo VRP: {otimo_txt} | diferença: {diff_txt}
- Rota aleatória: {distancia_aleatoria:.0f} km | convergência: geração {geracao_convergencia}
- Entregas: {total_cidades} | prioridade 10: {prioridade_10} | prioridade 9-10: {prioridade_9_10}
- Média prioridade top 10: {media_top10:.1f} | prioridades top 10: {top10_prioridades}
- Capacidade/veículo: {capacidade_veiculo} kits | autonomia: {distancia_maxima_veiculo} km
- Depósito: Hospital Central (saída/retorno)

Veículos:
{texto_veiculos}

Projeção semanal (5 dias úteis — NÃO é histórico real):
{texto_resumo_semanal}

Benchmark: {nota_benchmark}

Gere APENAS o conteúdo abaixo, com estes 4 marcadores (copie literalmente).
NÃO repita estas instruções. NÃO escreva linhas como "máx. N palavras" ou títulos de seção.
Cada marcador em linha própria; conteúdo começa na linha seguinte.

=== ANALISE ===
(qualidade, convergência, prioridades, benchmark, conclusão — até 200 palavras)

=== RELATORIO_DIARIO ===
(resumo, eficiência, capacidade/autonomia POR VEÍCULO, prioridades, recomendações — até 250 palavras)

=== RELATORIO_SEMANAL ===
(projeção ×5 dias úteis, tendências, recomendações — deixe claro que é projeção — até 250 palavras)

=== INSTRUCOES ===
(por veículo: carga, distância, status; cite a parada de MAIOR prioridade (9-10) — até 180 palavras)

Regras:
- Português operacional, sem tom acadêmico.
- Prioridade clínica = número p9/p10 maior, NÃO a última parada da rota.
- Não diga "ajuste a rota" — a ordem do AG é a oficial.
- Use capacidade/autonomia dos dados ({capacidade_veiculo} kits, {distancia_maxima_veiculo} km).
"""

    def _processar_resposta(texto: str) -> Dict[str, str]:
        parsed = _parse_resposta_combinada(texto)
        fallback = _fallback_completo(**kwargs)
        for chave in fallback:
            if not parsed.get(chave):
                parsed[chave] = fallback[chave]
        return parsed

    resposta = chamar_llm(prompt, lambda: "", temperature=0.2)
    if not resposta.strip():
        return _fallback_completo(**kwargs)
    return _processar_resposta(resposta)
