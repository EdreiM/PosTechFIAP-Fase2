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
5. **LLM (Groq — padrão `llama-3.1-8b-instant`)** para análise, relatórios, instruções e chat
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
              Pygame + AG (ag_runner.py) geração a geração
                    ↓
              Convergência (ou limite de gerações)
                    ↓
              priorizar_entregas_capacidade() — kits excedentes ficam no hospital
                    ↓
              Benchmark VRP (≤ 6 entregas) + heurísticas + métricas finais
                    ↓
              Divisão por veículo + relatórios numéricos
                    ↓
              Groq (1 chamada): análise | relatório diário | semanal | instruções
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
| `docs/CONTEXTO_IA.md` | Contexto fixo (VRP, kits, regras de resposta) |
| `groq_contexto.py` | Carrega contexto + formata histórico do chat |
| `groq_utils.py` | Cliente, `.env`, fallback se API falhar |
| `groq_conteudo.py` | **1 chamada** gera análise + relatórios + instruções |
| `groq_perguntas.py` | Chat com histórico (últimos 6 turnos) |
| `groq_respostas_locais.py` | Respostas locais (instruções, tipos de medicamento, remanescentes) |
| `groq_analysis.py`, etc. | Fallbacks locais por módulo |

Capacidade/autonomia nos prompts vêm dos **dados da execução** (ex.: 80 kits), não de valores fixos do `config.py`.

Variáveis `.env`: `GROQ_API_KEY`, `GROQ_MODEL` (opcional), `GROQ_DESABILITADO=1` (modo offline).

---

## 8. Testes — `tests/test_projeto.py`

```bash
pytest tests/test_projeto.py -v
```

| Classe | Cobertura |
|--------|-----------|
| `TestConfig` | `config.py`, cidades fixo/aleatório |
| `TestConfigUI` | Parâmetros padrão da janela |
| `TestDadosHospitalares` | Nomes, kits fixos, CSV, viabilidade, priorização por capacidade |
| `TestGeneticAlgorithm` | AG, VRP, depósito, crossover, fitness |
| `TestAgRunner` | Execução do AG reutilizável |
| `TestGroqUtils` | Fallback Groq, contexto IA, histórico do chat |
| `TestGroqRespostasLocais` | Chat local: instruções, medicamentos, remanescentes no hospital |
| `TestDashboardAnalise` | Bloco de métricas na aba Análise (ótimo, heurísticas, omissões) |
| `TestMetricasBenchmark` | Heurísticas, motivo de omissão do ótimo, economia relativa |
| `TestRegressaoBugsUsuario` | Cenário real 18 entregas — chat, abas IA, benchmark N/A |

**84 testes** no total.

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
| Onde está a IA? | `groq_*.py`, `docs/CONTEXTO_IA.md` |
| Como rodar testes? | `pytest tests/test_projeto.py -v` |

---

*Documento para uso interno da equipe. Para instalação e comandos, ver também o `README.md`.*
