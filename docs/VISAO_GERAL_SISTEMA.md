# Visão geral do sistema — Tech Challenge Fase 2 (Projeto 2)

Documento resumido para o grupo entender **como cada parte funciona hoje**.  
Última revisão com base no código atual do repositório.

---

## 1. O que o projeto faz

Sistema de **otimização de rotas hospitalares** (entrega de medicamentos e insumos) que combina:

1. **Algoritmo Genético (AG)** para resolver um **VRP** (Vehicle Routing Problem) com vários veículos
2. **Depósito hospitalar** — saída e retorno de todos os veículos
3. **Dados hospitalares realistas** — nomes de unidades e tipos de entrega (CRITICO, REGULAR, INSUMO)
4. **Simulação visual** em tempo real (Pygame)
5. **LLM (Groq — padrão `llama-3.1-8b-instant`)** para análise, relatórios e chat; **Guia Motoristas** montado localmente
6. **Painel operacional** (Tkinter) com abas após a simulação
7. **Scripts de evidência experimental** — comparativo e 3 experimentos do AG

**Entrada:** coordenadas, nomes, tipos, prioridade, demanda, parâmetros da frota.  
**Saída:** melhor rota + alocação por veículo, métricas, textos da IA, `melhor_rota.txt`, `results/`.

---

## 2. Fluxo completo (do início ao fim)

```
config_ui.py  →  entregas, veículos, capacidade (kits), autonomia, CSV opcional
                    ↓
              Resumo dos pedidos + viabilidade da frota
                    ↓
config.py + dados_hospitalares (demandas fixas ou CSV)
                    ↓
              Pygame + AG (ag_runner.py) — gráfico de fitness + mapa em tempo real
                    ↓
              Parada do AG (convergência ou limite de gerações)
                    ↓
              priorizar_entregas_capacidade() — kits excedentes ficam no hospital
                    ↓
              Benchmark VRP (≤ 6 entregas) + heurísticas + métricas finais
                    ↓
              Divisão por veículo + relatórios numéricos
                    ↓
              Groq (1 chamada): análise | relatório diário | semanal
                    ↓
              Guia Motoristas (local): rota passo a passo por veículo
                    ↓
              Fallback local se API indisponível (429, sem chave)
                    ↓
              Salva melhor_rota.txt  →  Abre dashboard_ui.py (chat com histórico)
```

**Scripts adicionais (sem Pygame/LLM):**

```bash
python benchmark_comparativo.py   # AG vs heurísticas → results/
python experimentos_ag.py         # 3 configs do AG → results/
```

---

## 3. Configuração central — `config.py`

| Grupo | Parâmetros principais | O que controlam |
|-------|----------------------|-----------------|
| Problema | `N_CIDADES`, `MODO_CIDADES`, `SEED` | Quantas cidades e de onde vêm |
| Depósito | `DEPOT` | Hospital central (saída/retorno) |
| VRP | `NUM_VEICULOS`, `CAPACIDADE_VEICULO`, `DISTANCIA_MAXIMA_VEICULO` | Frota e restrições |
| AG | `POPULATION_SIZE`, `N_GENERATIONS`, `MUTATION_PROBABILITY`, `LIMITE_SEM_MELHORA` | Evolução e parada antecipada |
| Experimentos | `EXPERIMENTOS_AG` | 3 configs para `experimentos_ag.py` |
| Interface | `WIDTH`, `HEIGHT`, `FPS`, `PLOT_WIDTH`, `MAP_X`, `MAP_WIDTH`, `PLOT_UPDATE_EVERY` | Janela Pygame (gráfico + mapa lado a lado) |

---

## 3.1 Janela de configuração — `config_ui.py`

Abre **antes** do Pygame quando você roda `python tsp.py`:

| Campo | Descrição |
|-------|-----------|
| Modo de entregas | `fixo` (unidades hospitalares) ou `aleatorio` |
| Quantidade de entregas | 5, 10, 12 ou 15 (fixo) · 3–25 (aleatório) |
| Demandas (modo fixo) | Tabela fixa em `dados_hospitalares.py` (kits por unidade) |
| Capacidade / autonomia | 40/60/80 kits · 1200/1500/2000 km |
| Importar CSV | `exemplos/pedidos_exemplo.csv` |
| Quantidade de veículos | 2–8 (excedentes permanecem no hospital) |
| Cenário diferente | Seed aleatória a cada execução |
| Iniciar simulação | Resumo dos pedidos → confirma → Pygame + AG |
| Viabilidade | `avaliar_viabilidade_frota()` — alerta se kits > frota; excedente vai para o hospital |
| Iniciar com padrão (config.py) | Carrega `N_CIDADES`, `NUM_VEICULOS`, `MODO_CIDADES` e `SEED` |

