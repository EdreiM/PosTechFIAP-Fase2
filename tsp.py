import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import (
    generate_random_population,
    calculate_fitness_individuo,
    calculate_distance_only,
    calcular_distancia_operacao,
    dividir_rota_em_veiculos,
    calcular_solucao_otima_vrp,
    gerar_alocacao_aleatoria,
    crossover_vrp,
    mutate_individuo,
    sort_population,
    city_priorities,
    city_demands,
    NUM_VEICULOS,
    CAPACIDADE_VEICULO,
    DISTANCIA_MAXIMA_VEICULO,
)
from config import (
    N_CIDADES,
    POPULATION_SIZE,
    N_GENERATIONS,
    MUTATION_PROBABILITY,
    LIMITE_CIDADES_BENCHMARK,
    LIMITE_SEM_MELHORA,
    SEED,
    WIDTH,
    HEIGHT,
    NODE_RADIUS,
    FPS,
    PLOT_UPDATE_EVERY,
    PRIORIDADE_MIN,
    PRIORIDADE_MAX,
    DEMANDA_MIN,
    DEMANDA_MAX,
    obter_cidades,
)
from draw_functions import draw_paths, create_plot_surface, draw_cities
import sys
import math
import numpy as np

from groq_analysis import analisar_resultado
from groq_relatorio import gerar_relatorio_operacional
from groq_relatorio_semanal import gerar_relatorio_semanal
from groq_perguntas import responder_pergunta
from groq_rotas import gerar_instrucoes_rota
from dashboard_ui import abrir_dashboard

# Cores da interface (específicas da simulação Pygame)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
CORES_VEICULOS = [
    (37, 99, 235),
    (220, 38, 38),
    (22, 163, 74),
]

cities_locations = obter_cidades()

random.seed(SEED)

for city in cities_locations:
    city_priorities[city] = random.randint(PRIORIDADE_MIN, PRIORIDADE_MAX)
    city_demands[city] = random.randint(DEMANDA_MIN, DEMANDA_MAX)

print("\nPRIORIDADES DAS CIDADES")
print("-" * 50)

for indice, (cidade, prioridade) in enumerate(city_priorities.items(), start=1):
    print(f"Cidade {indice}: Prioridade {prioridade}")

print(f"Quantidade de cidades: {len(cities_locations)}")

population = generate_random_population(cities_locations, POPULATION_SIZE)
fitness_target_solution = None

# Initialize Pygame (após preparar dados — janela abre já pronta para simular)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Logística — Simulação AG")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)
plot_surface = create_plot_surface([1], [0], y_label="Fitness (distância + restrições)")
screen.fill(WHITE)
screen.blit(plot_surface, (0, 0))
draw_cities(screen, cities_locations, RED, NODE_RADIUS)
pygame.display.flip()

# Using att48 benchmark (48 cidades)
# WIDTH, HEIGHT = 1500, 800
# att_cities_locations = np.array(att_48_cities_locations)
# ...

best_fitness_values = []
best_solutions = []




# Guarda a fitness da primeira geração
fitness_inicial = None
distancia_inicial = None
melhor_fitness_global = float("inf")

geracoes_sem_melhora = 0

geracao_convergencia = None
# Main game loop

running = True
generation = 0 

