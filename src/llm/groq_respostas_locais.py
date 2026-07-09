"""Montagem determinística do Guia Motoristas (aba Instruções).

O chat do painel NÃO usa este módulo — todas as respostas do chat passam pela Groq
em groq_perguntas.py. As funções aqui servem apenas para groq_rotas.py.
"""

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
            "somente",
            "só a",
            "so a",
            "quantos kits",
            "quantas cargas",
            "faltaram",
            "faltou",
            "falta",
            "falaram",
            "ultima parada",
            "última parada",
            "primeira parada",
        )
    )


def pergunta_sobre_parada_especifica(pergunta: str) -> Optional[str]:
    """Detecta pedido de primeira ou última parada (resposta curta, não rota completa)."""
    p = pergunta.lower().strip()
    if any(
        k in p
        for k in (
            "última parada",
            "ultima parada",
            "última entrega",
            "ultima entrega",
        )
    ):
        return "ultima"
    if any(
        k in p
        for k in (
            "primeira parada",
            "primeira entrega",
            "1ª parada",
            "1a parada",
        )
    ):
        return "primeira"
    if "somente" in p or p.startswith("só ") or p.startswith("so "):
        if "ultima" in p or "última" in p:
            return "ultima"
        if "primeira" in p:
            return "primeira"
    return None


def resolver_veiculo_contexto(
    pergunta: str,
    historico: Optional[Sequence[Tuple[str, str]]] = None,
) -> Optional[int]:
    num = extrair_numero_veiculo(pergunta)
    if num is not None:
        return num
    if historico and (
        pergunta_followup_contextual(pergunta)
        or pergunta_sobre_parada_especifica(pergunta)
        or pergunta_sobre_faltantes_veiculo(pergunta)
    ):
        return extrair_veiculo_do_historico(historico)
    return None


def pergunta_sobre_faltantes_veiculo(pergunta: str) -> bool:
    """Perguntas sobre kits/entregas que o veículo não cumpriu ou capacidade livre."""
    p = pergunta.lower().strip()
    if re.search(r"n[aã]o\s+entreg", p):
        return True
    if any(
        k in p
        for k in (
            "deixou de entregar",
            "deixaram de entregar",
            "falhou entregar",
            "falaram entregar",
            "não conseguiu entregar",
            "nao conseguiu entregar",
        )
    ):
        return True
    if any(k in p for k in ("faltaram", "faltou")):
        return True
    if "falta " in p or p.startswith("falta"):
        return True
    return False


def pergunta_explicita_sobre_hospital(pergunta: str) -> bool:
    """Pergunta sobre remanescentes da operação inteira (hospital), não de um veículo."""
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
            "depósito",
            "deposito",
            "frota inteira",
            "operação inteira",
            "operacao inteira",
            "todo o dia",
        )
    )


def pergunta_sobre_kits_faltantes_operacao(pergunta: str) -> bool:
    """Kits não entregues pela frota (sem citar veículo específico)."""
    p = pergunta.lower()
    if extrair_numero_veiculo(pergunta) is not None:
        return False
    if re.search(r"ve[ií]culo|carro|van\b", p):
        return False
    tem_falta = any(
        k in p
        for k in ("faltaram", "faltou", "falaram", "não entreg", "nao entreg")
    )
    tem_kit = "kit" in p or "entreg" in p
    return tem_falta and tem_kit


def pergunta_sobre_rota_ou_instrucoes(pergunta: str) -> bool:
    if pergunta_sobre_parada_especifica(pergunta):
        return False
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
    if pergunta_sobre_faltantes_veiculo(pergunta):
        return False
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
            "entregou",
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


def _extrair_linha_ultima_parada(texto_rotas: str, num: int) -> Optional[str]:
    m = re.search(
        rf"Última parada do veículo {num}:\s*(.+)",
        texto_rotas,
    )
    return m.group(1).strip() if m else None


def responder_parada_especifica_local(
    num_veiculo: int,
    texto_rotas_detalhado: str,
    qual: str,
) -> Optional[str]:
    """Resposta curta: só a primeira ou última parada do veículo."""
    if qual == "ultima":
        linha = _extrair_linha_ultima_parada(texto_rotas_detalhado, num_veiculo)
        if linha:
            return f"Última parada do veículo {num_veiculo}: {linha}"
        paradas_raw = _paradas_veiculo(texto_rotas_detalhado, num_veiculo)
        if paradas_raw:
            texto = paradas_raw[-1].split("ª parada:", 1)[-1].strip()
            return f"Última parada do veículo {num_veiculo}: {texto}"
        return None

    if qual == "primeira":
        paradas_raw = _paradas_veiculo(texto_rotas_detalhado, num_veiculo)
        if paradas_raw:
            texto = paradas_raw[0].split("ª parada:", 1)[-1].strip()
            return f"Primeira parada do veículo {num_veiculo}: {texto}"
        return None

    return None


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


