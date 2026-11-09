# Análise de Regras de Ponderação — Momentum e GJR-GARCH

**Projeto:** Trainee FGV Quant  
**Notebook:** `regras_de_ponderacao.ipynb`  
**Estratégia:** Momentum 12–1, Top 5, rebalanceamento mensal  
**Períodos:** Treinamento (2017–2020) e validação (2021)

## 1. Objetivo

Este estudo investiga como diferentes intensidades de penalização por volatilidade afetam o desempenho de uma estratégia quantitativa de Momentum no mercado acionário brasileiro.

Em experimentos anteriores, constatamos que a carteira Momentum Top 5 com pesos iguais apresentou maior retorno e maior Índice de Sharpe do que a carteira ponderada pelo inverso da volatilidade prevista pelo GJR-GARCH.

Entretanto, a ponderação por volatilidade conseguiu reduzir o risco realizado e, no treinamento, o drawdown máximo.

Esses resultados levantaram uma questão importante:

**O desempenho inferior da carteira GJR-GARCH decorre do modelo utilizado para estimar a volatilidade ou da regra de ponderação que penaliza excessivamente os ativos de maior risco?**

Para investigar o papel da regra de ponderação, mantivemos fixas as previsões de volatilidade e alteramos somente a intensidade com que essas previsões determinam os pesos das ações.

O objetivo é avaliar se regras menos agressivas conseguem preservar parte dos benefícios de redução de risco sem sacrificar tanto o retorno associado ao Momentum.

## 2. Dados e estratégia de investimento

### 2.1. Base de dados

O estudo utiliza dados de preços de 30 ações brasileiras obtidos da Economatica.

A base compreende o período de janeiro de 2015 a dezembro de 2021.

O histórico de 2015 e 2016 é utilizado para permitir o cálculo dos indicadores antes do início dos backtests.

Os resultados são separados em:

- **Treinamento:** janeiro de 2017 a dezembro de 2020.
- **Validação:** janeiro a dezembro de 2021.

O período de 2022–2026 permanece reservado para a avaliação final fora da amostra.

Foram identificadas 60 datas mensais de formação de carteira, com previsões GJR disponíveis em uma matriz de 60 datas por 30 ativos.

### 2.2. Estratégia Momentum 12–1

A seleção das ações utiliza o indicador Momentum 12–1:

$$
M_{i,t}=\frac{P_{i,t-21}}{P_{i,t-252}}-1
$$

O indicador mede a variação do preço aproximadamente entre 12 meses e um mês antes da data de formação da carteira.

Ao desconsiderar os 21 pregões mais recentes, a estratégia procura capturar o Momentum intermediário, reduzindo a influência da reversão de curtíssimo prazo.

No último pregão de cada mês, as ações são classificadas de acordo com o indicador e são selecionadas as cinco com maior Momentum.

O rebalanceamento é mensal, com execução no fechamento do pregão seguinte ao sinal. Assim, os retornos passam a ser realizados com os novos pesos a partir do pregão posterior à execução.

**Todas as estratégias analisadas possuem exatamente as mesmas ações selecionadas em cada mês.** A única diferença entre elas é a regra utilizada para determinar os pesos.

## 3. Metodologia de ponderação

### 3.1. Regra original

No experimento anterior, a carteira GJR-GARCH utilizava pesos inversamente proporcionais à volatilidade prevista:

$$
w_{i,t}=
\frac{\hat{\sigma}_{i,t}^{-1}}
{\sum_{j=1}^{5}\hat{\sigma}_{j,t}^{-1}}
$$

Nessa regra, ações com volatilidade prevista elevada recebem menor participação, enquanto ações consideradas menos voláteis recebem maior peso.

Apesar de reduzir a volatilidade realizada, essa metodologia também reduziu o retorno e o Sharpe da estratégia.

### 3.2. Generalização com o parâmetro α

Para estudar a intensidade da penalização, utilizamos a seguinte regra:

$$
\boxed{
w_{i,t}(\alpha)=
\frac{\hat{\sigma}_{i,t}^{-\alpha}}
{\sum_{j=1}^{5}\hat{\sigma}_{j,t}^{-\alpha}}
}
$$

