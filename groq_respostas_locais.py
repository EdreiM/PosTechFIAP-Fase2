"""Respostas determinísticas do chat (sem LLM) quando os dados já estão estruturados."""

import re
from typing import List, Optional, Tuple


def extrair_numero_veiculo(pergunta: str) -> Optional[int]:
    m = re.search(r"ve[ií]culo\s*(\d+)", pergunta.lower())
    return int(m.group(1)) if m else None


def pergunta_sobre_rota_ou_instrucoes(pergunta: str) -> bool:
    p = pergunta.lower()
    return any(
        k in p
        for k in (
            "instru",
            "entrega",
            "parada",
            "sequência",
            "sequencia",
            "rota",
            "ordem",
            "visita",
            "to no",
            "tô no",
            "estou no",
            "sou o",
        )
    )


def _stats_veiculo(texto_veiculos: str, num: int) -> str:
    m = re.search(rf"Veículo {num} \|[^\n]+", texto_veiculos)
    return m.group(0).replace("Veículo ", "").strip() if m else ""


def _paradas_veiculo(texto_rotas: str, num: int) -> List[str]:
    bloco = re.search(
        rf"Veículo {num} \(\d+ paradas\):\n((?:  \d+ª parada:.*(?:\n|$))+)",
        texto_rotas,
    )
    if not bloco:
        return []
    return [ln.strip() for ln in bloco.group(1).splitlines() if "ª parada:" in ln]


def _prioridade_da_parada(linha: str) -> int:
    m = re.search(r"\((\d+)\s+prioridade", linha)
    return int(m.group(1)) if m else 0


def _nome_da_parada(linha: str) -> str:
    m = re.match(r"\d+\.\s*(.+?)\s*\[", linha)
    if m:
        return m.group(1).strip()
    m = re.match(r"(.+?)\s*\[", linha)
    return m.group(1).strip() if m else linha


def gerar_instrucoes_veiculo_local(
    num_veiculo: int,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
) -> Optional[str]:
    """Monta instruções exatas a partir dos dados da simulação."""
    stats = _stats_veiculo(texto_veiculos, num_veiculo)
    paradas_raw = _paradas_veiculo(texto_rotas_detalhado, num_veiculo)
    if not stats and not paradas_raw:
        return None

    paradas = []
    for raw in paradas_raw:
        texto = raw.split("ª parada:", 1)[-1].strip()
        paradas.append(texto)

    if not paradas:
        return f"Veículo {num_veiculo}: permanece no hospital (sem entregas nesta execução)."

    prioridades = [(i, _prioridade_da_parada(p), _nome_da_parada(p)) for i, p in enumerate(paradas, 1)]
    urgentes = sorted(
        [(p, nome) for _, p, nome in prioridades if p >= 9],
        key=lambda x: -x[0],
    )
    foco = ", ".join(f"{nome} (p{p})" for p, nome in urgentes[:3])
    if not foco:
        melhor = max(prioridades, key=lambda x: x[1])
        foco = f"{melhor[2]} (p{melhor[1]})"

    linhas_seq = "\n".join(f"  {i}. {p}" for i, p in enumerate(paradas, 1))
    stats_fmt = stats if stats else f"{num_veiculo} | (dados parciais)"

    return (
        f"Instruções — Veículo {num_veiculo}\n"
        f"{stats_fmt}\n\n"
        f"Prioridade clínica: atenda primeiro {foco}.\n"
        f"Siga esta ordem (saída e retorno pelo Hospital Central):\n\n"
        f"{linhas_seq}\n\n"
        f"Não altere a sequência otimizada pelo AG. Confirme a carga antes de sair."
    )


def pergunta_sobre_medicamentos_ou_tipos(pergunta: str) -> bool:
    p = pergunta.lower()
    return any(
        k in p
        for k in (
            "medicamento",
            "medicamentos",
            "fármaco",
            "farmaco",
            "remédio",
            "remedio",
            "insumo",
            "insumos",
            "critico",
            "crítico",
            "criticos",
            "críticos",
            "tipo de entrega",
            "tipos de entrega",
            "categoria",
            "categorias",
        )
    )


def responder_medicamentos_local(texto_entregas_por_tipo: str) -> Optional[str]:
    if not texto_entregas_por_tipo.strip():
        return None
    return (
        "O sistema registra categorias de kits (não nomes de fármacos específicos). "
        "Segue o resumo por tipo:\n\n"
        f"{texto_entregas_por_tipo}"
    )


def pergunta_sobre_remanescentes_hospital(pergunta: str) -> bool:
    p = pergunta.lower()
    return any(
        k in p
        for k in (
            "hospital",
            "remanescente",
            "ficou no",
            "ficaram no",
            "não saiu",
            "nao saiu",
            "pendente",
            "pendentes",
            "aguardando",
            "não coube",
            "nao coube",
            "excedente",
        )
    )


def responder_remanescentes_local(texto_remanescentes: str) -> Optional[str]:
    if not texto_remanescentes.strip():
        return None
    if "Nenhum kit remanescente" in texto_remanescentes:
        return texto_remanescentes
    return (
        "Kits que não couberam na frota permanecem no Hospital Central "
        "(prioridade mais baixa aguarda próximo turno):\n\n"
        f"{texto_remanescentes}"
    )


def tentar_resposta_local(
    pergunta: str,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
    texto_entregas_por_tipo: str = "",
    texto_remanescentes: str = "",
) -> Optional[str]:
    if pergunta_sobre_remanescentes_hospital(pergunta):
        resposta = responder_remanescentes_local(texto_remanescentes)
        if resposta:
            return resposta

    if pergunta_sobre_medicamentos_ou_tipos(pergunta):
        resposta = responder_medicamentos_local(texto_entregas_por_tipo)
        if resposta:
            return resposta

    num = extrair_numero_veiculo(pergunta)
    if num is None or not pergunta_sobre_rota_ou_instrucoes(pergunta):
        return None
    return gerar_instrucoes_veiculo_local(num, texto_veiculos, texto_rotas_detalhado)
