import pygame
from pygame.locals import *
import random
import math
from genetic_algorithm import (
    calculate_distance_only,
    calcular_distancia_operacao,
    calcular_solucao_otima_vrp,
    dividir_rota_em_veiculos,
    gerar_alocacao_aleatoria,
    aplicar_parametros_frota,
    city_priorities,
    city_demands,
    city_names,
    city_types,
    DEPOT,
)
from config import (
    POPULATION_SIZE,
    N_GENERATIONS,
    MUTATION_PROBABILITY,
    LIMITE_CIDADES_BENCHMARK,
    LIMITE_SEM_MELHORA,
    WIDTH,
    HEIGHT,
    NODE_RADIUS,
    FPS,
    PLOT_UPDATE_EVERY,
    PLOT_WIDTH,
    MAP_X,
    MAP_WIDTH,
    UNIDADE_MEDIDA,
    UNIDADE_MEDIDA_ABREV,
    obter_cidades,
)
from dados_hospitalares import (
    aplicar_entregas,
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
    priorizar_entregas_capacidade,
    resumo_tipos,
)
from draw_functions import (
    create_plot_surface,
    criar_projecao_mapa,
    desenhar_fundo_paineis,
    draw_mapa_projecao,
)
import sys

from ag_runner import executar_ag
from groq_conteudo import gerar_conteudo_completo
from groq_perguntas import responder_pergunta
from config_ui import abrir_configuracao
from dashboard_ui import abrir_dashboard
from metricas_benchmark import (
    MetricasComparativoMetodos,
    calcular_distancias_heuristicas,
    montar_bloco_analise_metricas,
    motivo_omissao_benchmark,
)
CORES_VEICULOS = [
    (37, 99, 235),   # V1 azul
    (220, 38, 38),   # V2 vermelho
    (22, 163, 74),   # V3 verde
    (147, 51, 234),  # V4 roxo
    (234, 88, 12),   # V5 laranja
    (8, 145, 178),   # V6 ciano
    (190, 24, 93),   # V7 rosa
    (100, 116, 139), # V8 cinza
]


params = abrir_configuracao()
num_veiculos = params.num_veiculos
seed_execucao = params.seed

aplicar_parametros_frota(
    capacidade=params.capacidade_veiculo,
    autonomia=params.distancia_maxima_veiculo,
)
capacidade_veiculo = params.capacidade_veiculo
distancia_maxima_veiculo = params.distancia_maxima_veiculo

if params.arquivo_csv:
    entregas_dia = parse_pedidos_csv(params.arquivo_csv)
    cities_locations = aplicar_entregas(entregas_dia)
    params.n_cidades = len(cities_locations)
else:
    cities_locations = obter_cidades(
        params.n_cidades,
        params.modo_cidades,
        params.seed,
    )
    configurar_cenario(
        cities_locations,
        seed=seed_execucao,
        n_cidades=params.n_cidades,
        modo=params.modo_cidades,
    )
    entregas_dia = montar_entregas(
        cities_locations,
        seed=seed_execucao,
        n_cidades=params.n_cidades,
        modo=params.modo_cidades,
    )

carga_dia = carga_total_dia(entregas_dia)

print("\nCONFIGURAÇÃO DA EXECUÇÃO")
print("-" * 50)
print(f"Entregas: {params.n_cidades} ({params.modo_cidades})")
print(f"Veículos: {num_veiculos}")
print(f"Capacidade/veículo: {capacidade_veiculo} {UNIDADE_MEDIDA_ABREV}")
print(f"Autonomia/veículo: {distancia_maxima_veiculo} km")
print(f"Carga total do dia: {carga_dia} {UNIDADE_MEDIDA_ABREV}")
print(f"Unidade: 1 {UNIDADE_MEDIDA}")
print(f"Seed: {seed_execucao}")
if params.arquivo_csv:
    print(f"Pedidos: {params.arquivo_csv}")

print("\nENTREGAS HOSPITALARES")
print("-" * 50)
for indice, cidade in enumerate(cities_locations, start=1):
    print(formatar_entrega(cidade, ordem=indice))

contagem_tipos = resumo_tipos(cities_locations)
print(
    f"\nTipos: CRITICO={contagem_tipos['CRITICO']} | "
    f"REGULAR={contagem_tipos['REGULAR']} | "
    f"INSUMO={contagem_tipos['INSUMO']}"
)