O parâmetro α controla quanto a volatilidade prevista influencia a distribuição de capital.

Foram testados cinco valores:

| α | Regra | Interpretação |
|---|---|---|
| 0 | Pesos iguais | Nenhuma penalização por volatilidade |
| 0,25 | Penalização leve | Mantém pesos próximos de 20% |
| 0,5 | Penalização moderada | Reduz parcialmente a exposição ao risco individual |
| 1 | Inverso da volatilidade | Reproduz o GJR utilizado anteriormente |
| 2 | Inverso da volatilidade ao quadrado | Penalização intensa |

A formulação permite investigar o trade-off entre preservar a exposição às ações com maior Momentum e reduzir a participação nos ativos de maior volatilidade prevista.

### 3.3. Previsões GJR-GARCH

Todas as carteiras utilizam as mesmas previsões de volatilidade produzidas pelo GJR-GARCH, com janela de estimação de 756 pregões e horizonte de previsão de 21 pregões.

As previsões foram recuperadas do arquivo `cache_vol_modelos.pkl`, utilizado anteriormente na comparação entre modelos de volatilidade.

Dessa maneira, evitamos reestimar os modelos e garantimos que alterações nos resultados não sejam decorrentes de diferenças nas previsões.

Quando uma previsão apresenta valor ausente ou inválido, a função de ponderação utiliza a mediana das volatilidades válidas entre as ações selecionadas. Caso todas estejam indisponíveis, são utilizados pesos iguais.

### 3.4. Verificação da implementação

Antes de executar os backtests, verificamos se a função generalizada reproduzia os métodos originais.

Os resultados foram:

- Para α = 0, diferença máxima em relação aos pesos iguais: **0,0**.
- Para α = 1, diferença máxima em relação ao GJR original: **0,0**.
- Soma média dos pesos em todas as estratégias: **1,0**.

Isso confirma que a nova função reproduz os dois casos de referência e que as carteiras permanecem totalmente investidas.

## 4. Metodologia dos backtests

Os cinco backtests foram executados utilizando as mesmas funções de cálculo de retornos, execução das ordens e aplicação dos custos.

Foram mantidas as seguintes condições:

| Parâmetro | Configuração |
|---|---|
| Indicador de seleção | Momentum 12–1 |
| Quantidade de ações | Top 5 |
| Rebalanceamento | Mensal |
| Modelo de volatilidade | GJR-GARCH |
| Janela de estimação | 756 pregões |
| Horizonte de previsão | 21 pregões |
| Custos de transação | 0,1% sobre o turnover |
| Taxa livre de risco | CDI diário, série SGS 12 do Banco Central |
| Pregões por ano | 252 |

As métricas calculadas foram retorno anualizado composto, volatilidade anualizada, Índice de Sharpe, Max Drawdown e turnover anualizado.

O Sharpe utiliza os retornos líquidos excedentes ao CDI. O turnover corresponde à soma das variações absolutas dos pesos nas operações de rebalanceamento.

Os resultados são apresentados separadamente para treinamento e validação, com patrimônio reiniciado em cada período para o cálculo do retorno anualizado e do drawdown.

## 5. Resultados dos backtests

### 5.1. Treinamento — 2017 a 2020

| α | Retorno anual (%) | Volatilidade (%) | Sharpe | Max Drawdown (%) | Turnover anual |
|---|---:|---:|---:|---:|---:|
| **0** | **48,951** | 36,387 | **1,115** | -51,292 | 6,034 |
| 0,25 | 46,088 | 35,597 | 1,077 | -49,842 | 6,234 |
| 0,5 | 43,334 | 34,921 | 1,036 | -48,460 | 6,484 |
| 1 | 38,234 | 33,885 | 0,950 | -45,915 | 7,101 |
| 2 | 30,083 | **32,798** | 0,784 | **-41,675** | 8,322 |

#### Interpretação

Os resultados apresentam uma relação monotônica entre α e desempenho.

Conforme aumentamos a intensidade da penalização por volatilidade, observamos uma redução contínua da volatilidade realizada. Entretanto, o retorno anualizado e o Sharpe também diminuem.

