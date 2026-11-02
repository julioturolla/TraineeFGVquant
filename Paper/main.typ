#import "@preview/charged-ieee:0.1.4": ieee

#set text(lang: "pt")
#show "TABLE": "TABELA"
#show "Abstract": "Resumo"
#show "Index Terms": "Palavras-chave"

#show: ieee.with(
  title: [Seleção por momentum e ponderação por previsões GARCH no mercado acionário brasileiro],
  abstract: [
    Este trabalho desenvolve uma estratégia quantitativa para o mercado acionário brasileiro que separa a construção da carteira em duas camadas: (i) a seleção dos ativos, conduzida por um sinal de momentum de seção transversal, e (ii) o dimensionamento das posições, conduzido por previsões de volatilidade condicional obtidas por um modelo GARCH(1,1). Em cada data de rebalanceamento mensal, os ativos de um universo da B3 são ordenados pelo retorno acumulado entre doze meses e um mês antes da formação, e os mais bem classificados recebem pesos inversamente proporcionais ao risco esperado para o período de manutenção. O modelo de volatilidade é reestimado a cada data com informação disponível apenas até aquele ponto, e sua adoção é sustentada por testes de heterocedasticidade condicional que indicam memória longa da volatilidade em todos os ativos do universo. A carteira é avaliada em backtest com execução defasada e custos proporcionais ao turnover, por meio de retorno, volatilidade, índice de Sharpe sobre o CDI, máximo drawdown e turnover, e comparada com variantes que alteram a janela do sinal, a regra de seleção e o esquema de ponderação. O desenho amostral separa treino (2017 a 2020), validação (2021) e teste (2022 a 2026), este último mantido intocado até a fixação de todos os parâmetros. O documento descreve os dados, a metodologia e as especificações de aplicação da estratégia.
  ],
  authors: (
    (
      name: "Gabriel Hansen",
      department: [Trainee at FGV Quant],
      location: [São Paulo, Brazil],
      email: "lukas.kall@fgv.br"
    ),
    (
      name: "Júlio Turolla",
      department: [Trainee at FGV Quant],
      location: [São Paulo, Brazil],
      email: "julioreisturolla@gmail.com"
    ),
    (
      name: "Theo Koga",
      department: [Trainee at FGV Quant],
      location: [São Paulo, Brazil],
      email: "koga.y.theo@gmail.com"
    )
  ),
  index-terms: ("Scientific writing", "Typesetting", "Document creation", "Syntax"),
  bibliography: bibliography("refs.bib"),
  figure-supplement: [Fig.],
)

