"""Validadores reutilizáveis — garantem qualidade mínima das saídas de IA."""

from typing import Iterable

ECOS_PROMPT_PROIBIDOS = (
    "máx. 200 palavras",
    "máx. 250 palavras",
    "máx. 180 palavras",
    "Análise técnica CURTA (máx.",
    "Relatório operacional diário (máx.",
    "Relatório semanal PROJETADO (máx.",
    "Instruções para motoristas (máx.",
)


def assert_sem_eco_prompt(texto: str, *, contexto: str = "") -> None:
    prefixo = f"{contexto}: " if contexto else ""
    for eco in ECOS_PROMPT_PROIBIDOS:
        assert eco not in texto, f"{prefixo}eco do prompt encontrado: {eco!r}"


def assert_instrucoes_veiculo_coerentes(
    texto: str,
    num_veiculo: int,
    *,
    capacidade: int = 80,
    prioridade_minima_foco: int = 9,
) -> None:
    assert f"Veículo {num_veiculo}" in texto or f"veículo {num_veiculo}" in texto.lower()
    assert f"/{capacidade}" in texto, "Capacidade da execução ausente"
    assert "ajuste a rota" not in texto.lower(), "Não deve sugerir alterar rota do AG"
    assert_sem_eco_prompt(texto, contexto=f"instruções veículo {num_veiculo}")

    linha_prior = next(
        (ln for ln in texto.splitlines() if "Prioridade clínica" in ln),
        "",
    )
    assert linha_prior, "Linha de prioridade clínica ausente"

    tem_alta = any(f"p{p}" in linha_prior for p in range(prioridade_minima_foco, 11))
    assert tem_alta, (
        f"Foco deve citar prioridade ≥{prioridade_minima_foco}, "
        f"obteve: {linha_prior!r}"
    )

    if "p4)" in linha_prior and not any(f"p{p}" in linha_prior for p in (9, 10)):
        raise AssertionError("Bug: priorizou p4 (última parada) em vez de p9/p10")


def assert_analise_benchmark_na_ok(texto: str) -> None:
    """Com >7 entregas, análise não deve culpar o AG por 'não alcançar ótimo'."""
    lower = texto.lower()
    assert_sem_eco_prompt(texto, contexto="análise")
    proibidos = (
        "ag falhou",
        "não alcançou o ótimo",
        "benchmark não foi alcançado",
        "continue otimizando para alcançar o ótimo",
    )
    for frase in proibidos:
        assert frase not in lower, f"Análise misleading: {frase!r}"
    assert any(
        k in lower
        for k in (
            "n/a",
            "não calculado",
            "omitido",
            ">7",
            "mais de 7",
            "força bruta",
        )
    ), "Deveria explicar que ótimo não foi calculado"


def assert_todas_abas_ia(conteudo: dict) -> None:
    for chave in ("analise", "relatorio", "relatorio_semanal", "instrucoes"):
        assert conteudo.get(chave), f"Aba {chave!r} vazia"
        assert_sem_eco_prompt(conteudo[chave], contexto=chave)
