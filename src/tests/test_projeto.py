"""
Testes unitários — TSP Logística Hospitalar.

Guia completo: tests/README.md
Cenários reutilizáveis: tests/fixtures_dados.py

Mapa rápido:
  TestConfig / TestConfigUI     → configuração e janela
  TestDadosHospitalares         → modo FIXO do sistema (tabelas reprodutíveis)
  TestGeneticAlgorithm / AgRunner → AG/VRP (cidades mínimas 4 pontos)
  TestGroq*                     → IA e chat (textos simulados em fixtures_dados)
  TestDashboard*                → painel e métricas
  TestRegressaoBugsUsuario      → bugs de demo real (18 entregas)

Execute:
  py -m pytest src/tests/test_projeto.py -v
"""

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
    montar_catalogo_entregas,
    montar_entregas,
    montar_entregas_por_tipo,
    montar_ordem_global,
    montar_rotas_por_veiculo,
    obter_nome,
    obter_tipo,
    parse_pedidos_csv,
    prioridade_para_tipo,
    priorizar_entregas_capacidade,
    resumo_tipos,
)

from tests.fixtures_dados import (
    CHAT_V2_38_VEICULOS,
    CHAT_V2_ROTAS,
    CHAT_V2_VEICULOS,
    CHAT_V3_ROTAS,
    CHAT_V3_VEICULOS,
    CIDADES_AG_MINI,
    REGRESSAO_18_ROTAS,
    REGRESSAO_18_VEICULO_4_POS_PRIORIZACAO,
    REGRESSAO_18_VEICULOS,
    configurar_cenario_fixo,
    configurar_dados_ag_mini,
    kwargs_fallback_analise_18_entregas,
    kwargs_groq_conteudo_18_entregas,
)

# ---------------------------------------------------------------------------
# AG mínimo — alias local (ver fixtures_dados.CIDADES_AG_MINI)
# ---------------------------------------------------------------------------

CIDADES_AG = CIDADES_AG_MINI


def _configurar_dados_ag():
    configurar_dados_ag_mini()


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

    def test_avisos_benchmark_muitos_veiculos(self):
        from config_ui import avisos_benchmark_solucao_otima

        avisos = avisos_benchmark_solucao_otima(8, 5)
        assert any("6 veículos" in a for a in avisos)

    def test_avisos_benchmark_muitas_entregas(self):
        from config_ui import avisos_benchmark_solucao_otima

        avisos = avisos_benchmark_solucao_otima(4, 7)
        assert any("limitações computacionais" in a for a in avisos)

    def test_avisos_benchmark_cenario_viavel(self):
        from config_ui import avisos_benchmark_solucao_otima

        assert avisos_benchmark_solucao_otima(4, 5) == []


# =============================================================================
# dados_hospitalares.py
# =============================================================================