= Introdução
Estratégias baseadas em retornos passados ocupam posição central em finanças quantitativas por 
uma razão simples: ativos que superaram seus pares nos últimos meses tendem a continuar supe
­
rando no horizonte seguinte, padrão observado em diferentes mercados e períodos. Na sua forma de 
seção transversal, o momentum compara os ativos entre si em cada data e concentra a carteira nos 
vencedores relativos. O retorno médio elevado, no entanto, vem acompanhado de um risco que não 
é constante. As perdas mais severas dessas estratégias tendem a ocorrer em episódios de volatilidade 
alta, justamente quando a carteira está concentrada em ativos que acumularam ganhos rápidos e são 
mais sensíveis a reversões.
Essa característica sugere que a decisão de quais ativos comprar e a decisão de quanto alocar em 
cada um podem ser tratadas separadamente. A estratégia desenvolvida neste trabalho formaliza essa 
separação. O sinal de momentum define a composição da carteira, e uma previsão de volatilidade 
condicional define os pesos, de modo que ativos com risco esperado maior recebem participação 
menor. A escolha de um modelo condicional, e não de uma medida histórica fixa, decorre da própria 
dinâmica dos retornos: a volatilidade das ações se agrupa no tempo e é persistente, o que torna 
seu nível nas semanas seguintes parcialmente previsível a partir do comportamento recente. Há, 
contudo, uma tensão embutida na combinação. Os ativos selecionados pelo momentum costumam 
ser os de maior volatilidade recente, e ponderar pelo inverso do risco reduz a exposição exatamente 
1
a eles. O efeito líquido sobre a carteira é uma questão empírica, avaliada pelos indicadores de 
desempenho e risco em comparação com variantes de referência.
A aplicação ao mercado brasileiro é deliberada. Um universo restrito à B3 tem uma única moeda, 
um único calendário de negociação e uma única taxa livre de risco, o que elimina fontes de ruído 
alheias ao objeto do estudo. A combinação de mercados exigiria tratar risco cambial, que passaria a 
compor o resultado da carteira, e conciliar feriados não coincidentes, que distorcem retornos diários 
e correlações. Além disso, o CDI elevado em boa parte da amostra torna exigente a avaliação de 
qualquer estratégia acionária por excesso de retorno, e a disponibilidade de preços ajustados por 
proventos com cobertura adequada permite reconstruir a série de retornos totais com confiabilidade. 
Por outro lado, o mercado brasileiro impõe restrições que precisam ser explicitadas: histórico mais 
curto, universo de ativos líquidos reduzido e maior sensibilidade dos resultados a poucos episódios 
extremo.
== Seleção e dimensionamento
Considere um universo de ativos indexados por $i$ e datas de rebalanceamento $t$. Em cada data, a estratégia produz um conjunto de ativos selecionados $S_t$ e um vetor de pesos $w_t$, mantidos até a data seguinte. O retorno diário da carteira entre rebalanceamentos é

$ r_p (d) = sum_(i in S_t) w_(i,d-1) dot r_(i,d), $ <eq:retorno-carteira>

em que $r_(i,d)$ é o retorno simples do ativo $i$ no dia $d$ e os pesos $w_(i,d-1)$ evoluem com os retornos dos ativos desde a última execução. A separação em camadas tem duas implicações. A primeira é que cada camada pode ser avaliada isoladamente: mantida a mesma seleção $S_t$, a comparação entre pesos iguais e pesos baseados em volatilidade atribui as diferenças nos indicadores exclusivamente ao dimensionamento. A segunda é que as duas camadas operam em horizontes compatíveis. O sinal de momentum resume o desempenho relativo dos últimos meses, enquanto a previsão de volatilidade descreve o risco esperado durante o mês em que a posição ficará aberta.

= Base de Dados
== Base e cobertura
A implementação parte de preços de fechamento diários, ajustados por proventos e em moeda original, extraídos da Economatica para 30 ações negociadas na B3, de janeiro de 2015 a outubro de 2026. O universo distribui-se entre setores distintos, como bancos, commodities, energia elétrica, consumo, construção e indústria, o que reduz o risco de que o sinal reflita a dinâmica de um único setor. O ajuste por proventos é necessário porque pagamentos de dividendos reduzem o preço de tela sem representar perda ao acionista; a série ajustada preserva o retorno total entre duas datas, que é a grandeza relevante para o backtest.

A composição do universo exige dois cuidados. O primeiro é a presença de duas classes de ações de um mesmo emissor em dois casos, Klabin (KLBN3 e KLBN11) e Santander (SANB3 e SANB11), cujos retornos são altamente correlacionados, de modo que o número de emissores distintos é 28. O segundo é mais sensível: a lista de ativos foi definida com base na relevância atual das empresas. Esse critério incorpora informação sobre sobrevivência que não estaria disponível no início da amostra, pois empresas que perderam relevância ou deixaram de ser negociadas ao longo do período não fazem parte do universo. É uma forma de forward bias na construção do universo investível, que tende a favorecer estratégias compradas e deve ser considerada na leitura dos resultados.

== Tratamento dos preços e retornos