print(f"Quantidade de cidades: {len(cities_locations)}")
print(f"Depósito hospitalar: {DEPOT}")

projecao_mapa = criar_projecao_mapa(
    cities_locations,
    DEPOT,
    map_x=MAP_X,
    map_y=0,
    map_w=MAP_WIDTH,
    map_h=HEIGHT,
)

# Initialize Pygame (após preparar dados — janela abre já pronta para simular)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Logística — Simulação AG")
clock = pygame.time.Clock()
plot_surface = create_plot_surface(
    [1], [0],
    y_label="Fitness (distância + restrições)",
    width=PLOT_WIDTH,
    height=HEIGHT,
)
desenhar_fundo_paineis(screen, PLOT_WIDTH, MAP_X, HEIGHT, MAP_WIDTH)
screen.blit(plot_surface, (0, 0))
draw_mapa_projecao(
    screen,
    projecao_mapa,
    cities_locations,
    DEPOT,
    [[] for _ in range(num_veiculos)],
    CORES_VEICULOS,
    NODE_RADIUS,
)
pygame.display.flip()

best_fitness_values = []
estado_simulacao = {"running": True}


def _encerrar_pygame_com_rotas_finais(rotas, remanescentes=None):
    """Último frame: rotas efetivas pós-priorização; encerra Pygame antes do pós-processamento."""
    pygame.display.set_caption("TSP Logística — Rotas finais")
    desenhar_fundo_paineis(screen, PLOT_WIDTH, MAP_X, HEIGHT, MAP_WIDTH)
    if plot_surface is not None:
        screen.blit(plot_surface, (0, 0))
    rem_set = set(remanescentes) if remanescentes else None
    draw_mapa_projecao(
        screen,
        projecao_mapa,
        cities_locations,
        DEPOT,
        rotas,
        CORES_VEICULOS,
        NODE_RADIUS,
        remanescentes=rem_set,
    )
    pygame.display.flip()
    for _ in range(3):
        pygame.event.pump()
        pygame.time.wait(100)
    pygame.quit()


def callback_pygame(generation, best_individual, best_fitness):
    global plot_surface

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            estado_simulacao["running"] = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                estado_simulacao["running"] = False

    if not estado_simulacao["running"]:
        return False

    best_fitness_values.append(best_fitness)
    best_path, best_alocacao = best_individual
    rotas = dividir_rota_em_veiculos(best_path, best_alocacao, num_veiculos)

    if generation == 1 or generation % PLOT_UPDATE_EVERY == 0:
        plot_surface = create_plot_surface(
            list(range(1, len(best_fitness_values) + 1)),
            best_fitness_values,
            y_label="Fitness (distância + restrições)",
            width=PLOT_WIDTH,
            height=HEIGHT,
        )

    desenhar_fundo_paineis(screen, PLOT_WIDTH, MAP_X, HEIGHT, MAP_WIDTH)
    if plot_surface is not None:
        screen.blit(plot_surface, (0, 0))

    draw_mapa_projecao(
        screen,
        projecao_mapa,
        cities_locations,
        DEPOT,
        rotas,
        CORES_VEICULOS,
        NODE_RADIUS,
    )

    if generation % 50 == 0:
        print(
            f"Generation {generation}: "
            f"Best fitness = {round(best_fitness, 2)}"
        )

    pygame.display.flip()
    clock.tick(FPS)
    return True


print("\nIniciando Algoritmo Genético...")
resultado_ag = executar_ag(
    cities_locations,
    population_size=POPULATION_SIZE,
    n_generations=N_GENERATIONS,
    mutation_probability=MUTATION_PROBABILITY,
    limite_sem_melhora=LIMITE_SEM_MELHORA,
    seed=seed_execucao,
    num_veiculos=num_veiculos,
    verbose=False,
    callback=callback_pygame,
)

if not best_fitness_values:
    best_fitness_values = resultado_ag["best_fitness_values"]

fitness_inicial = resultado_ag["fitness_inicial"]
distancia_inicial = resultado_ag["distancia_inicial"]
geracao_convergencia = resultado_ag["geracao_convergencia"]
best_path = resultado_ag["path"]
best_alocacao = resultado_ag["alocacao"]
fitness_final_prioridade = resultado_ag["fitness_final_prioridade"]