def responder_faltantes_veiculo_local(
    num_veiculo: int,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
) -> Optional[str]:
    """Kits não entregues pelo veículo ou capacidade livre na van."""
    entregas, carga, capacidade = _extrair_metricas_veiculo(
        texto_veiculos, num_veiculo
    )
    paradas_raw = _paradas_veiculo(texto_rotas_detalhado, num_veiculo)

    if entregas is None and carga is None and not paradas_raw:
        return None

    n_entregas = entregas if entregas is not None else len(paradas_raw)
    if n_entregas == 0:
        return (
            f"Veículo {num_veiculo}: sem entregas na rota — "
            "não há kits a entregar neste turno."
        )

    if carga is None and paradas_raw:
        carga = sum(
            _kits_da_parada(raw.split("ª parada:", 1)[-1])
            for raw in paradas_raw
        )

    carga_val = carga or 0
    cap = capacidade if capacidade is not None else carga_val
    slack = max(0, cap - carga_val)

    if slack > 0:
        return (
            f"Veículo {num_veiculo}: 0 kits deixaram de ser entregues nas "
            f"{n_entregas} parada(s) da rota ({carga_val} kits entregues). "
            f"Capacidade livre na van: {slack} kit(s) ({carga_val}/{cap})."
        )
    return (
        f"Veículo {num_veiculo}: entregou todas as {n_entregas} parada(s) "
        f"({carga_val}/{cap} kits). Não há entregas pendentes desse veículo."
    )


