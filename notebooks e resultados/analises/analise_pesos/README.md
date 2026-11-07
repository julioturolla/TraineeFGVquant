# Análise dos Pesos e da Contribuição de Retorno — Momentum e GJR-GARCH

**Projeto:** Trainee FGV Quant  
**Notebook:** `analise_pesos.ipynb`  
**Estratégia:** Momentum 12–1, Top 5, rebalanceamento mensal  
**Períodos:** Treinamento (2017–2020) e validação (2021)

## 1. Objetivo

Este estudo investiga por que a ponderação por volatilidade prevista pelo modelo GJR-GARCH reduziu o retorno de uma estratégia de Momentum no mercado acionário brasileiro, apesar de ter proporcionado menor volatilidade realizada.

Nos experimentos anteriores, verificou-se que a carteira Momentum 12–1 Top 5 com pesos iguais apresentou maior rentabilidade e maior Índice de Sharpe do que a mesma carteira ponderada pelo inverso da volatilidade prevista pelo GJR-GARCH.

A presente análise busca identificar os mecanismos econômicos responsáveis por essa diferença.

Mais especificamente, investigamos três questões:

1. O GJR-GARCH reduz sistematicamente os pesos das ações com maior Momentum?
2. As ações penalizadas pelo modelo apresentam retornos futuros superiores às demais?
3. A perda de desempenho decorre principalmente da distribuição média dos pesos, da variação desses pesos ao longo do tempo ou dos custos adicionais de transação?

Para responder a essas perguntas, foram analisados os pesos mensais, o ranking de Momentum, os retornos posteriores das ações, uma decomposição estatística das contribuições de retorno e as diferenças efetivas entre os backtests.

## 2. Dados e metodologia

### 2.1. Base de dados

A análise utiliza preços de 30 ações brasileiras obtidos da Economatica.

Os dados abrangem o período de janeiro de 2015 a dezembro de 2021. Os anos de 2015 e 2016 fornecem histórico inicial para o cálculo dos indicadores.

Os resultados são separados em treinamento (2017–2020) e validação (2021). O período de 2022–2026 permanece reservado para o teste final fora da amostra.

O notebook utiliza 60 datas mensais de formação de carteira, de janeiro de 2017 a dezembro de 2021.

### 2.2. Seleção das ações

A estratégia utiliza o indicador Momentum 12–1:

\[
M_{i,t}=\frac{P_{i,t-21}}{P_{i,t-252}}-1
\]

O indicador mede a valorização acumulada aproximadamente nos últimos 12 meses, desconsiderando os 21 pregões mais recentes.

No último pregão de cada mês, as ações são ordenadas por Momentum, sendo selecionadas as cinco primeiras.

As duas estratégias comparadas utilizam exatamente as mesmas ações. A diferença está exclusivamente nos pesos atribuídos a cada posição.

### 2.3. Carteira com pesos iguais

A carteira de referência distribui o capital igualmente entre as cinco ações selecionadas:

\[
w_{i,t}^{igual}=0,20
\]

Cada posição recebe 20% do patrimônio no momento do rebalanceamento.

### 2.4. Carteira ponderada pelo GJR-GARCH

A segunda carteira utiliza previsões de volatilidade geradas pelo modelo GJR-GARCH, com janela de estimação de 756 pregões.

As previsões utilizadas correspondem à volatilidade diária estimada a partir das variâncias previstas para um horizonte de 21 pregões.

Os pesos são inversamente proporcionais à volatilidade prevista:

\[
w_{i,t}^{GJR}=
\frac{1/\widehat{\sigma}_{i,t}}
{\sum_{j=1}^{5}1/\widehat{\sigma}_{j,t}}
\]

Dessa maneira, ações com maior volatilidade prevista recebem menos capital, enquanto ações com menor volatilidade prevista recebem maior participação.

As previsões do GJR foram recuperadas do arquivo `cache_vol_modelos.pkl`, produzido anteriormente no notebook de comparação de modelos de volatilidade.

Isso permitiu reutilizar as estimativas existentes, sem repetir o processo de estimação.

## 3. Comparação dos pesos por ranking de Momentum

A primeira análise consistiu em construir uma tabela contendo, para cada ação selecionada e data de rebalanceamento, seu ranking de Momentum, peso igualitário, peso GJR e diferença entre os pesos.

