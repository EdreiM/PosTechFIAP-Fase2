# Evidências experimentais — Tech Challenge Fase 2

Documento de apoio ao **relatório técnico** com instruções para reproduzir comparativos e experimentos do AG.

---

## 1. Como gerar as evidências

### Comparativo AG vs heurísticas

```bash
python benchmark_comparativo.py
```

**Saída:**

| Arquivo | Conteúdo |
|---------|----------|
| `results/benchmark_comparativo.txt` | Tabela legível para o relatório |
| `results/benchmark_comparativo.csv` | Dados para gráficos/planilhas |

**Métodos comparados:**

| Método | Descrição |
|--------|-----------|
| Algoritmo Genético | Solução evolutiva com VRP + restrições |
| Rota Aleatória | Baseline inferior (ordem e alocação aleatórias) |
| Vizinho Mais Próximo | Heurística construtiva a partir do depósito |
| Greedy por Prioridade | Críticos primeiro, alocação por carga |
| Ótimo (força bruta) | ≤ 6 entregas, ≤ 6 veículos, veículos ≤ entregas |

### Três experimentos com configurações do AG

```bash
python experimentos_ag.py
```

**Saída:**

| Arquivo | Conteúdo |
|---------|----------|
| `results/experimentos_ag.txt` | Resumo dos 3 experimentos |
| `results/experimentos_convergencia.png` | Gráfico de convergência sobreposto |

**Configurações (definidas em `config.py` → `EXPERIMENTOS_AG`):**

| Experimento | População | Mutação | Gerações | Objetivo |
|-------------|-----------|---------|----------|----------|
| A - Padrão | 100 | 0.5 | 1000 | Configuração equilibrada |
| B - Exploração | 200 | 0.7 | 500 | Mais diversidade genética |
| C - Refino | 50 | 0.2 | 2000 | Convergência gradual |

---

## 2. Cenário hospitalar modelado

### Unidade de carga

- **1 kit de medicamentos** = 1 caixa/kits fechados pela farmácia (`config.UNIDADE_MEDIDA`)
- Capacidade por veículo: **40, 60 ou 80 kits** (janela de configuração; valores usados na exibição vêm da UI, não do padrão fixo do `config.py`)

### Depósito

- Coordenada: `DEPOT = (400, 200)` em `config.py`
- Todos os veículos saem e retornam ao **Hospital Central** (marcado como **H** no mapa)
- Distância calculada: `depósito → entregas → depósito`

### Nomes das unidades

Definidos em `dados_hospitalares.py` → `NOMES_POR_TAMANHO` (modo fixo):

- UTI Norte, Home Care Zona Sul, Farmácia Central, Pronto-Socorro, etc.

### Tipos de entrega e demandas

| Tipo | Descrição | Prioridade | Kits |
|------|-----------|------------|------|
| **CRITICO** | Medicamentos críticos | 8–10 | Fixo: ex. UTI 12 · Aleatório: 5–15 |
| **REGULAR** | Medicamentos contínuos | 4–7 | Fixo: ex. Farmácia 18 · Aleatório: 10–25 |
| **INSUMO** | Material hospitalar | 1–3 | Fixo: ex. Maternidade 30 · Aleatório: 15–30 |

No **modo fixo**, valores exatos em `DEMANDAS_FIXAS_POR_TAMANHO` (`dados_hospitalares.py`) — reprodutíveis.  
Demo interativa: capturas em `exemplos/janela_configuracao.png`, `exemplos/resumo_pedidos.png`, `exemplos/simulacao_pygame.png`, `exemplos/painel_operacional.png`.

Configuração: `configurar_cenario()` ou CSV via `parse_pedidos_csv()`.

---

## 3. Métricas registradas

| Métrica | Significado |
|---------|-------------|
| **Distância** | Soma das rotas (com depósito), em unidades do mapa |
| **Fitness** | Distância + penalidades (prioridade, carga, autonomia) |
| **Viável** | Capacidade respeitada na operação efetiva; autonomia OK por veículo (benchmarks usam AG bruto) |
| **Remanescentes** | Kits/unidades que ficaram no hospital por falta de capacidade (após priorização) |
| **Tempo** | Segundos de execução |
| **Conv.** | Geração de convergência (só AG) |

No fluxo interativo (`python tsp.py`), as mesmas métricas aparecem na **aba Análise** do painel e no arquivo **`melhor_rota.txt`** (módulo `metricas_benchmark.py`).

---

## 4. O que incluir no relatório técnico

### Seção: Comparativo de abordagens

1. Tabela copiada de `results/benchmark_comparativo.txt`
2. Destaque: economia percentual do AG vs rota aleatória
3. Análise: por que o AG supera heurísticas simples em cenários com restrições

### Seção: Experimentos do AG

1. Tabela dos 3 experimentos (`results/experimentos_ag.txt`)
2. Gráfico `experimentos_convergencia.png`
3. Conclusão: qual configuração convergiu melhor e por quê

### Seção: Realismo hospitalar

1. Descrição do depósito e tipos de entrega
2. Exemplo de entradas (saída de `python tsp.py` — seção ENTREGAS HOSPITALARES)
3. Mapa do painel com H = Hospital e cores por tipo
4. Relatório semanal: deixar claro na banca que é **projeção** (1 dia × 5), conforme indicado no próprio relatório gerado

### Seção: Demonstração da LLM

1. Aba **Guia Motoristas** — rota passo a passo (montada localmente, sem Groq)
2. Aba **Chat** — pelo menos 3 perguntas, incluindo uma encadeada (ex.: veículo 2 → "e a distância dele?")
3. Critérios: usa só dados da execução, respostas curtas, não sugere alterar a ordem do AG

Modelo padrão: `llama-3.1-8b-instant` (Groq). Contexto fixo em `docs/CONTEXTO_IA.md` (carregado por `groq_contexto.py`).

---

## 5. Reprodutibilidade

Todos os scripts usam:

- `SEED = 42` em `config.py`
- `MODO_CIDADES = "fixo"` com `N_CIDADES = 15` (padrão)
- Mesma função `configurar_cenario()` para dados idênticos entre execuções

Para testar com outro cenário, altere apenas `config.py` e rode os três comandos novamente.

---

*Gerado para uso no relatório técnico da Fase 2 — Projeto 2 (Otimização de Rotas Médicas).*