def _extrair_total_kits_remanescentes(
    texto_remanescentes: str,
) -> Optional[Tuple[int, int]]:
    """Retorna (unidades, kits) do bloco de remanescentes."""
    if not texto_remanescentes.strip():
        return 0, 0
    if "Nenhum kit remanescente" in texto_remanescentes:
        return 0, 0
    m = re.search(
        r"Unidades afetadas:\s*(\d+)\s*\|\s*Kits no hospital:\s*(\d+)",
        texto_remanescentes,
    )
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def responder_kits_faltantes_operacao_local(
    texto_remanescentes: str,
) -> Optional[str]:
    """Resposta curta sobre kits que ficaram no hospital (operação inteira)."""
    parsed = _extrair_total_kits_remanescentes(texto_remanescentes)
    if parsed is None:
        return responder_remanescentes_local(texto_remanescentes)
    unidades, kits = parsed
    if kits == 0:
        return (
            "Nenhum kit ficou no hospital — toda a demanda coube na frota."
        )
    return (
        f"Kits que não couberam na frota (aguardam no Hospital Central): "
        f"{kits} kits em {unidades} unidade(s)."
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
    if pergunta_sobre_contagem_tipo(pergunta):
        return False
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


def pergunta_sobre_contagem_tipo(pergunta: str) -> bool:
    """Perguntas do tipo 'quantos críticos entregues?' — resposta curta, não dump."""
    p = pergunta.lower().strip()
    if not any(
        k in p
        for k in ("quantos", "quantas", "numero", "número", "qtd", "total de")
    ):
        return False
    return (
        extrair_tipo_da_pergunta(pergunta) is not None
        or "entreg" in p
        or "medicamento" in p
        or "insumo" in p
    )


def pergunta_sobre_listagem_tipos_explicita(pergunta: str) -> bool:
    """Pedido explícito de lista/detalhamento por tipo."""
    p = pergunta.lower()
    return any(
        k in p
        for k in (
            "quais",
            "liste",
            "listar",
            "lista ",
            "mostre",
            "mostrar",
            "enumere",
            "detalhe",
            "detalhar",
            "detalhamento",
        )
    )


def extrair_tipo_da_pergunta(pergunta: str) -> Optional[str]:
    p = pergunta.lower()
    if any(k in p for k in ("critico", "crítico", "criticos", "críticos")):
        return "CRITICO"
    if "insumo" in p:
        return "INSUMO"
    if "regular" in p:
        return "REGULAR"
    return None


def _parse_resumo_tipos_do_texto(texto_entregas_por_tipo: str) -> dict[str, dict]:
    """Extrai entregas, kits e nomes por tipo do bloco montar_entregas_por_tipo."""
    resultado: dict[str, dict] = {
        t: {"entregas": 0, "kits": 0, "unidades": []}
        for t in ("CRITICO", "REGULAR", "INSUMO")
    }
    if not texto_entregas_por_tipo.strip():
        return resultado

    for tipo in resultado:
        m = re.search(
            rf"{tipo}[^\n]*\((\d+)\s+entregas?\)",
            texto_entregas_por_tipo,
            re.IGNORECASE,
        )
        if m:
            resultado[tipo]["entregas"] = int(m.group(1))

        bloco = re.search(
            rf"({tipo}[^\n]*\(\d+\s+entregas?\):.*?)(?=\n(?:CRITICO|REGULAR|INSUMO)|\Z)",
            texto_entregas_por_tipo,
            re.DOTALL | re.IGNORECASE,
        )
        if not bloco:
            continue
        trecho = bloco.group(1)
        resultado[tipo]["kits"] = sum(
            int(k) for k in re.findall(r"(\d+)\s+kits", trecho)
        )
        resultado[tipo]["unidades"] = [
            u.strip()
            for u in re.findall(r"•\s*(.+?)\s*\(\d+\s+kits", trecho)
        ]

    return resultado


def responder_contagem_tipo_local(
    texto_entregas_por_tipo: str,
    pergunta: str,
) -> Optional[str]:
    """Resposta conversacional e curta sobre quantidade por tipo."""
    if not texto_entregas_por_tipo.strip():
        return None

    resumo = _parse_resumo_tipos_do_texto(texto_entregas_por_tipo)
    tipo = extrair_tipo_da_pergunta(pergunta)

    rotulo = {
        "CRITICO": "críticas",
        "REGULAR": "regulares",
        "INSUMO": "de insumo",
    }

    if tipo:
        dados = resumo[tipo]
        n = dados["entregas"]
        kits = dados["kits"]
        if n == 0:
            return f"Nenhuma entrega {rotulo[tipo]} nesta operação."
        nomes = dados["unidades"]
        if len(nomes) <= 3:
            lista = ", ".join(nomes)
            return (
                f"Foram {n} entrega(s) {rotulo[tipo]} ({kits} kits): {lista}."
            )
        lista = ", ".join(nomes[:3])
        return (
            f"Foram {n} entrega(s) {rotulo[tipo]} ({kits} kits), "
            f"incluindo {lista} e mais {n - 3} unidade(s)."
        )

    c = resumo["CRITICO"]["entregas"]
    r = resumo["REGULAR"]["entregas"]
    i = resumo["INSUMO"]["entregas"]
    total = c + r + i
    return (
        f"Nesta operação há {total} entrega(s): "
        f"{c} crítica(s), {r} regular(es) e {i} de insumo."
    )


def responder_medicamentos_local(texto_entregas_por_tipo: str) -> Optional[str]:
    if not texto_entregas_por_tipo.strip():
        return None
    resumo = _parse_resumo_tipos_do_texto(texto_entregas_por_tipo)
    c, r, i = (
        resumo["CRITICO"]["entregas"],
        resumo["REGULAR"]["entregas"],
        resumo["INSUMO"]["entregas"],
    )
    return (
        f"No dia temos {c} entrega(s) crítica(s), {r} regular(es) "
        f"e {i} de insumo. Detalhamento:\n\n"
        f"{texto_entregas_por_tipo}"
    )


def pergunta_sobre_remanescentes_hospital(pergunta: str) -> bool:
    return pergunta_explicita_sobre_hospital(pergunta)


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
    """Perguntas conceituais sobre kits, carga e capacidade — não operacionais por veículo."""
    p = pergunta.lower()
    if extrair_numero_veiculo(pergunta) is not None:
        return False
    if re.search(r"ve[ií]culo|carro|van\b", p) and pergunta_sobre_carga_veiculo(pergunta):
        return False
    if any(k in p for k in ("entregou", "levou", "transportou", "carregou")):
        return False
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
    historico = historico_conversa or []

    num = resolver_veiculo_contexto(pergunta, historico)
    qual_parada = pergunta_sobre_parada_especifica(pergunta)

    if num is not None and qual_parada:
        resposta = responder_parada_especifica_local(
            num, texto_rotas_detalhado, qual_parada
        )
        if resposta:
            return resposta

    if num is not None and pergunta_sobre_faltantes_veiculo(pergunta):
        resposta = responder_faltantes_veiculo_local(
            num, texto_veiculos, texto_rotas_detalhado
        )
        if resposta:
            return resposta

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

    if pergunta_sobre_remanescentes_hospital(pergunta):
        resposta = responder_remanescentes_local(texto_remanescentes)
        if resposta:
            return resposta

    if pergunta_sobre_kits_faltantes_operacao(pergunta):
        resposta = responder_kits_faltantes_operacao_local(texto_remanescentes)
        if resposta:
            return resposta

    if pergunta_sobre_funcionamento_kits(pergunta):
        return responder_funcionamento_kits_local(
            texto_rota_resumo,
            texto_veiculos,
            historico,
        )

    if pergunta_sobre_contagem_tipo(pergunta):
        resposta = responder_contagem_tipo_local(
            texto_entregas_por_tipo, pergunta
        )
        if resposta:
            return resposta

    if pergunta_sobre_medicamentos_ou_tipos(pergunta):
        if pergunta_sobre_listagem_tipos_explicita(pergunta):
            resposta = responder_medicamentos_local(texto_entregas_por_tipo)
            if resposta:
                return resposta
        return None

    return None
