# Avaliação da qualidade das respostas da LLM

Documento de avaliação manual conforme exigido pelo Tech Challenge Fase 2 (Projeto 2).

## Modelo utilizado

- **Provedor:** Groq
- **Modelo:** `llama-3.3-70b-versatile`
- **Temperatura:** 0.2 (respostas mais consistentes)

## Critérios de avaliação

| Critério | Descrição | Peso |
|----------|-----------|------|
| Correção | Usa apenas dados fornecidos (veículos, carga, distância, prioridades) | Alto |
| Clareza | Linguagem operacional, sem texto acadêmico longo | Alto |
| Concisão | Respeita limites de palavras por módulo | Médio |
| Contexto VRP | Avalia capacidade/autonomia **por veículo**, não pelo total | Alto |
| Honestidade | Informa quando dado não está disponível | Alto |

## Resultados por módulo

### 1. Análise técnica (`groq_analysis.py`)

**Objetivo:** resumo técnico do AG (qualidade, convergência, prioridades, benchmark).

| Aspecto | Avaliação |
|---------|-----------|
| Correção | Boa — usa fitness, convergência e comparativos numéricos |
| Clareza | Boa — seções fixas, ~250 palavras |
| Limitação | Não inventa cidades; depende dos números enviados |

### 2. Relatório operacional (`groq_relatorio.py`)

**Objetivo:** fechamento diário da operação logística.

| Aspecto | Avaliação |
|---------|-----------|
| Correção | Boa — avalia cada veículo separadamente |
| Utilidade | Alta — inclui recomendações práticas |
| Limitação | Qualidade varia se `texto_veiculos` estiver incompleto |

### 3. Instruções de entrega (`groq_rotas.py`)

**Objetivo:** orientar motoristas/equipe de campo.

| Aspecto | Avaliação |
|---------|-----------|
| Clareza | Alta — linguagem direta por veículo |
| Concisão | Boa — ~200 palavras, sem listar todas as cidades |
| Limitação | Não substitui ordem oficial da rota do AG |

### 4. Chat (`groq_perguntas.py`)

**Objetivo:** perguntas em linguagem natural sobre a operação.

| Aspecto | Avaliação |
|---------|-----------|
| Respostas curtas | Boa — máximo 5 frases |
| Dados por veículo | Boa — após correção do contexto VRP |
| Pegadinhas | Responde corretamente quando informação não existe |

## Exemplos de teste manual (roteiro para vídeo/banca)

| Pergunta | Resposta esperada |
|----------|-------------------|
| Todos os veículos respeitam capacidade e autonomia? | Sim/Não por veículo, com números |
| Qual veículo tem maior carga? | Identifica veículo e valor X/400 |
| Quais cidades têm prioridade 10? | Lista posições ou quantidade |
| A solução ficou melhor que a rota aleatória? | Compara distâncias |
| Qual o horário de chegada? | "Essa informação não está disponível..." |

## Pontos fortes

- Prompts separados por função (análise ≠ relatório ≠ instruções ≠ chat)
- Contexto estruturado com blocos `=== VEÍCULOS ===`, `=== RELATÓRIO ===`
- Regras explícitas contra listagem de 48 cidades e texto acadêmico longo

## Limitações conhecidas

1. **Dependência de API externa** — sem `GROQ_API_KEY`, a LLM não funciona.
2. **Variabilidade** — pequenas diferenças entre execuções mesmo com temperatura baixa.
3. **Sem RAG** — a LLM não consulta banco de dados; só o contexto enviado no prompt.
4. **Depósito hospitalar** — não modelado; rotas são fechadas por trecho de veículo.

## Conclusão

A integração atende aos requisitos do PDF: instruções, relatório operacional, sugestões de melhoria e chat. A qualidade é **adequada para uso operacional** quando os dados VRP são enviados corretamente por veículo. Recomenda-se demonstrar no vídeo pelo menos 3 perguntas do roteiro acima.

## Como reproduzir a avaliação

1. Configure `.env` com `GROQ_API_KEY`.
2. Execute `python tsp.py` e aguarde o painel.
3. Teste as perguntas da tabela na aba **Chat**.
4. Compare respostas com a aba **Veículos** e o terminal.