A carteira equiponderada apresentou retorno anualizado de 48,95% e Sharpe de 1,115, os maiores valores entre as cinco estratégias.

Já a carteira com α = 2 apresentou a menor volatilidade, 32,80%, mas também o menor retorno, 30,08%, e o menor Sharpe, 0,784.

Comparando esses dois extremos, o aumento de α reduziu a volatilidade em aproximadamente **3,59 pontos percentuais**, mas sacrificou **18,87 pontos percentuais de retorno anualizado**.

Portanto, a redução do risco ocorreu acompanhada de uma perda proporcionalmente mais expressiva de rentabilidade.

Por outro lado, o drawdown máximo melhorou significativamente. A carteira equiponderada apresentou perda máxima de 51,29%, enquanto α = 2 apresentou perda máxima de 41,68%.

A diferença representa uma redução de aproximadamente **9,62 pontos percentuais na profundidade da maior queda observada**.

Assim, no treinamento, penalizações mais intensas ofereceram maior proteção contra perdas acumuladas, mas não melhoraram a eficiência medida pelo Sharpe.

### 5.2. Validação — 2021

| α | Retorno anual (%) | Volatilidade (%) | Sharpe | Max Drawdown (%) | Turnover anual |
|---|---:|---:|---:|---:|---:|
| **0** | **24,656** | 33,602 | **0,695** | **-23,028** | 5,746 |
| 0,25 | 24,081 | 33,492 | 0,682 | -23,224 | 5,899 |
| 0,5 | 23,479 | 33,396 | 0,669 | -23,410 | 6,082 |
| 1 | 22,197 | 33,244 | 0,639 | -23,756 | 6,567 |
| 2 | 19,424 | **33,082** | 0,571 | -24,343 | 7,784 |

#### Interpretação

Na validação, o comportamento foi semelhante em relação ao retorno e ao Sharpe, mas o benefício de redução de risco foi consideravelmente menor.

A carteira equiponderada apresentou retorno anualizado de 24,66%, enquanto α = 2 apresentou 19,42%.

Entretanto, a volatilidade caiu apenas de 33,60% para 33,08%, uma redução de aproximadamente **0,52 ponto percentual**.

Isso significa que, em 2021, a penalização mais intensa reduziu pouco a volatilidade, mas continuou prejudicando a rentabilidade.

O Sharpe caiu continuamente de 0,695 para 0,571 conforme α aumentou.

Também observamos uma mudança no comportamento do drawdown: diferentemente do treinamento, penalizações mais intensas apresentaram quedas máximas ligeiramente maiores.

O Max Drawdown passou de -23,03% na carteira equiponderada para -24,34% em α = 2.

Portanto, a maior penalização por volatilidade não proporcionou proteção superior contra perdas acumuladas durante 2021.

### 5.3. Comparação entre os períodos

Os resultados permitem destacar três padrões.

**Primeiro:** a redução do retorno e do Sharpe com o aumento de α foi observada nos dois períodos.

**Segundo:** o benefício de redução da volatilidade foi substancialmente maior no treinamento do que na validação.

**Terceiro:** a melhora do drawdown observada no treinamento não se repetiu em 2021.

Consequentemente, os resultados indicam que a utilidade econômica de penalizar a volatilidade pode variar de acordo com as condições do mercado.

Entretanto, os dados não permitem concluir que essa regra seja necessariamente superior em períodos de crise. Essa hipótese exige uma análise específica dos diferentes regimes de volatilidade.

## 6. Trade-off entre risco e retorno

O notebook apresenta dois gráficos relacionando a volatilidade anualizada, no eixo horizontal, ao retorno anualizado, no eixo vertical.

Cada ponto representa uma estratégia com determinado valor de α.

### Treinamento

O gráfico mostra que a redução de volatilidade foi acompanhada por quedas progressivamente maiores no retorno.

A carteira equiponderada aparece na região de maior volatilidade e maior retorno, enquanto α = 2 aparece na região de menor volatilidade e menor retorno.

Não existe dominância estrita entre as estratégias em termos de retorno e volatilidade, pois as carteiras com menor retorno também apresentam menor risco realizado.

