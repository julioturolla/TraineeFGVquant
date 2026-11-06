# Comparação de benchmarks — Momentum 12–1 e GJR-GARCH

**Projeto:** [TraineeFGVquant](https://github.com/julioturolla/TraineeFGVquant)  
**Notebook:** `comparacao_benchmarks.ipynb`  
**Períodos:** treinamento de 2017 a 2020 e validação em 2021, com histórico a partir de 2015. O período de 2022–2026 permanece reservado para o teste final.

## 1. Objetivo do estudo

O objetivo desta análise é investigar se a utilização da volatilidade prevista por um modelo GJR-GARCH para determinar os pesos de uma carteira selecionada por Momentum melhora seu desempenho ajustado ao risco no mercado acionário brasileiro.

A comparação central envolve duas estratégias que utilizam exatamente o mesmo critério de seleção de ativos:

1. **Momentum 12–1 Top 5 com pesos iguais:** seleciona mensalmente as cinco ações de maior Momentum e distribui o capital igualmente entre elas.
2. **Momentum 12–1 Top 5 com GJR-GARCH:** seleciona as mesmas cinco ações, mas determina os pesos de acordo com o inverso de suas volatilidades previstas.

A metodologia permite isolar o efeito da ponderação por risco, mantendo constante a seleção das ações.

Além dessas duas estratégias, são utilizados como benchmarks o Ibovespa (IBOV), o IBrX 50 (IBXL), o índice Small Cap (SMLL), o índice de Dividendos (IDIV), uma carteira equiponderada de 30 ações e o CDI.

## 2. Dados e metodologia

### 2.1. Base de dados

Os dados de preços foram obtidos da Economatica, abrangendo um universo de 30 ações brasileiras.

A amostra foi dividida em três etapas:

| Período | Utilização |
|---|---|
| 2015–2016 | Histórico inicial para cálculo dos sinais e estimação da volatilidade |
| 2017–2020 | Treinamento (*in-sample*) |
| 2021 | Validação |
| 2022–2026 | Teste final reservado (*out-of-sample*) |

A divisão permite estudar o comportamento das estratégias em diferentes períodos, sem utilizar a amostra final na escolha dos parâmetros.

### 2.2. Sinal de Momentum

O sinal utilizado é o Momentum 12–1, que mede o retorno acumulado da ação aproximadamente nos últimos 12 meses, desconsiderando o mês mais recente.

Sua fórmula é:

\[
M_{i,t}=\frac{P_{i,t-21}}{P_{i,t-252}}-1
\]

Em que:

- \(P_{i,t-21}\) representa o preço da ação 21 pregões antes da formação da carteira.
- \(P_{i,t-252}\) representa o preço da ação 252 pregões antes da formação.

A exclusão do último mês busca evitar a influência de movimentos de reversão de curtíssimo prazo sobre o sinal de Momentum.

Mensalmente, são selecionadas as cinco ações com os maiores valores desse indicador.

### 2.3. Ponderação por pesos iguais

Na estratégia tradicional, cada uma das cinco ações selecionadas recebe 20% do capital no momento do rebalanceamento.

A metodologia não utiliza informações sobre o risco individual de cada ação para determinar sua participação na carteira.

Consequentemente, ações com volatilidades muito diferentes recebem inicialmente a mesma alocação de capital.

### 2.4. Ponderação por GJR-GARCH

A segunda estratégia utiliza previsões de volatilidade produzidas pelo modelo GJR-GARCH.

O GJR-GARCH é uma extensão do GARCH tradicional que permite capturar assimetrias na volatilidade, reconhecendo que choques negativos e positivos podem produzir efeitos diferentes sobre a volatilidade futura.

A configuração utilizada no notebook é `("gjr", 756)`, correspondente a uma janela de estimação de 756 pregões.

A carteira utiliza pesos inversamente proporcionais às volatilidades previstas:

\[
w_{i,t}=
\frac{1/\widehat{\sigma}_{i,t}}
{\sum_{j\in C_t}1/\widehat{\sigma}_{j,t}}
\]

Em que \(\widehat{\sigma}_{i,t}\) representa a volatilidade prevista para a ação \(i\).

Portanto, ações com maior volatilidade prevista recebem pesos menores, enquanto ações com menor volatilidade prevista recebem pesos maiores.

O objetivo dessa metodologia não é necessariamente maximizar o retorno bruto, mas melhorar a distribuição do risco entre os ativos selecionados.

**É importante distinguir previsão de volatilidade e eficiência da alocação:** mesmo que um modelo estime adequadamente a volatilidade futura, isso não garante que utilizar suas previsões para definir os pesos produza maior Sharpe.

### 2.5. Rebalanceamento e custos

As carteiras são rebalanceadas mensalmente. As ordens decorrentes dos sinais são executadas no pregão seguinte, e os pesos evoluem conforme os retornos das ações entre os rebalanceamentos.

As simulações consideram um custo de transação de **0,10% sobre o volume negociado**, calculado a partir do turnover.

Os índices e o CDI são utilizados como benchmarks teóricos sem custos de replicação.

### 2.6. Taxa livre de risco

O CDI foi incorporado utilizando a série diária SGS 12 do Banco Central, já empregada em outros códigos do projeto.

O Índice de Sharpe é calculado utilizando os retornos excedentes ao CDI:

\[
Sharpe =
\frac{E[r_{p,t}-r_{CDI,t}]}
{\sigma(r_{p,t}-r_{CDI,t})}
\sqrt{252}
\]

Dessa maneira, o Sharpe representa a remuneração excedente à taxa livre de risco por unidade de volatilidade do retorno excedente.

A inclusão do CDI altera o Sharpe, mas não os retornos anualizados, a volatilidade total, o drawdown ou o turnover das estratégias.

## 3. Resultados finais

### 3.1. Treinamento — 2017 a 2020

| Estratégia | Retorno anual (%) | Volatilidade (%) | Sharpe com CDI | Max Drawdown (%) | Turnover anual |
|---|---:|---:|---:|---:|---:|
| **Momentum 12–1 Top 5** | **48,951** | 36,387 | **1,115** | -51,292 | 6,034 |
| **Momentum Top 5 + GJR** | 38,234 | 33,885 | 0,950 | -45,915 | 7,101 |
| Equiponderada 30 | 31,130 | 27,973 | 0,894 | -47,108 | 1,060 |
| SMLL | 26,816 | 28,667 | 0,764 | -51,693 | 0,000 |
| IDIV | 20,655 | 25,399 | 0,629 | -40,931 | 0,000 |
| IBOV | 18,974 | 28,161 | 0,544 | -46,816 | 0,000 |
| IBXL | 18,474 | 28,677 | 0,525 | -47,675 | 0,000 |

Durante o treinamento, ambas as estratégias Momentum apresentaram retornos e índices de Sharpe superiores aos benchmarks acionários.

A estratégia Momentum com pesos iguais apresentou retorno anualizado de 48,95%, enquanto a estratégia ponderada pelo GJR-GARCH apresentou 38,23%.

A diferença de aproximadamente 10,72 pontos percentuais evidencia que a utilização do GJR reduziu consideravelmente o retorno da carteira.

Por outro lado, a volatilidade anualizada diminuiu de 36,39% para 33,89%, indicando que a ponderação por risco conseguiu reduzir a exposição à volatilidade dos ativos selecionados.

Entretanto, essa redução não foi suficiente para compensar a perda de retorno: o Sharpe caiu de 1,115 para 0,950.

O GJR também apresentou menor drawdown, de -45,92%, comparado a -51,29% da estratégia com pesos iguais. Esse resultado sugere alguma capacidade de proteção durante episódios de perda acentuada, embora essa proteção não tenha gerado maior eficiência segundo o Sharpe.

### 3.2. Validação — 2021

| Estratégia | Retorno anual (%) | Volatilidade (%) | Sharpe com CDI | Max Drawdown (%) | Turnover anual |
|---|---:|---:|---:|---:|---:|
| **Momentum 12–1 Top 5** | **24,656** | 33,602 | **0,695** | -23,028 | 5,746 |
| **Momentum Top 5 + GJR** | 22,197 | 33,244 | 0,639 | -23,756 | 6,567 |
| Equiponderada 30 | 1,249 | 21,167 | -0,040 | -18,479 | 0,851 |
| IDIV | -6,538 | 19,059 | -0,486 | -15,993 | 0,000 |
| IBXL | -10,742 | 21,474 | -0,623 | -23,428 | 0,000 |
| IBOV | -12,153 | 20,987 | -0,718 | -22,941 | 0,000 |
| SMLL | -16,496 | 25,528 | -0,747 | -31,305 | 0,000 |

Na validação, as duas estratégias Momentum continuaram apresentando desempenho superior aos benchmarks acionários.

O Momentum com pesos iguais obteve retorno anualizado de 24,66%, enquanto o GJR apresentou 22,20%.

A volatilidade foi novamente menor na estratégia GJR, mas a redução foi bastante pequena: aproximadamente 0,36 ponto percentual.

O Sharpe com CDI permaneceu superior na versão com pesos iguais, registrando 0,695 contra 0,639 do GJR.

Além disso, diferentemente do treinamento, o GJR não melhorou o drawdown, que passou de -23,03% para -23,76%.

Esse resultado indica que a proteção observada no treinamento não se repetiu integralmente em 2021.

## 4. Contribuição incremental do GJR-GARCH

Para investigar especificamente a contribuição do modelo, comparamos as duas regras de ponderação mantendo constantes o sinal Momentum, as cinco ações selecionadas, as datas de negociação e os custos.

| Métrica | Efeito do GJR em 2017–2020 | Efeito do GJR em 2021 |
|---|---:|---:|
| Retorno anualizado | -10,717 p.p. | -2,459 p.p. |
| Volatilidade | -2,502 p.p. | -0,358 p.p. |
| Sharpe com CDI | -0,165 | -0,056 |
| Max Drawdown | Melhora 5,377 p.p. | Piora 0,728 p.p. |
| Turnover anual | +1,067 | +0,821 |

### 4.1. Redução de volatilidade

A principal contribuição positiva do GJR-GARCH foi a redução da volatilidade realizada da carteira.

No treinamento, a volatilidade diminuiu aproximadamente 6,9% em termos relativos. Na validação, a redução foi de apenas 1,1%.

Isso indica que a ponderação inversa à volatilidade prevista conseguiu diminuir o risco total, mas seu efeito foi mais expressivo no treinamento.

É importante destacar que essa constatação não demonstra, isoladamente, que o GJR ofereça previsões de volatilidade superiores às de modelos mais simples.

Para avaliar a qualidade preditiva do modelo, seria necessário comparar suas previsões com medidas de volatilidade realizada, utilizando métricas como QLIKE ou erro quadrático.

### 4.2. Efeito sobre o retorno

A ponderação por GJR-GARCH apresentou retornos inferiores à ponderação igualitária nos dois períodos.

Uma hipótese econômica para esse resultado é que ações de Momentum elevado também podem apresentar volatilidade elevada. Nesse caso, a ponderação inversa à volatilidade reduziria a exposição justamente a algumas ações com maior potencial de valorização.

Porém, essa hipótese ainda precisa ser testada por meio da análise dos pesos e das contribuições individuais de cada ativo.

Os resultados permitem concluir que houve redução do retorno, mas não identificar definitivamente qual mecanismo produziu essa redução.

### 4.3. Índice de Sharpe

A redução de volatilidade não foi acompanhada por melhora do Índice de Sharpe.

No treinamento, o Sharpe caiu de 1,115 para 0,950. Na validação, caiu de 0,695 para 0,639.

Isso significa que o retorno excedente ao CDI diminuiu proporcionalmente mais do que o benefício proporcionado pela redução de risco.

Portanto, **a ponderação por GJR-GARCH não melhorou o desempenho ajustado ao risco da estratégia Momentum na configuração testada**.

Essa conclusão permanece válida mesmo após incorporar o CDI, diferentemente das análises preliminares realizadas com taxa livre de risco igual a zero.

### 4.4. Drawdown

O comportamento do máximo drawdown foi diferente entre os dois períodos.

Durante o treinamento, o GJR reduziu a maior perda acumulada de 51,29% para 45,92%, uma melhora de aproximadamente 5,38 pontos percentuais.

Entretanto, na validação, o drawdown foi ligeiramente maior com o GJR.

Assim, não há evidência de uma proteção consistente contra perdas extremas nos dois períodos examinados.

### 4.5. Turnover e custos

A estratégia com GJR apresentou maior turnover anual nos dois períodos.

No treinamento, o turnover aumentou de 6,034 para 7,101. Em 2021, passou de 5,746 para 6,567.

Isso ocorre porque os pesos da estratégia variam não apenas com as mudanças nas ações selecionadas, mas também com as atualizações das previsões de volatilidade.

O maior volume de negociação gera custos adicionais e pode reduzir a rentabilidade líquida.

Os resultados já consideram um custo de 0,10% sobre o turnover, mas ainda não foi realizada uma decomposição que determine quanto da perda de retorno do GJR decorre exclusivamente dos custos de transação.

## 5. Comparação com o Ibovespa

Além das métricas tradicionais, foram calculados beta, correlação, retorno ativo, tracking error e Information Ratio em relação ao Ibovespa.

| Período | Estratégia | Beta IBOV | Correlação | Retorno ativo (%) | Tracking Error (%) | Information Ratio |
|---|---|---:|---:|---:|---:|---:|
| 2017–2020 | Momentum Top 5 | 1,040 | 0,805 | 25,273 | 21,605 | 1,170 |
| 2017–2020 | Momentum + GJR | 0,958 | 0,796 | 16,879 | 20,529 | 0,822 |
| 2017–2020 | Equiponderada 30 | 0,961 | 0,967 | 9,692 | 7,189 | 1,348 |
| 2021 | Momentum Top 5 | 1,085 | 0,678 | 38,418 | 24,779 | 1,550 |
| 2021 | Momentum + GJR | 1,083 | 0,683 | 36,306 | 24,330 | 1,492 |
| 2021 | Equiponderada 30 | 0,975 | 0,967 | 14,228 | 5,430 | 2,620 |

### 5.1. Beta e correlação

Durante o treinamento, a introdução do GJR reduziu o beta da carteira de 1,040 para 0,958.

Isso sugere que a ponderação por volatilidade também diminuiu sua sensibilidade média aos movimentos do Ibovespa nesse período.

Entretanto, em 2021, os betas das duas estratégias foram praticamente idênticos: 1,085 e 1,083.

Portanto, a redução da volatilidade total não necessariamente implica redução proporcional do risco sistemático.

A correlação do Momentum com o Ibovespa também foi menor do que a da carteira equiponderada, sugerindo maior importância de fatores específicos da seleção de ativos e de outras fontes de risco não capturadas pelo índice.

### 5.2. Retorno ativo e Information Ratio

O Information Ratio mede o retorno ativo médio em relação ao benchmark por unidade de tracking error.

\[
IR =
\frac{E[r_{p,t}-r_{IBOV,t}]}
{\sigma(r_{p,t}-r_{IBOV,t})}
\sqrt{252}
\]

O Momentum com pesos iguais apresentou Information Ratio superior ao GJR nos dois períodos.

No treinamento, o IR caiu de 1,170 para 0,822 com a introdução do GJR. Em 2021, caiu de 1,550 para 1,492.

Embora o GJR tenha reduzido moderadamente o tracking error, também diminuiu o retorno ativo da carteira, resultando em pior eficiência em relação ao benchmark.

A carteira equiponderada apresentou Information Ratio mais elevado que as estratégias Momentum, especialmente em 2021. Isso se explica por sua elevada correlação com o Ibovespa e pelo menor tracking error.

Contudo, o maior Information Ratio não significa necessariamente maior retorno absoluto ou maior Sharpe.

## 6. Interpretação dos gráficos de patrimônio

Os gráficos apresentam a evolução de um patrimônio inicial de R$ 100 em cada período, considerando os retornos líquidos dos custos modelados para as carteiras.

### 6.1. Treinamento

Entre 2017 e 2020, o Momentum com pesos iguais apresentou a maior valorização acumulada.

A estratégia GJR acompanhou parte dessa valorização, mas terminou o período com patrimônio significativamente inferior.

As diferenças entre as estratégias tornaram-se especialmente expressivas durante a recuperação posterior à queda de março de 2020.

Embora o GJR tenha reduzido o máximo drawdown, não conseguiu acompanhar integralmente os ganhos posteriores do Momentum com pesos iguais.

O CDI apresentou crescimento mais estável, servindo como referência de retorno de baixo risco.

### 6.2. Validação

Em 2021, as duas estratégias Momentum apresentaram trajetórias bastante semelhantes.

Ambas terminaram o período com retorno positivo, superando os índices de ações e o CDI.

O Momentum com pesos iguais, entretanto, encerrou o ano à frente da versão ponderada pelo GJR.

A proximidade entre as curvas também é consistente com a redução relativamente pequena de volatilidade observada nessa amostra.

## 7. Limitações metodológicas

Apesar dos resultados relevantes, algumas limitações precisam ser consideradas.

**Viés de sobrevivência:** o universo de 30 ações pode ter sido selecionado com base em informações disponíveis posteriormente aos períodos históricos analisados. Isso pode produzir resultados excessivamente favoráveis ao backtest.

**Validação curta:** a amostra de validação compreende apenas 2021, o que limita a generalização dos resultados para diferentes regimes de mercado.

**Uma configuração específica:** esta comparação utiliza Momentum 12–1, seleção Top 5 e GJR com 756 pregões de estimação. Outras combinações podem produzir resultados diferentes.

**Ausência de teste formal de significância:** as diferenças de Sharpe e retorno foram avaliadas descritivamente. Ainda não foram realizados testes estatísticos para determinar se são significativamente diferentes de zero.

**Precisão da previsão de volatilidade:** a redução da volatilidade da carteira não demonstra que o GJR apresenta maior capacidade preditiva do que EWMA, GARCH tradicional ou volatilidade histórica simples.

**Custos de implementação:** os custos modelados não incluem todas as fricções do mercado, como spread, impacto de mercado, impostos e possíveis dificuldades de execução.

**Benchmark e CDI:** os índices e o CDI foram representados sem custos de replicação. As métricas de Sharpe incorporam o CDI, mas ainda não foi estimado o alfa CAPM utilizando retornos excedentes à taxa livre de risco.

**Cache do GJR:** a execução utilizou previsões armazenadas previamente. A reprodução integral exige preservar ou reestimar essas previsões com os mesmos dados e parâmetros.

## 8. Organização e reprodução

Estrutura dos principais arquivos:

```text
TraineeFGVquant/
├── baseDeDados/
│   ├── economatica-3.xlsx
│   ├── indices_benchmark_limpo.xlsx
│   └── cdi_sgs12.csv
│
├── cache_vol_mensal.pkl
│
└── notebooks e resultados/
    ├── momentum com garch/
    │   ├── initial_test.py
    │   └── funcoes_momentum.py
    │
    └── benchmarcks/
        └── comparacao_benchmarks/
            ├── comparacao_benchmarks.ipynb
            └── README.md
```

O notebook utiliza as funções já implementadas em `initial_test.py` e `funcoes_momentum.py`.

As principais bibliotecas necessárias são `pandas`, `numpy`, `matplotlib`, `openpyxl`, `requests` e `arch`.

A função `baixar_cdi()` permite utilizar a série diária do CDI armazenada em cache, enquanto `calcular_metricas()` recebe essa série para calcular o Sharpe com taxa livre de risco.

Para reproduzir o estudo, é necessário garantir que as bases de preços, os índices e as previsões de volatilidade estejam disponíveis e que as células sejam executadas na ordem correta.

As tabelas finais com CDI foram calculadas antes da inclusão do CDI como estratégia independente no dicionário de benchmarks. Por esse motivo, as tabelas apresentam sete alternativas, enquanto os gráficos finais incluem oito curvas.

## 9. Conclusão

O experimento investigou se a utilização da volatilidade prevista por GJR-GARCH para ponderar uma carteira de ações selecionadas por Momentum melhora o desempenho ajustado ao risco.

Os resultados mostram que a estratégia Momentum apresentou desempenho superior aos benchmarks acionários tanto no treinamento quanto na validação.

Entretanto, **a incorporação do GJR-GARCH não melhorou o desempenho ajustado ao risco em nenhuma das duas amostras analisadas**.

A ponderação inversa à volatilidade prevista conseguiu reduzir a volatilidade realizada, especialmente no treinamento, mas esse benefício foi acompanhado por perda de retorno, redução do Índice de Sharpe e aumento do turnover.

A redução do máximo drawdown durante o treinamento representa um benefício potencial, mas essa proteção não se manteve em 2021.

Assim, a principal conclusão é que **a seleção de ações por Momentum produziu resultados favoráveis, enquanto a utilização do GJR-GARCH como regra de ponderação não demonstrou contribuição econômica adicional consistente na configuração examinada**.

Isso não significa que o GJR-GARCH seja inadequado para prever volatilidade ou que modelos de volatilidade não possam melhorar estratégias quantitativas. Os resultados indicam apenas que, nesta aplicação específica, a menor volatilidade realizada não se traduziu em maior eficiência ajustada ao risco.

### Próximas etapas

Para aprofundar a pesquisa, recomenda-se comparar a ponderação igualitária com métodos alternativos de estimação de volatilidade, incluindo volatilidade histórica, EWMA, GARCH tradicional e GJR-GARCH, mantendo constantes os sinais de Momentum e as regras de negociação.

Também seria relevante avaliar a precisão das previsões, decompor os custos de transação, analisar a concentração das posições e realizar testes estatísticos das diferenças de desempenho.

Após consolidar essas análises e definir os parâmetros finais, o projeto poderá avançar para o teste fora da amostra de 2022–2026, preservando a independência desse período.

---

**Fonte:** resultados e saídas do notebook `comparacao_benchmarks.ipynb`, com dados da Economatica e CDI diário do Banco Central.

**Observação:** os resultados apresentados correspondem ao treinamento de 2017–2020 e à validação de 2021. Não representam resultados do período reservado de teste final.
