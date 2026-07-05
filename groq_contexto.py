"""Carrega contexto persistente para prompts da Groq e formata histórico do chat."""

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

_RAIZ = Path(__file__).resolve().parent
_CAMINHO_CONTEXTO = _RAIZ / "docs" / "CONTEXTO_IA.md"

_contexto_cache: Optional[str] = None


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


def recarregar_contexto() -> str:
    """Força releitura do arquivo (útil após editar CONTEXTO_IA.md)."""
    global _contexto_cache
    _contexto_cache = None
    return carregar_contexto_sistema()


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
    """Seção de contexto fixo a incluir no início dos prompts."""
    texto = carregar_contexto_sistema()
    if not texto:
        return ""
    return f"=== CONTEXTO DO SISTEMA (referência fixa) ===\n\n{texto}\n"
