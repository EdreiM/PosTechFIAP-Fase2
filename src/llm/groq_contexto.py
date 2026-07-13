"""Carrega contexto persistente para prompts da Groq e formata histórico do chat."""

from pathlib import Path
from typing import Optional, Sequence, Tuple

_RAIZ_PROJETO = Path(__file__).resolve().parents[2]
_CAMINHO_CONTEXTO = _RAIZ_PROJETO / "docs" / "CONTEXTO_IA.md"

_contexto_cache: Optional[str] = None

# Resumo enxuto das regras de docs/CONTEXTO_IA.md — só o essencial para a LLM.
_CONTEXTO_LLM = (
    "=== CONTEXTO DO SISTEMA (referência fixa) ===\n"
    "VRP hospitalar: um Algoritmo Genético (AG) otimiza rotas de entrega de "
    "kits de medicamentos a partir do Hospital Central (depósito, nó H — todos "
    "os veículos saem e retornam a ele). Tipos de entrega: CRITICO (p8-10), "
    "REGULAR (p2-7), INSUMO (p1-3); prioridade clínica = maior p (ex.: p9/p10), "
    "NÃO a última parada da rota. Capacidade e autonomia são POR veículo "
    "(ex.: 'carga 70/80', 'distância 747/1500') — nunca assuma 40/1500 fixos. "
    "Veículos NUNCA excedem capacidade: quando a frota não comporta a demanda, "
    "o sistema carrega cada veículo ao máximo e deixa os kits de menor "
    "prioridade no hospital (remanescentes). Benchmark ótimo por força bruta só "
    "com ≤ 6 entregas e ≤ 6 veículos; com ≥ 7 entregas ou > 6 veículos é N/A "
    "(limitação computacional, não falha do AG — compare com as heurísticas). "
    "Relatório semanal é PROJEÇÃO (1 dia × 5 dias úteis), não histórico real. "
    "Use apenas os dados numéricos da execução atual; não invente valores. "
    "Responda em português, curto e humano, com números integrados na frase; "
    "não copie blocos crus nem liste tudo — resuma o que a pergunta pede.\n"
)


def carregar_contexto_sistema() -> str:
    """Retorna o texto de docs/CONTEXTO_IA.md (com cache em memória)."""
    global _contexto_cache
    if _contexto_cache is not None:
        return _contexto_cache
    if _CAMINHO_CONTEXTO.is_file():
        _contexto_cache = _CAMINHO_CONTEXTO.read_text(encoding="utf-8").strip()
    else:
        _contexto_cache = ""
    return _contexto_cache


def formatar_historico_conversa(
    turnos: Sequence[Tuple[str, str]],
    *,
    max_turnos: int = 6,
) -> str:
    """
    Formata perguntas/respostas anteriores para o prompt.

    turnos: lista de (pergunta_usuario, resposta_assistente), ordem cronológica.
    """
    if not turnos:
        return "(primeira mensagem desta conversa)"

    recentes = list(turnos)[-max_turnos:]
    linhas = []
    for indice, (pergunta, resposta) in enumerate(recentes, start=1):
        linhas.append(f"--- Turno {indice} ---")
        linhas.append(f"Usuário: {pergunta.strip()}")
        linhas.append(f"Assistente: {resposta.strip()}")
    return "\n".join(linhas)


def bloco_contexto_para_prompt() -> str:
    """Contexto fixo (versão condensada) incluído no início dos prompts.

    Envia ~250 tokens à LLM para economizar; o docs/CONTEXTO_IA.md completo
    continua como referência humana (via carregar_contexto_sistema()).
    """
    return _CONTEXTO_LLM