### while running:
while running and generation < N_GENERATIONS:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    generation = next(generation_counter)

    screen.fill(WHITE)

    if plot_surface is not None:
        screen.blit(plot_surface, (0, 0))

    population_fitness = [
        calculate_fitness_individuo(ind) for ind in population
    ]

    population, population_fitness = sort_population(
        population, population_fitness)

    best_fitness = population_fitness[0]
    best_path, best_alocacao = population[0]

    if best_fitness < melhor_fitness_global:

        melhor_fitness_global = best_fitness
        geracoes_sem_melhora = 0

    else:
        geracoes_sem_melhora += 1

    if fitness_inicial is None:
        fitness_inicial = best_fitness
        distancia_inicial = calcular_distancia_operacao(
            best_path, best_alocacao
        )

    best_fitness_values.append(best_fitness)
    best_solutions.append((best_path, best_alocacao))

    draw_cities(screen, cities_locations, RED, NODE_RADIUS)
    for indice, rota in enumerate(
        dividir_rota_em_veiculos(best_path, best_alocacao)
    ):
        if len(rota) >= 2:
            draw_paths(
                screen,
                rota,
                CORES_VEICULOS[indice % len(CORES_VEICULOS)],
                width=3,
            )

    if generation == 1 or generation % PLOT_UPDATE_EVERY == 0:
        plot_surface = create_plot_surface(
            list(range(1, len(best_fitness_values) + 1)),
            best_fitness_values,
            y_label="Fitness (distância + restrições)",
        )
        screen.blit(plot_surface, (0, 0))

    if generation % 50 == 0:

        print(
            f"Generation {generation}: "
            f"Best fitness = {round(best_fitness, 2)} | "
            f"Sem melhora = {geracoes_sem_melhora}"
        )

    if geracoes_sem_melhora >= LIMITE_SEM_MELHORA:

        geracao_convergencia = generation

        print("\nConvergência detectada.")
        print(
            f"Sem melhoria por "
            f"{LIMITE_SEM_MELHORA} gerações."
        )

        break

    new_population = [population[0]]  # Keep the best individual: ELITISM

    while len(new_population) < POPULATION_SIZE:

        # selection
        # simple selection based on first 10 best solutions
        # parent1, parent2 = random.choices(population[:10], k=2)

        # solution based on fitness probability
        probability = 1 / np.array(population_fitness)
        parent1, parent2 = random.choices(population, weights=probability, k=2)

        child1 = crossover_vrp(parent1, parent2)
        child1 = mutate_individuo(child1, MUTATION_PROBABILITY)

        new_population.append(child1)

    population = new_population

    pygame.display.flip()
    clock.tick(FPS)


# TODO: save the best individual in a file if it is better than the one saved.


# Fitness usado pelo AG (distância + prioridade)
fitness_final_prioridade = best_fitness_values[-1]

best_path, best_alocacao = best_solutions[-1]

print("Calculando benchmark VRP (força bruta)...")
fitness_target_solution = calcular_solucao_otima_vrp(
    cities_locations,
    NUM_VEICULOS,
    LIMITE_CIDADES_BENCHMARK,
)
if not math.isnan(fitness_target_solution):
    print(
        f"Solução ótima VRP ({NUM_VEICULOS} veículos): "
        f"{fitness_target_solution:.2f}"
    )
else:
    print(
        f"Benchmark exato omitido: mais de {LIMITE_CIDADES_BENCHMARK} cidades "
        f"(ordem + alocação)."
    )

fitness_final = calcular_distancia_operacao(best_path, best_alocacao)

rotas_veiculos = dividir_rota_em_veiculos(best_path, best_alocacao)
ordens_veiculos = [[] for _ in range(NUM_VEICULOS)]

for indice, cidade in enumerate(best_path):
    ordens_veiculos[best_alocacao[cidade]].append(indice + 1)

dados_veiculos = []
texto_veiculos = ""

print("\nROTAS DOS VEÍCULOS")
print("=" * 50)

for indice, rota in enumerate(rotas_veiculos, start=1):

    carga = sum(city_demands[cidade] for cidade in rota)
    distancia = calculate_distance_only(rota) if rota else 0
    capacidade_ok = carga <= CAPACIDADE_VEICULO
    autonomia_ok = distancia <= DISTANCIA_MAXIMA_VEICULO
    status = (
        "operacionalmente viável"
        if capacidade_ok and autonomia_ok
        else "com restrição"
    )

    ordens = ordens_veiculos[indice - 1]
    amostra_ordens = ordens[:5]
    resumo_ordens = ", ".join(
        f"{o}(p{city_priorities[best_path[o - 1]]})"
        for o in amostra_ordens
    )
    if len(ordens) > 5:
        resumo_ordens += f", ... (+{len(ordens) - 5})"

    dados_veiculos.append({
        "veiculo": indice,
        "cidades": len(rota),
        "carga": carga,
        "distancia": distancia,
        "capacidade_ok": capacidade_ok,
        "autonomia_ok": autonomia_ok,
        "status": status,
    })

    linha = (
        f"Veículo {indice} | {len(rota)} cidades | "
        f"carga {carga}/{CAPACIDADE_VEICULO} | "
        f"distância {distancia:.0f}/{DISTANCIA_MAXIMA_VEICULO} | "
        f"status: {status}\n"
        f"  Primeiras paradas: {resumo_ordens}\n"
    )
    texto_veiculos += linha

    print(f"Veículo {indice}")
    print(f"Cidades: {len(rota)}")
    print(f"Carga: {carga}/{CAPACIDADE_VEICULO}")
    print(f"Distância: {distancia:.2f}/{DISTANCIA_MAXIMA_VEICULO}")
    print(f"Status: {status}")
    print("-" * 50)

