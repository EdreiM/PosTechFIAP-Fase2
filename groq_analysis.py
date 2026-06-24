import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analisar_resultado(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    melhoria_fitness,
    melhoria_distancia,
    fitness_target_solution,
    diferenca_benchmark,
    top10_prioridades,
    texto_rota,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10
):

    prompt = f"""
Analise os resultados abaixo de um Algoritmo Genético aplicado ao Problema do Caixeiro Viajante (TSP).

Dados do experimento:

Fitness inicial: {fitness_inicial:.2f}
Fitness final utilizado pelo algoritmo:
{fitness_final_prioridade:.2f}

Distância real da rota encontrada:
{fitness_final:.2f}

Importante:

O algoritmo otimiza o fitness com prioridades.
A distância real é apresentada apenas para comparação com o benchmark ATT48.

Não trate distância real e fitness como a mesma métrica.

Melhoria do fitness: {melhoria_fitness:.2f}%

Melhoria da distância real: {melhoria_distancia:.2f}%

Solução ótima do benchmark ATT48:
{fitness_target_solution:.2f}

Diferença para a solução ótima:
{diferenca_benchmark:.2f}%
Geração de convergência:
{geracao_convergencia:.2f}
Ao avaliar a convergência:

- considere a geração de convergência informada
- explique se a convergência ocorreu cedo ou tarde
- explique o que isso indica sobre a busca do algoritmo
Objetivo da estratégia:

Cidades com prioridade mais alta devem aparecer o mais cedo possível na rota.

Escala:
1 = baixa prioridade
10 = prioridade crítica

Top 10 prioridades encontradas nas primeiras posições da rota:

{top10_prioridades}

Quantidade de cidades com prioridade 10:
{prioridade_10}

Quantidade de cidades com prioridade 9 ou 10:
{prioridade_9_10}

Média das prioridades das 10 primeiras posições:
{media_top10:.2f}

Rota detalhada encontrada:

Cada item possui:

- ordem
- nome
- x
- y
- prioridade

{texto_rota}

Considere a estratégia bem sucedida quando:

- mais da metade das 10 primeiras posições possuir prioridade igual ou superior a 8

- prioridades 9 e 10 estiverem concentradas no início da rota

Não exija que todas as primeiras posições sejam prioridades máximas.
Avalie a distribuição de forma estatística.

Parâmetros do algoritmo:

População: 100
Gerações: 1000
Taxa de mutação: 0.5
Importante:

Não invente cidades.
Não invente coordenadas.
Não invente prioridades.
Utilize exclusivamente os dados fornecidos.
Caso alguma informação não esteja disponível, informe isso explicitamente.
Explique em linguagem acadêmica:

1. O que os resultados significam.
2. Se houve convergência.
3. Qualidade da solução encontrada.
4. Comparação com a solução ótima.
5. Conclusão final.
6. Avalie se as prioridades mais altas realmente aparecem no início da rota.
7. Explique se a estratégia baseada em prioridades foi bem sucedida.
8. Analise a rota completa.

9. Utilize TODAS as cidades presentes em "Rota detalhada encontrada".

Não resuma a rota.

Liste todas as cidades na ordem de visita.


Para cada cidade informe:

- ordem
- nome
- coordenadas
- prioridade

10. Gere um plano operacional.

Importante:

NÃO crie uma nova ordem de atendimento.

NÃO reorganize as cidades por prioridade.

Considere que a ordem produzida pelo algoritmo genético já é a ordem oficial da rota.

Explique apenas como a equipe deve executar essa rota.
11. Gere um plano de entrega detalhado.
"""

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return resposta.choices[0].message.content