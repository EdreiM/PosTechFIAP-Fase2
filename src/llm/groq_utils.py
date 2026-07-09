"""Utilitários compartilhados para chamadas à API Groq com fallback local."""

import os
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv

_RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(_RAIZ_PROJETO / ".env", override=True)

_client = None
_chave_carregada: Optional[str] = None
_erro_ultima_chamada: Optional[str] = None

# Modelo leve por padrão (menos tokens); override via GROQ_MODEL no .env
MODELO_GROQ = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"


def obter_erro_ultima_chamada() -> Optional[str]:
    return _erro_ultima_chamada


def ia_desabilitada() -> bool:
    return os.getenv("GROQ_DESABILITADO", "").strip().lower() in ("1", "true", "sim", "yes")


def reiniciar_cliente() -> None:
    """Descarta cliente em cache (útil após trocar GROQ_API_KEY no .env)."""
    global _client, _chave_carregada
    _client = None
    _chave_carregada = None


def _obter_cliente():
    global _client, _chave_carregada
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    if _client is not None and _chave_carregada == api_key:
        return _client
    from groq import Groq

    _client = Groq(api_key=api_key)
    _chave_carregada = api_key
    return _client


def _formatar_erro_groq(exc: Exception) -> str:
    mensagem = str(exc)
    nome = type(exc).__name__
    if "RateLimitError" in nome or "rate_limit" in mensagem.lower():
        return (
            "Limite diário de tokens da Groq atingido para esta organização. "
            "Uma nova chave API na mesma conta compartilha a mesma cota — "
            "aguarde o reset (meia-noite UTC), use GROQ_DESABILITADO=1 ou faça upgrade em console.groq.com."
        )
    if "AuthenticationError" in nome or "401" in mensagem:
        return "Chave GROQ_API_KEY inválida ou ausente."
    if "APIConnectionError" in nome:
        return "Sem conexão com a API Groq."
    return mensagem[:200] if mensagem else nome


def chamar_llm(
    prompt: str,
    fallback: Callable[[], str],
    *,
    temperature: float = 0.2,
    system: Optional[str] = None,
) -> str:
    """Chama a Groq; em falha ou sem chave, retorna texto gerado localmente."""
    global _erro_ultima_chamada

    if ia_desabilitada():
        _erro_ultima_chamada = "IA desabilitada (GROQ_DESABILITADO)."
        print(f"[IA] {_erro_ultima_chamada} Usando texto local.")
        return fallback()

    cliente = _obter_cliente()
    if cliente is None:
        _erro_ultima_chamada = "GROQ_API_KEY não configurada no .env."
        print(f"[IA] {_erro_ultima_chamada} Usando texto local.")
        return fallback()

    mensagens = []
    if system and system.strip():
        mensagens.append({"role": "system", "content": system.strip()})
    mensagens.append({"role": "user", "content": prompt})

    try:
        resposta = cliente.chat.completions.create(
            model=MODELO_GROQ,
            messages=mensagens,
            temperature=temperature,
        )
        _erro_ultima_chamada = None
        return resposta.choices[0].message.content
    except Exception as exc:
        _erro_ultima_chamada = _formatar_erro_groq(exc)
        print(f"[IA] Falha na API Groq: {_erro_ultima_chamada}")
        print("[IA] Usando conteúdo local de fallback.")
        return fallback()