distancia_total_rota = fitness_final
capacidade_veiculo = CAPACIDADE_VEICULO
distancia_maxima_veiculo = DISTANCIA_MAXIMA_VEICULO

rota_aleatoria = random.sample(cities_locations, len(cities_locations))
alocacao_aleatoria = gerar_alocacao_aleatoria(cities_locations)
distancia_aleatoria = calcular_distancia_operacao(
    rota_aleatoria, alocacao_aleatoria
)

# Calcula a melhoria percentual usando a mesma métrica do algoritmo:
# distância + penalidade de prioridade.
melhoria_percentual = (
    (fitness_inicial - fitness_final_prioridade)
    / fitness_inicial
) * 100

if math.isnan(fitness_target_solution):
    diferenca_benchmark = float("nan")
    otimo_txt = "N/A"
else:
    diferenca_benchmark = (
        (fitness_final - fitness_target_solution)
        / fitness_target_solution
    ) * 100
    otimo_txt = f"{fitness_target_solution:.2f}"

print("\n" + "=" * 60)
print("RESULTADOS FINAIS")
print("=" * 60)

print(f"Fitness inicial: {fitness_inicial:.2f}")
print(f"Fitness final:   {fitness_final:.2f}")
print(f"Fitness com prioridade: {fitness_final_prioridade:.2f}")
melhoria_prioridade = (
    (fitness_inicial - fitness_final_prioridade)
    / fitness_inicial
) * 100

melhoria_distancia = (
    (distancia_inicial - fitness_final)
    / distancia_inicial
) * 100

print(
    f"Melhoria (fitness): "
    f"{melhoria_prioridade:.2f}%"
)

print(
    f"Melhoria (distância): "
    f"{melhoria_distancia:.2f}%"
)

print(f"Solução ótima VRP:  {fitness_target_solution:.2f}" if not math.isnan(fitness_target_solution) else "Solução ótima VRP:  N/A")
print(f"Diferença para ótimo: {diferenca_benchmark:.2f}%" if not math.isnan(diferenca_benchmark) else "Diferença para ótimo: N/A")
print(f"Distância rota aleatória: {distancia_aleatoria:.2f}")
print(
    f"Comparativo VRP -> AG: {fitness_final:.2f} | "
    f"Aleatória: {distancia_aleatoria:.2f} | "
    f"Ótimo: {otimo_txt}"
)

print(f"Distância total da operação: {distancia_total_rota:.2f}")

todos_viaveis = all(
    v["capacidade_ok"] and v["autonomia_ok"]
    for v in dados_veiculos
)
print(
    "Todos os veículos respeitam capacidade e autonomia."
    if todos_viaveis
    else "Há veículo(s) com restrição de capacidade ou autonomia."
)
print("\nTOP 10 CIDADES DA ROTA FINAL")
print("-" * 50)

for indice, cidade in enumerate(best_path[:10], start=1):

    prioridade = city_priorities[cidade]

    print(
        f"Posição {indice} -> Prioridade {prioridade}"
    )


top10_prioridades = []

for cidade in best_path[:10]:
    top10_prioridades.append(
        city_priorities[cidade]
    )    

rota_detalhada = []

for indice, cidade in enumerate(best_path, start=1):

    prioridade = city_priorities[cidade]

    nome_cidade = f"Cidade {indice}"

    rota_detalhada.append({
        "ordem": indice,
        "nome": nome_cidade,
        "x": cidade[0],
        "y": cidade[1],
        "prioridade": prioridade,
        "demanda": city_demands[cidade],
        "veiculo": best_alocacao[cidade] + 1,
    })
# ==========================
# ANÁLISE DA IA (GROQ)
# ==========================

# Quantidade de cidades prioridade 10
prioridade_10 = sum(
    1 for cidade in rota_detalhada
    if cidade["prioridade"] == 10
)

# Quantidade de cidades prioridade 9 ou 10
prioridade_9_10 = sum(
    1 for cidade in rota_detalhada
    if cidade["prioridade"] >= 9
)

