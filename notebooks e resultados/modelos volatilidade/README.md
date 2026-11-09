# Comparação de Modelos de Volatilidade — Momentum 12–1

**Projeto:** Trainee FGV Quant  
**Notebook:** `comparacao_modelos_volatilidade.ipynb`  
**Estratégia-base:** Momentum 12–1, Top 5, rebalanceamento mensal  
**Períodos:** Treinamento (2017–2020) e validação (2021)

## 1. Objetivo

Este estudo investiga se modelos de estimação e previsão de volatilidade conseguem melhorar o desempenho ajustado ao risco de uma estratégia de Momentum aplicada ao mercado acionário brasileiro.

O objetivo principal é avaliar se a utilização de modelos econométricos mais complexos, como GARCH e GJR-GARCH, apresenta vantagens em relação a métodos mais simples, como volatilidade histórica e EWMA.

Para isso, comparamos cinco metodologias de ponderação:

1. **Pesos iguais:** alocação de 20% em cada uma das cinco ações selecionadas.
2. **Volatilidade histórica:** pesos inversamente proporcionais ao desvio-padrão dos retornos dos últimos 252 pregões.
3. **EWMA (0,94):** pesos inversamente proporcionais à volatilidade estimada por uma média móvel exponencial.
4. **GARCH(1,1):** pesos inversamente proporcionais à volatilidade prevista por um modelo GARCH.
5. **GJR-GARCH(1,1,1):** pesos inversamente proporcionais à volatilidade prevista por um modelo GARCH com assimetria.

Todas as estratégias utilizam os mesmos sinais de Momentum e selecionam as mesmas ações nas mesmas datas. A diferença está exclusivamente na regra de ponderação.

Dessa maneira, buscamos identificar o valor econômico incremental de utilizar previsões de volatilidade na construção de uma carteira de Momentum.

## 2. Base de dados e divisão temporal

Os dados foram obtidos da Economatica, utilizando preços ajustados de um universo de 30 ações brasileiras.

O histórico começa em janeiro de 2015, permitindo calcular os indicadores de Momentum e estimar os modelos de volatilidade antes do início do backtest.

| Período | Finalidade |
|---|---|
| 2015–2016 | Histórico inicial para os indicadores e modelos |
| 2017–2020 | Treinamento (*in-sample*) |
| 2021 | Validação |
| 2022–2026 | Teste final reservado (*out-of-sample*) |

A base utilizada no notebook contém 30 ativos e gera 60 datas mensais de formação de carteira entre janeiro de 2017 e dezembro de 2021.

O período de 2022–2026 não foi utilizado nesta comparação e permanece reservado para uma avaliação posterior, após a definição final dos parâmetros da estratégia.

## 3. Metodologia

### 3.1. Seleção das ações por Momentum

A estratégia utiliza o indicador Momentum 12–1, calculado como:

`Momentum(i,t) = P(i,t-21) / P(i,t-252) - 1`

A fórmula representa a valorização acumulada aproximadamente nos últimos 12 meses, excluindo os 21 pregões mais recentes.

No último pregão de cada mês, as ações são ordenadas pelo indicador e selecionamos as cinco maiores.

A seleção é mantida constante entre as cinco estratégias, permitindo comparar diretamente os efeitos dos diferentes métodos de ponderação.

### 3.2. Regra de ponderação

Na estratégia de referência, os cinco ativos recebem pesos iguais de 20%.

Nas outras quatro estratégias, os pesos são inversamente proporcionais à volatilidade estimada ou prevista:

`w(i,t) = [1 / sigma(i,t)] / soma[1 / sigma(j,t)]`

Essa regra atribui maior participação às ações consideradas menos voláteis e menor participação àquelas consideradas mais voláteis.

A soma dos pesos é igual a 1, sem alavancagem e sem posições vendidas.

O objetivo é reduzir a exposição a ações de maior volatilidade, mantendo a seleção produzida pelo Momentum.

### 3.3. Volatilidade histórica

A volatilidade histórica é calculada pelo desvio-padrão dos retornos logarítmicos em uma janela móvel de 252 pregões.

Esse método atribui o mesmo peso às observações dentro da janela.

Sua principal vantagem é a simplicidade: não exige estimação de parâmetros por máxima verossimilhança nem pressupõe uma dinâmica paramétrica específica para a volatilidade.

Por outro lado, pode reagir mais lentamente às mudanças recentes do mercado.

### 3.4. EWMA