Os dias sem cotação para nenhum ativo, correspondentes a feriados da B3, são removidos. Ausências pontuais de um único pregão em um ativo são preenchidas com o último preço disponível, procedimento que usa apenas informação passada; lacunas mais longas permanecem ausentes. Preços não positivos ou infinitos interrompem o processamento em vez de serem corrigidos silenciosamente. Os retornos diários simples são calculados entre observações válidas de cada ativo, e um ativo só participa do ranking de uma data se possuir os preços necessários para o cálculo do sinal. Por esse critério, ativos listados ao longo da amostra entram no universo apenas após acumularem histórico suficiente, como a CAML3, listada em setembro de 2017 e elegível a partir do final de 2018.

Até a definição da configuração final, apenas os dados de 2015 a 2021 participam das decisões de modelagem. Os anos de 2022 a 2026 são reservados ao teste.

== Taxa livre de risco

A taxa livre de risco é o CDI diário divulgado pelo Banco Central, expresso como taxa ao dia e alinhado às datas de negociação. O CDI é usado no cálculo do excesso de retorno de todas as estratégias e, portanto, em todas as medidas de Sharpe do trabalho.

// ------------------------------------------------------------------ 4
= Estrutura metodológica

== Sinal de momentum e seleção

Em cada data de formação $t$, correspondente ao último pregão de cada mês, o sinal do ativo $i$ é o retorno acumulado entre $L$ e 21 pregões antes de $t$:

$ M_(i,t) = P_(i,t-21) / P_(i,t-L) - 1, quad L in \{126, 189, 252\}. $

A janela principal é a 12-1 ($L = 252$), e as alternativas 9-1 e 6-1 são avaliadas no treino. A exclusão do último mês não é meramente uma convenção: no curtíssimo prazo, retornos tendem a apresentar reversão, e incluir o mês mais recente misturaria ao sinal um componente de sentido oposto.

Os ativos elegíveis são ordenados de forma decrescente pelo sinal, e a carteira contém apenas posições compradas. São avaliadas duas famílias de regras. Na regra Top $N$, com $N in \{5, 10, 15\}$, a carteira é formada pelos $N$ primeiros ativos do ranking. Na regra de deadband, a carteira mantém cinco posições, mas um ativo já presente só é vendido se cair abaixo de uma posição limite, igual a 7 ou 10; as vagas abertas são preenchidas pelos ativos mais bem classificados ainda fora da carteira. O deadband reduz o turnover associado a oscilações marginais no ranking, que em geral refletem ruído e não mudança efetiva de sinal.

== Evidência de heterocedasticidade condicional

A camada de dimensionamento pressupõe que a variância dos retornos não seja constante e que dependa do seu próprio passado. Essa hipótese foi testada ativo a ativo, com log-retornos diários em pontos percentuais e a amostra completa. Os testes têm caráter diagnóstico: caracterizam o processo gerador dos retornos e não participam da escolha de parâmetros da estratégia.

O teste ARCH-LM rejeita a hipótese de variância constante, ao nível de 5%, em todos os 30 ativos com 1, 5 e 10 defasagens, e em 29 dos 30 com 20 defasagens. O teste de Ljung-Box aplicado aos retornos ao quadrado rejeita a ausência de autocorrelação em todos os ativos. A autocorrelação média dos retornos ao quadrado nas 20 primeiras defasagens é de 0,116, contra 0,022 em valor absoluto para os retornos, contraste que caracteriza o agrupamento de volatilidade: a direção do retorno é pouco previsível, mas sua magnitude é persistente. A distribuição dos retornos também se afasta da normal, com curtose em excesso mediana de 6,7. A análise em janelas móveis de três anos indica que o efeito não é produzido por poucos episódios extremos, já que, na mediana dos ativos, 71% das janelas rejeitam a variância constante.

== Modelo de volatilidade

O modelo principal é um GARCH(1,1) com média zero e inovações $t$ de Student padronizadas:

$ r_(i,t) &= sigma_(i,t) dot z_(i,t), quad z_(i,t) tilde.op t(nu), \
  sigma_(i,t)^2 &= omega + alpha dot r_(i,t-1)^2 + beta dot sigma_(i,t-1)^2, $

em que $r_(i,t)$ é o log-retorno diário em pontos percentuais, $alpha$ mede a reação da variância a choques recentes e $beta$ a persistência da variância passada. A opção por um GARCH(1,1), em vez de um ARCH de ordem elevada, decorre da memória longa identificada na seção anterior. A persistência $alpha + beta$ tem mediana de 0,984 entre os ativos, o que corresponde a uma meia-vida de cerca de 44 pregões para um choque de volatilidade, calculada como $ln("0,5") \/ ln(alpha + beta)$. Um ARCH só reproduziria esse padrão com dezenas de defasagens e, portanto, dezenas de parâmetros estimados em janelas de dois a quatro anos, com perda de estabilidade. No GARCH, o termo $sigma_(i,t-1)^2$ resume todo o histórico de choques, e o mesmo comportamento é capturado com três parâmetros de variância. Os critérios de informação são consistentes com essa escolha: o BIC prefere o GARCH(1,1) à variância constante em todos os ativos e ao GJR em 23 dos 30, e os resíduos padronizados deixam de apresentar efeito ARCH em 24 dos 30 ativos após a estimação. A meia-vida superior a um mês tem também uma implicação prática: como a carteira é mantida por cerca de 21 pregões, a volatilidade observada na data do sinal ainda carrega informação sobre o período em que a posição estará aberta. A distribuição $t$ acomoda as caudas pesadas dos retornos, e os graus de liberdade estimados têm mediana de 6,5, distante do caso normal.

Duas especificações alternativas compõem a comparação. A primeira é o GJR, que permite resposta assimétrica da variância a retornos negativos:

$ sigma_(i,t)^2 = omega + (alpha + gamma dot I[r_(i,t-1) < 0]) dot r_(i,t-1)^2 + beta dot sigma_(i,t-1)^2. $

O coeficiente $gamma$ é positivo em 26 dos 30 ativos, mas estatisticamente significativo em apenas 13, o que justifica tratar o GJR como alternativa e não como especificação principal. A segunda é o EWMA, uma média exponencial dos retornos ao quadrado que dispensa estimação, avaliada com fatores de decaimento $lambda in \{"0,90"; "0,94"; "0,97"\}$. O EWMA com $lambda = "0,94"$ é usado ainda como previsão de reserva quando o otimizador do GARCH não converge.

== Previsão e ponderação

Em cada data de sinal, o modelo é reestimado para cada ativo usando somente os retornos observados até o fechamento daquela data, em uma janela móvel de $w$ pregões, com $w in \{504, 756, 1008\}$ e mínimo de 252 observações. A volatilidade usada na decisão é a média prevista para o horizonte de manutenção:

$ hat(sigma)_(i,t) = lr([ 1/21 sum_(h=1)^21 E_t (sigma_(i,t+h)^2) ])^(1/2). $

Como a variância prevista converge gradualmente para seu nível de longo prazo à medida que o horizonte aumenta, a média sobre 21 pregões é mais adequada a uma carteira mensal do que a previsão de um único dia. Os pesos dos ativos selecionados são proporcionais ao inverso dessa volatilidade:

$ w_(i,t) = (display(1 / hat(sigma)_(i,t))) / (sum_(j in S_t) display(1 / hat(sigma)_(j,t))). $

A carteira permanece integralmente investida, sem alavancagem nem posições vendidas. Cada regra de seleção é avaliada também com pesos iguais, de modo que as duas versões compartilham os mesmos ativos em cada data e diferem apenas na ponderação.

O início da amostra em janeiro de 2015 impõe uma restrição às janelas de estimação. As janelas de 756 e 1008 pregões só ficam completas a partir de 2018 e 2019, respectivamente; antes disso, a estimação utiliza todo o histórico disponível, e as três janelas produzem previsões muito próximas ou idênticas no início do treino. A comparação entre janelas é interpretada à luz dessa restrição.