# Média das prioridades das 10 primeiras posições
media_top10 = (
    sum(top10_prioridades)
    / len(top10_prioridades)
)

# Soma toda a demanda da rota
carga_total = sum(
    item["demanda"]
    for item in rota_detalhada
)



print(f"Carga total da operação: {carga_total}")
print(f"Capacidade por veículo: {capacidade_veiculo}")

texto_rota = ""

for item in rota_detalhada:

    texto_rota += (
        f"Ordem {item['ordem']} | "
        f"Nome={item['nome']} | "
        f"X={item['x']} | "
        f"Y={item['y']} | "
        f"Prioridade={item['prioridade']} | "
        f"Demanda={item['demanda']}\n"
    )

top10_resumo = ", ".join(
    f"pos{i}(p{city_priorities[c]})"
    for i, c in enumerate(best_path[:10], start=1)
)
texto_rota_resumo = (
    f"Total: {len(rota_detalhada)} cidades | "
    f"Distância total: {distancia_total_rota:.0f} | "
    f"Carga total: {carga_total} | "
    f"Veículos: {NUM_VEICULOS}\n"
    f"Top 10 posições: {top10_resumo}\n"
    f"Prioridade 10: {prioridade_10} cidades | "
    f"Prioridade 9-10: {prioridade_9_10} cidades"
)

if geracao_convergencia is None:
    geracao_convergencia = generation

print("\nGerando análise, relatório e instruções com IA...")

analise = analisar_resultado(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    melhoria_prioridade,
    melhoria_distancia,
    fitness_target_solution,
    diferenca_benchmark,
    top10_prioridades,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    len(rota_detalhada),
    NUM_VEICULOS,
    distancia_aleatoria,
)

relatorio = gerar_relatorio_operacional(
    fitness_final,
    melhoria_distancia,
    diferenca_benchmark,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    texto_veiculos,
    len(rota_detalhada),
    NUM_VEICULOS,
    distancia_aleatoria,
    fitness_target_solution,
)

economia_diaria_km = max(distancia_aleatoria - fitness_final, 0)
texto_resumo_semanal = (
    f"Período: semana operacional (5 dias úteis simulados)\n"
    f"Cidades atendidas por dia: {len(rota_detalhada)}\n"
    f"Entregas totais na semana: {len(rota_detalhada) * 5}\n"
    f"Veículos na frota: {NUM_VEICULOS}\n"
    f"Distância média diária: {fitness_final:.2f}\n"
    f"Distância total semanal estimada: {fitness_final * 5:.2f}\n"
    f"Carga média diária: {carga_total}\n"
    f"Carga total semanal estimada: {carga_total * 5}\n"
    f"Melhoria de distância (AG vs início): {melhoria_distancia:.2f}%\n"
    f"Melhoria de fitness (AG): {melhoria_prioridade:.2f}%\n"
    f"Economia diária vs rota aleatória: {economia_diaria_km:.2f}\n"
    f"Economia semanal estimada vs aleatória: {economia_diaria_km * 5:.2f}\n"
    f"Geração de convergência do AG: {geracao_convergencia}\n"
    f"Cidades prioridade 10 (por dia): {prioridade_10}\n"
    f"Cidades prioridade 9-10 (por dia): {prioridade_9_10}\n"
    f"Comparativo VRP -> AG: {fitness_final:.2f} | "
    f"Aleatória: {distancia_aleatoria:.2f} | "
    f"Ótimo: {otimo_txt}"
)

relatorio_semanal = gerar_relatorio_semanal(
    texto_resumo_semanal,
    texto_veiculos,
    relatorio,
)

instrucoes = gerar_instrucoes_rota(
    texto_veiculos,
    prioridade_10,
    prioridade_9_10,
)

print("Conteúdo gerado. Abrindo painel com abas...")

# Salva o resultado em arquivo texto

