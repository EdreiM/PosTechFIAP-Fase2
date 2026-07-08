# Testes do projeto

## Como rodar

Na raiz do repositório:

```bash
py -m pytest tests/test_projeto.py -v          # todos
py -m pytest tests/test_projeto.py -q          # resumo
py -m pytest tests/test_projeto.py -k chat -v  # só testes com "chat" no nome
```

## Arquivos

| Arquivo | Função |
|---------|--------|
| `test_projeto.py` | Suite principal (88 testes) |
| `fixtures_dados.py` | Cenários reutilizáveis — **leia este arquivo primeiro** |
| `validadores_ia.py` | Regras compartilhadas (eco de prompt, prioridade p10, etc.) |
| `conftest.py` | Ajusta `sys.path` para importar módulos da raiz |

## Dois tipos de cenário (não confundir)

### 1. Modo fixo do sistema

Função: `configurar_cenario_fixo(5)` em `fixtures_dados.py`

- Igual à opção **fixo** na janela de configuração.
- UTI Norte, kits, prioridades vêm de tabelas fixas.
- **Seed não muda** nomes nem demandas.
- Usado em `TestDadosHospitalares`, `TestConfig`, AG com dados hospitalares reais.

### 2. Textos simulados (chat / regressão)

Constantes: `CHAT_V3_*`, `CHAT_V2_*`, `REGRESSAO_18_*`

- Strings no formato que o `tsp.py` gera (`texto_veiculos`, rotas).
- Permitem testar **chat e IA** sem abrir Pygame nem chamar Groq.
- Não precisam ser idênticos a uma execução sua — só ao **formato** esperado.

## Mapa das classes em `test_projeto.py`

| Classe | O que valida |
|--------|----------------|
| `TestConfig` | `config.py`, cidades fixo/aleatório |
| `TestConfigUI` | Parâmetros da janela, avisos de benchmark |
| `TestDadosHospitalares` | Modo fixo, CSV, priorização, viabilidade da frota |
| `TestGeneticAlgorithm` | VRP, fitness, crossover (usa `CIDADES_AG_MINI`) |
| `TestAgRunner` | Loop do algoritmo genético |
| `TestGroqUtils` / `TestGroqConteudo` | API Groq desabilitada, parsing de relatórios |
| `TestGroqRespostasLocais` | Chat local (veículo 2, 3, kits, motorista) |
| `TestDashboardMapa` / `TestDashboardAnalise` | Painel e bloco de métricas |
| `TestRegressaoBugsUsuario` | Bugs encontrados em demo real (18 entregas, V3) |

## Modo fixo vs aleatório na aplicação

| | Modo fixo | Modo aleatório |
|---|-----------|----------------|
| Coordenadas | `DEFAULT_PROBLEMS` em `config.py` | Sorteadas com seed |
| Nomes/kits | Tabelas em `dados_hospitalares.py` | Sorteados com seed |
| Demo/apresentação | Recomendado (sempre igual) | Cenário diferente a cada seed |
