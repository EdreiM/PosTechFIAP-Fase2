import math

import genetic_algorithm as ga


CIDADES = [(0, 0), (10, 0), (10, 10), (0, 10)]


def configurar_dados():
    ga.city_priorities.clear()
    ga.city_demands.clear()
    for cidade in CIDADES:
        ga.city_priorities[cidade] = 5
        ga.city_demands[cidade] = 10


def test_dividir_rota_com_alocacao_explicita():
    rota = CIDADES.copy()
    alocacao = {
        CIDADES[0]: 0,
        CIDADES[1]: 1,
        CIDADES[2]: 2,
        CIDADES[3]: 0,
    }
    rotas = ga.dividir_rota_em_veiculos(rota, alocacao)

    assert len(rotas) == 3
    assert rotas[0] == [CIDADES[0], CIDADES[3]]
    assert rotas[1] == [CIDADES[1]]
    assert rotas[2] == [CIDADES[2]]


def test_dividir_rota_round_robin_sem_alocacao():
    rota = CIDADES.copy()
    rotas = ga.dividir_rota_em_veiculos(rota, num_veiculos=3)

    assert len(rotas) == 3
    assert sum(len(r) for r in rotas) == len(rota)
    assert rotas[0] == [CIDADES[0], CIDADES[3]]
    assert rotas[1] == [CIDADES[1]]
    assert rotas[2] == [CIDADES[2]]


def test_gerar_alocacao_usa_todos_veiculos():
    alocacao = ga.gerar_alocacao_aleatoria(CIDADES, num_veiculos=3)
    veiculos_usados = {alocacao[c] for c in CIDADES}

    assert len(alocacao) == len(CIDADES)
    assert veiculos_usados == {0, 1, 2}


def test_calcular_distancia_operacao_com_alocacao():
    rota = CIDADES.copy()
    alocacao = {c: i % 2 for i, c in enumerate(CIDADES)}
    distancia = ga.calcular_distancia_operacao(rota, alocacao, num_veiculos=2)
    rotas = ga.dividir_rota_em_veiculos(rota, alocacao, num_veiculos=2)
    esperado = sum(ga.calculate_distance_only(r) for r in rotas if r)

    assert distancia == esperado
    assert distancia > 0


def test_fitness_penaliza_excesso_de_carga():
    configurar_dados()
    rota = CIDADES.copy()
    alocacao = ga.gerar_alocacao_aleatoria(CIDADES, num_veiculos=2)

    fitness_ok = ga.calculate_fitness(rota, alocacao, num_veiculos=2)

    for cidade in CIDADES:
        ga.city_demands[cidade] = 300

    fitness_excesso = ga.calculate_fitness(rota, alocacao, num_veiculos=2)

    assert fitness_excesso > fitness_ok


def test_avaliar_restricoes_veiculos():
    configurar_dados()
    rota = CIDADES.copy()
    alocacao = ga.gerar_alocacao_aleatoria(CIDADES, num_veiculos=2)
    resumo = ga.avaliar_restricoes_veiculos(rota, alocacao, num_veiculos=2)

    assert len(resumo) == 2
    assert all("viavel" in veiculo for veiculo in resumo)
    assert all(veiculo["viavel"] for veiculo in resumo)


def test_melhor_alocacao_exaustiva():
    rota = CIDADES.copy()
    distancia, alocacao = ga.melhor_alocacao_exaustiva(rota, num_veiculos=2)

    assert distancia > 0
    assert len(alocacao) == len(rota)
    assert len(set(alocacao.values())) == 2


def test_crossover_vrp_preserva_cidades_e_alocacao():
    random = __import__("random")
    random.seed(0)

    ind1 = ga.criar_individuo_aleatorio(CIDADES, num_veiculos=2)
    ind2 = ga.criar_individuo_aleatorio(CIDADES, num_veiculos=2)
    filho_path, filho_aloc = ga.crossover_vrp(ind1, ind2)

    assert sorted(filho_path) == sorted(CIDADES)
    assert set(filho_aloc.keys()) == set(CIDADES)
    assert len(set(filho_aloc.values())) == 2


def test_solucao_otima_vrp_poucas_cidades():
    configurar_dados()
    otimo = ga.calcular_solucao_otima_vrp(CIDADES, num_veiculos=2, limite_cidades=10)
    rota = CIDADES.copy()
    alocacao = ga.gerar_alocacao_aleatoria(CIDADES, num_veiculos=2)
    distancia_rota_atual = ga.calcular_distancia_operacao(
        rota, alocacao, num_veiculos=2
    )

    assert otimo > 0
    assert otimo <= distancia_rota_atual


def test_solucao_otima_omitida_com_muitas_cidades():
    configurar_dados()
    muitas = [(i, 0) for i in range(15)]
    otimo = ga.calcular_solucao_otima_vrp(muitas, limite_cidades=10)

    assert math.isnan(otimo)
