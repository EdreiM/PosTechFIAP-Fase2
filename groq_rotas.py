import re

from groq_utils import chamar_llm


def _fallback_instrucoes(texto_veiculos, prioridade_10, prioridade_9_10):
    linhas = []
    blocos = re.split(r"(?=Veículo \d+ \|)", texto_veiculos.strip())
    for bloco in blocos:
        if not bloco.strip():
            continue
        partes = [p.strip() for p in bloco.split("\n") if p.strip()]
        linhas.append("• " + " | ".join(partes[:2]))
        if any("p10" in p or "p9" in p for p in partes):
            linhas.append("  Priorize entregas com prioridade 9–10 (maior número p) no início da rota.")
        else:
            melhor_p = 0
            melhor_nome = ""
            for p in partes:
                m = re.search(r"\(p(\d+)\)", p)
                if m and int(m.group(1)) > melhor_p:
                    melhor_p = int(m.group(1))
                    melhor_nome = p.split("(p")[0].strip()
            if melhor_nome:
                linhas.append(f"  Priorize: {melhor_nome} (p{melhor_p}).")

    corpo = "\n".join(linhas) if linhas else texto_veiculos

    return f"""INSTRUÇÕES DE ENTREGA (geradas localmente)

Operação com {prioridade_10} entrega(s) prioridade 10 e {prioridade_9_10} com prioridade 9–10.
Saída e retorno pelo depósito hospitalar (Hospital Central).

{corpo}

Orientação geral: confirmar carga antes da saída, respeitar ordem da rota e registrar entregas críticas primeiro.
"""


def gerar_instrucoes_rota(texto_veiculos, prioridade_10, prioridade_9_10):
    prompt = f"""
Você é um coordenador de logística hospitalar.

Com base nos dados dos veículos abaixo, gere INSTRUÇÕES DE ENTREGA para motoristas e equipe.

Dados dos veículos:

{texto_veiculos}

Cidades críticas na operação: {prioridade_10} com prioridade 10, {prioridade_9_10} com prioridade 9 ou 10.

Para CADA veículo, informe:
- Quantidade de cidades a atender
- Carga (atual/máxima)
- Distância (atual/máxima)
- Status operacional (viável ou com restrição)
- Orientação prática de execução (1-2 frases)

Regras:
- Máximo 200 palavras no total.
- NÃO liste todas as cidades de cada rota.
- Priorize orientar sobre cidades com prioridade 9 e 10.
- Linguagem clara para equipe de campo.
- NÃO reorganize a ordem das cidades.
"""

    return chamar_llm(
        prompt,
        lambda: _fallback_instrucoes(texto_veiculos, prioridade_10, prioridade_9_10),
    )
