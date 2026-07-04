import genetic_algorithm as ga


CIDADES = [(0, 0), (10, 0), (10, 10), (0, 10)]


def configurar_dados():
    ga.city_priorities.clear()
    ga.city_demands.clear()
    for cidade in CIDADES:
        ga.city_priorities[cidade] = 5
        ga.city_demands[cidade] = 10


def test_dividir_rota_em_tres_veiculos():
    rota = CIDADES.copy()
    rotas = ga.dividir_rota_em_veiculos(rota, num_veiculos=3)

    assert len(rotas) == 3
    assert sum(len(r) for r in rotas) == len(rota)
    assert rotas[0] == [CIDADES[0], CIDADES[3]]
    assert rotas[1] == [CIDADES[1]]
    assert rotas[2] == [CIDADES[2]]


def test_calcular_distancia_operacao_soma_por_veiculo():
    rota = CIDADES.copy()
    distancia = ga.calcular_distancia_operacao(rota, num_veiculos=2)
    rotas = ga.dividir_rota_em_veiculos(rota, num_veiculos=2)
    esperado = sum(ga.calculate_distance_only(r) for r in rotas if r)

    assert distancia == esperado
    assert distancia > 0


def test_fitness_penaliza_excesso_de_carga():
    configurar_dados()
    rota = CIDADES.copy()

    fitness_ok = ga.calculate_fitness(rota, num_veiculos=2)

    for cidade in CIDADES:
        ga.city_demands[cidade] = 300

    fitness_excesso = ga.calculate_fitness(rota, num_veiculos=2)

    assert fitness_excesso > fitness_ok


def test_avaliar_restricoes_veiculos():
    configurar_dados()
    rota = CIDADES.copy()
    resumo = ga.avaliar_restricoes_veiculos(rota, num_veiculos=2)

    assert len(resumo) == 2
    assert all("viavel" in veiculo for veiculo in resumo)
    assert all(veiculo["viavel"] for veiculo in resumo)


def test_solucao_otima_vrp_poucas_cidades():
    configurar_dados()
    otimo = ga.calcular_solucao_otima_vrp(CIDADES, num_veiculos=2, limite_cidades=10)
    distancia_rota_atual = ga.calcular_distancia_operacao(CIDADES, num_veiculos=2)

    assert otimo > 0
    assert otimo <= distancia_rota_atual


def test_solucao_otima_omitida_com_muitas_cidades():
    import math

    configurar_dados()
    muitas = [(i, 0) for i in range(15)]
    otimo = ga.calcular_solucao_otima_vrp(muitas, limite_cidades=10)

    assert math.isnan(otimo)