Entretanto, a carteira com pesos iguais possui o maior Sharpe, indicando melhor desempenho ajustado ao risco segundo essa métrica.

### Validação

Em 2021, os pontos apresentam diferenças relativamente pequenas na volatilidade, mas diferenças maiores no retorno.

Isso sugere que a redução marginal de risco proporcionada por valores elevados de α teve um custo significativo em termos de rentabilidade.

**Conclusão da análise risco-retorno:** a penalização pela volatilidade funcionou como mecanismo de redução de risco, mas não produziu uma combinação superior de retorno e Sharpe nos períodos estudados.

## 7. Efeito de α sobre os pesos do ranking de Momentum

Para investigar como a regra de ponderação modifica a exposição ao fator Momentum, calculamos o peso médio atribuído a cada uma das cinco posições do ranking.

### Resultados

| α | 1º (%) | 2º (%) | 3º (%) | 4º (%) | 5º (%) |
|---|---:|---:|---:|---:|---:|
| 0 | 20,00 | 20,00 | 20,00 | 20,00 | 20,00 |
| 0,25 | 18,78 | 19,36 | 20,18 | 20,57 | 21,12 |
| 0,5 | 17,61 | 18,68 | 20,35 | 21,11 | 22,25 |
| 1 | 15,52 | 17,25 | 20,66 | 22,07 | 24,51 |
| 2 | 12,31 | 14,49 | 21,10 | 23,47 | 28,64 |

### Interpretação

A relação entre intensidade da penalização e distribuição dos pesos é bastante clara.

Com α = 0, todas as posições recebem 20% do patrimônio.

Conforme α aumenta, as primeiras posições do ranking recebem sistematicamente menos capital, enquanto as últimas posições recebem participações maiores.

Em α = 1, a primeira colocada recebe, em média, apenas 15,52%, enquanto a quinta recebe 24,51%.

Em α = 2, a diferença torna-se ainda maior: a primeira colocada recebe 12,31% e a quinta recebe 28,64%.

Isso significa que, com a penalização mais intensa, a quinta posição do ranking recebe mais que o dobro do peso médio da primeira.

Como os pesos dependem apenas da volatilidade prevista, esse padrão é compatível com uma associação positiva entre a força relativa do Momentum e a volatilidade prevista das ações selecionadas.

### Implicação econômica

A estratégia utiliza Momentum para selecionar os ativos, mas emprega a volatilidade prevista para determinar suas participações.

Esses dois critérios podem produzir efeitos conflitantes.

Quando as ações com maior Momentum também apresentam maior volatilidade prevista, a regra de ponderação reduz sua exposição, mesmo que tenham sido selecionadas por apresentar o sinal mais forte.

Em análises anteriores do projeto, observamos que as primeiras posições do ranking apresentaram retornos futuros relativamente elevados.

Portanto, a redução sistemática da exposição às primeiras posições oferece uma possível explicação para a queda de rentabilidade conforme α aumenta.

Entretanto, essa relação não demonstra causalidade. O retorno da carteira também depende de como os pesos variam ao longo do tempo e de suas relações com os retornos futuros individuais.

## 8. Concentração e diversificação

Aumentar a penalização por volatilidade também pode provocar maior concentração do capital em determinadas ações.

Para investigar esse efeito, utilizamos o Índice Herfindahl-Hirschman (HHI):

$$
HHI_t=\sum_{i=1}^{5}w_{i,t}^{2}
$$

O HHI mede a concentração dos pesos de uma carteira.

Para cinco ativos com pesos iguais, seu valor é 0,20. Valores maiores indicam distribuições de capital mais concentradas.

Também calculamos o número efetivo de ações:

$$
N_{\text{efetivo},t}=\frac{1}{HHI_t}
$$

Essa métrica permite interpretar a concentração em termos de uma quantidade equivalente de ativos equiponderados.

### Resultados

| α | HHI médio | Nº efetivo médio | Maior peso médio (%) | Maior peso observado (%) |
|---|---:|---:|---:|---:|
| 0 | 0,200 | 5,000 | 20,000 | 20,000 |
| 0,25 | 0,201 | 4,969 | 21,973 | 23,588 |
| 0,5 | 0,205 | 4,880 | 24,017 | 27,469 |
| 1 | 0,219 | 4,578 | 28,230 | 35,846 |
| 2 | 0,267 | 3,843 | 36,604 | 52,876 |