Posteriormente, os resultados foram agrupados pela posição no ranking.

### Resultados

| Ranking de Momentum | Peso igual (%) | Peso médio GJR (%) | Diferença (p.p.) |
|---|---:|---:|---:|
| 1º | 20,000 | 15,516 | -4,484 |
| 2º | 20,000 | 17,252 | -2,748 |
| 3º | 20,000 | 20,657 | +0,657 |
| 4º | 20,000 | 22,069 | +2,069 |
| 5º | 20,000 | 24,507 | +4,507 |

Cada posição apresenta 60 observações, uma para cada rebalanceamento.

### Interpretação

Os resultados revelam uma relação crescente entre a posição no ranking e o peso médio atribuído pelo GJR.

A ação de maior Momentum recebeu, em média, apenas 15,52% do capital, enquanto a quinta colocada recebeu aproximadamente 24,51%.

Portanto, a diferença média de alocação entre a primeira e a quinta posição foi de aproximadamente 9 pontos percentuais.

Esse resultado mostra que o GJR reduziu sistematicamente a exposição às ações com maior Momentum e aumentou a participação das ações com Momentum relativamente menor dentro do Top 5.

Como a ponderação depende do inverso da volatilidade prevista, esse padrão é compatível com uma associação positiva entre a intensidade do Momentum e a volatilidade prevista.

Em outras palavras, as ações melhor classificadas tenderam a receber menor alocação porque o modelo lhes atribuiu maior risco relativo.

Entretanto, essa constatação ainda não demonstra que a redistribuição tenha prejudicado a rentabilidade. Para investigar essa possibilidade, analisamos os retornos futuros das ações.

## 4. Retornos futuros por posição no ranking

A segunda análise consistiu em calcular o retorno acumulado de cada ação durante o intervalo posterior à formação da carteira.

O cálculo considera a execução no fechamento do pregão seguinte ao sinal, de maneira compatível com a lógica do backtest.

Foram utilizados 59 intervalos mensais completos, uma vez que a última formação de carteira não possui um intervalo mensal posterior completo dentro da amostra.

Para cada ranking, calculamos o retorno futuro médio das ações e o peso médio atribuído pelo GJR.

### Resultados

| Ranking | Retorno futuro médio (%) | Peso médio GJR (%) |
|---|---:|---:|
| 1º | 5,289 | 15,492 |
| 2º | 2,953 | 17,214 |
| 3º | 3,251 | 20,741 |
| 4º | 2,866 | 22,053 |
| 5º | 3,882 | 24,500 |

### Interpretação

A ação de maior Momentum apresentou o maior retorno futuro médio, de 5,29% por intervalo mensal.

Entretanto, essa mesma posição recebeu o menor peso médio do GJR, de aproximadamente 15,49%.

Isso sugere que a ponderação por volatilidade pode ter reduzido a participação em ações que posteriormente apresentaram retornos elevados.

Contudo, a relação entre ranking e retorno futuro não é perfeitamente monotônica. A quinta colocada, por exemplo, apresentou retorno médio superior ao da segunda, terceira e quarta posições.

Portanto, não podemos afirmar que retornos futuros diminuem continuamente conforme piora o ranking de Momentum.

Também não basta comparar pesos e retornos médios separadamente. O resultado da carteira depende de como os pesos atribuídos em cada mês se relacionam com os retornos efetivamente realizados naquele mesmo intervalo.

Essa questão motivou a análise seguinte.

## 5. Atribuição aproximada da diferença de retorno

Para investigar o impacto econômico da redistribuição dos pesos, calculamos a contribuição diferencial de cada posição em relação à carteira equiponderada.

A medida utilizada foi:

\[
\Delta C_{i,t}=
(w_{i,t}^{GJR}-w_{i,t}^{igual})R_{i,t+1}
\]

Em que:

- \(w_{i,t}^{GJR}\) é o peso-alvo da ação determinado pelo GJR.
- \(w_{i,t}^{igual}\) é o peso de referência de 20%.
- \(R_{i,t+1}\) representa o retorno acumulado da ação no intervalo posterior ao sinal.

A medida estima quanto a alteração de peso contribuiu para aumentar ou diminuir o retorno da carteira.