O modelo EWMA utiliza a seguinte dinâmica:

`sigma²(t) = lambda * sigma²(t-1) + (1-lambda) * r²(t)`

Neste trabalho, utilizamos `lambda = 0,94`.

Com isso, a volatilidade estimada incorpora informações anteriores, atribuindo peso exponencialmente decrescente às observações mais antigas.

O método permite responder mais rapidamente a choques recentes do que uma janela de volatilidade histórica com pesos uniformes.

### 3.5. GARCH(1,1)

O GARCH modela a variância condicional como função dos choques anteriores e da própria variância passada:

`sigma²(t) = omega + alpha * epsilon²(t-1) + beta * sigma²(t-1)`

O parâmetro `alpha` representa a resposta da volatilidade a novas informações, enquanto `beta` representa sua persistência.

Na implementação utilizada:

- A janela máxima de estimação é de 756 pregões.
- São exigidas pelo menos 252 observações válidas por ativo.
- A distribuição dos erros é t de Student.
- A média condicional dos retornos é especificada como zero.
- A previsão considera um horizonte de 21 pregões.
- A volatilidade utilizada nos pesos é obtida a partir da média das variâncias previstas nesse horizonte.

### 3.6. GJR-GARCH(1,1,1)

O GJR-GARCH acrescenta um componente de assimetria ao GARCH tradicional:

`sigma²(t) = omega + alpha * epsilon²(t-1) + gamma * I(t-1) * epsilon²(t-1) + beta * sigma²(t-1)`

A variável `I(t-1)` assume valor 1 quando o choque anterior é negativo e 0 caso contrário.

Com isso, o modelo permite que choques negativos e positivos de mesma magnitude produzam efeitos distintos sobre a volatilidade futura.

Se o parâmetro `gamma` for positivo, choques negativos produzem maior aumento de volatilidade.

Essa característica pode ser relevante no mercado acionário, em que quedas de preços frequentemente estão associadas a aumentos expressivos de volatilidade.

O GJR utiliza a mesma janela máxima de 756 pregões e o mesmo horizonte de previsão de 21 pregões do GARCH tradicional.

### 3.7. Backtest e custos

Os backtests utilizam rebalanceamento mensal. Os sinais são calculados no último pregão do mês e as ordens correspondentes são executadas no pregão seguinte.

Entre rebalanceamentos, os pesos evoluem de acordo com os retornos das ações.

As simulações consideram custos de transação de **0,10% sobre o turnover**, aplicados aos retornos das carteiras.

O CDI diário, obtido da série SGS 12 do Banco Central, é utilizado como taxa livre de risco para o cálculo do Índice de Sharpe.

O Sharpe é calculado como a média do retorno excedente diário ao CDI dividida pelo desvio-padrão desse retorno excedente, multiplicada pela raiz quadrada de 252.

## 4. Resultados — Treinamento (2017–2020)

| Estratégia | Retorno anual (%) | Volatilidade (%) | Sharpe com CDI | Max Drawdown (%) | Turnover anual |
|---|---:|---:|---:|---:|---:|
| **Pesos iguais** | **48,951** | 36,387 | **1,115** | -51,292 | 6,034 |
| Volatilidade histórica | 41,732 | 34,529 | 1,012 | -48,598 | 6,510 |
| EWMA (0,94) | 42,225 | 34,547 | 1,021 | -47,882 | 7,088 |
| GARCH (756) | 37,612 | 34,111 | 0,933 | -46,836 | 7,035 |
| GJR-GARCH (756) | 38,234 | **33,885** | 0,950 | **-45,915** | 7,101 |

### 4.1. Comparação de rentabilidade

A estratégia com pesos iguais apresentou o maior retorno anualizado, de 48,95%, seguida por EWMA (42,23%), volatilidade histórica (41,73%), GJR (38,23%) e GARCH (37,61%).

Portanto, todos os métodos de ponderação por volatilidade apresentaram retornos inferiores aos da carteira equiponderada.

A diferença foi particularmente expressiva nos modelos GARCH e GJR.

Comparado aos pesos iguais, o GARCH reduziu o retorno anualizado em 11,34 pontos percentuais, enquanto o GJR reduziu em 10,72 pontos percentuais.

Esses resultados sugerem que reduzir a exposição às ações mais voláteis pode ter significado também reduzir a participação em ativos que contribuíram fortemente para a rentabilidade da estratégia.

Entretanto, essa é uma hipótese que ainda precisa ser investigada mediante a análise das posições individuais.

