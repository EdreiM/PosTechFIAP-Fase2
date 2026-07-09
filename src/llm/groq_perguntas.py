from typing import Optional, Sequence, Tuple

from groq_contexto import bloco_contexto_para_prompt, formatar_historico_conversa
from groq_utils import chamar_llm

_SYSTEM_CHAT = """Você é um coordenador de logística hospitalar experiente, em português brasileiro.

Seu papel: INTERPRETAR os dados da operação e responder como numa conversa real — natural, direto, humano.
Você fala com motoristas, farmácia e equipe operacional. Não é um robô que despeja relatórios.

Como responder:
- Leia os blocos de dados como memória interna; interprete e reformule com suas palavras.
- Responda só ao que foi perguntado, em 1–3 frases (mais se pedirem rota ou lista completa).
- Use números quando fizer sentido, integrados na frase — não em tabelas ou listas longas.
- Mantenha o fio da conversa (histórico): "quantas faltaram?" refere-se ao veículo do turno anterior.

Nunca faça:
- Copiar ou colar blocos, tabelas, bullets ou seções dos dados.
- Dizer "Com base nos dados", "Portanto", "Essa informação está disponível", "Posso responder".
- Listar todas as unidades quando perguntaram só uma quantidade.
- Inventar valores que não estão nos dados.

Exemplo BOM: "Hoje foram 4 entregas críticas, 44 kits no total — destaque para UTI Norte e Farmácia Central."
Exemplo RUIM: "Com base nos dados fornecidos... CRITICO (4 entregas): • Farmácia Central (8 kits)..."
"""


def _secao_prompt(titulo: str, conteudo: str, vazio: str = "(não disponível nesta execução)") -> str:
    texto = (conteudo or "").strip()
    corpo = texto if texto else vazio
    return f"=== {titulo} ===\n\n{corpo}\n"


def _montar_prompt_chat(
    pergunta: str,
    *,
    contexto: str,
    texto_catalogo_entregas: str,
    texto_entregas_por_tipo: str,
    texto_remanescentes: str,
    texto_veiculos: str,
    texto_rotas_detalhado: str,
    texto_rota_resumo: str,
    texto_entregas_coordenadas: str,
    texto_benchmark: str,
    texto_parametros_ag: str,
    analise: str,
    relatorio: str,
    relatorio_semanal: str,
    texto_resumo_semanal_projecao: str,
    instrucoes: str,
    historico_texto: str,
) -> str:
    remanescentes = (
        texto_remanescentes.strip()
        if texto_remanescentes.strip()
        else "Nenhum — toda demanda coube na frota."
    )

    blocos = [
        "Dados da execução atual (memória interna — não copie na resposta):",
        contexto,
        _secao_prompt(
            "CATÁLOGO DE ENTREGAS (unidade, tipo, prioridade, kits, veículo)",
            texto_catalogo_entregas,
        ),
        _secao_prompt(
            "ENTREGAS POR TIPO DE MEDICAMENTO/INSUMO",
            texto_entregas_por_tipo,
        ),
        _secao_prompt(
            "ENTREGAS NA ROTA OTIMIZADA (ordem, coordenadas, veículo)",
            texto_entregas_coordenadas,
        ),
        _secao_prompt("KITS REMANESCENTES NO HOSPITAL", remanescentes),
        _secao_prompt("VEÍCULOS (resumo operacional)", texto_veiculos),
        _secao_prompt(
            "ORDEM DAS ENTREGAS (ordem global + paradas por veículo)",
            texto_rotas_detalhado,
        ),
        _secao_prompt("RESUMO DA ROTA (totais e configuração)", texto_rota_resumo),
        _secao_prompt(
            "MÉTRICAS E BENCHMARK (AG vs heurísticas e convergência)",
            texto_benchmark,
        ),
        _secao_prompt(
            "PARÂMETROS DO ALGORITMO GENÉTICO (configuração da simulação)",
            texto_parametros_ag,
        ),
        _secao_prompt("ANÁLISE TÉCNICA GERADA PELA IA", analise),
        _secao_prompt("RELATÓRIO OPERACIONAL DIÁRIO (IA)", relatorio),
        _secao_prompt(
            "PROJEÇÃO SEMANAL (dados numéricos — 5 dias úteis simulados)",
            texto_resumo_semanal_projecao,
        ),
        _secao_prompt("RELATÓRIO OPERACIONAL SEMANAL (IA)", relatorio_semanal),
        _secao_prompt(
            "GUIA PARA MOTORISTAS (rota passo a passo por veículo)",
            instrucoes,
        ),
        _secao_prompt("HISTÓRICO DESTA CONVERSA", historico_texto),
        "",
        "Pergunta do usuário agora:",
        pergunta,
    ]

    return "\n".join(blocos)


def _fallback_pergunta(
    pergunta: str,
    historico_conversa: Optional[Sequence[Tuple[str, str]]] = None,
) -> str:
    return (
        "Desculpe, não consigo conversar agora — a conexão com a IA está indisponível. "
        "Confira se a GROQ_API_KEY está no arquivo .env e tente de novo.\n\n"
        "Enquanto isso, as abas Veículos, Instruções e Análise do painel têm os detalhes da operação."
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
    texto_remanescentes="",
    historico_conversa: Optional[Sequence[Tuple[str, str]]] = None,
    texto_benchmark: str = "",
    texto_parametros_ag: str = "",
    texto_resumo_semanal_projecao: str = "",
    texto_entregas_coordenadas: str = "",
):
    historico = historico_conversa or []

    historico_texto = formatar_historico_conversa(historico)
    contexto = bloco_contexto_para_prompt()

    prompt = _montar_prompt_chat(
        pergunta,
        contexto=contexto,
        texto_catalogo_entregas=texto_catalogo_entregas,
        texto_entregas_por_tipo=texto_entregas_por_tipo,
        texto_remanescentes=texto_remanescentes,
        texto_veiculos=texto_veiculos,
        texto_rotas_detalhado=texto_rotas_detalhado,
        texto_rota_resumo=texto_rota_resumo,
        texto_entregas_coordenadas=texto_entregas_coordenadas,
        texto_benchmark=texto_benchmark,
        texto_parametros_ag=texto_parametros_ag,
        analise=analise,
        relatorio=relatorio,
        relatorio_semanal=relatorio_semanal,
        texto_resumo_semanal_projecao=texto_resumo_semanal_projecao,
        instrucoes=instrucoes,
        historico_texto=historico_texto,
    )

    return chamar_llm(
        prompt,
        lambda: _fallback_pergunta(pergunta, historico),
        temperature=0.7,
        system=_SYSTEM_CHAT,
    )