resultado_cap = priorizar_entregas_capacidade(
    best_path,
    best_alocacao,
    num_veiculos,
    capacidade_veiculo,
)
best_path = resultado_cap["path_efetivo"]
best_alocacao = resultado_cap["alocacao_efetiva"]
texto_remanescentes = resultado_cap["texto_remanescentes"]
houve_corte_capacidade = resultado_cap["houve_corte"]
kits_remanescentes_hospital = resultado_cap["kits_hospital"]
entregas_remanescentes = len(resultado_cap["remanescentes"])
total_pedidos_dia = len(cities_locations)

if houve_corte_capacidade:
    print("\nCAPACIDADE INSUFICIENTE — PRIORIZAÇÃO APLICADA")
    print("-" * 50)
    print(texto_remanescentes)

rotas_veiculos = resultado_cap["rotas_efetivas"]
_encerrar_pygame_com_rotas_finais(rotas_veiculos, resultado_cap["remanescentes"])

print("Calculando benchmark VRP (força bruta)...")
fitness_target_solution = calcular_solucao_otima_vrp(
    cities_locations,
    num_veiculos,
    LIMITE_CIDADES_BENCHMARK,
)
motivo_otimo_omitido = motivo_omissao_benchmark(
    num_veiculos,
    len(cities_locations),
    LIMITE_CIDADES_BENCHMARK,
    fitness_target_solution,
)
if not math.isnan(fitness_target_solution):
    print(
        f"Solução ótima VRP ({num_veiculos} veículos): "
        f"{fitness_target_solution:.2f}"
    )
else:
    if motivo_otimo_omitido:
        print(f"Benchmark exato omitido: {motivo_otimo_omitido}.")
    else:
        print(
            f"Benchmark exato omitido: {LIMITE_CIDADES_BENCHMARK}+ entregas "
            f"(limitação computacional da força bruta)."
        )

fitness_final = calcular_distancia_operacao(
    best_path, best_alocacao, num_veiculos
)

ordens_veiculos = [[] for _ in range(num_veiculos)]

for indice, cidade in enumerate(best_path):
    ordens_veiculos[best_alocacao[cidade]].append(indice + 1)

dados_veiculos = []
texto_veiculos = ""

print("\nROTAS DOS VEÍCULOS")
print("=" * 50)