Scripts `benchmark_comparativo.py` e `experimentos_ag.py` **não** usam esta janela — leem só `config.py`.

---

## 4. Dados hospitalares — `dados_hospitalares.py`

Centraliza nomes, tipos e **demandas fixas (kits)** no modo fixo.

**Unidade:** 1 kit de medicamentos = 1 caixa/kits fechados pela farmácia (`config.UNIDADE_MEDIDA`).

| Tipo | Prioridade (fixo) | Kits (fixo, ex.) | Modo aleatório |
|------|-------------------|--------------------|----------------|
| CRITICO | 8–10 | UTI Norte: 12 | 5–15 kits |
| REGULAR | 4–7 | Farmácia: 18 | 10–25 kits |
| INSUMO | 1–3 | Maternidade: 30 | 15–30 kits |

**Funções principais:** `montar_entregas()`, `configurar_cenario()`, `parse_pedidos_csv()`, `avaliar_viabilidade_frota()`, `priorizar_entregas_capacidade()`, `montar_texto_remanescentes_hospital()`

---

## 5. Núcleo do AG / VRP — `genetic_algorithm.py`

### Cromossomo

`(path, alocacao)` — ordem global + veículo por cidade.

### Fitness (quanto menor, melhor)

| Componente | Descrição |
|------------|-----------|
| Distância total | Soma por veículo: **depósito → cidades → depósito** |
| Penalidade de prioridade | Críticos devem aparecer cedo na ordem |
| Penalidade de carga | Excesso de `CAPACIDADE_VEICULO` |
| Penalidade de autonomia | Excesso de `DISTANCIA_MAXIMA_VEICULO` |
| Penalidade veículo vazio | Veículo sem entregas |

### Execução reutilizável

`ag_runner.executar_ag()` — usado por `tsp.py`, `benchmark_comparativo.py` e `experimentos_ag.py`.

---

## 6. Heurísticas e benchmarks

| Arquivo | Função |
|---------|--------|
| `heuristics.py` | Rota aleatória, vizinho mais próximo, greedy por prioridade |
| `metricas_benchmark.py` | Métricas AG vs heurísticas vs ótimo (aba Análise + `melhor_rota.txt`) |
| `benchmark_comparativo.py` | Compara AG vs todas as heurísticas |
| `experimentos_ag.py` | 3 configs do AG + gráfico de convergência |

Ver [EVIDENCIAS_EXPERIMENTAIS.md](EVIDENCIAS_EXPERIMENTAIS.md) para uso no relatório técnico.

---

## 7. Integração LLM (Groq)

| Arquivo | Papel |
|---------|-------|
| `docs/CONTEXTO_IA.md` | Regras fixas nos prompts Groq (arquivo operacional — `groq_contexto.py`) |
| `groq_contexto.py` | Carrega contexto + formata histórico do chat |
| `groq_utils.py` | Cliente, `.env`, fallback se API falhar |
| `groq_conteudo.py` | **1 chamada** gera análise + relatório diário + semanal (3 seções LLM) |
| `groq_rotas.py` | **Guia Motoristas** — montado localmente a partir das rotas (aba do painel) |
| `groq_perguntas.py` | Chat com histórico (últimos 6 turnos) |
| `groq_respostas_locais.py` | Chat **local** (sem Groq): instruções, trajetória do motorista, carga por veículo, tipos, kits, remanescentes |
| `groq_analysis.py`, etc. | Fallbacks locais por módulo (textos enxutos, sem repetir métricas da aba Análise) |

Capacidade/autonomia nos prompts vêm dos **dados da execução** (ex.: 80 kits), não de valores fixos do `config.py`.

Variáveis `.env`: `GROQ_API_KEY`, `GROQ_MODEL` (opcional), `GROQ_DESABILITADO=1` (modo offline).

---

## 7.1 Painel operacional — `dashboard_ui.py`

Cabeçalho enxuto: apenas o título **Painel Operacional — Rotas Otimizadas** (sem bloco de resumo no topo; KPIs ficam nas abas).

Abas após a simulação:

| Aba | Conteúdo |
|-----|----------|
| **Mapa da Rota** | Entregas numeradas, cores por veículo, remanescentes cinza tracejado |
| **Veículos** | Status operacional completo por van (carga, distância, paradas) |
| **Análise** | Bloco de métricas (AG + heurísticas + ótimo*) + interpretação da IA |
| **Relatório Diário** | Fechamento do dia (sem repetir tabela de métricas) |
| **Relatório Semanal** | Projeção × 5 dias úteis |
| **Guia Motoristas** | Rota passo a passo por veículo (`groq_rotas.montar_instrucoes_motoristas`) — linguagem direta para quem dirige |
| **Chat** | Perguntas em linguagem natural (respostas locais ou Groq) |

\*Ótimo VRP só com ≤ 6 entregas e ≤ 6 veículos.

A **evolução do fitness** aparece na simulação **Pygame** (gráfico à esquerda), não no painel.

O **chat** prioriza `groq_respostas_locais.py` para: instruções/trajetória (`carro 2`, `motorista`), carga por veículo, `quantas de cada?` (com histórico), explicação de kits/capacidade, medicamentos por tipo e remanescentes.

---

## 8. Testes — `tests/`

```bash
py -m pytest tests/test_projeto.py -v
```

Guia completo: [`tests/README.md`](../tests/README.md)  
Cenários reutilizáveis: [`tests/fixtures_dados.py`](../tests/fixtures_dados.py)

| Classe | Cobertura |
|--------|-----------|
| `TestConfig` | `config.py`, cidades fixo/aleatório |
| `TestConfigUI` | Parâmetros padrão da janela |
| `TestDadosHospitalares` | Modo fixo: nomes, kits, CSV, viabilidade, priorização |
| `TestGeneticAlgorithm` | AG, VRP, depósito, crossover, fitness |
| `TestAgRunner` | Execução do AG reutilizável |
| `TestGroqUtils` / `TestGroqConteudo` | Fallback Groq, parsing, contexto IA |
| `TestGroqRespostasLocais` | Chat local: instruções, motorista, carga, kits, follow-up |
| `TestDashboardMapa` / `TestDashboardAnalise` | Mapa e bloco de métricas |
| `TestMetricasBenchmark` | Heurísticas, omissão do ótimo, economia relativa |
| `TestRegressaoBugsUsuario` | Bugs de demo real (18 entregas, veículo 3) |

**88 testes** no total.

---

## 9. Restrições modeladas

### Implementado

- Depósito hospitalar (saída/retorno)
- Nomes de unidades hospitalares
- Tipos CRITICO / REGULAR / INSUMO
- Múltiplos veículos com alocação evoluída
- Capacidade e autonomia por veículo
- **Priorização por capacidade:** kits excedentes permanecem no hospital (maior prioridade sai primeiro)
- Comparativo AG vs heurísticas
- 3 experimentos documentados do AG

### Limitações conhecidas

- Benchmark exato **N/A** com **≥ 7 entregas**, **> 6 veículos** ou veículos > entregas
- Relatório semanal é **projeção** (5 dias simulados)
- Durante o AG, restrições usam **penalidade** no fitness; na **saída operacional**, capacidade é **respeitada** via `priorizar_entregas_capacidade()`
- Autonomia ainda pode gerar status "com restrição de autonomia" se a rota for longa demais

---

## 10. Checklist para o grupo

| Pergunta | Onde olhar |
|----------|------------|
| Como mudar cidades/veículos? | Janela ao rodar `python tsp.py` ou `config.py` |
| Onde estão os nomes hospitalares? | `dados_hospitalares.py` |
| Como rodar comparativo? | `python benchmark_comparativo.py` |
| Como rodar experimentos? | `python experimentos_ag.py` |
| Evidências para relatório? | `docs/EVIDENCIAS_EXPERIMENTAIS.md` |
| Onde está a IA? | `groq_*.py` + `docs/CONTEXTO_IA.md` (prompts) |
| Documentação da equipe? | `VISAO_GERAL_SISTEMA.md`, `ARQUITETURA.md`, `EVIDENCIAS_EXPERIMENTAIS.md` |
| Guia para motoristas? | Aba **Guia Motoristas** no painel (`groq_rotas.py`) |
| Como rodar testes? | `py -m pytest tests/test_projeto.py -v` — ver `tests/README.md` |

---

*Documento para uso interno da equipe. Para instalação e comandos, ver também o `README.md`.*