### Resultados

| Ranking | Diferença média de peso (p.p.) | Contribuição média (p.p.) |
|---|---:|---:|
| 1º | -4,508 | -0,236 |
| 2º | -2,786 | -0,098 |
| 3º | +0,741 | -0,109 |
| 4º | +2,053 | -0,133 |
| 5º | +4,500 | -0,056 |
| **Total** | **≈ 0** | **-0,633** |

A diferença média aproximada entre GJR e pesos iguais foi de **-0,633 ponto percentual por intervalo mensal**.

### Interpretação

Todas as posições apresentaram contribuição média negativa.

A primeira colocada foi a principal responsável pela diferença, contribuindo com aproximadamente -0,236 ponto percentual.

Esse resultado é consistente com a hipótese de que reduzir a exposição à ação com maior Momentum prejudicou a rentabilidade.

Entretanto, encontramos um resultado adicional importante: as posições 3, 4 e 5 apresentaram contribuições negativas mesmo recebendo pesos médios superiores a 20%.

Portanto, o problema não parece estar exclusivamente na distribuição média dos pesos.

É possível que as variações mensais de alocação também estejam associadas desfavoravelmente aos retornos posteriores.

Para investigar essa possibilidade, realizamos uma decomposição estatística.

## 6. Decomposição entre efeito dos pesos médios e covariância

A contribuição média pode ser decomposta utilizando a identidade:

\[
E[\Delta w_i R_i]
=
E[\Delta w_i]E[R_i]
+
\operatorname{Cov}(\Delta w_i,R_i)
\]

Essa decomposição permite separar dois componentes:

**Efeito dos pesos médios:** representa a contribuição decorrente da diferença média de alocação em cada posição do ranking.

**Efeito da covariância:** representa a contribuição associada à maneira como os desvios dos pesos em relação à média se relacionaram com os retornos futuros.

Uma covariância negativa indica que pesos relativamente maiores estiveram associados a retornos posteriores relativamente menores, dentro da mesma posição do ranking.

### Resultados — Amostra completa

| Ranking | Efeito peso médio (p.p.) | Efeito covariância (p.p.) | Contribuição total (p.p.) |
|---|---:|---:|---:|
| 1º | -0,238 | +0,002 | -0,236 |
| 2º | -0,082 | -0,016 | -0,098 |
| 3º | +0,024 | -0,133 | -0,109 |
| 4º | +0,059 | -0,192 | -0,133 |
| 5º | +0,175 | -0,231 | -0,056 |
| **Total** | **-0,063** | **-0,569** | **-0,633** |

*Pequenas diferenças nas somas decorrem do arredondamento.*

### Interpretação

A decomposição apresenta um resultado central para o estudo.

A contribuição negativa estimada decorre predominantemente do componente de covariância.

O efeito dos pesos médios foi de aproximadamente -0,063 ponto percentual, enquanto o efeito da covariância foi de -0,569 ponto percentual.

Dessa maneira, aproximadamente **90% da contribuição negativa estimada está associada ao componente de covariância**.

Isso sugere que o principal problema não foi apenas o GJR atribuir pesos sistematicamente menores às primeiras posições do ranking.

A maneira como os pesos variaram ao longo do tempo também esteve associada negativamente aos retornos futuros.

Nas posições 3, 4 e 5, o efeito dos pesos médios foi positivo, mas o componente de covariância negativa foi suficientemente forte para tornar a contribuição total negativa.

Esse resultado é compatível com uma regra de ponderação que, em determinados momentos, aumentou a participação em ações que posteriormente apresentaram retornos relativamente fracos.

**Essa interpretação é descritiva, não causal.** A covariância negativa não demonstra que o GJR tenha causado os retornos observados, nem prova que suas previsões de volatilidade sejam imprecisas.

## 7. Decomposição por período

Para verificar a estabilidade dos resultados, a decomposição foi realizada separadamente para treinamento e validação.

### 7.1. Treinamento — 2017 a 2020

| Ranking | Efeito médio (p.p.) | Efeito covariância (p.p.) | Contribuição total (p.p.) |
|---|---:|---:|---:|
| 1º | -0,355 | +0,102 | -0,253 |
| 2º | -0,121 | +0,003 | -0,119 |
| 3º | +0,029 | -0,164 | -0,134 |
| 4º | +0,073 | -0,262 | -0,189 |
| 5º | +0,130 | -0,164 | -0,034 |
| **Total** | **-0,244** | **-0,485** | **-0,729** |

