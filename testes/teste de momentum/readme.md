## Estratégia de Momentum — Backtest e Análise de Robustez

### 1. Objetivo

O objetivo desta etapa foi desenvolver e avaliar uma estratégia quantitativa de **Momentum**, investigando diferentes regras de seleção e manutenção de ativos.

Foram comparadas três abordagens: **Top 5**, **Deadband 7** e **Deadband 10**, buscando identificar qual apresenta o melhor desempenho ajustado ao risco e como a redução do turnover afeta os resultados.

O período de desenvolvimento e avaliação utilizado foi **2017–2023**, reservando 2024–2026 para uma posterior análise fora da amostra (*out-of-sample*).

### 2. Tratamento dos dados

Foram utilizados preços históricos de ações brasileiras extraídos da Economatica.

O pré-processamento incluiu:

- Padronização dos nomes das colunas e conversão das datas.
- Conversão dos preços para valores numéricos.
- Tratamento de valores ausentes e exclusão de datas sem observações válidas.
- Preenchimento limitado de lacunas nos preços (`ffill(limit=1)`).
- Cálculo dos retornos diários simples.

### 3. Construção das estratégias

**Indicador de Momentum 12-1**

O indicador foi calculado utilizando a valorização acumulada entre aproximadamente 12 meses e 1 mês antes da formação da carteira:

\[
M_{i,t}=\frac{P_{i,t-21}}{P_{i,t-252}}-1
\]

Essa definição exclui o mês mais recente, seguindo a abordagem tradicional de Momentum 12-1.

Os ativos são classificados mensalmente pelo indicador, do maior para o menor.

**Estratégias avaliadas**

| Estratégia | Regra de seleção |
|---|---|
| Top 5 | Seleciona mensalmente as cinco ações com maior Momentum |
| Deadband 7 | Mantém as ações existentes enquanto permanecerem entre as sete primeiras do ranking |
| Deadband 10 | Mantém as ações existentes enquanto permanecerem entre as dez primeiras do ranking |

Nos Deadbands, as posições que deixam a faixa permitida são substituídas pelas ações mais bem classificadas que ainda não estão na carteira.

Todas as estratégias utilizam:

- Cinco ações por carteira.
- Pesos iguais de 20% no rebalanceamento.
- Rebalanceamento mensal.
- Execução das novas alocações após a geração dos sinais, evitando utilizar retornos anteriores à decisão.

### 4. Backtest

Foi desenvolvido um backtest que acompanha os retornos diários das carteiras, permitindo que os pesos variem com a valorização dos ativos entre os rebalanceamentos.

Nos rebalanceamentos mensais, os pesos são ajustados novamente aos valores-alvo.

O algoritmo também calcula o **turnover**, definido como a soma das variações absolutas dos pesos, possibilitando incorporar custos proporcionais ao volume negociado.

### 5. Resultados

**Tabela 1 — Desempenho geral (2017–2023)**

| Indicador | Top 5 | Deadband 7 | Deadband 10 |
|---|---:|---:|---:|
| Retorno anualizado bruto | 35,3% | 29,5% | 29,7% |
| Sharpe bruto | 1,091 | 0,962 | 0,924 |
| Máximo drawdown | -51,3% | -50,5% | -58,8% |
| Turnover anual | 6,733 | 4,270 | 3,282 |

O Top 5 apresentou o maior retorno anualizado e o maior Sharpe. Os Deadbands reduziram o turnover, mas essa redução veio acompanhada de menor desempenho ajustado ao risco na amostra analisada.

**Tabela 2 — Sensibilidade aos custos de transação**

| Estratégia | Sem custos | Custo 0,10% | Custo 0,30% |
|---|---:|---:|---:|
| Top 5 | 1,091 | 1,070 | 1,029 |
| Deadband 7 | 0,962 | 0,949 | 0,923 |
| Deadband 10 | 0,924 | 0,914 | 0,896 |

*Valores apresentados em Sharpe anualizado.*

Foram simulados custos proporcionais ao volume negociado. Como esperado, o Top 5 apresentou maior sensibilidade aos custos devido ao turnover mais elevado. Entretanto, manteve o maior Sharpe nos três cenários.

**Tabela 3 — Robustez temporal**

| Estratégia | 2017–2020 | 2021–2023 |
|---|---:|---:|
| Top 5 | 1,283 | 0,722 |
| Deadband 7 | 1,171 | 0,582 |
| Deadband 10 | 1,061 | 0,676 |

*Sharpe anualizado considerando custo de transação de 0,10%.*

O Top 5 apresentou desempenho superior nos dois subperíodos, embora todas as estratégias tenham registrado redução do Sharpe em 2021–2023.

### 6. Conclusões preliminares

Os resultados favorecem a estratégia Top 5 dentro da amostra analisada. A utilização dos Deadbands reduziu a rotatividade das carteiras, mas não proporcionou melhora suficiente no desempenho para superar o Top 5, mesmo após a inclusão dos custos simulados.

Os resultados sugerem que a substituição mais frequente de ativos pode ser vantajosa quando a seleção é baseada no Momentum 12-1.




4. Após definir e congelar os parâmetros da estratégia completa, realizar o teste fora da amostra em **2024–2026**.

