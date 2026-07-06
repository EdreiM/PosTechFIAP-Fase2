"""
Testes unitários consolidados do projeto TSP Logística Hospitalar.

Cobre: config, dados hospitalares, AG/VRP, ag_runner, Groq (fallback, contexto, conteúdo).

Inclui TestRegressaoBugsUsuario — reproduz falhas encontradas em teste manual real
(chat priorizando parada errada, eco de prompt nas abas, benchmark N/A mal explicado).

Execute (na raiz do projeto):
  pytest tests/test_projeto.py -v
  python tests/test_projeto.py
"""

import sys
from pathlib import Path

# Permite importar módulos da raiz ao rodar direto: python tests/test_projeto.py
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import math
import random

import genetic_algorithm as ga
from ag_runner import executar_ag
from config import (
    DEFAULT_PROBLEMS,
    OPCOES_AUTONOMIA,
    OPCOES_CAPACIDADE,
    UNIDADE_MEDIDA,
    obter_cidades,
)
from config_ui import ParametrosSimulacao
from dados_hospitalares import (
    TIPOS_ENTREGA,
    avaliar_viabilidade_frota,
    carga_total_dia,
    configurar_cenario,
    formatar_entrega,
    montar_entregas,
    montar_ordem_global,
    montar_rotas_por_veiculo,
    obter_nome,
    obter_tipo,
    parse_pedidos_csv,
    prioridade_para_tipo,
    resumo_tipos,
)

# ---------------------------------------------------------------------------
# Fixtures locais (AG)
# ---------------------------------------------------------------------------

CIDADES_AG = [(0, 0), (10, 0), (10, 10), (0, 10)]


def _configurar_dados_ag():
    ga.city_priorities.clear()
    ga.city_demands.clear()
    ga.city_names.clear()
    ga.city_types.clear()
    for cidade in CIDADES_AG:
        ga.city_priorities[cidade] = 5
        ga.city_demands[cidade] = 10


# =============================================================================
# config.py
# =============================================================================


class TestConfig:
    def test_unidade_medida_definida(self):
        assert "kit" in UNIDADE_MEDIDA.lower()

    def test_opcoes_frota(self):
        assert 40 in OPCOES_CAPACIDADE
        assert 1500 in OPCOES_AUTONOMIA

    def test_obter_cidades_modo_fixo(self):
        cities = obter_cidades(5, "fixo", 42)
        assert len(cities) == 5
        assert cities == DEFAULT_PROBLEMS[5]

    def test_obter_cidades_modo_aleatorio(self):
        cities = obter_cidades(8, "aleatorio", 42)
        assert len(cities) == 8

    def test_obter_cidades_fixo_invalido(self):
        import pytest

        with pytest.raises(ValueError, match="inválido"):
            obter_cidades(7, "fixo", 42)


# =============================================================================
# config_ui.py
# =============================================================================


class TestConfigUI:
    def test_parametros_padrao(self):
        p = ParametrosSimulacao.padrao()
        assert p.n_cidades >= 5
        assert p.num_veiculos >= 2
        assert p.capacidade_veiculo in OPCOES_CAPACIDADE
        assert p.distancia_maxima_veiculo in OPCOES_AUTONOMIA
        assert p.arquivo_csv is None


# =============================================================================
# dados_hospitalares.py
# =============================================================================