### 4.2. Comparação de volatilidade

Todos os modelos de volatilidade reduziram o risco realizado da carteira.

A volatilidade anualizada passou de 36,39% nos pesos iguais para valores entre 33,89% e 34,55%.

O GJR apresentou a menor volatilidade, seguido pelo GARCH.

Isso sugere que os modelos econométricos foram mais efetivos em reduzir a volatilidade durante o treinamento do que as duas metodologias mais simples.

Porém, **reduzir a volatilidade não significa necessariamente melhorar a eficiência econômica da estratégia**.

### 4.3. Índice de Sharpe

A estratégia com pesos iguais apresentou Sharpe de 1,115, superior ao de todas as alternativas.

Entre os modelos de volatilidade, o EWMA apresentou o maior Sharpe (1,021), seguido pela volatilidade histórica (1,012), GJR (0,950) e GARCH (0,933).

Esse resultado é importante porque mostra que os métodos mais sofisticados não foram os melhores em termos de rentabilidade ajustada ao risco durante o treinamento.

Embora GARCH e GJR tenham produzido menores volatilidades, a perda de retorno foi proporcionalmente maior que o benefício da redução de risco.

Assim, a complexidade adicional desses modelos não se traduziu em maior Sharpe no treinamento.

### 4.4. Drawdown

A estratégia com pesos iguais apresentou o maior drawdown, com perda máxima de 51,29%.

Todos os métodos de ponderação por volatilidade reduziram essa perda.

O GJR apresentou o melhor resultado, com drawdown de -45,92%, seguido pelo GARCH, com -46,84%.

Em comparação aos pesos iguais, o GJR melhorou o máximo drawdown em aproximadamente 5,38 pontos percentuais.

Portanto, durante o treinamento, o principal benefício do GJR não foi aumentar a rentabilidade, mas reduzir a volatilidade e a magnitude da maior queda acumulada.

## 5. Resultados — Validação (2021)

| Estratégia | Retorno anual (%) | Volatilidade (%) | Sharpe com CDI | Max Drawdown (%) | Turnover anual |
|---|---:|---:|---:|---:|---:|
| **Pesos iguais** | **24,656** | 33,602 | **0,695** | **-23,028** | **5,746** |
| Volatilidade histórica | 21,103 | **32,876** | 0,615 | -23,867 | 6,774 |
| EWMA (0,94) | 20,014 | 32,878 | 0,587 | -23,767 | 6,964 |
| GARCH (756) | 22,170 | 33,150 | 0,639 | -23,706 | 6,715 |
| GJR-GARCH (756) | 22,197 | 33,244 | 0,639 | -23,756 | 6,567 |

### 5.1. Rentabilidade

Na validação, os pesos iguais permaneceram superiores, com retorno anualizado de 24,66%.

Entretanto, a ordem de desempenho entre os modelos de volatilidade mudou.

GARCH e GJR apresentaram retornos de aproximadamente 22,2%, superando a volatilidade histórica e o EWMA.

Isso contrasta com o treinamento, quando os modelos mais simples apresentaram maior rentabilidade.

O resultado indica que o desempenho relativo dos métodos depende do período analisado e pode variar conforme o regime de mercado.

### 5.2. Volatilidade

Todos os modelos continuaram reduzindo a volatilidade em relação à carteira equiponderada.

Contudo, as menores volatilidades passaram a ser observadas nos modelos mais simples.

A volatilidade histórica apresentou 32,876%, enquanto o EWMA registrou 32,878%.

O GARCH apresentou 33,150% e o GJR, 33,244%.

Portanto, a vantagem observada anteriormente pelo GJR na redução da volatilidade não se manteve na validação.

### 5.3. Índice de Sharpe

Os pesos iguais continuaram apresentando o maior Sharpe, de 0,695.

Entre os modelos de volatilidade, GARCH e GJR registraram 0,639, superando a volatilidade histórica (0,615) e o EWMA (0,587).

Isso sugere que GARCH e GJR ofereceram melhor relação entre retorno excedente ao CDI e volatilidade do que os modelos mais simples em 2021.

Entretanto, nenhum deles superou os pesos iguais.

O resultado reforça a importância de distinguir duas comparações: a superioridade de um modelo GARCH em relação a outros modelos de volatilidade e a superioridade da ponderação por volatilidade em relação à carteira original.

Um modelo pode vencer a primeira comparação sem vencer a segunda.