// ------------------------------------------------------------------ 5
= Especificações da aplicação

== Calendário de rebalanceamento e execução

O sinal é calculado com preços de fechamento do último pregão de cada mês. Como esse preço só é conhecido após o encerramento do pregão, a ordem é executada no fechamento do pregão seguinte, e a nova composição passa a afetar os retornos a partir do dia posterior. A defasagem evita o uso de informação indisponível no momento da decisão, fonte clássica de forward bias em backtests que executam no mesmo preço usado para gerar o sinal. Entre rebalanceamentos, os pesos evoluem com os retornos dos ativos, como em uma carteira real não rebalanceada, e voltam aos pesos-alvo na execução seguinte. O backtest se inicia em janeiro de 2017, com a primeira ordem executada em 1º de fevereiro de 2017.

A ausência de vazamento de informação na implementação foi verificada empiricamente: substituindo todos os preços posteriores a uma data de corte por valores artificiais, os sinais, as volatilidades previstas e os retornos da estratégia até essa data permanecem inalterados.

== Custos de transação e retorno líquido

O turnover de cada data de execução é a soma das variações absolutas entre os pesos-alvo e os pesos vigentes imediatamente antes da ordem,

$ tau_t = sum_i abs(w_(i,t)^"alvo" - w_(i,t)^"vigente"), $

sem divisão por dois, de modo que compras e vendas são contabilizadas, e a entrada inicial também gera custo. O retorno líquido é

$ r_"líq" (t) = (1 + r_"bruto" (t)) dot (1 - c dot tau_t) - 1, $

com custo-base #box[$c = "0,10%"$] sobre o valor negociado e análise de sensibilidade com #box[$c = "0%"$] e #box[$c = "0,30%"$]. A ponderação por volatilidade tende a elevar o turnover em relação aos pesos iguais, pois os pesos se alteram a cada mês mesmo quando a composição da carteira se mantém, e a modelagem de custos captura esse efeito.

== Divisão amostral e seleção da configuração

A amostra é dividida em quatro períodos. O biênio 2015-2016 serve apenas como histórico inicial para formar os primeiros sinais e estimar os primeiros modelos. O período de 2017 a 2020 é o treino, no qual as configurações são comparadas e a configuração final é definida. O ano de 2021 é a validação, usada para verificar se a configuração escolhida mantém seu comportamento fora do período de escolha; as posições e a memória do deadband são preservadas na passagem de 2020 para 2021, sem nova entrada artificial. Os anos de 2022 a 2026 formam o teste, executado uma única vez com todos os parâmetros congelados. O treino inclui deliberadamente o choque de 2020, de modo que a configuração escolhida seja exposta também a um período de estresse.

A grade avaliada combina três janelas de momentum, cinco regras de seleção e dez esquemas de ponderação (pesos iguais; GARCH e GJR com três janelas cada; EWMA com três fatores de decaimento), totalizando 150 configurações. A configuração final é a de maior Sharpe no treino. Esse procedimento exige disciplina: ao escolher entre muitas alternativas, a configuração vencedora tende a carregar parte de acaso específico da amostra, e só a validação e o teste permitem distinguir desempenho persistente de ajuste ao período. A qualidade das previsões de volatilidade é avaliada separadamente pela função de perda QLIKE, tomando como variância realizada a média dos retornos ao quadrado nos 21 pregões seguintes.

== Métricas de avaliação

As estratégias são avaliadas pelo retorno anual composto, pela volatilidade anualizada (desvio-padrão diário multiplicado por $sqrt(252)$), pelo máximo drawdown, medido em relação ao maior patrimônio anterior e incluindo o patrimônio inicial, e pelo turnover anual. A métrica principal é o índice de Sharpe sobre o excesso de retorno em relação ao CDI:

$ "Sharpe" = frac("média"(r_t - "cdi"_t), "desvio-padrão"(r_t - "cdi"_t)) dot sqrt(252). $

Todas as medidas de Sharpe são calculadas sobre o CDI, o que garante comparabilidade entre configurações e entre períodos.

== Implementação

A implementação está organizada em três módulos complementares. O primeiro reúne as regras comuns a todas as variantes: preparação da base, seleção por Top $N$ e deadband, backtest com p  esos que evoluem entre rebalanceamentos, custos e métricas. O segundo acrescenta a leitura da base, a obtenção do CDI, a estimação dos modelos de volatilidade nas datas de sinal e a ponderação pelo inverso da volatilidade prevista. O terceiro executa a grade de configurações, seleciona a melhor de cada família no treino e reporta seu desempenho na validação e a qualidade das previsões. Um script separado conduz os testes de heterocedasticidade da seção 4.2. Como todas as etapas compartilham o mesmo conjunto de funções, as variantes diferem apenas no componente de interesse.

// ------------------------------------------------------------------ 6
= Considerações finais

O desenho apresentado define uma estratégia de duas camadas, com seleção por momentum e dimensionamento por volatilidade condicional, e um protocolo de avaliação que separa escolha, validação e teste. A próxima etapa consiste em reportar os indicadores da grade no treino e na validação, fixar a configuração final e aplicá-la ao período de 2022 a 2026, acompanhando a sensibilidade dos resultados aos custos de transação. A interpretação dos resultados deverá considerar as restrições discutidas ao longo do texto: o viés de sobrevivência na composição do universo, a presença de classes de um mesmo emissor, o histórico curto para as janelas longas de estimação e a sensibilidade de amostras brasileiras a poucos episódios extremos.

= Apêndice

== Tabela do universo de ativos
A Tabela A1 lista os 30 ativos que compõem o universo da estratégia, com a empresa emissora, o setor, a data da primeira cotação disponível, o número de pregões com cotação e a volatilidade anualizada. A amostra cobre de 02/01/2015 a 21/10/2026, totalizando 2.930 pregões. A volatilidade é o desvio-padrão dos log-retornos diários entre 2015 e 2021, período utilizado nas decisões de modelagem, multiplicado por $sqrt(252)$. KLBN3 e KLBN11, assim como SANB3 e SANB11, são classes de ações de um mesmo emissor. A CAML3 inicia sua série em setembro de 2017, data de sua listagem, e a KLBN3 apresenta cerca de 5% de pregões sem negociação, a maior proporção do universo.

#let ativos = (
  // Financeiro
  ("B3", "B3SA3", "Financeiro"),
  ("Banco do Brasil", "BBAS3", "Financeiro"),
  ("Bradesco", "BBDC4", "Financeiro"),
  ("Itaú Unibanco", "ITUB4", "Financeiro"),
  ("Multiplan", "MULT3", "Financeiro"),
  ("Santander Brasil (ON)", "SANB3", "Financeiro"),
  ("Santander Brasil (unit)", "SANB11", "Financeiro"),
  // Materiais básicos
  ("Braskem", "BRKM5", "Materiais básicos"),
  ("CSN", "CSNA3", "Materiais básicos"),
  ("Gerdau", "GGBR4", "Materiais básicos"),
  ("Klabin (ON)", "KLBN3", "Materiais básicos"),
  ("Klabin (unit)", "KLBN11", "Materiais básicos"),
  ("Metalúrgica Gerdau", "GOAU4", "Materiais básicos"),
  ("Usiminas", "USIM5", "Materiais básicos"),
  ("Vale", "VALE3", "Materiais básicos"),
  // Petróleo, gás e biocombustíveis
  ("Petrobras", "PETR4", "Petróleo, gás e biocombustíveis"),
  ("PRIO", "PRIO3", "Petróleo, gás e biocombustíveis"),
  // Utilidade pública
  ("Cemig", "CMIG4", "Utilidade pública"),
  ("Engie Brasil Energia", "EGIE3", "Utilidade pública"),
  ("Equatorial", "EQTL3", "Utilidade pública"),
  ("Taesa", "TAEE11", "Utilidade pública"),
  // Consumo cíclico
  ("Cyrela", "CYRE3", "Consumo cíclico"),
  ("Localiza", "RENT3", "Consumo cíclico"),
  ("Magazine Luiza", "MGLU3", "Consumo cíclico"),
  ("MRV Engenharia", "MRVE3", "Consumo cíclico"),
  // Consumo não cíclico
  ("Ambev", "ABEV3", "Consumo não cíclico"),
  ("Camil Alimentos", "CAML3", "Consumo não cíclico"),
  // Bens industriais
  ("Embraer", "EMBJ3", "Bens industriais"),
  ("WEG", "WEGE3", "Bens industriais"),
  // Saúde
  ("Raia Drogasil", "RADL3", "Saúde"),
)