with open("melhor_rota.txt", "w", encoding="utf-8") as arquivo:

    arquivo.write("RESULTADOS DO ALGORITMO GENÉTICO\n")

    
    arquivo.write("PARÂMETROS UTILIZADOS\n")
    arquivo.write("-" * 50 + "\n")

    arquivo.write(f"População: {POPULATION_SIZE}\n")
    arquivo.write(f"Gerações: {N_GENERATIONS}\n")
    arquivo.write(f"Taxa de mutação: {MUTATION_PROBABILITY}\n")
    arquivo.write(f"Cidades: {len(cities_locations)}\n")
    arquivo.write(f"Veículos: {NUM_VEICULOS}\n")
    arquivo.write(f"Capacidade por veículo: {CAPACIDADE_VEICULO}\n")
    arquivo.write(f"Autonomia por veículo: {DISTANCIA_MAXIMA_VEICULO}\n\n")

    arquivo.write(
        f"Geração de convergência: {geracao_convergencia}\n\n"
    )
    
    arquivo.write("PRIORIDADES DAS CIDADES\n")
    arquivo.write("-" * 50 + "\n")

    for indice, (cidade, prioridade) in enumerate(city_priorities.items(), start=1):
        arquivo.write(f"Cidade {indice}: prioridade {prioridade}\n")

    arquivo.write("\n")
   
    arquivo.write("=" * 50 + "\n\n")

    arquivo.write(f"Fitness inicial: {fitness_inicial:.2f}\n")
    arquivo.write(f"Fitness final: {fitness_final:.2f}\n")
    arquivo.write(f"Fitness com prioridade: {fitness_final_prioridade:.2f}\n")
    arquivo.write(
        f"Melhoria (fitness): {melhoria_prioridade:.2f}%\n"
    )

    arquivo.write(
        f"Melhoria (distância): {melhoria_distancia:.2f}%\n\n"
    )

    arquivo.write(
        f"Solução ótima: {otimo_txt}\n\n"
    )

    if math.isnan(diferenca_benchmark):
        arquivo.write("Diferença para ótimo VRP: N/A\n\n")
    else:
        arquivo.write(
            f"Diferença para ótimo VRP: {diferenca_benchmark:.2f}%\n\n"
        )

    arquivo.write(
        f"Comparativo VRP -> AG: {fitness_final:.2f} | "
        f"Aleatória: {distancia_aleatoria:.2f} | "
        f"Ótimo: {otimo_txt}\n\n"
    )




    arquivo.write("Melhor rota encontrada:\n")

    for indice, cidade in enumerate(best_path, start=1):

        prioridade = city_priorities[cidade]
        veiculo = best_alocacao[cidade] + 1

        arquivo.write(
            f"{indice}. {cidade} | Veículo: {veiculo} | Prioridade: {prioridade}\n"
        )

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("ANÁLISE GERADA PELA IA\n")
    arquivo.write("=" * 50 + "\n\n")

    arquivo.write(analise)
    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("RELATÓRIO OPERACIONAL DIÁRIO\n")
    arquivo.write("=" * 50 + "\n\n")
    arquivo.write(relatorio)

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("RELATÓRIO OPERACIONAL SEMANAL\n")
    arquivo.write("=" * 50 + "\n\n")
    arquivo.write(relatorio_semanal)

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("INSTRUÇÕES DE ENTREGA\n")
    arquivo.write("=" * 50 + "\n\n")
    arquivo.write(instrucoes)

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("STATUS DOS VEÍCULOS\n")
    arquivo.write("=" * 50 + "\n\n")
    arquivo.write(texto_veiculos)

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("ROTA DETALHADA\n")
    arquivo.write("=" * 50 + "\n\n")

    for item in rota_detalhada:

        arquivo.write(
            f"Ordem: {item['ordem']} | "
            f"Veículo: {item['veiculo']} | "
            f"X: {item['x']} | "
            f"Y: {item['y']} | "
            f"Prioridade: {item['prioridade']} | "
            f"Demanda: {item['demanda']}\n"
        )


def _responder_pergunta_chat(pergunta):
    return responder_pergunta(
        pergunta,
        texto_veiculos,
        texto_rota_resumo,
        analise,
        relatorio,
        relatorio_semanal,
        instrucoes,
    )


pygame.quit()

abrir_dashboard(
    best_solution=best_path,
    cities_locations=cities_locations,
    city_priorities=city_priorities,
    analise=analise,
    relatorio=relatorio,
    relatorio_semanal=relatorio_semanal,
    instrucoes=instrucoes,
    texto_veiculos=texto_veiculos,
    texto_rota_resumo=texto_rota_resumo,
    best_fitness_values=best_fitness_values,
    fitness_final=fitness_final,
    responder_pergunta_fn=_responder_pergunta_chat,
    rotas_veiculos=rotas_veiculos,
)

sys.exit()