Durante o treinamento, a ponderação GJR apresentou contribuição negativa aproximada de 0,729 ponto percentual por intervalo mensal.

O efeito da covariância respondeu por aproximadamente dois terços dessa contribuição negativa.

O efeito médio dos pesos também foi desfavorável, especialmente nas duas primeiras posições.

Portanto, durante o treinamento, tanto a distribuição média de capital quanto suas variações temporais contribuíram para o resultado inferior ao dos pesos iguais.

### 7.2. Validação — 2021

| Ranking | Efeito médio (p.p.) | Efeito covariância (p.p.) | Contribuição total (p.p.) |
|---|---:|---:|---:|
| 1º | +0,021 | -0,184 | -0,163 |
| 2º | +0,027 | -0,036 | -0,008 |
| 3º | -0,018 | +0,020 | +0,002 |
| 4º | -0,044 | +0,154 | +0,109 |
| 5º | +0,076 | -0,228 | -0,152 |
| **Total** | **+0,062** | **-0,274** | **-0,212** |

Na validação, a contribuição negativa foi menor, aproximadamente -0,212 ponto percentual por intervalo mensal.

O efeito dos pesos médios tornou-se positivo (+0,062 p.p.), enquanto o efeito da covariância permaneceu negativo (-0,274 p.p.).

Isso significa que, em 2021, a distribuição média dos pesos não foi o principal fator responsável pelo desempenho inferior do GJR.

O componente desfavorável esteve associado principalmente às variações temporais dos pesos e sua relação com os retornos posteriores.

O fato de o componente de covariância permanecer negativo nas duas amostras oferece evidência descritiva de persistência do mecanismo.

Entretanto, o período de validação contém apenas 11 intervalos classificados pela data do sinal, o que limita a força estatística dessa conclusão.

## 8. Diferenças efetivas dos retornos dos backtests

As decomposições anteriores utilizam pesos-alvo mensais e retornos acumulados por intervalo. Portanto, representam uma aproximação e não incorporam integralmente a evolução diária dos pesos e os custos de transação.

Para verificar os resultados nas carteiras efetivamente simuladas, foram executados novamente os backtests de pesos iguais e GJR, utilizando a mesma função de negociação.

Posteriormente, calculamos a diferença diária entre os retornos das duas estratégias, com e sem custos.

Os resultados foram anualizados aritmeticamente, multiplicando a diferença média diária por 252.

### Resultados

| Indicador | Treinamento (2017–2020) | Validação (2021) |
|---|---:|---:|
| Diferença bruta anualizada (p.p.) | -8,286 | -2,030 |
| Diferença líquida anualizada (p.p.) | -8,394 | -2,112 |
| Efeito adicional dos custos (p.p.) | -0,108 | -0,082 |

### 8.1. Diferença bruta

O GJR apresentou desempenho inferior aos pesos iguais mesmo antes da aplicação dos custos.

No treinamento, a diferença média diária anualizada foi de -8,286 pontos percentuais.

Na validação, a diferença foi de -2,030 pontos percentuais.

Isso confirma que a rentabilidade inferior do GJR não decorre exclusivamente dos custos de transação.

### 8.2. Diferença líquida

Após incluir os custos de negociação de 0,10% sobre o turnover, a diferença negativa aumentou para -8,394 pontos percentuais no treinamento e -2,112 pontos percentuais na validação.

Os resultados permanecem desfavoráveis ao GJR nos dois períodos.

### 8.3. Efeito adicional dos custos

O efeito adicional dos custos foi de apenas -0,108 ponto percentual anualizado no treinamento e -0,082 ponto percentual na validação.

Portanto, os custos aumentaram a desvantagem do GJR, mas explicaram apenas uma pequena parcela da diferença total de desempenho.

Isso reforça a interpretação de que o principal fator responsável pela perda de rentabilidade está associado à regra de alocação e aos retornos realizados, e não apenas à maior frequência ou intensidade das negociações.

**Importante:** essas diferenças representam retornos médios diários anualizados aritmeticamente. Elas não são equivalentes à diferença entre as taxas anuais compostas de cada carteira.

