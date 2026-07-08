"""Respostas determinísticas do chat (sem LLM) quando os dados já estão estruturados."""

import re
from typing import List, Optional, Sequence, Tuple


def extrair_numero_veiculo(pergunta: str) -> Optional[int]:
    p = pergunta.lower()
    for padrao in (
        r"ve[ií]culo\s*(\d+)",
        r"carro\s*(\d+)",
        r"van\s*(\d+)",
        r"\bv(\d+)\b",
    ):
        m = re.search(padrao, p)
        if m:
            return int(m.group(1))
    return None


def extrair_veiculo_do_historico(
    historico: Sequence[Tuple[str, str]],
) -> Optional[int]:
    """Recupera o último veículo mencionado na conversa."""
    for pergunta, resposta in reversed(historico):
        num = extrair_numero_veiculo(pergunta)
        if num is not None:
            return num
        m = re.search(r"Veículo\s*(\d+)", resposta, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m = re.search(r"carro\s*(\d+)", pergunta, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def pergunta_followup_contextual(pergunta: str) -> bool:
    """Perguntas curtas que dependem do turno anterior (ex.: 'Quantas de cada?')."""
    p = pergunta.lower().strip()
    return any(
        k in p
        for k in (
            "de cada",
            "quantas de cada",
            "e a carga",
            "e os kits",
            "e quantos kits",
            "por tipo",
            "qual tipo",
            "quais tipos",
            "desse veículo",
            "desse veiculo",
            "esse veículo",
            "esse veiculo",
            "dele",
            "dela",
        )
    )


def resolver_veiculo_contexto(
    pergunta: str,
    historico: Optional[Sequence[Tuple[str, str]]] = None,
) -> Optional[int]:
    num = extrair_numero_veiculo(pergunta)
    if num is not None:
        return num
    if historico and pergunta_followup_contextual(pergunta):
        return extrair_veiculo_do_historico(historico)
    return None


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
            "sou a",
            "motorista",
            "motorist",
            "trajet",
            "caminho",
            "percurso",
            "seguir",
            "dirigir",
            "trajeto",
        )
    )


def pergunta_sobre_carga_veiculo(pergunta: str) -> bool:
    p = pergunta.lower()
    return any(
        k in p
        for k in (
            "carga",
            "cargas",
            "entrega",
            "entregas",
            "parada",
            "paradas",
            "kits",
            "levou",
            "carregou",
            "transportou",
        )
    )


