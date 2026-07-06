# Avaliação da qualidade das respostas da LLM

Documento de avaliação manual conforme exigido pelo Tech Challenge Fase 2 (Projeto 2).

## Modelo utilizado

- **Provedor:** Groq
- **Modelo padrão:** `llama-3.1-8b-instant` (menor consumo de tokens)
- **Modelo alternativo:** `llama-3.3-70b-versatile` (via `GROQ_MODEL` no `.env`)
- **Temperatura:** 0.2 (respostas mais consistentes)
- **Contexto fixo:** `docs/CONTEXTO_IA.md` (incluído em todos os prompts)

## Critérios de avaliação

| Critério | Descrição | Peso |
|----------|-----------|------|
| Correção | Usa apenas dados fornecidos (veículos, carga, distância, prioridades) | Alto |
| Clareza | Linguagem operacional, sem texto acadêmico longo | Alto |
| Concisão | Respeita limites de palavras por módulo | Médio |
| Contexto VRP | Avalia capacidade/autonomia **por veículo**, com valores da execução (ex.: X/80) | Alto |
| Honestidade | Informa quando dado não está disponível | Alto |
| Coerência | Chat mantém contexto das perguntas anteriores (histórico) | Médio |

## Arquitetura da integração (atual)

| Componente | Função |
|------------|--------|
| `groq_conteudo.py` | 1 chamada API → análise + relatório diário + semanal + instruções |
| `groq_perguntas.py` | Chat com histórico (últimos 6 turnos) |
| `groq_utils.py` | Cliente, `.env`, fallback local se API falhar |
| `docs/CONTEXTO_IA.md` | Regras fixas (depósito, kits, último ponto, etc.) |

## Resultados por módulo

### 1. Análise técnica

**Objetivo:** resumo técnico do AG (qualidade, convergência, prioridades, benchmark).

| Aspecto | Avaliação |
|---------|-----------|
| Correção | Boa — usa fitness, convergência e comparativos numéricos |
| Clareza | Boa — seções fixas, ~250 palavras |
| Limitação | Não inventa cidades; depende dos números enviados |

### 2. Relatório operacional diário

**Objetivo:** fechamento do dia (eficiência, veículos, prioridades).

| Aspecto | Avaliação |
|---------|-----------|
| Correção | Boa — avalia cada veículo separadamente |
| Utilidade | Alta — inclui recomendações para o próximo dia |

### 3. Relatório operacional semanal

**Objetivo:** consolidado da semana (tendências, economia, padrões) — **projeção** de 1 dia × 5.

| Aspecto | Avaliação |
|---------|-----------|
| Correção | Boa — deixa explícito que é projeção, não histórico real |
| Contexto hospitalar | Boa — depósito, tipos CRITICO/REGULAR/INSUMO no prompt e nos dados |
| Utilidade | Alta — foco em economia de tempo/recursos e padrões |
| Diferenciação | Boa — não repete o relatório diário |

### 4. Instruções de entrega

**Objetivo:** orientar motoristas/equipe de campo.

| Aspecto | Avaliação |
|---------|-----------|
| Clareza | Alta — linguagem direta por veículo |
| Concisão | Boa — ~200 palavras, sem listar todas as cidades |
| Limitação | Não substitui ordem oficial da rota do AG |

### 5. Chat (`groq_perguntas.py`)

**Objetivo:** perguntas em linguagem natural sobre a operação.

| Aspecto | Avaliação |
|---------|-----------|
| Respostas curtas | Boa — máximo 5 frases |
| Dados por veículo | Boa — contexto VRP com rotas detalhadas (primeira/última parada) |
| Histórico | Boa — entende "e a distância dele?" após pergunta sobre veículo |
| Pegadinhas | Responde corretamente quando informação não existe |

## Exemplos de teste manual (roteiro para vídeo/banca)

| Pergunta | Resposta esperada |
|----------|-------------------|
| Todos os veículos respeitam capacidade e autonomia? | Sim/Não por veículo, com números |
| Qual veículo tem maior carga? | Identifica veículo e valor X/Y (Y = capacidade configurada) |
| Quais cidades têm prioridade 10? | Lista posições ou quantidade |
| A solução ficou melhor que a rota aleatória? | Comparativo diário/semanal |
| Qual o último ponto de entrega? | Nome da última entrega global (ordem global) |
| Qual a última parada do veículo 2? | Nome da última parada na rota do veículo 2 |
| E a distância dele? (após pergunta sobre veículo) | Usa histórico — responde sobre o mesmo veículo |

## Pontos fortes

- Contexto fixo em `CONTEXTO_IA.md` evita confusão (kits, depósito, capacidade da execução)
- Uma chamada API para relatórios (economia de tokens vs. 4 chamadas separadas)
- Fallback local se Groq indisponível — simulação nunca trava
- Chat com histórico de conversa

## Limitações conhecidas

1. **Dependência de API externa** — sem `GROQ_API_KEY`, usa fallback local (texto gerado no código).
2. **Cota Groq** — limite diário é por **organização**; nova chave na mesma conta não aumenta cota.
3. **Variabilidade** — pequenas diferenças entre execuções mesmo com temperatura baixa.
4. **Sem RAG** — a LLM não consulta banco de dados; só o contexto enviado no prompt.
5. **Relatório semanal** — projeção simulada (1 execução × 5 dias).

## Conclusão

A integração atende aos requisitos do PDF: instruções, relatório operacional, sugestões de melhoria e chat. A qualidade é **adequada para uso operacional** quando os dados VRP são enviados corretamente por veículo. Recomenda-se demonstrar no vídeo pelo menos 3 perguntas do roteiro acima, incluindo uma pergunta encadeada no chat.

## Como reproduzir a avaliação

1. Configure `.env` com `GROQ_API_KEY` (opcional: `GROQ_MODEL`, `GROQ_DESABILITADO=1` para teste offline).
2. Execute `python tsp.py` e aguarde o painel.
3. Teste as perguntas da tabela na aba **Chat**.
4. Compare respostas com a aba **Veículos** e o terminal.