## 9. Síntese dos resultados

A análise produziu quatro resultados principais.

### 9.1. O GJR subponderou as ações com maior Momentum

A primeira colocada do ranking recebeu peso médio de aproximadamente 15,5%, enquanto a quinta colocada recebeu cerca de 24,5%.

Isso confirma uma associação entre ranking de Momentum e alocação de capital.

### 9.2. A ação de maior Momentum apresentou o maior retorno futuro médio

A primeira colocada obteve retorno futuro médio de aproximadamente 5,29% por intervalo mensal, apesar de receber a menor participação na carteira GJR.

Isso é consistente com a hipótese de que a ponderação por volatilidade sacrificou parte da exposição às posições mais rentáveis.

### 9.3. A covariância explica a maior parte da contribuição negativa aproximada

A decomposição mostrou que o componente de covariância entre as alterações dos pesos e os retornos posteriores foi o principal responsável pela contribuição negativa estimada.

Na amostra completa, esse componente representou aproximadamente 90% do efeito negativo.

O mesmo sinal desfavorável foi observado nas análises separadas de treinamento e validação.

### 9.4. Os custos não explicam a maior parte da perda

A comparação entre os retornos brutos e líquidos confirmou que o GJR apresentou desempenho inferior mesmo antes dos custos.

Os custos adicionais de negociação agravaram o resultado, mas seu efeito foi relativamente pequeno.

## 10. Limitações metodológicas

Apesar das evidências encontradas, existem limitações importantes.

### 10.1. Atribuição mensal aproximada

A decomposição por ranking utiliza pesos-alvo mensais e retornos acumulados entre rebalanceamentos.

Ela não reproduz exatamente a evolução diária dos pesos dentro de cada carteira.

Por esse motivo, o resultado aproximado de -0,633 ponto percentual por intervalo mensal não deve ser interpretado como a diferença exata dos backtests.

A atribuição exata por ativo exigiria utilizar os pesos efetivamente mantidos em cada pregão e calcular suas contribuições diárias para os retornos.

Essa análise ainda não foi realizada no notebook.

### 10.2. Classificação temporal dos intervalos

Na decomposição mensal, os intervalos foram classificados de acordo com a data de formação do sinal.

Assim, a carteira formada em dezembro de 2020 foi classificada no treinamento, embora parte de seus retornos posteriores tenha ocorrido em janeiro de 2021.

Nas diferenças efetivas dos backtests, a separação foi realizada pelas datas dos retornos diários.

Portanto, as duas análises não utilizam uma divisão temporal perfeitamente equivalente.

Uma versão posterior deverá classificar as contribuições mensais de acordo com os retornos efetivamente realizados em cada período.

### 10.3. Amostra de validação reduzida

A análise de validação considera apenas 2021 e contém 11 intervalos mensais completos classificados por data de formação.

Essa quantidade de observações limita a possibilidade de generalizar o padrão de covariância negativa.

### 10.4. Ausência de testes de significância

Os resultados são descritivos.

Ainda não foram realizados testes formais para verificar se as diferenças de retorno e os componentes de covariância são estatisticamente significativos.

A relação observada não deve ser interpretada automaticamente como evidência de causalidade ou de capacidade sistemática de previsão dos retornos.

### 10.5. Qualidade preditiva do GJR

O presente estudo avalia os efeitos econômicos de utilizar a volatilidade prevista na determinação dos pesos.

Não foi realizada uma avaliação direta da precisão das previsões de volatilidade.

Consequentemente, o desempenho inferior da carteira GJR não demonstra que o modelo tenha baixa qualidade estatística como estimador de risco.

### 10.6. Universo de ativos

O universo utilizado contém 30 ações e pode estar sujeito a viés de sobrevivência.

Caso os ativos tenham sido selecionados utilizando informações posteriores ao início da amostra, os resultados históricos poderão apresentar distorções.

### 10.7. Cache de volatilidade

As previsões GJR são recuperadas de um arquivo de cache produzido anteriormente.

O código verifica se a estrutura temporal e a lista de ativos correspondem às características esperadas, mas essa assinatura não confirma integralmente se os valores das bases permanecem inalterados.

A reprodução integral requer preservar os dados, o modelo, os parâmetros e o cache utilizados.

