import re
from typing import List

from groq_respostas_locais import gerar_instrucoes_veiculo_local
from groq_utils import chamar_llm


def _numeros_veiculos(texto_veiculos: str, texto_rotas: str = "") -> List[int]:
    nums = set()
    for txt in (texto_veiculos, texto_rotas):
        for m in re.finditer(r"Veículo\s*(\d+)", txt):
            nums.add(int(m.group(1)))
    return sorted(nums)


def montar_instrucoes_motoristas(
    texto_veiculos: str,
    texto_rotas_detalhado: str,
) -> str:
    """Guia da aba Instruções — linguagem direta para motoristas, rota passo a passo."""
    blocos = []
    for num in _numeros_veiculos(texto_veiculos, texto_rotas_detalhado):
        bloco = gerar_instrucoes_veiculo_local(
            num,
            texto_veiculos,
            texto_rotas_detalhado,
        )
        if bloco:
            blocos.append(bloco)

    if not blocos:
        return (
            "GUIA PARA MOTORISTAS\n\n"
            "Nenhuma rota atribuída nesta execução. "
            "Aguarde orientação da coordenação no Hospital Central."
        )

    intro = (
        "GUIA PARA MOTORISTAS\n"
        "Instruções de rota do dia — saída e retorno pelo Hospital Central (H).\n"
        "Cada bloco abaixo é a rota do seu veículo. Siga a ordem das paradas.\n"
        + ("─" * 40)
    )
    separador = "\n\n" + ("─" * 40) + "\n\n"
    return intro + "\n\n" + separador.join(blocos)


def _fallback_instrucoes(
    texto_veiculos,
    prioridade_10,
    prioridade_9_10,
    texto_rotas_detalhado: str = "",
):
    if texto_rotas_detalhado.strip():
        return montar_instrucoes_motoristas(texto_veiculos, texto_rotas_detalhado)

    linhas = []
    blocos = re.split(r"(?=Veículo \d+ \|)", texto_veiculos.strip())
    for bloco in blocos:
        if not bloco.strip():
            continue
        partes = [p.strip() for p in bloco.split("\n") if p.strip()]
        linhas.append("• " + " | ".join(partes[:2]))
        if any("p10" in p or "p9" in p for p in partes):
            linhas.append(
                "  Priorize entregas com prioridade 9–10 (maior número p) no início da rota."
            )
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

    return f"""GUIA PARA MOTORISTAS (gerado localmente)

Operação com {prioridade_10} entrega(s) prioridade 10 e {prioridade_9_10} com prioridade 9–10.
Saída e retorno pelo Hospital Central (H).

{corpo}

Antes de sair: confirme a carga com a farmácia. Respeite a ordem da rota e registre entregas críticas primeiro.
"""


def gerar_instrucoes_rota(
    texto_veiculos,
    prioridade_10,
    prioridade_9_10,
    texto_rotas_detalhado: str = "",
):
    if texto_rotas_detalhado.strip():
        return montar_instrucoes_motoristas(texto_veiculos, texto_rotas_detalhado)

    prompt = f"""
Você é coordenador de logística hospitalar escrevendo para MOTORISTAS em campo.

Com base nos dados dos veículos abaixo, gere um GUIA PARA MOTORISTAS.

Dados dos veículos:

{texto_veiculos}

Cidades críticas na operação: {prioridade_10} com prioridade 10, {prioridade_9_10} com prioridade 9 ou 10.

Para CADA veículo com entregas, informe em linguagem direta (como se falasse com o motorista):
- Resumo: entregas, carga atual/máxima, distância, status
- Ordem de saída: Hospital Central (H) → paradas → retorno ao H
- Qual parada tem maior prioridade clínica (p9/p10)
- Lembrete: confirmar carga antes de sair

Regras:
- Máximo 200 palavras no total.
- Use "você" ou imperativo — tom de instrução de campo, não relatório técnico.
- NÃO liste todas as cidades se forem muitas — cite as de maior prioridade.
- NÃO reorganize a ordem das paradas.
"""

    return chamar_llm(
        prompt,
        lambda: _fallback_instrucoes(
            texto_veiculos,
            prioridade_10,
            prioridade_9_10,
            texto_rotas_detalhado,
        ),
    )
