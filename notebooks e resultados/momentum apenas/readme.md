# Momentum — janelas, Top N e Deadband

Este README documenta o notebook [`momentums.ipynb`](notebooks/momentum%20apenas/momentums.ipynb), atualizado com janelas de Momentum, custos de transação e cálculo do Sharpe com CDI histórico na comparação principal das estratégias.

**Escopo:** Momentum com pesos iguais; **GARCH ainda não implementado** neste notebook.

## 1. Dados e períodos

- **Fonte:** planilha `bases de dados/economatica-3.xlsx` (Economatica), lida com `header=3`.
- **Amostra de preços utilizada:** 02/01/2015 a 30/12/2021; **1.730 observações** e **30 ativos**.
- **Histórico inicial:** 2015–2016, destinado à formação dos indicadores.
- **Treinamento:** 2017–2020, usado para comparar as configurações.
- **Validação:** 2021, separado do treinamento.
- **Dados de 2022 em diante:** não utilizados.

### Tratamento dos dados

1. Padronização dos nomes das colunas e conversão da coluna de datas.
2. Ordenação cronológica, exclusão de linhas sem data e restrição ao intervalo 2015–2021.
3. Conversão dos preços para valores numéricos, com `'-'` tratado como ausente.
4. Remoção de dias sem nenhum preço disponível.
5. Preenchimento para a frente de **no máximo um registro ausente** (`ffill(limit=1)`).
6. Verificações de datas/tickers duplicados, preços não positivos ou infinitos.
7. Cálculo dos retornos diários por `pct_change(fill_method=None)`.

## 2. Estratégias implementadas

### Indicador de Momentum

Para cada ativo e data de formação `t`, o indicador é:

```text
Momentum(k-1) = P(t-21) / P(t-k) - 1
```

Em que `P` representa o preço e `k` é a janela de formação, em pregões:

| Janela | Pregões de formação (`k`) | Pregões recentes desconsiderados |
|:--|--:|--:|
| 6–1 | 126 | 21 |
| 9–1 | 189 | 21 |
| 12–1 | 252 | 21 |

Os rankings são calculados no último pregão disponível de cada mês.

### Regras de seleção

| Método | Regra | Número de posições |
|:--|:--|--:|
| Top 5 | Seleciona os cinco maiores indicadores | 5 |
| Top 10 | Seleciona os dez maiores indicadores | 10 |
| Top 15 | Seleciona os quinze maiores indicadores | 15 |
| Deadband 7 | Mantém as posições existentes enquanto estiverem entre as sete primeiras; completa até cinco posições com o ranking | 5 |
| Deadband 10 | Mesma regra, com permanência até a décima posição do ranking | 5 |

São **3 janelas × 5 regras de seleção = 15 combinações**.

### Pesos e execução

- Os ativos selecionados recebem pesos iguais no rebalanceamento (por exemplo, 20% para cinco ativos).
- Entre rebalanceamentos, os pesos variam conforme os retornos dos ativos.
- O sinal é formado no último pregão do mês, a ordem é executada **no fechamento do pregão seguinte** e os novos pesos passam a afetar os retornos a partir do pregão posterior.
- O backtest começa em caixa em janeiro de 2017, até a primeira ordem.
- A passagem de 2020 para 2021 preserva as posições e o estado do Deadband.
- Meses com quantidade insuficiente de ações elegíveis não geram nova ordem.

## 3. Backtest, custos e métricas

Os backtests utilizam retornos diários, com custos proporcionais ao turnover. O **turnover** corresponde à soma das mudanças absolutas dos pesos, sem divisão por dois; a primeira compra também gera custo. Não há liquidação fictícia no fim de cada período.

```text
Retorno líquido diário = (1 + retorno bruto diário) × (1 − custo × turnover diário) − 1
```

Custos simulados: **0%**, **0,10%** e **0,30%** por valor negociado. O custo-base é **0,10%**.

Métricas calculadas:

- **Retorno anual (%):** retorno composto anualizado com 252 pregões por ano.
- **Volatilidade anual (%):** desvio-padrão dos retornos diários líquidos multiplicado por `√252`.
- **Sharpe:** excesso de retorno médio diário dividido pelo desvio-padrão do excesso diário, multiplicado por `√252`.
- **Max Drawdown (%):** maior queda do patrimônio acumulado em relação ao pico anterior, incluindo o patrimônio inicial de 1.
- **Turnover anual:** soma do turnover diário, anualizada para 252 pregões.

### CDI no cálculo do Sharpe

O notebook passou a consultar o **CDI diário**, série **SGS 12** da API do Banco Central, com dados solicitados de **01/12/2016 a 31/12/2021**. Os valores da série, informados em percentual diário, são divididos por 100 para obter taxas em formato decimal. O alinhamento aos retornos é feito por data, com preenchimento pelo último CDI disponível (`ffill`).

```text
Sharpe com CDI = média(retorno líquido diário − CDI diário)
                 / desvio-padrão(retorno líquido diário − CDI diário) × √252
```