### 5.4. Drawdown

Diferentemente do treinamento, nenhum dos modelos de volatilidade conseguiu reduzir o máximo drawdown em relação aos pesos iguais.

A carteira equiponderada apresentou drawdown de -23,03%, enquanto as outras estratégias registraram perdas máximas entre -23,71% e -23,87%.

Isso significa que a redução da volatilidade total não foi acompanhada por proteção superior contra a maior perda acumulada no período.

Portanto, os benefícios de proteção observados no treinamento não foram robustos à mudança de amostra.

## 6. Contribuição incremental dos modelos

Para avaliar diretamente a utilidade de cada método de ponderação, calculamos a diferença entre seus resultados e os da carteira com pesos iguais.

### 6.1. Treinamento: diferenças em relação aos pesos iguais

| Modelo | Δ Retorno (p.p.) | Δ Volatilidade (p.p.) | Δ Sharpe | Δ Drawdown (p.p.) | Δ Turnover |
|---|---:|---:|---:|---:|---:|
| Volatilidade histórica | -7,218 | -1,858 | -0,104 | +2,694 | +0,476 |
| EWMA | -6,725 | -1,840 | -0,094 | +3,410 | +1,054 |
| GARCH | -11,339 | -2,276 | -0,182 | +4,457 | +1,001 |
| GJR-GARCH | -10,717 | -2,502 | -0,165 | +5,377 | +1,067 |

Todos os modelos apresentam a mesma combinação geral: menor volatilidade, menor retorno, menor Sharpe e maior turnover.

Durante o treinamento, também apresentaram menor drawdown.

O GJR foi o mais efetivo em reduzir a volatilidade e o drawdown, mas não apresentou o melhor equilíbrio entre risco e retorno.

### 6.2. Validação: diferenças em relação aos pesos iguais

| Modelo | Δ Retorno (p.p.) | Δ Volatilidade (p.p.) | Δ Sharpe | Δ Drawdown (p.p.) | Δ Turnover |
|---|---:|---:|---:|---:|---:|
| Volatilidade histórica | -3,553 | -0,726 | -0,080 | -0,839 | +1,029 |
| EWMA | -4,642 | -0,724 | -0,107 | -0,738 | +1,218 |
| GARCH | -2,486 | -0,452 | -0,056 | -0,678 | +0,969 |
| GJR-GARCH | -2,459 | -0,358 | -0,056 | -0,728 | +0,821 |

Na validação, todas as metodologias continuaram reduzindo a volatilidade, mas também reduziram o retorno e o Sharpe.

Além disso, todos os modelos apresentaram drawdowns ligeiramente piores do que os pesos iguais.

Esse resultado indica que uma carteira menos volátil não necessariamente sofre uma menor perda acumulada máxima.

## 7. GARCH versus GJR-GARCH

Uma das questões centrais do estudo é verificar se a capacidade do GJR de representar choques assimétricos oferece benefícios econômicos em relação ao GARCH tradicional.

No treinamento, o GJR apresentou retorno e Sharpe ligeiramente superiores aos do GARCH, além de menor volatilidade e menor drawdown.

O retorno anualizado aumentou de 37,61% para 38,23%, enquanto o Sharpe passou de 0,933 para 0,950.

A volatilidade diminuiu de 34,11% para 33,89%, e o drawdown melhorou de -46,84% para -45,92%.

Esses resultados favorecem moderadamente o GJR no treinamento.

Entretanto, na validação, os desempenhos foram praticamente idênticos.

O GARCH apresentou retorno anualizado de 22,170% e o GJR de 22,197%. Ambos tiveram Sharpe arredondado de 0,639.

O GARCH apresentou volatilidade e drawdown ligeiramente menores, enquanto o GJR apresentou menor turnover.

**Portanto, não identificamos uma vantagem econômica expressiva e consistente do GJR sobre o GARCH tradicional nas duas amostras.**

Isso não significa que a assimetria seja irrelevante para a previsão de volatilidade. Significa apenas que os resultados disponíveis não demonstram que incorporar essa característica tenha melhorado substancialmente a performance da carteira.

## 8. Turnover e custos de transação

Os cinco backtests consideram custos de transação de 0,10% sobre o turnover.

O turnover representa o volume de negociações necessário para ajustar a carteira aos novos pesos.

Em ambos os períodos, a estratégia equiponderada apresentou o menor turnover.