#show figure.where(kind: table): set block(breakable: true)
#show figure.where(kind: table): set figure.caption(position: top)

#figure(
  table(
    columns: (1fr, auto, 1.4fr),
    align: (left, center, left),
    inset: (x: 4pt, y: 2pt),
    stroke: none,
    table.hline(stroke: 1pt),
    table.header(
      repeat: true,
      [*Empresa*], [*Ticker*], [*Setor*],
    ),
    table.hline(stroke: 0.5pt),
    ..ativos.flatten().map(c => text(size: 7pt, c)),
    table.hline(stroke: 1pt),
  ),
  caption: [Universo de ativos e classificação setorial],
)

#set par(first-line-indent: (amount: 1em, all: true))

#show raw: set text(size: 7.5pt)
#show raw.where(block: true): set block(above: 12pt, below: 12pt)

== Código

=== Sinal de Momentum

Implementa a equação (2), da seção 4.1. O sinal é calculado para todos os pregões e, em seguida, apenas o último pregão de cada mês é mantido como data de formação.

```python
def calcular_momentum_mensal(precos, dias, skip=SKIP,
inicio_bt=INICIO_BACKTEST, fim=FIM_DADOS):
    indicador = precos.shift(skip) / precos.shift(dias) - 1
    mensal = indicador.groupby(indicador.index.to_period("M")).tail(1)
    return mensal.loc[inicio_bt:fim]
```
=== Seleção Top N e deadband

Regras de seleção da seção 4.1. No deadband, os ativos já presentes na carteira são mantidos enquanto permanecerem entre as primeiras posições do ranking definidas pelo limite, e as vagas restantes são preenchidas pelos mais bem classificados.

```python
def criar_top_n(momentum_mensal, n):
    if not isinstance(n, int) or n < 1:
        raise ValueError('n deve ser inteiro positivo.')
    historico = {}
    for data, linha in momentum_mensal.iterrows():
        ranking = linha.dropna().sort_values(ascending=False,
kind='stable')
        if len(ranking) >= n:
            historico[data] = ranking.head(n).index.tolist()
    return pd.DataFrame.from_dict(historico, orient='index',
                                  columns=[f'Ativo {i}' for i in
range(1, n + 1)])

def criar_deadband(momentum_mensal, limite, n=5):
    if not isinstance(n, int) or not isinstance(limite, int) or n < 1
or limite < n:
        raise ValueError('Use limite inteiro >= n >= 1.')
    carteira, historico = [], {}
    for data, linha in momentum_mensal.iterrows():
        ranking = linha.dropna().sort_values(ascending=False,
kind='stable')
        if len(ranking) < n:
            continue
        permitidos = ranking.head(limite).index
        carteira = [ativo for ativo in carteira if ativo in
permitidos]
        for ativo in ranking.index:
            if len(carteira) == n:
                break
            if ativo not in carteira:
                carteira.append(ativo)
        historico[data] = carteira.copy()
    return pd.DataFrame.from_dict(historico, orient='index',
                                  columns=[f'Ativo {i}' for i in
range(1, n + 1)])
```