A função `calcular_sharpe(retornos, pregoes_ano=252, cdi=None)` aceita uma série de CDI opcional; quando não é informada, utiliza **taxa livre de risco zero**.

**Distinção entre as saídas do notebook:**

- **Tabela das 15 estratégias e matriz de Sharpe (seção 5):** `calcular_metricas(..., cdi=cdi_diario)`, portanto **Sharpe com CDI diário**.
- **Sensibilidade aos custos (seção 5):** `calcular_metricas(...)` sem `cdi`, portanto **Sharpe com rf = 0**.
- **Tabelas originais de treinamento e validação das cinco estratégias 12–1 (seção 6):** **Sharpe com rf = 0**.

## 4. Alterações em relação à versão anterior

A versão inicial avaliava apenas o Momentum **12–1**, com Top 5, Top 10, Top 15, Deadband 7 e Deadband 10. A versão atual inclui:

1. Janelas de Momentum **6–1**, **9–1** e **12–1** e comparação de **15 combinações**.
2. Dicionários `momentums`, `carteiras_grid`, `pesos_grid` e `resultados_grid`.
3. Tabela de métricas de treinamento `tabela_grid_treino` e matriz `matriz_sharpe`.
4. Tabela `tabela_robustez` com Sharpes para três custos de negociação.
5. Consulta ao **CDI diário histórico** do Banco Central e argumentos opcionais `cdi` em `calcular_sharpe` e `calcular_metricas`.
6. Aplicação do **Sharpe com CDI** à tabela principal das 15 combinações. As tabelas de custos e de validação anteriores permanecem com `rf = 0`.
7. Célula auxiliar destinada à extração das funções para `funcoes_momentum.py`, sujeita à disponibilidade do caminho local do notebook.

Permanecem os gráficos de patrimônio e as tabelas das cinco estratégias originais 12–1, separadas entre treinamento e validação.

## 5. Resultados — treinamento (2017–2020)

### Comparação das 15 combinações — custo 0,10%, Sharpe com CDI diário

Valores registrados na saída de `tabela_grid_treino` do notebook atualizado, ordenados pelo Sharpe com CDI. As demais métricas consideram os retornos líquidos dos custos.

| Janela   | Seleção     |   Retorno anual (%) |   Volatilidade (%) |   Sharpe |   Max Drawdown (%) |   Turnover anual |
|:---------|:------------|--------------------:|-------------------:|---------:|-------------------:|-----------------:|
| 6-1      | Top 5       |              64.226 |             36.626 |    1.378 |            -56.746 |            9.141 |
| 6-1      | Deadband 7  |              58.919 |             37.600 |    1.265 |            -56.173 |            7.465 |
| 6-1      | Deadband 10 |              53.891 |             35.430 |    1.228 |            -51.292 |            5.616 |
| 12-1     | Top 5       |              48.951 |             36.387 |    1.115 |            -51.292 |            6.034 |
| 9-1      | Deadband 7  |              44.863 |             35.754 |    1.051 |            -51.292 |            4.882 |
| 6-1      | Top 10      |              38.629 |             30.343 |    1.032 |            -47.599 |            6.870 |
| 12-1     | Top 15      |              37.304 |             29.203 |    1.027 |            -44.064 |            3.767 |
| 9-1      | Top 5       |              42.781 |             35.108 |    1.022 |            -51.292 |            6.722 |
| 9-1      | Top 15      |              35.237 |             28.510 |    0.991 |            -42.800 |            4.357 |
| 12-1     | Deadband 7  |              41.730 |             36.424 |    0.978 |            -51.292 |            4.674 |
| 12-1     | Top 10      |              37.752 |             32.894 |    0.958 |            -48.355 |            4.733 |
| 6-1      | Top 15      |              34.177 |             29.214 |    0.948 |            -47.668 |            5.353 |
| 9-1      | Deadband 10 |              37.775 |             36.111 |    0.905 |            -51.870 |            3.946 |
| 12-1     | Deadband 10 |              38.059 |             39.170 |    0.870 |            -58.732 |            3.581 |
| 9-1      | Top 10      |              32.054 |             32.042 |    0.843 |            -50.273 |            5.995 |

### Matriz de Sharpe com CDI diário — treinamento (2017–2020)

| Janela   |   Top 5 |   Top 10 |   Top 15 |   Deadband 7 |   Deadband 10 |
|:---------|--------:|---------:|---------:|-------------:|--------------:|
| 6-1      |   1.378 |    1.032 |    0.948 |        1.265 |         1.228 |
| 9-1      |   1.022 |    0.843 |    0.991 |        1.051 |         0.905 |
| 12-1     |   1.115 |    0.958 |    1.027 |        0.978 |         0.870 |

### Sensibilidade do Sharpe aos custos — treinamento (2017–2020), rf = 0

Nesta tabela específica, o código utiliza `calcular_metricas(treino, custo=custo_valor)` sem passar o CDI.