for indice, rota in enumerate(rotas_veiculos, start=1):

    carga = sum(city_demands[cidade] for cidade in rota)
    distancia = calculate_distance_only(rota) if rota else 0
    capacidade_ok = True
    autonomia_ok = distancia <= distancia_maxima_veiculo

    if not rota:
        status = "permanece no hospital"
    elif autonomia_ok:
        status = "operacionalmente viável"
    else:
        status = "com restrição de autonomia"

    ordens = ordens_veiculos[indice - 1]
    amostra_ordens = ordens[:5]
    resumo_ordens = ", ".join(
        f"{obter_nome(best_path[o - 1])}[{obter_tipo(best_path[o - 1])}]"
        f"(p{city_priorities[best_path[o - 1]]})"
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

    parada_vazia = "N/A (veículo ocioso — permanece no hospital)"
    linha = (
        f"Veículo {indice} | {len(rota)} entregas | "
        f"carga {carga}/{capacidade_veiculo} | "
        f"distância {distancia:.0f}/{distancia_maxima_veiculo} | "
        f"status: {status}\n"
        f"  Primeira parada: "
        f"{formatar_entrega(rota[0]) if rota else parada_vazia}\n"
        f"  Última parada: "
        f"{formatar_entrega(rota[-1]) if rota else parada_vazia}\n"
        f"  Sequência (início): {resumo_ordens if rota else '—'}\n"
    )
    texto_veiculos += linha

    print(f"Veículo {indice}")
    print(f"Cidades: {len(rota)}")
    print(f"Carga: {carga}/{capacidade_veiculo}")
    print(f"Distância: {distancia:.2f}/{distancia_maxima_veiculo}")
    print(f"Status: {status}")
    print("-" * 50)

distancia_total_rota = fitness_final

rota_aleatoria = random.sample(cities_locations, len(cities_locations))
alocacao_aleatoria = gerar_alocacao_aleatoria(
    cities_locations, num_veiculos=num_veiculos
)
distancia_aleatoria = calcular_distancia_operacao(
    rota_aleatoria, alocacao_aleatoria, num_veiculos
)

print("Calculando heurísticas de referência (vizinho próximo, greedy)...")
distancia_vizinho, distancia_greedy = calcular_distancias_heuristicas(
    cities_locations,
    num_veiculos,
    DEPOT,
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

metricas_comparativo = MetricasComparativoMetodos(
    fitness_inicial=fitness_inicial,
    distancia_inicial=distancia_inicial,
    fitness_final=fitness_final,
    fitness_final_prioridade=fitness_final_prioridade,
    melhoria_fitness_pct=melhoria_prioridade,
    melhoria_distancia_pct=melhoria_distancia,
    geracao_convergencia=geracao_convergencia,
    distancia_aleatoria=distancia_aleatoria,
    distancia_vizinho_proximo=distancia_vizinho,
    distancia_greedy_prioridade=distancia_greedy,
    fitness_target_solution=fitness_target_solution,
    diferenca_benchmark_pct=diferenca_benchmark,
    num_veiculos=num_veiculos,
    total_entregas=len(cities_locations),
    motivo_otimo_omitido=motivo_otimo_omitido,
)

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
print(f"Vizinho mais próximo:     {distancia_vizinho:.2f}")
print(f"Greedy por prioridade:    {distancia_greedy:.2f}")
print(
    f"Comparativo VRP -> AG: {fitness_final:.2f} | "
    f"Aleatória: {distancia_aleatoria:.2f} | "
    f"Ótimo: {otimo_txt}"
)

print(f"Distância total da operação: {distancia_total_rota:.2f}")

todos_viaveis = all(v["autonomia_ok"] for v in dados_veiculos)
print(
    "Todos os veículos respeitam autonomia e capacidade (kits excedentes no hospital)."
    if todos_viaveis and not houve_corte_capacidade
    else (
        "Há veículo(s) com restrição de autonomia."
        if todos_viaveis is False
        else "Capacidade priorizada — kits excedentes permanecem no hospital (ver relatório)."
    )
)
print("\nTOP 10 CIDADES DA ROTA FINAL")
print("-" * 50)

for indice, cidade in enumerate(best_path[:10], start=1):
    print(f"Posição {indice} -> {formatar_entrega(cidade)}")


top10_prioridades = []

for cidade in best_path[:10]:
    top10_prioridades.append(
        city_priorities[cidade]
    )    

rota_detalhada = []

for indice, cidade in enumerate(best_path, start=1):
    rota_detalhada.append({
        "ordem": indice,
        "nome": obter_nome(cidade),
        "tipo": obter_tipo(cidade),
        "x": cidade[0],
        "y": cidade[1],
        "prioridade": city_priorities[cidade],
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
        f"Tipo={item['tipo']} | "
        f"X={item['x']} | "
        f"Y={item['y']} | "
        f"Prioridade={item['prioridade']} | "
        f"Demanda={item['demanda']}\n"
    )

top10_resumo = ", ".join(
    f"{obter_nome(c)}[{obter_tipo(c)}](p{city_priorities[c]})"
    for i, c in enumerate(best_path[:10], start=1)
)
contagem_tipos_entregues = resumo_tipos(best_path)
texto_catalogo_entregas = montar_catalogo_entregas(best_path, best_alocacao)
texto_entregas_por_tipo = montar_entregas_por_tipo(best_path)
texto_rota_resumo = (
    f"Pedidos do dia: {total_pedidos_dia} | Entregas efetivas: {len(rota_detalhada)} | "
    f"Distância total: {distancia_total_rota:.0f} | "
    f"Carga em rota: {carga_total} {UNIDADE_MEDIDA_ABREV} | "
    f"Kits no hospital: {kits_remanescentes_hospital} {UNIDADE_MEDIDA_ABREV} | "
    f"Veículos: {num_veiculos} | "
    f"Capacidade/veículo: {capacidade_veiculo} {UNIDADE_MEDIDA_ABREV} | "
    f"Autonomia/veículo: {distancia_maxima_veiculo} km | "
    f"Depósito: Hospital Central\n"
    f"Tipos (entregues): CRITICO={contagem_tipos_entregues['CRITICO']} | "
    f"REGULAR={contagem_tipos_entregues['REGULAR']} | "
    f"INSUMO={contagem_tipos_entregues['INSUMO']}\n"
    f"Top 10: {top10_resumo}\n"
    f"Prioridade 10: {prioridade_10} | Prioridade 9-10: {prioridade_9_10}"
)
if houve_corte_capacidade:
    texto_rota_resumo += (
        f"\nPriorização: {entregas_remanescentes} unidade(s) com "
        f"{kits_remanescentes_hospital} kits aguardam no hospital."
    )

texto_rotas_detalhado = (
    montar_ordem_global(best_path, best_alocacao)
    + "\n\n"
    + montar_rotas_por_veiculo(rotas_veiculos)
)
if houve_corte_capacidade:
    texto_rotas_detalhado += "\n\n" + texto_remanescentes

if geracao_convergencia is None:
    geracao_convergencia = resultado_ag["geracoes_executadas"]

print("\nGerando análise, relatório e instruções com IA...")

economia_diaria_km = max(distancia_aleatoria - fitness_final, 0)
economia_semanal_pct = (
    economia_diaria_km / distancia_aleatoria * 100
    if distancia_aleatoria > 0
    else 0.0
)
texto_resumo_semanal = (
    f"NOTA: projeção semanal — baseada em 1 execução do AG, "
    f"replicada por 5 dias úteis (não é histórico real de operação).\n"
    f"Período projetado: 5 dias úteis simulados\n"
    f"Depósito: Hospital Central {DEPOT} (saída/retorno de todos os veículos)\n"
    f"Veículos na frota: {num_veiculos}\n"
    f"Capacidade por veículo: {capacidade_veiculo} {UNIDADE_MEDIDA_ABREV}\n"
    f"Autonomia por veículo: {distancia_maxima_veiculo} km\n"
    f"Entregas por dia (efetivas): {len(rota_detalhada)} | Pedidos totais: {total_pedidos_dia}\n"
    f"Kits remanescentes no hospital (por dia): {kits_remanescentes_hospital}\n"
    f"Tipos entregues por dia: CRITICO={contagem_tipos_entregues['CRITICO']} | "
    f"REGULAR={contagem_tipos_entregues['REGULAR']} | "
    f"INSUMO={contagem_tipos_entregues['INSUMO']}\n"
    f"Tipos pedidos (total): CRITICO={contagem_tipos['CRITICO']} | "
    f"REGULAR={contagem_tipos['REGULAR']} | "
    f"INSUMO={contagem_tipos['INSUMO']}\n"
    f"Tipos na semana (projetados — entregues): CRITICO={contagem_tipos_entregues['CRITICO'] * 5} | "
    f"REGULAR={contagem_tipos_entregues['REGULAR'] * 5} | "
    f"INSUMO={contagem_tipos_entregues['INSUMO'] * 5}\n"
    f"Distância média diária (com depósito): {fitness_final:.2f}\n"
    f"Distância total semanal projetada: {fitness_final * 5:.2f}\n"
    f"Carga média diária: {carga_total}\n"
    f"Carga total semanal projetada: {carga_total * 5}\n"
    f"Melhoria de distância (AG vs início): {melhoria_distancia:.2f}%\n"
    f"Melhoria de fitness (AG): {melhoria_prioridade:.2f}%\n"
    f"Economia diária vs rota aleatória: {economia_diaria_km:.2f} km\n"
    f"Economia semanal projetada vs aleatória: {economia_diaria_km * 5:.2f} km "
    f"({economia_semanal_pct:.1f}%)\n"
    f"Geração de convergência do AG: {geracao_convergencia}\n"
    f"Entregas CRITICO prioridade 10 (por dia): {prioridade_10}\n"
    f"Entregas prioridade 9-10 (por dia): {prioridade_9_10}\n"
    f"Média de prioridade (top 10 da rota): {media_top10:.2f}\n"
    f"Comparativo diário -> AG: {fitness_final:.2f} | "
    f"Aleatória: {distancia_aleatoria:.2f} | "
    f"Ótimo: {otimo_txt}"
)

conteudo_ia = gerar_conteudo_completo(
    fitness_inicial=fitness_inicial,
    fitness_final=fitness_final,
    fitness_final_prioridade=fitness_final_prioridade,
    melhoria_fitness=melhoria_prioridade,
    melhoria_distancia=melhoria_distancia,
    fitness_target_solution=fitness_target_solution,
    diferenca_benchmark=diferenca_benchmark,
    top10_prioridades=top10_prioridades,
    geracao_convergencia=geracao_convergencia,
    prioridade_10=prioridade_10,
    prioridade_9_10=prioridade_9_10,
    media_top10=media_top10,
    total_cidades=len(rota_detalhada),
    num_veiculos=num_veiculos,
    distancia_aleatoria=distancia_aleatoria,
    texto_veiculos=texto_veiculos,
    texto_resumo_semanal=texto_resumo_semanal,
    texto_remanescentes=texto_remanescentes,
    houve_corte_capacidade=houve_corte_capacidade,
    capacidade_veiculo=capacidade_veiculo,
    distancia_maxima_veiculo=distancia_maxima_veiculo,
)
analise = conteudo_ia["analise"]
relatorio = conteudo_ia["relatorio"]
relatorio_semanal = conteudo_ia["relatorio_semanal"]
instrucoes = conteudo_ia["instrucoes"]

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
    arquivo.write(f"Veículos: {num_veiculos}\n")
    arquivo.write(f"Entregas: {params.n_cidades} ({params.modo_cidades})\n")
    arquivo.write(f"Seed: {seed_execucao}\n")
    arquivo.write(f"Capacidade por veículo: {capacidade_veiculo}\n")
    arquivo.write(f"Autonomia por veículo: {distancia_maxima_veiculo}\n")
    arquivo.write(f"Depósito hospitalar: {DEPOT}\n\n")

    arquivo.write(
        f"Geração de convergência: {geracao_convergencia}\n\n"
    )
    
    arquivo.write("ENTREGAS HOSPITALARES\n")
    arquivo.write("-" * 50 + "\n")

    for indice, cidade in enumerate(cities_locations, start=1):
        arquivo.write(formatar_entrega(cidade, ordem=indice) + "\n")

    arquivo.write(
        f"\nTipos: CRITICO={contagem_tipos['CRITICO']} | "
        f"REGULAR={contagem_tipos['REGULAR']} | "
        f"INSUMO={contagem_tipos['INSUMO']}\n\n"
    )
   
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
        f"Vizinho: {distancia_vizinho:.2f} | "
        f"Greedy: {distancia_greedy:.2f} | "
        f"Ótimo: {otimo_txt}\n\n"
    )

    arquivo.write("=" * 50 + "\n")
    arquivo.write("MÉTRICAS COMPARATIVAS (MÉTODOS)\n")
    arquivo.write("=" * 50 + "\n\n")
    arquivo.write(montar_bloco_analise_metricas(metricas_comparativo))
    arquivo.write("\n\n")
    arquivo.write("Melhor rota encontrada:\n")

    for indice, cidade in enumerate(best_path, start=1):
        arquivo.write(
            f"{indice}. {obter_nome(cidade)} [{obter_tipo(cidade)}] | "
            f"Veículo: {best_alocacao[cidade] + 1} | "
            f"Prioridade: {city_priorities[cidade]}\n"
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

    if houve_corte_capacidade:
        arquivo.write("\n\n")
        arquivo.write("=" * 50 + "\n")
        arquivo.write("KITS REMANESCENTES NO HOSPITAL\n")
        arquivo.write("=" * 50 + "\n\n")
        arquivo.write(texto_remanescentes)

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("ROTA DETALHADA\n")
    arquivo.write("=" * 50 + "\n\n")

    for item in rota_detalhada:

        arquivo.write(
            f"Ordem: {item['ordem']} | "
            f"Nome: {item['nome']} | "
            f"Tipo: {item['tipo']} | "
            f"Veículo: {item['veiculo']} | "
            f"Prioridade: {item['prioridade']} | "
            f"Demanda: {item['demanda']}\n"
        )


def _responder_pergunta_chat(pergunta, historico_conversa=None):
    return responder_pergunta(
        pergunta,
        texto_veiculos,
        texto_rota_resumo,
        texto_rotas_detalhado,
        analise,
        relatorio,
        relatorio_semanal,
        instrucoes,
        texto_catalogo_entregas=texto_catalogo_entregas,
        texto_entregas_por_tipo=texto_entregas_por_tipo,
        texto_remanescentes=texto_remanescentes,
        historico_conversa=historico_conversa,
    )


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
    depot=DEPOT,
    city_names=city_names,
    city_types=city_types,
    num_veiculos=num_veiculos,
    remanescentes=resultado_cap["remanescentes"],
    houve_corte_capacidade=houve_corte_capacidade,
    metricas_comparativo=metricas_comparativo,
)

sys.exit()