def pergunta_sobre_tipos_veiculo(pergunta: str) -> bool:
    p = pergunta.lower()
    return any(
        k in p
        for k in (
            "de cada",
            "quantas de cada",
            "por tipo",
            "qual tipo",
            "quais tipos",
            "critico",
            "crítico",
            "criticos",
            "críticos",
            "regular",
            "insumo",
            "insumos",
            "medicamento",
            "medicamentos",
            "categoria",
            "categorias",
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


def _extrair_metricas_veiculo(
    texto_veiculos: str,
    num: int,
) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Retorna (entregas, carga_kits, capacidade_kits) do resumo do veículo."""
    m = re.search(
        rf"Veículo {num} \| (\d+) entregas \| carga (\d+)/(\d+)",
        texto_veiculos,
    )
    if not m:
        return None, None, None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _kits_da_parada(linha: str) -> int:
    m = re.search(r"(\d+)\s+kits", linha)
    return int(m.group(1)) if m else 0


def _tipo_da_parada(linha: str) -> str:
    m = re.search(r"\[(\w+)\]", linha)
    return m.group(1) if m else "REGULAR"


def responder_cargas_veiculo_local(
    num_veiculo: int,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
) -> Optional[str]:
    """Responde quantas entregas e kits o veículo transporta."""
    paradas_raw = _paradas_veiculo(texto_rotas_detalhado, num_veiculo)
    entregas, carga, capacidade = _extrair_metricas_veiculo(
        texto_veiculos, num_veiculo
    )

    if not paradas_raw and entregas is None:
        return None

    n_entregas = entregas if entregas is not None else len(paradas_raw)
    if n_entregas == 0:
        return (
            f"Veículo {num_veiculo}: permanece no hospital "
            "(sem entregas nesta execução)."
        )

    if carga is None:
        carga = sum(
            _kits_da_parada(raw.split("ª parada:", 1)[-1])
            for raw in paradas_raw
        )

    cap_txt = f"/{capacidade}" if capacidade is not None else ""
    return (
        f"Veículo {num_veiculo}: {n_entregas} entrega(s) "
        f"({carga}{cap_txt} kits no total)."
    )


def responder_tipos_por_veiculo_local(
    num_veiculo: int,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
) -> Optional[str]:
    """Detalha entregas do veículo agrupadas por CRITICO/REGULAR/INSUMO."""
    paradas_raw = _paradas_veiculo(texto_rotas_detalhado, num_veiculo)
    if not paradas_raw:
        entregas, _, _ = _extrair_metricas_veiculo(texto_veiculos, num_veiculo)
        if entregas == 0:
            return (
                f"Veículo {num_veiculo}: permanece no hospital "
                "(sem entregas nesta execução)."
            )
        return None

    grupos: dict[str, List[str]] = {
        "CRITICO": [],
        "REGULAR": [],
        "INSUMO": [],
    }
    for raw in paradas_raw:
        texto = raw.split("ª parada:", 1)[-1].strip()
        tipo = _tipo_da_parada(texto)
        kits = _kits_da_parada(texto)
        nome = _nome_da_parada(texto)
        grupos.setdefault(tipo, []).append(f"{nome} ({kits} kits)")

    linhas = [f"Veículo {num_veiculo} — entregas por tipo:"]
    for tipo in ("CRITICO", "REGULAR", "INSUMO"):
        itens = grupos.get(tipo, [])
        if not itens:
            linhas.append(f"• {tipo}: 0 entrega(s)")
            continue
        lista = ", ".join(itens)
        linhas.append(f"• {tipo}: {len(itens)} entrega(s) — {lista}")

    entregas, carga, _ = _extrair_metricas_veiculo(texto_veiculos, num_veiculo)
    total_entregas = entregas if entregas is not None else len(paradas_raw)
    if carga is not None:
        linhas.append(f"Total do veículo: {total_entregas} entrega(s), {carga} kits.")
    else:
        linhas.append(f"Total do veículo: {total_entregas} entrega(s).")

    return "\n".join(linhas)


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
        return (
            f"Motorista — Veículo {num_veiculo}\n"
            "Permaneça no Hospital Central neste turno (sem entregas atribuídas). "
            "Aguarde novas instruções da coordenação."
        )

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
        f"Motorista — Veículo {num_veiculo}\n"
        f"{stats_fmt}\n\n"
        f"Trajetória: saída pelo Hospital Central (H), depois:\n\n"
        f"{linhas_seq}\n\n"
        f"Prioridade clínica: atenda primeiro {foco}.\n"
        f"Retorne ao Hospital Central após a última parada.\n"
        f"Confirme a carga com a farmácia antes de sair. "
        f"Siga a ordem acima — não pule nem inverta paradas."
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


def pergunta_sobre_funcionamento_kits(pergunta: str) -> bool:
    """Perguntas conceituais sobre kits, carga e capacidade."""
    p = pergunta.lower()
    tem_topico = any(
        k in p for k in ("kit", "kits", "carga", "capacidade", "demanda")
    )
    if not tem_topico:
        return False
    return any(
        k in p
        for k in (
            "como funciona",
            "como é calculad",
            "como e calculad",
            "o que é",
            "o que e",
            "o que são",
            "o que sao",
            "quantidade de",
            "quantos kits",
            "significa",
            "diferença entre",
            "diferenca entre",
            "por carga",
            "por entrega",
            "unidade de",
        )
    )


def _capacidade_do_resumo(texto_rota_resumo: str) -> Optional[int]:
    m = re.search(r"Capacidade/veículo:\s*(\d+)", texto_rota_resumo)
    return int(m.group(1)) if m else None


def responder_funcionamento_kits_local(
    texto_rota_resumo: str = "",
    texto_veiculos: str = "",
    historico: Optional[Sequence[Tuple[str, str]]] = None,
) -> str:
    capacidade = _capacidade_do_resumo(texto_rota_resumo)
    cap_txt = f"{capacidade} kits" if capacidade else "o limite configurado"

    linhas = [
        "No sistema, 1 kit = 1 caixa fechada pela farmácia hospitalar.",
        "",
        "Cada entrega (unidade hospitalar) tem uma demanda em kits "
        "(ex.: UTI 12 kits, Farmácia 8 kits). Isso é o pedido daquela unidade, "
        "não um limite fixo por viagem.",
        "",
        f"A capacidade do veículo ({cap_txt} nesta execução) é o teto de kits "
        "no total da rota — soma de todas as paradas daquele van.",
        "Por isso aparece carga 38/40: 38 kits carregados, limite 40.",
        "",
        "Resumo:",
        "• Entrega/parada = uma unidade na rota",
        "• Demanda = kits que aquela unidade precisa receber",
        "• Carga do veículo = soma dos kits de todas as suas entregas",
        "• Se a frota não comporta tudo, kits de menor prioridade ficam no hospital",
    ]

    historico = historico or []
    num = extrair_veiculo_do_historico(historico)
    if num is not None:
        entregas, carga, cap_veic = _extrair_metricas_veiculo(texto_veiculos, num)
        if entregas is not None and carga is not None:
            cap_ref = cap_veic or capacidade or "?"
            linhas.extend([
                "",
                f"Exemplo (veículo {num}, do histórico da conversa): "
                f"{entregas} entrega(s), {carga}/{cap_ref} kits no total. "
                "Cada parada contribui com sua demanda para essa soma.",
            ])

    return "\n".join(linhas)


def tentar_resposta_local(
    pergunta: str,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
    texto_entregas_por_tipo: str = "",
    texto_remanescentes: str = "",
    historico_conversa: Optional[Sequence[Tuple[str, str]]] = None,
    texto_rota_resumo: str = "",
) -> Optional[str]:
    if pergunta_sobre_remanescentes_hospital(pergunta):
        resposta = responder_remanescentes_local(texto_remanescentes)
        if resposta:
            return resposta

    historico = historico_conversa or []

    if pergunta_sobre_funcionamento_kits(pergunta):
        return responder_funcionamento_kits_local(
            texto_rota_resumo,
            texto_veiculos,
            historico,
        )

    num = resolver_veiculo_contexto(pergunta, historico)

    if num is not None:
        if pergunta_sobre_tipos_veiculo(pergunta):
            resposta = responder_tipos_por_veiculo_local(
                num, texto_veiculos, texto_rotas_detalhado
            )
            if resposta:
                return resposta

        if pergunta_sobre_rota_ou_instrucoes(pergunta):
            return gerar_instrucoes_veiculo_local(
                num, texto_veiculos, texto_rotas_detalhado
            )

        if pergunta_sobre_carga_veiculo(pergunta):
            resposta = responder_cargas_veiculo_local(
                num, texto_veiculos, texto_rotas_detalhado
            )
            if resposta:
                return resposta

    if pergunta_sobre_medicamentos_ou_tipos(pergunta):
        resposta = responder_medicamentos_local(texto_entregas_por_tipo)
        if resposta:
            return resposta

    return None