| Estratégia         |   Sharpe 0% |   Sharpe 0,10% |   Sharpe 0,30% |
|:-------------------|------------:|---------------:|---------------:|
| 6-1 | Top 5        |       1.569 |          1.544 |          1.494 |
| 6-1 | Top 10       |       1.255 |          1.232 |          1.187 |
| 6-1 | Top 15       |       1.175 |          1.156 |          1.120 |
| 6-1 | Deadband 7   |       1.446 |          1.427 |          1.387 |
| 6-1 | Deadband 10  |       1.415 |          1.400 |          1.368 |
| 9-1 | Top 5        |       1.214 |          1.195 |          1.157 |
| 9-1 | Top 10       |       1.051 |          1.033 |          0.995 |
| 9-1 | Top 15       |       1.220 |          1.205 |          1.175 |
| 9-1 | Deadband 7   |       1.235 |          1.221 |          1.193 |
| 9-1 | Deadband 10  |       1.085 |          1.074 |          1.052 |
| 12-1 | Top 5       |       1.299 |          1.283 |          1.250 |
| 12-1 | Top 10      |       1.157 |          1.143 |          1.114 |
| 12-1 | Top 15      |       1.248 |          1.235 |          1.210 |
| 12-1 | Deadband 7  |       1.158 |          1.145 |          1.120 |
| 12-1 | Deadband 10 |       1.035 |          1.026 |          1.008 |

## 6. Resultados — validação (2021)

A versão original do bloco de avaliação por período calcula os resultados em 2021 **para as cinco estratégias 12–1**. A tabela abaixo corresponde a esse bloco, com custo de 0,10% e **Sharpe com rf = 0**, e não à comparação das 15 combinações.

| Seleção     |   Retorno anual (%) |   Volatilidade (%) |   Sharpe |   Max Drawdown (%) |   Turnover anual |
|:------------|--------------------:|-------------------:|---------:|-------------------:|-----------------:|
| Top 5       |              24.656 |             33.602 |    0.823 |            -23.028 |            5.746 |
| Top 10      |              12.464 |             27.238 |    0.567 |            -20.084 |            4.289 |
| Top 15      |               9.226 |             23.385 |    0.494 |            -16.391 |            3.500 |
| Deadband 7  |               6.257 |             33.348 |    0.348 |            -31.805 |            4.040 |
| Deadband 10 |              -3.268 |             33.433 |    0.067 |            -34.027 |            3.335 |

## 7. Funções principais

| Função | Operação |
|:--|:--|
| `preparar_precos` | Limpeza e validação da base de preços |
| `criar_top_n` | Seleção das maiores pontuações de Momentum |
| `criar_deadband` | Seleção com faixa de permanência no ranking |
| `criar_pesos` | Conversão das seleções em pesos iguais |
| `backtest` | Simulação diária, execução defasada e registro do turnover |
| `aplicar_custos` | Desconto proporcional dos custos de transação |
| `calcular_sharpe` | Sharpe anualizado, com CDI opcional |
| `calcular_metricas` | Retorno, volatilidade, Sharpe, drawdown e turnover |

O notebook inclui uma célula auxiliar para exportar essas funções para `funcoes_momentum.py`. A execução salva dessa célula terminou com `FileNotFoundError` ao localizar o notebook pela estrutura de pastas definida nela; o arquivo `.py` não é uma dependência das demais análises do notebook.

## 8. Execução e dependências

Dependências: **Python, Jupyter, pandas, numpy, matplotlib, openpyxl, IPython e requests**.

```bash
pip install pandas numpy matplotlib openpyxl ipython notebook requests
```

1. Abrir `notebooks/momentum apenas/momentums.ipynb`.
2. Ajustar `ARQUIVO_PRECOS` para o caminho local de `economatica-3.xlsx`.
3. Executar as células de importação, consulta ao CDI, funções, leitura dos preços e análise na ordem apresentada. A consulta à API do Banco Central requer acesso à internet.
4. A célula opcional de exportação de funções depende da localização do notebook e não é necessária para os backtests.

### Limitações registradas no notebook

- Não há implementação de GARCH nem ponderação por volatilidade prevista.
- Não há filtro de liquidez, modelagem de impacto de mercado, impostos ou tratamento de deslistagem.
- O código não audita ajustes corporativos nem viés de sobrevivência dos ativos.
- Retornos ausentes nas posições compradas geram erro em vez de serem substituídos por zero.
- As métricas são anualizadas usando 252 pregões por ano.
- A base de preços cobre somente o intervalo **2015–2021** para estes cálculos.

### Origem das tabelas

Os resultados **com CDI** foram transcritos das saídas salvas em `momentums(2).ipynb`. Os resultados de **sensibilidade aos custos com `rf = 0`** foram também conferidos por execução do código com a planilha `economatica-3.xlsx`. O CDI histórico integral é obtido pela API do Banco Central durante a execução do notebook e não está embutido como série completa no arquivo `.ipynb`.