### Interpretação

Os resultados mostram que o aumento de α eleva a concentração da carteira.

Com α = 0, a carteira possui cinco ações efetivas, exatamente como esperado para pesos iguais.

Em α = 0,5, a concentração permanece relativamente próxima da carteira equiponderada, com aproximadamente 4,88 ações efetivas.

Já em α = 2, o número efetivo médio cai para aproximadamente 3,84 ações.

Isso significa que, embora a estratégia continue selecionando cinco ativos, a distribuição do patrimônio passa a se comportar, em termos de concentração dos pesos, como uma carteira com menos de quatro ações igualmente ponderadas.

Outro resultado relevante é o maior peso individual observado.

Com α = 2, uma única ação chegou a representar **52,88% do patrimônio no momento de um rebalanceamento**.

Essa concentração é elevada para uma estratégia que busca distribuir capital entre cinco ações.

### Implicação econômica

A penalização por volatilidade procura reduzir a exposição às ações individualmente mais voláteis, mas pode aumentar a concentração nas ações consideradas menos arriscadas.

Assim, dois efeitos ocorrem simultaneamente:

1. Redução da exposição aos ativos com maior volatilidade prevista.
2. Aumento da concentração do patrimônio nos ativos com menor volatilidade prevista.

O efeito final sobre o risco da carteira depende não apenas das volatilidades individuais, mas também das correlações entre as ações.

Dessa forma, menor volatilidade prevista dos ativos selecionados não significa necessariamente melhor diversificação.

No nosso experimento, a volatilidade realizada diminuiu, mas a concentração aumentou e o Sharpe piorou.

É importante observar que o HHI e o número efetivo foram calculados a partir dos pesos-alvo mensais, e não dos pesos diários após as oscilações de preços.

## 9. Evolução dos drawdowns

O notebook também apresenta gráficos da evolução dos drawdowns das cinco estratégias durante treinamento e validação.

O drawdown representa a queda percentual do patrimônio em relação ao maior valor anteriormente alcançado.

### 9.1. Treinamento — 2017 a 2020

As curvas apresentam comportamento semelhante durante grande parte do período.

A principal divergência aparece durante a queda acentuada de 2020, quando as carteiras com penalização mais intensa apresentaram drawdowns menores.

Nesse período, a estratégia com α = 2 sofreu uma perda máxima significativamente menor do que a carteira equiponderada.

Esse resultado sugere que a ponderação pela volatilidade pode ter funcionado como mecanismo de proteção durante a crise de 2020.

Entretanto, não foi realizada no notebook uma decomposição anual da contribuição de cada período para o drawdown total.

Portanto, a interpretação permanece baseada na inspeção visual das curvas e nas métricas agregadas do treinamento.

### 9.2. Validação — 2021

Em 2021, as curvas de drawdown ficaram relativamente próximas.

As estratégias com maior penalização não apresentaram proteção sistematicamente superior.

Pelo contrário, os valores máximos de drawdown pioraram conforme α aumentou.

Isso indica que a proteção observada durante o treinamento não foi reproduzida no período de validação.

### 9.3. Hipótese de dependência do regime de mercado

A diferença entre os períodos sugere uma hipótese para pesquisas posteriores: a utilidade da penalização pela volatilidade pode depender do regime de risco do mercado.

Em episódios de estresse elevado, reduzir a exposição às ações mais voláteis poderia diminuir perdas.

Em períodos menos turbulentos, essa mesma regra poderia prejudicar a captura dos retornos associados ao Momentum.

Entretanto, os resultados atuais não permitem confirmar essa hipótese, pois ainda não foi realizado um teste formal que classifique previamente os regimes de mercado.

## 10. Turnover e custos de negociação

O aumento de α também produziu crescimento consistente do turnover anualizado.

No treinamento, o turnover passou de 6,034 em α = 0 para 8,322 em α = 2.

Na validação, passou de 5,746 para 7,784.

Isso indica que penalizações mais intensas exigiram ajustes maiores na distribuição do patrimônio.

