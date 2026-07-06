from typing import Optional, Sequence, Tuple

from groq_contexto import bloco_contexto_para_prompt, formatar_historico_conversa
from groq_respostas_locais import tentar_resposta_local
from groq_utils import chamar_llm


def _fallback_pergunta(pergunta, texto_rotas_detalhado, historico_conversa):
    historico = formatar_historico_conversa(historico_conversa)
    return (
        "A IA Groq está indisponível no momento (limite de tokens ou sem conexão). "
        "Consulte as abas Veículos, Instruções e o bloco de ordem das entregas.\n\n"
        f"Pergunta: {pergunta}\n\n"
        f"Histórico recente:\n{historico}\n\n"
        f"{texto_rotas_detalhado[:1500]}"
    )


def responder_pergunta(
    pergunta,
    texto_veiculos,
    texto_rota_resumo,
    texto_rotas_detalhado,
    analise,
    relatorio,
    relatorio_semanal,
    instrucoes,
    texto_catalogo_entregas="",
    texto_entregas_por_tipo="",
    historico_conversa: Optional[Sequence[Tuple[str, str]]] = None,
):
    historico = historico_conversa or []

    resposta_local = tentar_resposta_local(
        pergunta,
        texto_veiculos,
        texto_rotas_detalhado,
        texto_entregas_por_tipo=texto_entregas_por_tipo,
    )
    if resposta_local:
        return resposta_local

    historico_texto = formatar_historico_conversa(historico)
    contexto = bloco_contexto_para_prompt()

    prompt = f"""
Você é um especialista em logística hospitalar (VRP com kits de medicamentos).

{contexto}

=== DADOS DA EXECUÇÃO ATUAL ===

=== CATÁLOGO DE ENTREGAS (unidade, tipo, prioridade, kits, veículo) ===

{texto_catalogo_entregas}

=== ENTREGAS POR TIPO DE MEDICAMENTO/INSUMO ===

{texto_entregas_por_tipo}

=== VEÍCULOS (resumo operacional) ===

{texto_veiculos}

=== ORDEM DAS ENTREGAS (primeira/última parada por veículo e ordem global) ===

{texto_rotas_detalhado}

=== RESUMO DA ROTA ===

{texto_rota_resumo}

=== ANÁLISE TÉCNICA ===

{analise}

=== RELATÓRIO OPERACIONAL DIÁRIO ===

{relatorio}

=== RELATÓRIO OPERACIONAL SEMANAL ===

{relatorio_semanal}

=== INSTRUÇÕES DE ENTREGA ===

{instrucoes}

=== HISTÓRICO DESTA CONVERSA (perguntas anteriores) ===

{historico_texto}

Responda a pergunta atual usando o CONTEXTO DO SISTEMA, os DADOS DA EXECUÇÃO e o HISTÓRICO acima.
Mantenha coerência com respostas anteriores quando o usuário usar "ele", "esse veículo", "e a carga?" etc.

Regras do chat:
- Resposta CURTA (máximo 5 frases), exceto pedido explícito de instruções completas de rota ou lista de medicamentos por tipo.
- ORDEM DAS ENTREGAS: use a sequência exata do bloco ORDEM DAS ENTREGAS — não invente ordem.
- Prioridade clínica = maior número p (9-10 primeiro), NÃO a última parada da rota.
- Veículo mencionado explicitamente → responda só sobre ele.
- Nunca diga "ajuste a rota" — a ordem do AG é oficial.
- Capacidade/autonomia sempre por veículo, usando os números ATUAL/MAX dos dados.
- MEDICAMENTOS / TIPOS: o sistema NÃO possui nomes de fármacos (ex.: dipirona). Use sempre o campo Tipo: CRITICO (medicamentos críticos), REGULAR (rotineiros) ou INSUMO (materiais). Cite unidade + tipo + kits quando listar entregas.
- Se perguntarem "quais medicamentos" → responda com as categorias CRITICO/REGULAR/INSUMO e liste unidades do bloco ENTREGAS POR TIPO.
- Se não houver dado: "Essa informação não está disponível nos resultados atuais."

Pergunta atual:

{pergunta}
"""

    return chamar_llm(
        prompt,
        lambda: _fallback_pergunta(pergunta, texto_rotas_detalhado, historico),
    )