Isso ocorre porque as estratégias baseadas em volatilidade precisam ajustar as posições não apenas quando muda a seleção das ações, mas também quando mudam as estimativas de risco.

No treinamento, o turnover anual passou de 6,034 nos pesos iguais para valores entre 6,510 e 7,101 nos modelos de volatilidade.

Na validação, passou de 5,746 para valores entre 6,567 e 6,964.

Esse aumento representa uma desvantagem potencial das metodologias de ponderação por risco, especialmente em mercados com custos elevados ou restrições de liquidez.

Embora os resultados já considerem os custos modelados, seria interessante executar uma comparação com custos de 0%, 0,1% e 0,3% para investigar a sensibilidade das conclusões.

## 9. Interpretação econômica

Os resultados sugerem que a ponderação por volatilidade produz uma troca entre risco e retorno.

Ao atribuir pesos menores às ações mais voláteis, as estratégias conseguem reduzir a volatilidade total da carteira. Entretanto, isso também pode reduzir a exposição a empresas com maior potencial de valorização.

Como a carteira é formada pelas cinco ações de maior Momentum, é possível que algumas dessas ações apresentem simultaneamente retornos passados elevados e maior volatilidade.

Se isso acontecer, os modelos de ponderação por risco podem diminuir a exposição justamente às posições responsáveis por parte relevante dos ganhos.

Essa hipótese é compatível com os resultados encontrados, mas não foi testada diretamente.

Para investigá-la, seria necessário analisar a relação entre volatilidade estimada, pesos atribuídos e retorno posterior de cada ação.

Também seria interessante verificar se os modelos deslocam sistematicamente a alocação para empresas maiores, setores defensivos ou ações com menor sensibilidade ao mercado.

**Outro ponto importante é que a qualidade da previsão de volatilidade e a qualidade da estratégia de alocação são conceitos diferentes.**

Um modelo pode prever corretamente períodos de maior volatilidade e, ainda assim, não melhorar o Sharpe da carteira, principalmente se a regra de alocação sacrificar retornos esperados elevados.

Por isso, os resultados deste notebook avaliam principalmente a utilidade econômica dos modelos como regras de ponderação, e não sua precisão estatística como previsores de volatilidade.

## 10. Limitações e pontos de atenção no código

### 10.1. Diferenças no horizonte de volatilidade

Os modelos GARCH e GJR utilizam previsões para um horizonte de 21 pregões.

Já a volatilidade histórica e o EWMA utilizam estimativas calculadas na data do sinal.

Isso significa que a comparação não mantém exatamente o mesmo horizonte preditivo entre os modelos.

Uma avaliação posterior poderá padronizar esse aspecto para isolar de maneira mais rigorosa as diferenças entre as técnicas.

### 10.2. Filtro de observações do EWMA

No notebook, a variável `n_obs` é calculada para contar as observações disponíveis de cada ação, mas não é aplicada à série `sigma_ewma`.

Assim, o filtro mínimo de 252 observações não está explicitamente imposto ao EWMA na versão analisada.

Isso deve ser corrigido e os resultados reavaliados antes de uma conclusão metodológica definitiva.

### 10.3. Falhas de convergência

As saídas do notebook registraram zero fallbacks para EWMA tanto no GARCH quanto no GJR.

Isso indica que, entre as estimações elegíveis realizadas, não houve necessidade registrada de substituir previsões por EWMA devido a falhas na estimação.

Esse resultado é favorável à estabilidade computacional dos modelos na amostra utilizada, embora não elimine a necessidade de verificar estimativas ausentes e ativos sem histórico suficiente.

### 10.4. Viés de sobrevivência

A base utiliza um universo fixo de 30 ações, cuja composição pode refletir informações disponíveis posteriormente ao início do período histórico.

Isso pode gerar viés de sobrevivência e afetar os resultados das estratégias.

Uma análise mais rigorosa exigiria utilizar o universo efetivamente negociável em cada período, incluindo empresas que posteriormente deixaram de ser negociadas.

### 10.5. Tamanho da validação

A validação contempla apenas o ano de 2021.

Embora represente um período distinto do treinamento, é insuficiente para estabelecer que as diferenças entre os modelos persistirão em diferentes regimes de mercado.

### 10.6. Significância estatística

As comparações foram feitas por meio de métricas descritivas.

Ainda não foram realizados testes formais para verificar a significância estatística das diferenças entre retornos, volatilidades ou índices de Sharpe.