Como os custos de transação foram aplicados sobre o turnover, regras com α elevado também estiveram sujeitas a maiores despesas de negociação.

Embora os retornos apresentados já incluam custos de 0,1%, o notebook não isolou quantitativamente quanto da diferença de desempenho entre os valores de α decorre exclusivamente dessas despesas.

Portanto, não é possível atribuir toda a perda de rentabilidade à redistribuição dos pesos sem considerar também o efeito dos custos.

Uma análise posterior poderá comparar retornos brutos e líquidos para cada valor de α, isolando a contribuição dos custos adicionais.

## 11. Síntese dos resultados

O experimento produziu cinco resultados principais.

### 11.1. Penalizar mais a volatilidade reduziu o risco realizado

A volatilidade anualizada diminuiu continuamente com o aumento de α, tanto no treinamento quanto na validação.

Isso mostra que a regra conseguiu reduzir parte do risco realizado da carteira.

Entretanto, a magnitude dessa redução foi muito menor em 2021.

### 11.2. Nenhuma penalização positiva melhorou o Sharpe

O maior Sharpe foi obtido pela carteira de pesos iguais, α = 0, nos dois períodos.

O Sharpe caiu monotonicamente conforme α aumentou.

Portanto, a hipótese de que uma penalização intermediária melhoraria a eficiência medida pelo Sharpe não foi confirmada pelos resultados.

### 11.3. A penalização reduziu a exposição às ações com maior Momentum

Quanto maior α, menor foi o peso médio das primeiras posições do ranking.

A estratégia com α = 2 atribuiu, em média, apenas 12,31% à ação com maior Momentum, contra 28,64% à quinta colocada.

Esse comportamento pode contribuir para explicar parte da perda de rentabilidade.

### 11.4. A concentração aumentou

O número efetivo médio de ações caiu de 5 para aproximadamente 3,84 entre α = 0 e α = 2.

Além disso, o maior peso individual observado chegou a 52,88% do patrimônio.

Portanto, a penalização mais intensa reduziu a diversificação dos pesos, embora tenha diminuído a volatilidade realizada.

### 11.5. A proteção contra drawdowns não foi consistente entre os períodos

Durante o treinamento, especialmente na queda de 2020, estratégias com maior α apresentaram drawdowns menores.

Em 2021, esse benefício não se repetiu.

Assim, a proteção contra perdas acumuladas parece depender das condições observadas no período, hipótese que ainda exige investigação específica.

## 12. Limitações metodológicas

### 12.1. O experimento não testa a qualidade das previsões GJR

Todas as estratégias utilizam as mesmas previsões de volatilidade.

Portanto, conseguimos avaliar como diferentes regras de ponderação afetam o desempenho econômico, mas não se o GJR prevê melhor ou pior a volatilidade do que outros modelos.

Essa distinção é importante para interpretar os resultados.

### 12.2. Horizonte de validação limitado

A validação utiliza apenas um ano, 2021.

Esse período pode não representar adequadamente diferentes regimes de volatilidade, crises e fases de recuperação.

Consequentemente, os resultados não devem ser generalizados automaticamente para outros períodos.

### 12.3. Possibilidade de sobreajuste

Os valores de α foram avaliados utilizando dados históricos e uma validação que já havia sido consultada em experimentos anteriores.

Portanto, qualquer seleção posterior de parâmetros com base nesses resultados pode introduzir viés de seleção.

A avaliação de 2021 deve ser interpretada como análise exploratória, e não como teste final completamente independente.

O período de 2022–2026 deve permanecer reservado até que a metodologia esteja definida.

### 12.4. Universo limitado de ações

A estratégia utiliza um universo de 30 ações brasileiras.

A composição desse universo pode gerar viés de sobrevivência se tiver sido estabelecida com informações posteriores ao início do backtest.

Além disso, os resultados podem depender das características específicas dos ativos selecionados.

### 12.5. Diversificação avaliada apenas pelos pesos

O HHI e o número efetivo de ações medem concentração de capital.

Essas medidas não incorporam as correlações entre os retornos dos ativos.

Consequentemente, não representam uma medida completa da diversificação de risco.