## 11. Organização e reprodução

O notebook está localizado em:

`notebooks e resultados/analises/analise_pesos.ipynb`

Ele utiliza os seguintes arquivos e módulos:

```text
TraineeFGVquant/
├── baseDeDados/
│   └── economatica-3.xlsx
│
└── notebooks e resultados/
    ├── momentum com garch/
    │   ├── initial_test.py
    │   └── funcoes_momentum.py
    │
    ├── modelos volatilidade/
    │   └── cache_vol_modelos.pkl
    │
    └── analises/
        ├── analise_pesos.ipynb
        └── README.md
```

As principais etapas implementadas foram:

1. Preparação dos preços, retornos e sinais de Momentum.
2. Recuperação das previsões GJR armazenadas em cache.
3. Reconstrução das carteiras com pesos iguais e GJR.
4. Comparação dos pesos por posição no ranking.
5. Cálculo dos retornos futuros das ações selecionadas.
6. Atribuição aproximada da diferença de retorno.
7. Decomposição entre efeito dos pesos médios e covariância.
8. Comparação entre treinamento e validação.
9. Reexecução dos backtests e comparação dos retornos brutos e líquidos.

Os resultados do notebook foram conferidos a partir das saídas executadas. A preparação da base Economatica, a seleção Momentum e o backtest de pesos iguais também foram reproduzidos independentemente, com resultados coincidentes. A reexecução integral das etapas GJR depende da disponibilidade do respectivo cache de volatilidade.

## 12. Conclusão

O objetivo deste estudo foi investigar por que a ponderação por GJR-GARCH produziu menor retorno do que a carteira Momentum com pesos iguais.

Os resultados mostram que o GJR alterou significativamente a distribuição de capital entre as ações selecionadas.

As posições com maior Momentum receberam, em média, pesos menores, enquanto as posições inferiores do Top 5 receberam pesos maiores.

Além disso, a ação com maior Momentum apresentou o maior retorno futuro médio, sugerindo que a redução de sua participação pode ter prejudicado a rentabilidade da carteira.

Entretanto, a decomposição da contribuição de retorno revelou um mecanismo mais importante: **a maior parte da contribuição negativa aproximada decorreu da covariância desfavorável entre as alterações dos pesos e os retornos posteriores das ações**.

Na amostra completa, aproximadamente 90% da contribuição negativa estimada esteve associada a esse componente.

O efeito também foi observado nas análises separadas de treinamento e validação, embora com magnitudes diferentes.

A comparação entre os backtests confirmou que o GJR apresentou retorno inferior mesmo antes dos custos de transação. Os custos adicionais agravaram a desvantagem, mas não foram sua principal explicação.

Assim, os resultados sugerem que **a utilização da volatilidade prevista como regra de ponderação reduziu o risco, mas também redistribuiu o capital de maneira desfavorável aos retornos posteriormente realizados**.

Essa conclusão não implica que o GJR seja inadequado para prever volatilidade. O experimento avalia sua utilidade econômica na construção de uma carteira de Momentum, e não sua precisão preditiva isoladamente.

O resultado reforça a importância de distinguir a qualidade estatística de um modelo de risco da eficiência econômica de sua aplicação em estratégias quantitativas.

## 13. Próximas etapas

Para aprofundar a análise, recomenda-se realizar uma atribuição exata de retorno por ativo, reconstruindo os pesos efetivamente mantidos diariamente e reconciliando suas contribuições com os retornos brutos dos backtests.

Também seria relevante analisar a concentração das carteiras por meio do índice Herfindahl-Hirschman (HHI), investigar exposições setoriais e verificar se as ações com maior Momentum apresentam sistematicamente maior volatilidade prevista.

Por fim, poderão ser aplicados testes estatísticos para avaliar a significância das diferenças observadas, além de testes de robustez para diferentes regras de ponderação e janelas de estimação.

O período de 2022–2026 deverá permanecer reservado até a conclusão dessas análises e a definição final da metodologia.

---

**Fonte:** `analise_pesos.ipynb`, dados da Economatica e funções do projeto TraineeFGVquant.

**Observação:** os resultados correspondem ao treinamento de 2017–2020 e à validação de 2021. Não representam resultados do teste final fora da amostra.