=== Previsão de Volatilidade

Implementa as equações (3) e (4), da seção 4.3, e a equação (5), da seção 4.4. O modelo é estimado com log-retornos em pontos percentuais, média zero e inovações t de Student; a previsão retornada é a raiz da variância média prevista para os 21 pregões seguintes. Em caso de não convergência, a função retorna valor ausente e a previsão de reserva por EWMA é utilizada.

```python
def garch_forecast(x: pd.Series, model: str, horizon: int, min_obs:
int) -> float:
    x = x.dropna() * 100
    if len(x) < min_obs:
        return np.nan
    try:
        am = arch_model(x, mean="Zero", vol="GARCH", p=1, o=1 if model
== "gjr" else 0, q=1,
                        dist="t", rescale=False)
        res = am.fit(disp="off", show_warning=False)
        if res.convergence_flag != 0:
            return np.nan
        var_path = res.forecast(horizon=horizon,
reindex=False).variance.values[-1]
        return float(np.sqrt(var_path.mean()) / 100)
    except Exception:

return `np.nan` ```

=== Ponderação pelo inverso da volatilidade prevista

Implementa a equação (6), da seção 4.5. Os ativos são os mesmos da seleção com pesos iguais; apenas os pesos mudam.

```python
def criar_pesos_vol(carteira, sigma, universo):
    pesos = pd.DataFrame(0.0, index=carteira.index, columns=universo)
    n_faltas = 0
    for data, linha in carteira.iterrows():
        ativos = linha.dropna().tolist()
        if not ativos or len(set(ativos)) != len(ativos):
            raise ValueError(f"Carteira vazia ou com duplicatas em {data}.")
        s = sigma.loc[data, ativos].astype(float).where(lambda x: x > 0)
        if s.isna().any():
            n_faltas += int(s.isna().sum())
            s = s.fillna(s.median() if s.notna().any() else 1.0)
        w = 1.0 / s
        pesos.loc[data, ativos] = (w / w.sum()).values
    if n_faltas:
        print(f"[pesos] {n_faltas} σ^ ausentes substituídos pela mediana da carteira")
    return pesos
```

=== Backtest, custos e índide de sharpe

Implementa a equação (1), da seção 2, as equações (7) e (8), da seção 5.2, e a equação (9), da seção 5.4. A ordem gerada no último pregão do mês é executada no pregão seguinte (deslocamento de um pregão em `ordens`), conforme a seção 5.1. Entre execuções, os pesos evoluem com os retornos dos ativos, e o turnover é registrado no dia da ordem.

```python
def backtest(pesos_alvo, retornos, inicio, fim):
    r_periodo = retornos.loc[inicio:fim]
    if r_periodo.empty or not retornos.index.is_monotonic_increasing or retornos.index.has_duplicates:
        raise ValueError('Retornos vazios ou datas fora de ordem/duplicadas.')
    if not pesos_alvo.columns.equals(retornos.columns):
        raise ValueError('Colunas dos pesos e retornos devem coincidir.')
    if pesos_alvo.index.has_duplicates or not pesos_alvo.index.isin(r_periodo.index).all():
        raise ValueError('Sinais duplicados ou fora dos pregões do backtest.')
    if (not np.isfinite(pesos_alvo.to_numpy()).all() or (pesos_alvo < 0).any().any()
            or not np.allclose(pesos_alvo.sum(axis=1), 1)):
        raise ValueError('Pesos devem ser finitos, não negativos e somar um.')
    ordens = pesos_alvo.reindex(r_periodo.index).shift(1)
    pesos_atuais = pd.Series(0.0, index=retornos.columns)
    historico = []
    for data, r in r_periodo.iterrows():
        faltantes = r.index[(pesos_atuais > 0) & r.isna)].tolist()```