Uma análise posterior poderá incluir volatilidade de carteira prevista, correlações e contribuições marginais ao risco.

### 12.6. Ausência de testes estatísticos

Não foram realizados testes de significância para as diferenças entre os retornos ou Índices de Sharpe das estratégias.

Portanto, as conclusões são descritivas e se referem aos resultados observados na amostra.

### 12.7. Previsões ausentes e cache

As previsões foram recuperadas de um cache gerado anteriormente.

A assinatura utilizada verifica a compatibilidade das datas, ativos e alguns parâmetros, mas não constitui uma verificação integral da identidade dos dados originais.

Além disso, previsões indisponíveis são substituídas conforme a regra de tratamento de valores ausentes.

A reprodução completa do experimento exige preservar a base, o cache e as funções utilizadas.

## 13. Próximas análises

Os resultados sugerem algumas extensões relevantes para o projeto.

**Análise de custos:** comparar retornos brutos e líquidos dos diferentes valores de α, quantificando o impacto do maior turnover.

**Ponderação dinâmica:** investigar regras em que α varie conforme indicadores de risco conhecidos no momento da decisão. Essa possibilidade exige especificar os regimes antecipadamente e evitar otimização excessiva.

**Regras combinadas:** avaliar ponderações que considerem simultaneamente a intensidade do Momentum e a volatilidade prevista, em vez de utilizar exclusivamente o inverso da volatilidade.

**Restrições de concentração:** testar limites máximos para os pesos individuais, evitando alocações excessivamente elevadas em uma única ação.

**Qualidade preditiva:** comparar GJR-GARCH, GARCH, EWMA e volatilidade histórica utilizando métricas como MSE e QLIKE. Isso permitiria distinguir precisão estatística e desempenho econômico.

**Testes estatísticos:** avaliar a robustez das diferenças de Sharpe e retorno por meio de procedimentos adequados para séries temporais.

Após a definição das especificações, o teste final deverá ser realizado no período reservado de 2022–2026.

## 14. Conclusão

O objetivo deste estudo foi investigar se a intensidade da penalização pela volatilidade poderia explicar o desempenho inferior da carteira Momentum ponderada pelo GJR-GARCH.

Para isso, mantivemos constantes o modelo de previsão, o universo de ativos, o indicador de Momentum e as condições dos backtests, alterando apenas o parâmetro α da regra de ponderação.

Os resultados mostram que **aumentar α reduziu consistentemente a volatilidade realizada, mas também diminuiu o retorno e o Índice de Sharpe**.

Nenhum dos valores positivos testados superou a carteira equiponderada em Sharpe, tanto no treinamento quanto na validação.

Além disso, penalizações maiores reduziram sistematicamente a exposição às ações com maior Momentum, aumentaram a concentração do capital e elevaram o turnover.

Embora as estratégias com maior α tenham apresentado proteção superior contra drawdowns durante o treinamento, esse benefício não foi observado em 2021.

Dessa forma, os resultados sugerem que **a ponderação inversa à volatilidade possui um custo econômico relevante quando aplicada de maneira permanente a essa estratégia de Momentum**.

A regra consegue controlar parte do risco, mas pode penalizar excessivamente os ativos selecionados pelo sinal de Momentum, reduzindo a rentabilidade e a eficiência medida pelo Sharpe.

Entretanto, esses resultados não demonstram que o GJR-GARCH seja um modelo inadequado para prever volatilidade. Eles mostram apenas que utilizar suas previsões para determinar pesos por meio dessa família de regras não produziu uma melhora do Sharpe no universo e nos períodos estudados.

**A principal conclusão é que a qualidade de um modelo de previsão de risco e a eficiência de uma regra de alocação são questões distintas.** Uma boa estimativa de volatilidade não garante, por si só, uma estratégia de investimento superior.

---

**Fonte dos resultados:** notebook `regras_de_ponderacao.ipynb`, base Economatica, funções `initial_test.py` e `funcoes_momentum.py`, e previsões armazenadas em `cache_vol_modelos.pkl`.

**Escopo:** treinamento de 2017–2020 e validação exploratória de 2021. O teste final fora da amostra ainda não foi realizado.
