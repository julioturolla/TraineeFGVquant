# Momentum — janelas, Top N e Deadband

Este README documenta o notebook [`momentums.ipynb`](notebooks/momentum%20apenas/momentums.ipynb), que realiza backtests de estratégias de Momentum com diferentes janelas de formação, métodos de seleção de ações e custos de transação.

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

Os backtests utilizam retornos diários, com custos proporcionais ao turnover. O **turnover** é a soma dos valores absolutos das mudanças de pesos, sem divisão por dois. A primeira compra também gera custo; não há liquidação fictícia no final de cada período.

```text
Retorno líquido = (1 + Retorno bruto) × (1 − custo × Turnover) − 1
```

Custos avaliados: **0%**, **0,10%** e **0,30%** do valor negociado. O cenário-base das tabelas de desempenho utiliza **0,10%**.

Métricas calculadas:

- **Retorno anual (%):** retorno composto anualizado com 252 pregões/ano.
- **Volatilidade (%):** desvio-padrão diário anualizado por `√252`.
- **Sharpe:** retorno médio diário dividido pelo desvio-padrão diário, multiplicado por `√252`, com taxa livre de risco igual a zero.
- **Max Drawdown (%):** maior queda em relação ao pico acumulado, incluindo patrimônio inicial igual a 1.
- **Turnover anual:** soma do turnover diário anualizada por 252 pregões.

## 4. Alterações em relação à versão anterior

O notebook anterior avaliava a janela **12–1** com as cinco regras Top 5, Top 10, Top 15, Deadband 7 e Deadband 10.

A versão atual acrescenta:

1. Indicadores para as janelas **6–1** e **9–1**, mantendo **12–1**.
2. Geração das **15 carteiras** no dicionário `carteiras_grid`.
3. Geração dos pesos correspondentes em `pesos_grid`.
4. Execução dos backtests em `resultados_grid`.
5. Consolidação das métricas de 2017–2020 em `tabela_grid_treino`.
6. Matriz de Sharpe por janela e seleção em `matriz_sharpe`.
7. Comparação do Sharpe sob três custos em `tabela_robustez`.

Permanecem no notebook as tabelas e os gráficos de patrimônio das cinco estratégias originais de **12–1**, separados entre treinamento e validação.

## 5. Resultados — treinamento (2017–2020)

**Custo por valor negociado: 0,10%.** Resultados ordenados pelo Sharpe, conforme a tabela gerada no notebook.

| Janela   | Seleção     |   Retorno anual (%) |   Volatilidade (%) |   Sharpe |   Max Drawdown (%) |   Turnover anual |
|:---------|:------------|--------------------:|-------------------:|---------:|-------------------:|-----------------:|
| 6-1      | Top 5       |              64.226 |             36.626 |    1.544 |            -56.746 |            9.141 |
| 6-1      | Deadband 7  |              58.919 |             37.600 |    1.427 |            -56.173 |            7.465 |
| 6-1      | Deadband 10 |              53.891 |             35.430 |    1.400 |            -51.292 |            5.616 |
| 12-1     | Top 5       |              48.951 |             36.387 |    1.283 |            -51.292 |            6.034 |
| 12-1     | Top 15      |              37.304 |             29.203 |    1.235 |            -44.064 |            3.767 |
| 6-1      | Top 10      |              38.629 |             30.343 |    1.232 |            -47.599 |            6.870 |
| 9-1      | Deadband 7  |              44.863 |             35.754 |    1.221 |            -51.292 |            4.882 |
| 9-1      | Top 15      |              35.237 |             28.510 |    1.205 |            -42.800 |            4.357 |
| 9-1      | Top 5       |              42.781 |             35.108 |    1.195 |            -51.292 |            6.722 |
| 6-1      | Top 15      |              34.177 |             29.214 |    1.156 |            -47.668 |            5.353 |
| 12-1     | Deadband 7  |              41.730 |             36.424 |    1.145 |            -51.292 |            4.674 |
| 12-1     | Top 10      |              37.752 |             32.894 |    1.143 |            -48.355 |            4.733 |
| 9-1      | Deadband 10 |              37.775 |             36.111 |    1.074 |            -51.870 |            3.946 |
| 9-1      | Top 10      |              32.054 |             32.042 |    1.033 |            -50.273 |            5.995 |
| 12-1     | Deadband 10 |              38.059 |             39.170 |    1.026 |            -58.732 |            3.581 |