Portanto, pequenas diferenças, como as observadas entre GARCH e GJR em 2021, não devem ser interpretadas como evidência conclusiva de superioridade de um modelo.

### 10.7. Reprodutibilidade

As previsões de GARCH e GJR são armazenadas em `cache_vol_modelos.pkl` para evitar reestimações desnecessárias.

A reprodução integral exige as mesmas bases, parâmetros, versões de bibliotecas e regras de estimação.

Também é importante validar o cache quando os dados ou o código forem alterados.

## 11. Organização dos arquivos

Estrutura principal:

```text
TraineeFGVquant/
├── baseDeDados/
│   ├── economatica-3.xlsx
│   └── cdi_sgs12.csv
│
└── notebooks e resultados/
    ├── momentum com garch/
    │   ├── initial_test.py
    │   └── funcoes_momentum.py
    │
    └── modelos volatilidade/
        ├── comparacao_modelos_volatilidade.ipynb
        ├── cache_vol_modelos.pkl
        └── README.md
```

O notebook reaproveita as funções de preparação dos dados, seleção de ativos, estimação da volatilidade e execução dos backtests do projeto.

As principais dependências são `pandas`, `numpy`, `openpyxl`, `requests` e `arch`.

Os resultados documentados correspondem às saídas salvas em `comparacao_modelos_volatilidade.ipynb`. Em uma verificação independente, foram reproduzidas as métricas de retorno, volatilidade, drawdown e turnover das estratégias com pesos iguais, volatilidade histórica e EWMA. As estimações GARCH/GJR e os índices de Sharpe com CDI foram conferidos a partir das saídas do notebook, não reexecutados integralmente nessa verificação.

## 12. Conclusão

O estudo comparou cinco metodologias de ponderação aplicadas à mesma estratégia de Momentum 12–1 Top 5 no mercado acionário brasileiro.

Os resultados mostram que **todos os métodos de ponderação por volatilidade reduziram a volatilidade realizada da carteira**, tanto no treinamento quanto na validação.

Entretanto, essa redução de risco foi acompanhada por menores retornos anualizados, menores índices de Sharpe e maior turnover.

A carteira com pesos iguais apresentou o maior Sharpe nos dois períodos, sugerindo que, na configuração examinada, a ponderação por volatilidade não ofereceu benefícios suficientes para superar a estratégia original.

Durante o treinamento, os métodos mais simples, EWMA e volatilidade histórica, apresentaram Sharpe superior aos modelos GARCH e GJR.

Na validação, essa relação se inverteu: GARCH e GJR superaram os dois métodos mais simples em Sharpe, embora continuassem inferiores aos pesos iguais.

O GJR apresentou a menor volatilidade e o menor drawdown durante o treinamento, mas essa vantagem não se manteve em 2021.

Além disso, as diferenças entre GARCH e GJR na validação foram muito pequenas, não permitindo identificar uma contribuição econômica consistente da modelagem de assimetria.

**A principal conclusão é que maior sofisticação na previsão de volatilidade não garante melhor desempenho ajustado ao risco quando as previsões são utilizadas para determinar os pesos de uma carteira de Momentum.**

Essa constatação não invalida a utilidade do GARCH para modelagem e previsão de volatilidade. Ela indica que é necessário avaliar separadamente a precisão preditiva do modelo e a eficiência econômica da regra de alocação.

## 13. Próximas etapas

Para aprofundar os resultados, o projeto poderá avançar nas seguintes direções:

1. **Avaliar a qualidade das previsões:** comparar volatilidade prevista e realizada por meio de métricas como QLIKE e MSE.
2. **Analisar os pesos das carteiras:** investigar concentração, contribuição individual dos ativos e relação entre volatilidade e retornos posteriores.
3. **Padronizar os horizontes de previsão:** garantir comparabilidade entre volatilidade histórica, EWMA, GARCH e GJR.
4. **Investigar custos e robustez:** repetir as análises com diferentes custos, janelas de estimação e parâmetros de Momentum.
5. **Realizar testes estatísticos:** avaliar a significância das diferenças de desempenho entre os modelos.
6. **Executar o teste final fora da amostra:** após definir e congelar as especificações, avaliar os resultados em 2022–2026.

---

**Fonte dos resultados:** `comparacao_modelos_volatilidade.ipynb`, com preços da Economatica, CDI do Banco Central e funções implementadas no repositório TraineeFGVquant.

**Observação:** os resultados são históricos e não devem ser interpretados como garantia de desempenho futuro.