class TestDadosHospitalares:
    def test_configurar_cenario_modo_fixo(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        configurar_cenario(cities, seed=42, n_cidades=5, modo="fixo")

        assert len(ga.city_priorities) == 5
        assert ga.city_names[cities[0]] == "UTI Norte"
        assert ga.city_types[cities[0]] == "CRITICO"

    def test_prioridade_para_tipo(self):
        assert prioridade_para_tipo(10) == "CRITICO"
        assert prioridade_para_tipo(8) == "CRITICO"
        assert prioridade_para_tipo(5) == "REGULAR"
        assert prioridade_para_tipo(2) == "INSUMO"

    def test_valores_fixos_respeitam_faixas(self):
        cities = DEFAULT_PROBLEMS[10].copy()
        configurar_cenario(cities, seed=42, n_cidades=10, modo="fixo")

        for cidade in cities:
            tipo = obter_tipo(cidade)
            cfg = TIPOS_ENTREGA[tipo]
            assert cfg["prioridade_min"] <= ga.city_priorities[cidade] <= cfg["prioridade_max"]
            assert cfg["demanda_min"] <= ga.city_demands[cidade] <= cfg["demanda_max"]

    def test_demandas_fixas_reproduziveis(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        configurar_cenario(cities, seed=42, n_cidades=5, modo="fixo")
        primeira = {c: ga.city_demands[c] for c in cities}

        configurar_cenario(cities, seed=999, n_cidades=5, modo="fixo")
        assert primeira == {c: ga.city_demands[c] for c in cities}
        assert ga.city_demands[cities[0]] == 12
        assert ga.city_priorities[cities[0]] == 10

    def test_carga_total_dia(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        entregas = montar_entregas(cities, seed=42, n_cidades=5, modo="fixo")
        assert carga_total_dia(entregas) == sum(e.demanda for e in entregas)

    def test_parse_pedidos_csv(self, tmp_path):
        arquivo = tmp_path / "pedidos.csv"
        arquivo.write_text(
            "nome,tipo,demanda_kits,prioridade,x,y\n"
            "UTI Norte,CRITICO,12,10,100,200\n"
            "Farmácia,INSUMO,28,2,300,400\n",
            encoding="utf-8",
        )
        entregas = parse_pedidos_csv(str(arquivo))
        assert len(entregas) == 2
        assert entregas[0].demanda == 12
        assert entregas[1].tipo == "INSUMO"

    def test_viabilidade_frota_insuficiente(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        entregas = montar_entregas(cities, seed=42, n_cidades=5, modo="fixo")
        r = avaliar_viabilidade_frota(entregas, num_veiculos=2, capacidade_veiculo=40)
        assert r["viavel"] is False
        assert r["carga_total"] == 81
        assert r["deficit"] == 1
        assert r["min_veiculos_carga"] == 3

    def test_viabilidade_frota_suficiente(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        entregas = montar_entregas(cities, seed=42, n_cidades=5, modo="fixo")
        r = avaliar_viabilidade_frota(entregas, num_veiculos=3, capacidade_veiculo=40)
        assert r["viavel"] is True

    def test_cenario_15_entregas_viavel_capacidade_80(self):
        cities = DEFAULT_PROBLEMS[15].copy()
        entregas = montar_entregas(cities, seed=42, n_cidades=15, modo="fixo")
        r = avaliar_viabilidade_frota(entregas, num_veiculos=4, capacidade_veiculo=80)
        assert r["carga_total"] == 264
        assert r["capacidade_frota"] == 320
        assert r["viavel"] is True

    def test_resumo_tipos(self):
        cities = DEFAULT_PROBLEMS[15].copy()
        configurar_cenario(cities, seed=42, n_cidades=15, modo="fixo")
        contagem = resumo_tipos(cities)
        assert sum(contagem.values()) == 15
        assert contagem["CRITICO"] == 4
        assert contagem["REGULAR"] == 6
        assert contagem["INSUMO"] == 5

    def test_formatar_entrega(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        configurar_cenario(cities, seed=42, n_cidades=5, modo="fixo")
        texto = formatar_entrega(cities[0], ordem=1)
        assert "UTI Norte" in texto
        assert "CRITICO" in texto
        assert "kits" in texto

    def test_montar_ordem_global(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        configurar_cenario(cities, seed=42, n_cidades=5, modo="fixo")
        alocacao = {c: i % 2 for i, c in enumerate(cities)}
        texto = montar_ordem_global(cities, alocacao)
        assert "Última entrega global:" in texto
        assert obter_nome(cities[-1]) in texto

    def test_montar_rotas_por_veiculo(self):
        cities = DEFAULT_PROBLEMS[5].copy()
        configurar_cenario(cities, seed=42, n_cidades=5, modo="fixo")
        rotas = [cities[:2], cities[2:4], [cities[4]]]
        texto = montar_rotas_por_veiculo(rotas)
        assert "Última parada do veículo 1:" in texto
        assert obter_nome(cities[1]) in texto


# =============================================================================
# genetic_algorithm.py
# =============================================================================


class TestGeneticAlgorithm:
    def test_aplicar_parametros_frota(self):
        ga.aplicar_parametros_frota(capacidade=60, autonomia=1200)
        assert ga.CAPACIDADE_VEICULO == 60
        assert ga.DISTANCIA_MAXIMA_VEICULO == 1200
        ga.aplicar_parametros_frota(capacidade=40, autonomia=1500)

    def test_restricoes_respeitam_capacidade_configurada(self):
        ga.aplicar_parametros_frota(capacidade=80, autonomia=1500)
        _configurar_dados_ag()
        for cidade in CIDADES_AG:
            ga.city_demands[cidade] = 10
        rota = CIDADES_AG.copy()
        alocacao = ga.gerar_alocacao_aleatoria(CIDADES_AG, num_veiculos=2)
        resumo = ga.avaliar_restricoes_veiculos(rota, alocacao, num_veiculos=2)
        assert all(v["capacidade_ok"] for v in resumo)
        ga.aplicar_parametros_frota(capacidade=40, autonomia=1500)

    def test_dividir_rota_com_alocacao(self):
        rota = CIDADES_AG.copy()
        alocacao = {CIDADES_AG[0]: 0, CIDADES_AG[1]: 1, CIDADES_AG[2]: 2, CIDADES_AG[3]: 0}
        rotas = ga.dividir_rota_em_veiculos(rota, alocacao, num_veiculos=3)
        assert rotas[0] == [CIDADES_AG[0], CIDADES_AG[3]]
        assert rotas[1] == [CIDADES_AG[1]]
        assert rotas[2] == [CIDADES_AG[2]]

    def test_dividir_rota_round_robin(self):
        rota = CIDADES_AG.copy()
        rotas = ga.dividir_rota_em_veiculos(rota, num_veiculos=3)
        assert sum(len(r) for r in rotas) == 4

    def test_dividir_rota_repara_indice_invalido(self):
        rota = CIDADES_AG.copy()
        alocacao = {c: 5 for c in CIDADES_AG}
        rotas = ga.dividir_rota_em_veiculos(rota, alocacao, num_veiculos=2)
        assert len(rotas) == 2
        assert sum(len(r) for r in rotas) == 4

    def test_gerar_alocacao_usa_todos_veiculos(self):
        alocacao = ga.gerar_alocacao_aleatoria(CIDADES_AG, num_veiculos=3)
        assert {alocacao[c] for c in CIDADES_AG} == {0, 1, 2}

    def test_calcular_distancia_operacao(self):
        rota = CIDADES_AG.copy()
        alocacao = {c: i % 2 for i, c in enumerate(CIDADES_AG)}
        distancia = ga.calcular_distancia_operacao(rota, alocacao, num_veiculos=2)
        rotas = ga.dividir_rota_em_veiculos(rota, alocacao, num_veiculos=2)
        esperado = sum(ga.calculate_distance_only(r) for r in rotas if r)
        assert distancia == esperado
        assert distancia > 0

    def test_num_veiculos_ui_diferente_do_config(self):
        cidades = [(i * 10, 0) for i in range(6)]
        num_ui = 6
        alocacao = ga.gerar_alocacao_aleatoria(cidades, num_veiculos=num_ui)
        ga.calcular_distancia_operacao(cidades, alocacao, num_veiculos=num_ui)
        rotas = ga.dividir_rota_em_veiculos(cidades, alocacao, num_veiculos=num_ui)
        assert len(rotas) == num_ui

    def test_fitness_penaliza_excesso_carga(self):
        _configurar_dados_ag()
        rota = CIDADES_AG.copy()
        alocacao = ga.gerar_alocacao_aleatoria(CIDADES_AG, num_veiculos=2)
        fitness_ok = ga.calculate_fitness(rota, alocacao, num_veiculos=2)
        for cidade in CIDADES_AG:
            ga.city_demands[cidade] = 300
        fitness_excesso = ga.calculate_fitness(rota, alocacao, num_veiculos=2)
        assert fitness_excesso > fitness_ok

    def test_avaliar_restricoes_veiculos(self):
        _configurar_dados_ag()
        rota = CIDADES_AG.copy()
        alocacao = ga.gerar_alocacao_aleatoria(CIDADES_AG, num_veiculos=2)
        resumo = ga.avaliar_restricoes_veiculos(rota, alocacao, num_veiculos=2)
        assert len(resumo) == 2
        assert all("viavel" in v for v in resumo)

    def test_melhor_alocacao_exaustiva(self):
        rota = CIDADES_AG.copy()
        distancia, alocacao = ga.melhor_alocacao_exaustiva(rota, num_veiculos=2)
        assert distancia > 0
        assert len(alocacao) == 4

    def test_crossover_vrp(self):
        random.seed(0)
        num_veiculos = 2
        ind1 = ga.criar_individuo_aleatorio(CIDADES_AG, num_veiculos=num_veiculos)
        ind2 = ga.criar_individuo_aleatorio(CIDADES_AG, num_veiculos=num_veiculos)
        filho_path, filho_aloc = ga.crossover_vrp(ind1, ind2, num_veiculos=num_veiculos)
        assert sorted(filho_path) == sorted(CIDADES_AG)
        assert all(0 <= v < num_veiculos for v in filho_aloc.values())

    def test_solucao_otima_poucas_cidades(self):
        _configurar_dados_ag()
        otimo = ga.calcular_solucao_otima_vrp(CIDADES_AG, num_veiculos=2, limite_cidades=10)
        assert otimo > 0

    def test_solucao_otima_omitida_muitas_cidades(self):
        muitas = [(i, 0) for i in range(15)]
        otimo = ga.calcular_solucao_otima_vrp(muitas, limite_cidades=10)
        assert math.isnan(otimo)

    def test_distancia_com_deposito(self):
        rota = [CIDADES_AG[0], CIDADES_AG[1]]
        assert ga.calculate_distance_only(rota, depot=(5, 5)) > ga.calculate_distance_only(
            rota, depot=None
        )

    def test_distancia_rota_vazia(self):
        assert ga.calculate_distance_only([], depot=(0, 0)) == 0.0


# =============================================================================
# ag_runner.py
# =============================================================================


class TestAgRunner:
    def test_executar_ag_retorna_metricas(self):
        _configurar_dados_ag()
        cities = DEFAULT_PROBLEMS[5].copy()
        configurar_cenario(cities, seed=42, n_cidades=5, modo="fixo")

        resultado = executar_ag(
            cities,
            population_size=20,
            n_generations=5,
            mutation_probability=0.5,
            limite_sem_melhora=50,
            seed=42,
            num_veiculos=3,
            verbose=False,
        )

        assert len(resultado["path"]) == 5
        assert len(resultado["alocacao"]) == 5
        assert resultado["geracoes_executadas"] == 5
        assert resultado["fitness_final"] > 0


# =============================================================================
# groq_utils — fallback quando API indisponível
# =============================================================================


class TestGroqUtils:
    def test_chamar_llm_usa_fallback_quando_desabilitado(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_utils import chamar_llm, obter_erro_ultima_chamada

        texto = chamar_llm("prompt qualquer", lambda: "resposta local")
        assert texto == "resposta local"
        assert obter_erro_ultima_chamada() is not None

    def test_gerar_instrucoes_fallback(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_rotas import gerar_instrucoes_rota

        texto = gerar_instrucoes_rota(
            "Veículo 1\n3 entregas | carga 56/80 | distância 629/1500 | status: ok\n",
            prioridade_10=2,
            prioridade_9_10=3,
        )
        assert "INSTRUÇÕES DE ENTREGA" in texto
        assert "56/80" in texto

    def test_contexto_ia_carregado(self):
        from groq_contexto import carregar_contexto_sistema

        ctx = carregar_contexto_sistema()
        assert "VRP" in ctx
        assert "kit" in ctx.lower()

    def test_historico_conversa_no_prompt(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_perguntas import responder_pergunta

        historico = [("Qual veículo tem maior carga?", "Veículo 2 com 72 kits.")]
        texto = responder_pergunta(
            "E a distância dele?",
            "Veículo 2\n4 entregas | carga 72/80 | distância 865/1500 | status: ok\n",
            "Resumo teste",
            "Ordem teste",
            "Análise teste",
            "Relatório teste",
            "Semanal teste",
            "Instruções teste",
            historico_conversa=historico,
        )
        assert "72" in texto or "865" in texto or "Veículo 2" in texto


class TestGroqConteudo:
    def test_parse_resposta_combinada(self):
        from groq_conteudo import _parse_resposta_combinada

        texto = """
=== ANALISE ===
Texto da análise aqui.

=== RELATORIO_DIARIO ===
Texto do relatório diário.

=== RELATORIO_SEMANAL ===
Texto semanal.

=== INSTRUCOES ===
Texto instruções.
"""
        partes = _parse_resposta_combinada(texto)
        assert "análise" in partes["analise"].lower() or "análise" in partes["analise"]
        assert "diário" in partes["relatorio"]
        assert "semanal" in partes["relatorio_semanal"]
        assert "instruções" in partes["instrucoes"].lower() or "instru" in partes["instrucoes"].lower()

    def test_gerar_conteudo_completo_fallback(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_conteudo import gerar_conteudo_completo

        resultado = gerar_conteudo_completo(
            fitness_inicial=6000,
            fitness_final=3000,
            fitness_final_prioridade=4800,
            melhoria_fitness=20.0,
            melhoria_distancia=15.0,
            fitness_target_solution=float("nan"),
            diferenca_benchmark=float("nan"),
            top10_prioridades=[10, 9, 8],
            geracao_convergencia=400,
            prioridade_10=2,
            prioridade_9_10=3,
            media_top10=7.5,
            total_cidades=15,
            num_veiculos=4,
            distancia_aleatoria=4500,
            texto_veiculos="Veículo 1\n3 entregas | carga 70/80 | distância 747/1500 | status: ok\n",
            texto_resumo_semanal="Projeção semanal teste",
            capacidade_veiculo=80,
            distancia_maxima_veiculo=1500,
        )
        assert resultado["analise"]
        assert resultado["relatorio"]
        assert resultado["relatorio_semanal"]
        assert resultado["instrucoes"]
        assert "80" in resultado["analise"] or "3000" in resultado["analise"]

    def test_limpar_eco_prompt(self):
        from groq_conteudo import _limpar_secao

        texto = (
            "Relatório operacional diário (máx. 250 palavras): resumo...\n"
            "Conteúdo real do relatório."
        )
        assert "máx. 250" not in _limpar_secao(texto)
        assert "Conteúdo real" in _limpar_secao(texto)


class TestGroqRespostasLocais:
    TEXTO_VEICULOS = (
        "Veículo 3 | 5 entregas | carga 79/80 | distância 831/1500 | status: ok\n"
    )
    TEXTO_ROTAS = """
Rotas por veículo (Hospital Central → paradas → Hospital Central):

Veículo 3 (5 paradas):
  1ª parada: Unidade Domiciliar 11 [CRITICO] (10 prioridade, 12 kits)
  2ª parada: Unidade de Hemodiálise 5 [CRITICO] (8 prioridade, 10 kits)
  3ª parada: Home Care 10 [CRITICO] (9 prioridade, 8 kits)
  4ª parada: Unidade Pediátrica 18 [INSUMO] (1 prioridade, 20 kits)
  5ª parada: Unidade de Hemodiálise 15 [REGULAR] (4 prioridade, 14 kits)
  Última parada do veículo 3: Unidade de Hemodiálise 15 [REGULAR]
"""

    def test_instrucoes_veiculo_local_prioridade_correta(self):
        from groq_respostas_locais import gerar_instrucoes_veiculo_local

        texto = gerar_instrucoes_veiculo_local(3, self.TEXTO_VEICULOS, self.TEXTO_ROTAS)
        assert "Unidade Domiciliar 11" in texto
        assert "p10" in texto or "(10 prioridade" in texto
        assert "Hemodiálise 15 (p4)" not in texto
        assert "Não altere a sequência" in texto

    def test_chat_usa_resposta_local(self):
        from groq_perguntas import responder_pergunta

        resposta = responder_pergunta(
            "Eu to no veículo 3 me dá as instruções das entregas",
            self.TEXTO_VEICULOS,
            "resumo",
            self.TEXTO_ROTAS,
            "a", "r", "s", "i",
        )
        assert "Veículo 3" in resposta
        assert "79/80" in resposta
        assert "Unidade Domiciliar 11" in resposta


# =============================================================================
# Regressão — bugs reportados em teste manual (18 entregas, veículo 3, etc.)
# =============================================================================

# Dados equivalentes ao cenário real do usuário (modo aleatório, 18 entregas, cap. 80)
_CENARIO_18_VEICULOS = (
    "Veículo 1 | 4 entregas | carga 71/80 | distância 571/1500 | status: operacionalmente viável\n"
    "Veículo 2 | 4 entregas | carga 63/80 | distância 776/1500 | status: operacionalmente viável\n"
    "Veículo 3 | 5 entregas | carga 79/80 | distância 831/1500 | status: operacionalmente viável\n"
    "Veículo 4 | 5 entregas | carga 81/80 | distância 728/1500 | status: com restrição\n"
)
_CENARIO_18_ROTAS = """
Rotas por veículo (Hospital Central → paradas → Hospital Central):

Veículo 3 (5 paradas):
  1ª parada: Unidade Domiciliar 11 [CRITICO] (10 prioridade, 12 kits)
  2ª parada: Unidade de Hemodiálise 5 [CRITICO] (8 prioridade, 10 kits)
  3ª parada: Home Care 10 [CRITICO] (9 prioridade, 8 kits)
  4ª parada: Unidade Pediátrica 18 [INSUMO] (1 prioridade, 20 kits)
  5ª parada: Unidade de Hemodiálise 15 [REGULAR] (4 prioridade, 14 kits)
  Última parada do veículo 3: Unidade de Hemodiálise 15 [REGULAR]

Veículo 4 (5 paradas):
  1ª parada: Unidade Domiciliar 1 [CRITICO] (9 prioridade, 10 kits)
  2ª parada: Posto de Saúde 2 [REGULAR] (5 prioridade, 16 kits)
  3ª parada: Ambulatório de Especialidades 16 [REGULAR] (6 prioridade, 18 kits)
  4ª parada: Centro de Cardiologia 9 [REGULAR] (5 prioridade, 16 kits)
  5ª parada: Posto de Saúde 12 [INSUMO] (3 prioridade, 22 kits)
  Última parada do veículo 4: Posto de Saúde 12 [INSUMO]
"""


def _kwargs_conteudo_18_entregas():
    return dict(
        fitness_inicial=6914.0,
        fitness_final=2905.56,
        fitness_final_prioridade=4859.0,
        melhoria_fitness=39.54,
        melhoria_distancia=44.14,
        fitness_target_solution=float("nan"),
        diferenca_benchmark=float("nan"),
        top10_prioridades=[10, 9, 9, 8, 7, 6, 5, 4, 3, 2],
        geracao_convergencia=646,
        prioridade_10=1,
        prioridade_9_10=5,
        media_top10=7.9,
        total_cidades=18,
        num_veiculos=4,
        distancia_aleatoria=6914.0,
        texto_veiculos=_CENARIO_18_VEICULOS,
        texto_resumo_semanal="Projeção semanal — 18 entregas × 5 dias",
        capacidade_veiculo=80,
        distancia_maxima_veiculo=1500,
    )


def _kwargs_fallback_analise_18():
    k = _kwargs_conteudo_18_entregas()
    k.pop("top10_prioridades")
    k.pop("texto_veiculos")
    k.pop("texto_resumo_semanal")
    k.pop("capacidade_veiculo")
    k.pop("distancia_maxima_veiculo")
    return k


class TestRegressaoBugsUsuario:
    """Falhas que os testes antigos NÃO pegavam — cenário real de demo."""

    def test_pergunta_exata_veiculo_3_instrucoes(self):
        from groq_perguntas import responder_pergunta
        from tests.validadores_ia import assert_instrucoes_veiculo_coerentes

        resposta = responder_pergunta(
            "Eu to no veículo 3 me dá as instruções das entregas",
            _CENARIO_18_VEICULOS,
            "Capacidade/veículo: 80 kits",
            _CENARIO_18_ROTAS,
            "", "", "", "",
        )
        assert_instrucoes_veiculo_coerentes(resposta, 3, capacidade=80)
        assert "1." in resposta and "5." in resposta
        assert "Hemodiálise 15" in resposta
        assert "Priorize" not in resposta or "Hemodiálise 15 (p4)" not in resposta.split("Prioridade")[0]

    def test_nao_prioriza_ultima_parada_p4_como_foco(self):
        from groq_respostas_locais import gerar_instrucoes_veiculo_local
        from tests.validadores_ia import assert_instrucoes_veiculo_coerentes

        texto = gerar_instrucoes_veiculo_local(
            3, _CENARIO_18_VEICULOS.split("\n")[2] + "\n", _CENARIO_18_ROTAS
        )
        assert_instrucoes_veiculo_coerentes(texto, 3)
        assert "Unidade Domiciliar 11 (p10)" in texto or "p10" in texto

    def test_veiculo_4_mostra_restricao_81_80(self):
        from groq_respostas_locais import gerar_instrucoes_veiculo_local

        texto = gerar_instrucoes_veiculo_local(
            4,
            _CENARIO_18_VEICULOS.split("\n")[3] + "\n",
            _CENARIO_18_ROTAS,
        )
        assert "81/80" in texto
        assert "com restrição" in texto or "81/80" in texto

    def test_benchmark_18_entregas_retorna_nan(self):
        cities = [(i * 10, i * 5) for i in range(18)]
        otimo = ga.calcular_solucao_otima_vrp(cities, num_veiculos=4, limite_cidades=7)
        assert math.isnan(otimo)

    def test_fallback_analise_18_entregas_explica_na(self):
        from groq_analysis import _fallback_analisar
        from tests.validadores_ia import assert_analise_benchmark_na_ok

        texto = _fallback_analisar(**_kwargs_fallback_analise_18())
        assert_analise_benchmark_na_ok(texto)

    def test_conteudo_fallback_18_entregas_sem_eco_nas_abas(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_conteudo import gerar_conteudo_completo
        from tests.validadores_ia import assert_todas_abas_ia

        resultado = gerar_conteudo_completo(**_kwargs_conteudo_18_entregas())
        assert_todas_abas_ia(resultado)

    def test_resposta_llm_com_eco_e_limpa_abas(self, monkeypatch):
        """Simula resposta ruim da Groq (como no teste manual) e exige limpeza."""
        resposta_ruim = """
=== ANALISE ===
Análise técnica CURTA (máx. 200 palavras): qualidade, convergência...
O AG reduziu a distância em 44%.

=== RELATORIO_DIARIO ===
Relatório operacional diário (máx. 250 palavras): resumo, eficiência...
Distância total 2905 km. Veículo 4 com restrição 81/80.

=== RELATORIO_SEMANAL ===
Relatório semanal PROJETADO (máx. 250 palavras): projeção ×5 dias...
Economia semanal projetada.

=== INSTRUCOES ===
Instruções para motoristas (máx. 180 palavras): por veículo...
Veículo 3: priorize Unidade Domiciliar 11 (p10).
"""
        monkeypatch.setenv("GROQ_DESABILITADO", "0")
        monkeypatch.setattr(
            "groq_conteudo.chamar_llm",
            lambda prompt, fallback, **kw: resposta_ruim,
        )
        from groq_conteudo import gerar_conteudo_completo
        from tests.validadores_ia import assert_todas_abas_ia

        resultado = gerar_conteudo_completo(**_kwargs_conteudo_18_entregas())
        assert_todas_abas_ia(resultado)
        assert "44%" in resultado["analise"] or "2905" in resultado["relatorio"]
        assert "81/80" in resultado["relatorio"]
        assert "p10" in resultado["instrucoes"] or "Domiciliar 11" in resultado["instrucoes"]

    def test_contexto_ia_documenta_benchmark_e_prioridade(self):
        from groq_contexto import carregar_contexto_sistema

        ctx = carregar_contexto_sistema()
        assert "> 7 entregas" in ctx or "≤ 7 entregas" in ctx
        assert "p9" in ctx.lower() or "9–10" in ctx
        assert "última parada" in ctx.lower()


if __name__ == "__main__":
    try:
        import pytest
    except ImportError:
        print("pytest não instalado. Rode: pip install pytest")
        raise SystemExit(1)
    raise SystemExit(pytest.main([__file__, "-v"]))