### Matriz de Sharpe — treinamento (2017–2020)

| Janela   |   Top 5 |   Top 10 |   Top 15 |   Deadband 7 |   Deadband 10 |
|:---------|--------:|---------:|---------:|-------------:|--------------:|
| 6-1      |   1.544 |    1.232 |    1.156 |        1.427 |         1.400 |
| 9-1      |   1.195 |    1.033 |    1.205 |        1.221 |         1.074 |
| 12-1     |   1.283 |    1.143 |    1.235 |        1.145 |         1.026 |

### Sensibilidade do Sharpe aos custos — treinamento (2017–2020)

A coluna `Queda Sharpe` corresponde à diferença entre o Sharpe sem custos e o Sharpe com custo de 0,30%.

| Janela   | Seleção     |   Sharpe 0% |   Sharpe 0,10% |   Sharpe 0,30% |   Queda Sharpe |
|:---------|:------------|------------:|---------------:|---------------:|---------------:|
| 6-1      | Top 5       |       1.569 |          1.544 |          1.494 |          0.075 |
| 6-1      | Deadband 7  |       1.446 |          1.427 |          1.387 |          0.059 |
| 6-1      | Deadband 10 |       1.415 |          1.400 |          1.368 |          0.048 |
| 12-1     | Top 5       |       1.299 |          1.283 |          1.250 |          0.049 |
| 12-1     | Top 15      |       1.248 |          1.235 |          1.210 |          0.038 |
| 6-1      | Top 10      |       1.255 |          1.232 |          1.187 |          0.067 |
| 9-1      | Deadband 7  |       1.235 |          1.221 |          1.193 |          0.041 |
| 9-1      | Top 15      |       1.220 |          1.205 |          1.175 |          0.045 |
| 9-1      | Top 5       |       1.214 |          1.195 |          1.157 |          0.057 |
| 6-1      | Top 15      |       1.175 |          1.156 |          1.120 |          0.055 |
| 12-1     | Deadband 7  |       1.158 |          1.145 |          1.120 |          0.038 |
| 12-1     | Top 10      |       1.157 |          1.143 |          1.114 |          0.043 |
| 9-1      | Deadband 10 |       1.085 |          1.074 |          1.052 |          0.033 |
| 9-1      | Top 10      |       1.051 |          1.033 |          0.995 |          0.056 |
| 12-1     | Deadband 10 |       1.035 |          1.026 |          1.008 |          0.027 |

## 6. Resultados — validação (2021)

A versão original do bloco de avaliação por período calcula os resultados em 2021 **para as cinco estratégias 12–1**. A tabela abaixo corresponde a esse bloco, com custo de 0,10%, e não à comparação das 15 combinações.

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
| `criar_top_n` | Geração de carteiras com as maiores pontuações de Momentum |
| `criar_deadband` | Geração de carteiras com faixa de permanência |
| `criar_pesos` | Conversão das carteiras em pesos iguais |
| `backtest` | Simulação diária, execução defasada das ordens e turnover |
| `aplicar_custos` | Aplicação do custo proporcional ao turnover |
| `calcular_sharpe` | Sharpe anualizado |
| `calcular_metricas` | Consolidação de retorno, volatilidade, Sharpe, drawdown e turnover |

As funções estão definidas diretamente no notebook. O código atual não depende de um módulo externo `funcoes_momentum.py`.

## 8. Execução

Dependências principais: **Python, Jupyter, pandas, numpy, matplotlib, openpyxl e IPython**.

```bash
pip install pandas numpy matplotlib openpyxl ipython notebook tabulate
```

1. Abrir `notebooks/momentum apenas/momentums.ipynb`.
2. Ajustar a variável `ARQUIVO_PRECOS` para a localização da planilha no computador.
3. Executar as células na ordem em que aparecem.

### Observações de implementação

- O código não implementa GARCH ou ponderação pela volatilidade prevista.
- Não há filtro de liquidez, simulação de impacto de mercado, impostos ou tratamento de deslistagem.
- O notebook não verifica, por si só, ajustes corporativos dos preços nem viés de sobrevivência da seleção de ativos.
- Retornos ausentes de posições compradas geram erro, em vez de serem convertidos em zero.
- A anualização utiliza 252 pregões por ano.