class TestDadosHospitalares:
    def test_configurar_cenario_modo_fixo(self):
        cities = configurar_cenario_fixo(5)

        assert len(ga.city_priorities) == 5
        assert ga.city_names[cities[0]] == "UTI Norte"
        assert ga.city_types[cities[0]] == "CRITICO"

    def test_prioridade_para_tipo(self):
        assert prioridade_para_tipo(10) == "CRITICO"
        assert prioridade_para_tipo(8) == "CRITICO"
        assert prioridade_para_tipo(5) == "REGULAR"
        assert prioridade_para_tipo(2) == "INSUMO"

    def test_valores_fixos_respeitam_faixas(self):
        cities = configurar_cenario_fixo(10)

        for cidade in cities:
            tipo = obter_tipo(cidade)
            cfg = TIPOS_ENTREGA[tipo]
            assert cfg["prioridade_min"] <= ga.city_priorities[cidade] <= cfg["prioridade_max"]
            assert cfg["demanda_min"] <= ga.city_demands[cidade] <= cfg["demanda_max"]

    def test_demandas_fixas_reproduziveis(self):
        cities = configurar_cenario_fixo(5)
        primeira = {c: ga.city_demands[c] for c in cities}

        configurar_cenario(cities, seed=999, n_cidades=5, modo="fixo")
        assert primeira == {c: ga.city_demands[c] for c in cities}
        assert ga.city_demands[cities[0]] == 12
        assert ga.city_priorities[cities[0]] == 10

    def test_carga_total_dia(self):
        cities = configurar_cenario_fixo(5)
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
        cities = configurar_cenario_fixo(5)
        entregas = montar_entregas(cities, seed=42, n_cidades=5, modo="fixo")
        r = avaliar_viabilidade_frota(entregas, num_veiculos=2, capacidade_veiculo=40)
        assert r["viavel"] is False
        assert r["carga_total"] == 81
        assert r["deficit"] == 1
        assert r["min_veiculos_carga"] == 3

    def test_viabilidade_frota_suficiente(self):
        cities = configurar_cenario_fixo(5)
        entregas = montar_entregas(cities, seed=42, n_cidades=5, modo="fixo")
        r = avaliar_viabilidade_frota(entregas, num_veiculos=3, capacidade_veiculo=40)
        assert r["viavel"] is True

    def test_cenario_15_entregas_viavel_capacidade_80(self):
        cities = configurar_cenario_fixo(15)
        entregas = montar_entregas(cities, seed=42, n_cidades=15, modo="fixo")
        r = avaliar_viabilidade_frota(entregas, num_veiculos=4, capacidade_veiculo=80)
        assert r["carga_total"] == 264
        assert r["capacidade_frota"] == 320
        assert r["viavel"] is True

    def test_resumo_tipos(self):
        cities = configurar_cenario_fixo(15)
        contagem = resumo_tipos(cities)
        assert sum(contagem.values()) == 15
        assert contagem["CRITICO"] == 4
        assert contagem["REGULAR"] == 6
        assert contagem["INSUMO"] == 5

    def test_formatar_entrega(self):
        cities = configurar_cenario_fixo(5)
        texto = formatar_entrega(cities[0], ordem=1)
        assert "UTI Norte" in texto
        assert "CRITICO" in texto
        assert "kits" in texto

    def test_montar_entregas_por_tipo(self):
        cities = configurar_cenario_fixo(5)
        texto = montar_entregas_por_tipo(cities)
        assert "CRITICO" in texto
        assert "UTI Norte" in texto
        assert "INSUMO" in texto

    def test_priorizar_entregas_capacidade(self):
        cities = configurar_cenario_fixo(5)
        path = cities.copy()
        alocacao = {c: i % 2 for i, c in enumerate(path)}
        resultado = priorizar_entregas_capacidade(
            path, alocacao, num_veiculos=2, capacidade_veiculo=30
        )
        assert resultado["houve_corte"] is True
        assert resultado["kits_hospital"] > 0
        assert resultado["kits_entregues"] <= 60
        for rota in resultado["rotas_efetivas"]:
            carga = sum(ga.city_demands[c] for c in rota)
            assert carga <= 30

    def test_priorizar_respeita_prioridade(self):
        cities = configurar_cenario_fixo(5)
        path = cities.copy()
        alocacao = {c: 0 for c in path}
        resultado = priorizar_entregas_capacidade(
            path, alocacao, num_veiculos=1, capacidade_veiculo=20
        )
        if resultado["remanescentes"]:
            min_entregue = min(
                ga.city_priorities[c] for c in resultado["path_efetivo"]
            )
            max_hospital = max(
                ga.city_priorities[c] for c in resultado["remanescentes"]
            )
            assert min_entregue >= max_hospital

    def _assert_veiculos_saturados(self, resultado, capacidade_veiculo):
        """Nenhum remanescente cabe no slack de veículos em operação."""
        for carga in resultado["carga_por_veiculo"]:
            if carga == 0:
                continue
            slack = capacidade_veiculo - carga
            for cidade in resultado["remanescentes"]:
                assert ga.city_demands.get(cidade, 0) > slack

    def test_priorizar_maximiza_carga_no_corte(self):
        cities = [(0, 0), (10, 0), (20, 0), (30, 0)]
        ga.city_priorities.clear()
        ga.city_demands.clear()
        ga.city_names.clear()
        ga.city_types.clear()
        configs = [
            (10, 40),
            (9, 40),
            (8, 10),
            (7, 10),
        ]
        for cidade, (prio, demanda) in zip(cities, configs):
            ga.city_priorities[cidade] = prio
            ga.city_demands[cidade] = demanda
            ga.city_names[cidade] = f"Unidade {cidade[0]}"
            ga.city_types[cidade] = "REGULAR"

        path = cities.copy()
        alocacao = {c: 0 for c in path}
        capacidade = 40
        resultado = priorizar_entregas_capacidade(
            path, alocacao, num_veiculos=2, capacidade_veiculo=capacidade
        )

        assert resultado["houve_corte"] is True
        assert resultado["kits_entregues"] == 80
        assert resultado["utilizacao_maxima"] is True
        assert sorted(resultado["carga_por_veiculo"]) == [40, 40]
        self._assert_veiculos_saturados(resultado, capacidade)

    def test_priorizar_preenchimento_slack_no_corte(self):
        cities = [(0, 0), (10, 0), (20, 0), (30, 0), (40, 0)]
        ga.city_priorities.clear()
        ga.city_demands.clear()
        ga.city_names.clear()
        ga.city_types.clear()
        configs = [
            (10, 35),
            (9, 35),
            (8, 5),
            (7, 5),
            (3, 20),
        ]
        for cidade, (prio, demanda) in zip(cities, configs):
            ga.city_priorities[cidade] = prio
            ga.city_demands[cidade] = demanda
            ga.city_names[cidade] = f"Unidade {cidade[0]}"
            ga.city_types[cidade] = "REGULAR"

        path = cities.copy()
        alocacao = {c: 0 for c in path}
        capacidade = 40
        resultado = priorizar_entregas_capacidade(
            path, alocacao, num_veiculos=2, capacidade_veiculo=capacidade
        )

        assert resultado["houve_corte"] is True
        assert resultado["kits_entregues"] == 80
        assert resultado["utilizacao_maxima"] is True
        assert all(c == capacidade for c in resultado["carga_por_veiculo"])
        self._assert_veiculos_saturados(resultado, capacidade)

    def test_priorizar_sem_corte_mantem_comportamento(self):
        cities = configurar_cenario_fixo(5)
        path = cities.copy()
        alocacao = {c: i % 2 for i, c in enumerate(path)}
        capacidade = 80
        resultado = priorizar_entregas_capacidade(
            path, alocacao, num_veiculos=2, capacidade_veiculo=capacidade
        )

        assert resultado["houve_corte"] is False
        assert resultado["kits_hospital"] == 0
        assert resultado["entregas_efetivas"] == len(path)
        assert resultado["utilizacao_maxima"] is False
        for carga in resultado["carga_por_veiculo"]:
            assert carga <= capacidade

    def test_montar_ordem_global(self):
        cities = configurar_cenario_fixo(5)
        alocacao = {c: i % 2 for i, c in enumerate(cities)}
        texto = montar_ordem_global(cities, alocacao)
        assert "Última entrega global:" in texto
        assert obter_nome(cities[-1]) in texto

    def test_montar_rotas_por_veiculo(self):
        cities = configurar_cenario_fixo(5)
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

    def test_gerar_alocacao_indices_validos(self):
        alocacao = ga.gerar_alocacao_aleatoria(CIDADES_AG, num_veiculos=3)
        assert len(alocacao) == 4
        assert all(0 <= alocacao[c] < 3 for c in CIDADES_AG)

    def test_reparar_alocacao_nao_forca_veiculo_vazio(self):
        rota = CIDADES_AG.copy()
        alocacao = {c: 0 for c in rota}
        reparada = ga.reparar_alocacao(alocacao, rota, num_veiculos=6)
        rotas = ga.dividir_rota_em_veiculos(rota, reparada, num_veiculos=6)
        assert len(rotas) == 6
        assert sum(len(r) for r in rotas) == 4
        assert sum(1 for r in rotas if not r) >= 2

    def test_veiculos_excedentes_permanecem_ociosos(self):
        _configurar_dados_ag()
        cidades = [(i * 10, 0) for i in range(5)]
        for cidade in cidades:
            ga.city_priorities[cidade] = 5
            ga.city_demands[cidade] = 10
        rota = cidades.copy()
        alocacao = {c: 0 for c in cidades}
        rotas = ga.dividir_rota_em_veiculos(rota, alocacao, num_veiculos=8)
        assert len(rotas) == 8
        assert sum(len(r) for r in rotas) == 5
        assert sum(1 for r in rotas if not r) == 7
        fitness_5v = ga.calculate_fitness(rota, alocacao, num_veiculos=5)
        fitness_8v = ga.calculate_fitness(rota, alocacao, num_veiculos=8)
        assert fitness_8v < fitness_5v

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

    def test_solucao_otima_omitida_mais_veiculos_que_entregas(self):
        otimo = ga.calcular_solucao_otima_vrp(CIDADES_AG, num_veiculos=8, limite_cidades=10)
        assert math.isnan(otimo)

    def test_solucao_otima_omitida_7_entregas(self):
        cities = DEFAULT_PROBLEMS[10][:7]
        otimo = ga.calcular_solucao_otima_vrp(cities, num_veiculos=4, limite_cidades=7)
        assert math.isnan(otimo)

    def test_solucao_otima_6_entregas_calculada(self):
        cities = DEFAULT_PROBLEMS[10][:6]
        otimo = ga.calcular_solucao_otima_vrp(cities, num_veiculos=4, limite_cidades=7)
        assert otimo > 0

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
        cities = configurar_cenario_fixo(5)

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
        from tests.fixtures_dados import CHAT_V3_ROTAS, CHAT_V3_VEICULOS

        texto = gerar_instrucoes_rota(
            CHAT_V3_VEICULOS,
            prioridade_10=2,
            prioridade_9_10=3,
            texto_rotas_detalhado=CHAT_V3_ROTAS,
        )
        assert "GUIA PARA MOTORISTAS" in texto
        assert "Trajetória" in texto
        assert "79/80" in texto

    def test_contexto_ia_carregado(self):
        from groq_contexto import carregar_contexto_sistema

        ctx = carregar_contexto_sistema()
        assert "VRP" in ctx
        assert "kit" in ctx.lower()

    def test_historico_conversa_no_prompt(self, monkeypatch):
        prompts: list[str] = []

        def _fake(prompt, fallback, *, temperature=0.2, system=None, max_tokens=None):
            prompts.append(prompt)
            return "O veículo 2 percorreu 865 km."

        monkeypatch.setattr("groq_perguntas.chamar_llm", _fake)
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
        assert "865" in texto
        assert "Qual veículo tem maior carga?" in prompts[0]

    def test_prompt_inclui_analise_benchmark_e_guia(self, monkeypatch):
        prompts: list[str] = []

        def _capturar(prompt, fallback, *, temperature=0.2, system=None, max_tokens=None):
            prompts.append(prompt)
            return "ok"

        monkeypatch.setattr("groq_perguntas.chamar_llm", _capturar)
        from groq_perguntas import responder_pergunta

        responder_pergunta(
            "Como foi o desempenho do AG?",
            "Veículo 1 | 2 entregas | carga 20/40",
            "Resumo rota",
            "Ordem paradas",
            "TEXTO_ANALISE_AG",
            "TEXTO_RELATORIO_DIA",
            "TEXTO_RELATORIO_SEM",
            "TEXTO_GUIA_MOTORISTAS",
            texto_benchmark="TEXTO_BENCHMARK_METRICAS",
            texto_parametros_ag="População: 100",
            texto_resumo_semanal_projecao="Projeção 5 dias",
            texto_entregas_coordenadas="1. UTI (10,20)",
        )
        assert len(prompts) == 1
        corpo = prompts[0]
        # Prompt enxuto (economia de tokens): mantém dados brutos + benchmark,
        # mas NÃO reenvia textos gerados pela própria IA (análise/relatórios/guia).
        assert "TEXTO_BENCHMARK_METRICAS" in corpo
        assert "MÉTRICAS E BENCHMARK" in corpo
        assert "População: 100" in corpo
        assert "Projeção 5 dias" in corpo
        assert "TEXTO_ANALISE_AG" not in corpo
        assert "TEXTO_RELATORIO_DIA" not in corpo
        assert "TEXTO_GUIA_MOTORISTAS" not in corpo


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


class TestGroqGuiaMotoristas:
    """Guia da aba Instruções (groq_rotas) — não é o chat do painel."""

    def test_instrucoes_veiculo_local_prioridade_correta(self):
        from groq_respostas_locais import gerar_instrucoes_veiculo_local

        texto = gerar_instrucoes_veiculo_local(3, CHAT_V3_VEICULOS, CHAT_V3_ROTAS)
        assert "Unidade Domiciliar 11" in texto
        assert "p10" in texto or "(10 prioridade" in texto
        assert "Hemodiálise 15 (p4)" not in texto
        assert "Siga a ordem" in texto or "Trajetória" in texto


class TestGroqChat:
    """Chat do painel — sempre via Groq, sem templates locais."""

    def test_chat_sempre_chama_groq(self, monkeypatch):
        capturado: dict = {}

        def _fake_groq(prompt, fallback, *, temperature=0.2, system=None, max_tokens=None):
            capturado["prompt"] = prompt
            capturado["temperature"] = temperature
            capturado["system"] = system
            return "Hoje temos 4 entregas críticas na operação."

        monkeypatch.setattr("groq_perguntas.chamar_llm", _fake_groq)
        from groq_perguntas import responder_pergunta

        resposta = responder_pergunta(
            "Quantos criticos entregues?",
            CHAT_V3_VEICULOS,
            "resumo",
            CHAT_V3_ROTAS,
            "", "", "", "",
        )
        assert resposta == "Hoje temos 4 entregas críticas na operação."
        assert capturado["temperature"] == 0.7
        assert "INTERPRETAR" in capturado["system"]
        assert "memória interna" in capturado["prompt"]

    def test_chat_prompt_inclui_todos_os_blocos(self, monkeypatch):
        prompts: list[str] = []

        def _fake_groq(prompt, fallback, *, temperature=0.2, system=None, max_tokens=None):
            prompts.append(prompt)
            return "ok"

        monkeypatch.setattr("groq_perguntas.chamar_llm", _fake_groq)
        from groq_perguntas import responder_pergunta

        responder_pergunta(
            "Como foi o AG?",
            "Veículo 1 | 2 entregas",
            "Resumo rota",
            "Ordem paradas",
            "TEXTO_ANALISE",
            "TEXTO_RELATORIO_DIA",
            "TEXTO_RELATORIO_SEM",
            "TEXTO_GUIA_MOTORISTAS",
            texto_benchmark="TEXTO_BENCHMARK",
            texto_parametros_ag="População: 100",
        )
        corpo = prompts[0]
        # Prompt enxuto: dados brutos + benchmark presentes; textos gerados pela
        # IA (análise/relatórios/guia) NÃO são reenviados (economia de tokens).
        assert "TEXTO_BENCHMARK" in corpo
        assert "População: 100" in corpo
        assert "Ordem paradas" in corpo
        assert "TEXTO_ANALISE" not in corpo
        assert "TEXTO_GUIA_MOTORISTAS" not in corpo

    def test_fallback_indisponivel_sem_dump_de_dados(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_perguntas import responder_pergunta

        resposta = responder_pergunta(
            "Quantos kits o veículo 2 entregou?",
            CHAT_V2_VEICULOS,
            "resumo",
            CHAT_V2_ROTAS,
            "", "", "", "",
        )
        assert "indisponível" in resposta.lower() or "GROQ" in resposta.lower()
        assert "3 entrega(s)" not in resposta
        assert "Veículos:" not in resposta


# =============================================================================
# Dashboard — mapa com entregues vs remanescentes
# =============================================================================


class TestDashboardMapa:
    def test_estilo_entregue_tem_ordem(self):
        from dashboard_ui import _estilo_no_mapa

        cidade = (100, 200)
        ordem = {cidade: 3}
        estilo = _estilo_no_mapa(
            cidade, ordem, set(), {cidade: 10}, {cidade: "CRITICO"}
        )
        assert estilo["label"] == "3"
        assert estilo["no_hospital"] is False
        assert estilo["fill"] == "#b91c1c"

    def test_estilo_remanescente_hospital(self):
        from dashboard_ui import _estilo_no_mapa

        cidade = (100, 200)
        estilo = _estilo_no_mapa(
            cidade, {}, {cidade}, {cidade: 2}, {cidade: "INSUMO"}
        )
        assert estilo["label"] == "—"
        assert estilo["no_hospital"] is True
        assert estilo["fill"] == "#94a3b8"

    def test_estilos_para_todas_cidades_20_com_corte(self):
        from dashboard_ui import _estilo_no_mapa

        random.seed(99)
        cities = [
            (random.randint(60, 790), random.randint(10, 390))
            for _ in range(20)
        ]
        configurar_cenario(cities, seed=99, n_cidades=20, modo="aleatorio")
        path = cities.copy()
        random.shuffle(path)
        alocacao = {c: i % 2 for i, c in enumerate(path)}
        resultado = priorizar_entregas_capacidade(
            path, alocacao, num_veiculos=2, capacidade_veiculo=40
        )

        ordem_visita = {
            c: i + 1 for i, c in enumerate(resultado["path_efetivo"])
        }
        remanescentes = set(resultado["remanescentes"])

        for cidade in cities:
            estilo = _estilo_no_mapa(
                cidade,
                ordem_visita,
                remanescentes,
                ga.city_priorities,
                ga.city_types,
            )
            assert estilo["label"]
            if cidade in remanescentes:
                assert estilo["no_hospital"] is True
                assert estilo["label"] == "—"
            else:
                assert estilo["no_hospital"] is False
                assert estilo["label"] == str(ordem_visita[cidade])

        assert len(resultado["path_efetivo"]) + len(remanescentes) == 20
        assert len(remanescentes) > 0


class TestMapaVeiculosOciosos:
    def test_indices_veiculos_ociosos(self):
        from draw_functions import indices_veiculos_ociosos

        rotas = [[(0, 0)], [], [(1, 1)], [], []]
        assert indices_veiculos_ociosos(rotas) == [1, 3, 4]

    def test_posicoes_marcadores_quantidade(self):
        from draw_functions import posicoes_marcadores_veiculos_ociosos

        posicoes = posicoes_marcadores_veiculos_ociosos((400, 200), 5)
        assert len(posicoes) == 5
        assert len(set(posicoes)) == 5

    def test_montar_legenda_veiculos_em_rota_e_hospital(self):
        from dashboard_ui import NOMES_CORES_VEICULOS
        from draw_functions import montar_legenda_veiculos

        rotas = [[(0, 0)], [], [(1, 1)], [], [], [], [], []]
        texto = montar_legenda_veiculos(rotas, NOMES_CORES_VEICULOS)
        assert "Em rota:" in texto
        assert "V1 azul" in texto
        assert "V3 verde" in texto
        assert "No hospital:" in texto
        assert "V2 vermelho (ocioso)" in texto
        assert "V8 cinza (ocioso)" in texto

    def test_veiculo_ativo_nao_listado_como_ocioso(self):
        from draw_functions import indices_veiculos_ociosos

        rotas = [[(0, 0)], [], [], [(1, 1)], [], [], [], []]
        ociosos = indices_veiculos_ociosos(rotas)
        assert 0 not in ociosos
        assert 3 not in ociosos
        assert 1 in ociosos
        assert 6 in ociosos

    def test_posicao_label_trecho(self):
        from draw_functions import _posicao_label_trecho

        p = _posicao_label_trecho((0, 0), (10, 0), offset=5)
        assert p == (5, 0)


class TestDashboardAnalise:
    def _metricas_exemplo(self, **kwargs) -> "MetricasComparativoMetodos":
        from metricas_benchmark import MetricasComparativoMetodos

        base = dict(
            fitness_inicial=3200.0,
            distancia_inicial=3300.0,
            fitness_final=2800.0,
            fitness_final_prioridade=2900.0,
            melhoria_fitness_pct=9.38,
            melhoria_distancia_pct=15.15,
            geracao_convergencia=190,
            distancia_aleatoria=3100.0,
            distancia_vizinho_proximo=2950.0,
            distancia_greedy_prioridade=2880.0,
            fitness_target_solution=2750.0,
            diferenca_benchmark_pct=1.82,
            num_veiculos=4,
            total_entregas=5,
            motivo_otimo_omitido="",
        )
        base.update(kwargs)
        return MetricasComparativoMetodos(**base)

    def test_bloco_analise_com_otimo(self):
        from metricas_benchmark import montar_bloco_analise_metricas

        bloco = montar_bloco_analise_metricas(self._metricas_exemplo())
        assert "Ótimo VRP (força bruta)" in bloco
        assert "2750.00" in bloco
        assert "1.82%" in bloco
        assert "Vizinho mais próximo" in bloco
        assert "Greedy por prioridade" in bloco
        assert "Melhoria de fitness" in bloco

    def test_bloco_analise_sem_otimo_muitas_entregas(self):
        from metricas_benchmark import montar_bloco_analise_metricas

        bloco = montar_bloco_analise_metricas(
            self._metricas_exemplo(
                fitness_target_solution=float("nan"),
                diferenca_benchmark_pct=float("nan"),
                total_entregas=13,
                motivo_otimo_omitido="13 entregas (≥ 7): limitações computacionais",
            )
        )
        assert "N/A" in bloco
        assert "≥ 7" in bloco or "13 entregas" in bloco

    def test_bloco_analise_sem_otimo_excesso_veiculos(self):
        from metricas_benchmark import (
            MetricasComparativoMetodos,
            montar_bloco_analise_metricas,
            motivo_omissao_benchmark,
        )

        motivo = motivo_omissao_benchmark(8, 4, 7, float("nan"))
        bloco = montar_bloco_analise_metricas(
            MetricasComparativoMetodos(
                fitness_inicial=2000,
                distancia_inicial=2100,
                fitness_final=1200,
                fitness_final_prioridade=1300,
                melhoria_fitness_pct=35,
                melhoria_distancia_pct=42,
                geracao_convergencia=50,
                distancia_aleatoria=1500,
                distancia_vizinho_proximo=1400,
                distancia_greedy_prioridade=1350,
                fitness_target_solution=float("nan"),
                diferenca_benchmark_pct=float("nan"),
                num_veiculos=8,
                total_entregas=4,
                motivo_otimo_omitido=motivo,
            )
        )
        assert "veículos ≤ entregas" in bloco


class TestMetricasBenchmark:
    def test_calcular_heuristicas_retorna_distancias(self):
        from metricas_benchmark import calcular_distancias_heuristicas
        from config import DEFAULT_PROBLEMS

        cities = DEFAULT_PROBLEMS[5]
        dist_nn, dist_gr = calcular_distancias_heuristicas(cities, num_veiculos=2)
        assert dist_nn > 0
        assert dist_gr > 0

    def test_motivo_omissao_7_entregas(self):
        from metricas_benchmark import motivo_omissao_benchmark

        motivo = motivo_omissao_benchmark(4, 7, 7, float("nan"))
        assert "≥ 7" in motivo

    def test_bloco_contem_todas_metricas_ag(self):
        from metricas_benchmark import montar_bloco_analise_metricas

        bloco = montar_bloco_analise_metricas(
            TestDashboardAnalise()._metricas_exemplo()
        )
        assert "Distância inicial (população)" in bloco
        assert "3300.00" in bloco
        assert "Geração de convergência" in bloco
        assert "190" in bloco
        assert "Melhoria de distância" in bloco
        assert "Frota: 4 veículos | Entregas: 5" in bloco
        assert "COMPARATIVO DE MÉTODOS" in bloco
        assert "ANÁLISE RELATIVA" in bloco

    def test_economia_vs_ag_no_bloco(self):
        from metricas_benchmark import montar_bloco_analise_metricas

        bloco = montar_bloco_analise_metricas(
            TestDashboardAnalise()._metricas_exemplo()
        )
        assert "Economia vs Rota aleatória" in bloco
        assert "Economia vs Vizinho mais próximo" in bloco


# =============================================================================
# Regressão — bugs de demo real (ver fixtures_dados.REGRESSAO_18_*)
# =============================================================================


class TestRegressaoBugsUsuario:
    """Falhas encontradas em teste manual que os testes genéricos não pegavam."""

    def test_pergunta_exata_veiculo_3_instrucoes(self):
        from groq_rotas import montar_instrucoes_motoristas
        from tests.validadores_ia import assert_instrucoes_veiculo_coerentes

        resposta = montar_instrucoes_motoristas(
            REGRESSAO_18_VEICULOS,
            REGRESSAO_18_ROTAS,
        )
        assert_instrucoes_veiculo_coerentes(resposta, 3, capacidade=80)
        assert "1." in resposta and "5." in resposta
        assert "Hemodiálise 15" in resposta
        assert "Priorize" not in resposta or "Hemodiálise 15 (p4)" not in resposta.split("Prioridade")[0]

    def test_nao_prioriza_ultima_parada_p4_como_foco(self):
        from groq_respostas_locais import gerar_instrucoes_veiculo_local
        from tests.validadores_ia import assert_instrucoes_veiculo_coerentes

        texto = gerar_instrucoes_veiculo_local(
            3, REGRESSAO_18_VEICULOS.split("\n")[2] + "\n", REGRESSAO_18_ROTAS
        )
        assert_instrucoes_veiculo_coerentes(texto, 3)
        assert "Unidade Domiciliar 11 (p10)" in texto or "p10" in texto

    def test_veiculo_4_capacidade_respeitada_apos_priorizacao(self):
        from groq_respostas_locais import gerar_instrucoes_veiculo_local

        texto = gerar_instrucoes_veiculo_local(
            4,
            REGRESSAO_18_VEICULO_4_POS_PRIORIZACAO,
            REGRESSAO_18_ROTAS,
        )
        assert "81/80" not in texto
        assert "com restrição" not in texto.lower() or "autonomia" in texto.lower()

    def test_benchmark_18_entregas_retorna_nan(self):
        cities = [(i * 10, i * 5) for i in range(18)]
        otimo = ga.calcular_solucao_otima_vrp(cities, num_veiculos=4, limite_cidades=7)
        assert math.isnan(otimo)

    def test_fallback_analise_18_entregas_explica_na(self):
        from groq_analysis import _fallback_analisar
        from tests.validadores_ia import assert_analise_benchmark_na_ok

        texto = _fallback_analisar(**kwargs_fallback_analise_18_entregas())
        assert_analise_benchmark_na_ok(texto)

    def test_conteudo_fallback_18_entregas_sem_eco_nas_abas(self, monkeypatch):
        monkeypatch.setenv("GROQ_DESABILITADO", "1")
        from groq_conteudo import gerar_conteudo_completo
        from tests.validadores_ia import assert_todas_abas_ia

        resultado = gerar_conteudo_completo(**kwargs_groq_conteudo_18_entregas())
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

        resultado = gerar_conteudo_completo(**kwargs_groq_conteudo_18_entregas())
        assert_todas_abas_ia(resultado)
        assert "44%" in resultado["analise"] or "2905" in resultado["relatorio"]
        assert "81/80" in resultado["relatorio"]
        assert "p10" in resultado["instrucoes"] or "Domiciliar 11" in resultado["instrucoes"]

    def test_contexto_ia_documenta_benchmark_e_prioridade(self):
        from groq_contexto import carregar_contexto_sistema

        ctx = carregar_contexto_sistema()
        assert "≥ 7 entregas" in ctx or "menos de 7 entregas" in ctx
        assert "p9" in ctx.lower() or "9–10" in ctx
        assert "última parada" in ctx.lower()


if __name__ == "__main__":
    try:
        import pytest
    except ImportError:
        print("pytest não instalado. Rode: pip install pytest")
        raise SystemExit(1)
    raise SystemExit(pytest.main([__file__, "-v"]))
