Comparação de benchmarks — Momentum 12–1 e GJR-GARCH
Projeto: TraineeFGVquant
Notebook analisado: comparacao_benchmarks.ipynb (versão atualizada enviada como comparacao_benchmarks(1).ipynb, com 17 células e saídas salvas)
Períodos: treinamento em 2017–2020; validação em 2021; histórico prévio a partir de 2015 para formar sinais e estimar volatilidade. 2022–2026 não foi utilizado nesta comparação.
Conclusão principal. No experimento de Momentum 12–1, Top 5, a ponderação pela volatilidade prevista por GJR-GARCH(756) reduziu a volatilidade realizada nos dois períodos, porém também diminuiu o retorno, o Sharpe descontado do CDI e o Information Ratio frente aos pesos iguais. O máximo drawdown melhorou no treinamento, mas não na validação, enquanto o turnover aumentou em ambos os períodos. Portanto, não há ganho consistente de eficiência ajustada ao risco com o GJR nesta configuração. Trata-se de evidência descritiva sobre uma aplicação do GJR à alocação; não é uma demonstração de que o modelo seja incapaz de prever volatilidade.

1. Objetivo e desenho do experimento
A pergunta central é: a utilização de volatilidade prevista por GJR-GARCH para definir o tamanho das posições melhora o desempenho de uma carteira selecionada por Momentum no mercado brasileiro?

O experimento distingue duas etapas:
1. Seleção de ativos: escolher mensalmente as cinco ações com maior sinal de Momentum 12–1.
2. Ponderação: distribuir o capital igualmente entre as ações selecionadas (pesos iguais) ou atribuir pesos inversamente proporcionais às previsões de volatilidade (GJR-GARCH).
As duas estratégias utilizam a mesma seleção mensal de cinco ações. Essa estrutura permite examinar especificamente o efeito da regra de ponderação, em vez de misturá-lo com mudanças no critério de seleção. Além das duas versões de Momentum, o notebook compara uma carteira equiponderada do universo de 30 ações, quatro índices de ações e o CDI.
2. Dados, formação das carteiras e premissas
2.1. Bases e períodos
- Ações: 30 papéis extraídos de baseDeDados/economatica-3.xlsx. Após o tratamento, o notebook registra preços de 02/01/2015 a 30/12/2021, com 1.730 datas de preços e 60 datas de sinal.
- Índices de ações: IBOV (Ibovespa), IBXL (IBrX 50), SMLL (índice de small caps) e IDIV (índice de dividendos), exportados da Economatica. A execução registra retornos sem valores ausentes nas datas de comparação entre 2017 e 2021.
- CDI: série diária SGS 12 do Banco Central, expressa em fração do retorno diário. A função baixar_cdi() de initial_test.py utilizou o cache local baseDeDados/cdi_sgs12.csv, recuperado de um commit histórico do próprio repositório. A saída registrada cobre 17/11/2016 a 31/12/2021. O alinhamento com o calendário de pregões utiliza preenchimento para frente (ffill).
- Janelas: 2015–2016 dão histórico para a formação dos sinais; 2017–2020 é o treinamento; 2021 é a validação. O período 2022–2026 permanece fora deste estudo.
2.2. Momentum e execução
O sinal é o retorno acumulado de aproximadamente 12 meses até um mês antes da formação, excluindo o mês mais recente:
\[
M_{i,t}=\frac{P_{i,t-21}}{P_{i,t-252}}-1.
\]
São selecionadas as cinco ações com maior sinal ao fim de cada mês. A ordem é executada no fechamento do próximo pregão e passa a afetar os retornos posteriores; os pesos variam com os preços entre os rebalanceamentos mensais.

A versão Momentum Top 5 (pesos iguais) atribui 20% por ação na formação. A versão Momentum Top 5 + GJR usa as mesmas ações e define:
\[
w_{i,t}^{GJR}=\frac{1/\widehat\sigma_{i,t}}{\sum_{j\in\mathcal C_t}1/\widehat\sigma_{j,t}}.
\]
A configuração solicitada ao código é ("gjr", 756): GJR-GARCH(1,1), janela de 756 pregões, com previsão de volatilidade para ponderar a carteira. O mecanismo de previsão do projeto utiliza distribuição Student-t, média condicional zero e horizonte de 21 pregões. A execução do notebook informa cache de volatilidade carregado (1/1) e zero fallbacks para EWMA. Isso comprova o uso do resultado armazenado, não uma nova reestimação independente do GJR nesta execução. As carteiras são compradas, sem alavancagem ou posições vendidas.
2.3. Benchmarks e custos
A Equiponderada 30 utiliza rebalanceamento mensal e admite ativos com 21 retornos diários consecutivos válidos na data de formação. O primeiro rebalanceamento possui 29 ações elegíveis; a quantidade chega a 30 em outubro de 2017. Essa carteira inicia em caixa até a primeira operação de fevereiro de 2017.

Para as três carteiras implementadas (Momentum igual, Momentum GJR e Equiponderada 30), o custo é 0,10% do volume negociado (custo=0.001, multiplicado pelo turnover). O turnover contabiliza negociações associadas à alteração de pesos. Índices e CDI têm turnover igual a zero no notebook, ou seja, são benchmarks teóricos sem custos de replicação. A comparação não modela spread, slippage, impostos, taxas de administração nem impacto de mercado.
2.4. Indicadores e CDI
O notebook reporta retorno anualizado composto, volatilidade anualizada, máximo drawdown, turnover anual e índice de Sharpe com o CDI como taxa livre de risco. As métricas das carteiras utilizam retornos líquidos dos custos modelados.

A função original calcular_metricas(..., cdi=cdi_diario) chama calcular_sharpe(), que calcula:
\[
S_{CDI}=\frac{\overline{(r_{p,t}-r_{CDI,t})}}{\operatorname{sd}(r_{p,t}-r_{CDI,t})}\sqrt{252}.
\]
Portanto, somente a coluna Sharpe muda quando se passa o CDI para calcular_metricas(); retorno, volatilidade, drawdown e turnover permanecem iguais. As tabelas mais antigas do notebook, calculadas com cdi=None, servem apenas como histórico da construção: as tabelas corretas para a interpretação final são aquelas intituladas “Sharpe com CDI”.
3. Resultados finais — métricas com CDI
As tabelas a seguir reproduzem as saídas da célula que criou tabelas_finais_cdi, após carregar o CDI. Todos os valores de retorno e volatilidade são anualizados; retornos e drawdowns estão em percentual.
3.1. Treinamento — 2017 a 2020
Estratégia	Retorno anual (%)	Volatilidade (%)	Sharpe com CDI	Max drawdown (%)	Turnover anual
Momentum 12–1 Top 5, pesos iguais	48,951	36,387	1,115	−51,292	6,034
Momentum 12–1 Top 5 + GJR	38,234	33,885	0,950	−45,915	7,101
Equiponderada 30	31,130	27,973	0,894	−47,108	1,060
SMLL	26,816	28,667	0,764	−51,693	0,000
IDIV	20,655	25,399	0,629	−40,931	0,000
IBOV	18,974	28,161	0,544	−46,816	0,000
IBXL	18,474	28,677	0,525	−47,675	0,000


3.2. Validação — 2021
Estratégia	Retorno anual (%)	Volatilidade (%)	Sharpe com CDI	Max drawdown (%)	Turnover anual
Momentum 12–1 Top 5, pesos iguais	24,656	33,602	0,695	−23,028	5,746
Momentum 12–1 Top 5 + GJR	22,197	33,244	0,639	−23,756	6,567
Equiponderada 30	1,249	21,167	−0,040	−18,479	0,851
IDIV	−6,538	19,059	−0,486	−15,993	0,000
IBXL	−10,742	21,474	−0,623	−23,428	0,000
IBOV	−12,153	20,987	−0,718	−22,941	0,000
SMLL	−16,496	25,528	−0,747	−31,305	0,000


Atenção à sequência do notebook: essas tabelas foram calculadas antes de inserir o CDI em resultados_benchmarks. Por isso, contêm sete estratégias, embora o gráfico final contenha oito curvas, incluindo o CDI. Não há uma linha de retorno anualizado do CDI impressa nessas tabelas; o README não atribui ao CDI um retorno numérico que não foi reportado ali. Se o CDI for incluído em uma futura reexecução das tabelas, seu Sharpe em excesso a ele mesmo será indefinido (NaN), pois a variância do excesso é zero.
4. Contribuição incremental do GJR-GARCH: comparação direta
Esta é a comparação decisiva para a hipótese do trabalho, pois mantém o sinal Momentum 12–1, o conjunto Top 5 e a regra de negociação e muda a ponderação.
Indicador	Pesos iguais 2017–2020	GJR 2017–2020	Efeito GJR	Pesos iguais 2021	GJR 2021	Efeito GJR
Retorno anual (%)	48,951	38,234	−10,717 p.p.	24,656	22,197	−2,459 p.p.
Volatilidade (%)	36,387	33,885	−2,502 p.p.	33,602	33,244	−0,358 p.p.
Sharpe com CDI	1,115	0,950	−0,165	0,695	0,639	−0,056
Max drawdown (%)	−51,292	−45,915	melhora 5,377 p.p.	−23,028	−23,756	piora 0,728 p.p.
Turnover anual	6,034	7,101	+1,067	5,746	6,567	+0,821


4.1. Redução da volatilidade: benefício real, mas insuficiente
No treinamento, a volatilidade do Momentum caiu de 36,387% para 33,885% com o GJR, redução de 2,502 pontos percentuais (cerca de 6,9% em termos relativos). Na validação, caiu apenas 0,358 ponto percentual, de 33,602% para 33,244% (aproximadamente 1,1% em termos relativos).

Essa evidência indica que a regra de pesos inversos à volatilidade conseguiu reduzir a volatilidade realizada da carteira em ambos os períodos. Não comprova, isoladamente, que as previsões GJR foram mais precisas que as de outros estimadores: essa pergunta exigiria comparar erro preditivo, por exemplo, via QLIKE ou contra volatilidade realizada.
4.2. Retorno e Sharpe: a proteção teve custo econômico
O retorno anualizado caiu 10,717 p.p. no treinamento e 2,459 p.p. em 2021. Mesmo descontando o CDI, a versão com pesos iguais continuou apresentando o maior Sharpe: 1,115 versus 0,950 no treinamento e 0,695 versus 0,639 em 2021.

Assim, a diminuição da volatilidade não compensou a perda de retorno por unidade de risco excedente ao CDI. Isso é especialmente relevante porque a conclusão não depende de se usar Sharpe com taxa livre de risco zero: ela se mantém após incorporar o CDI histórico.

Uma possível explicação econômica — ainda não testada diretamente — é que a ponderação inversa à volatilidade reduz a participação justamente de algumas ações que combinam alto Momentum com alta volatilidade e retornos posteriores expressivos. Seria necessário examinar os pesos mensais, as contribuições por ativo e as covariâncias para testar tal mecanismo. Não se deve tratá-lo como causa já demonstrada.
4.3. Drawdown e turnover: proteção não persistente, mais negociação
Durante 2017–2020, o maior drawdown melhorou de −51,292% para −45,915%, uma proteção de 5,377 p.p.. Na validação de 2021, porém, o GJR teve drawdown ligeiramente pior (−23,756%, contra −23,028%). Portanto, a vantagem de proteção contra perdas extremas não foi estável entre as amostras.

O turnover anual aumentou de 6,034 para 7,101 no treinamento (aproximadamente 17,7% a mais) e de 5,746 para 6,567 em 2021 (aproximadamente 14,3% a mais). Como a simulação aplica custo por volume transacionado, esse aumento penaliza a versão GJR e amplia sua sensibilidade a custos reais de execução. Os resultados apresentados já consideram o custo modelado de 0,10%; o notebook não isola quanto da perda de retorno se deve especificamente ao custo adicional, algo que poderia ser medido por uma análise de custos decompostos.
4.4. O que os gráficos finais mostram
Os gráficos finais de patrimônio-base 100, agora com a oitava curva referente ao CDI, reforçam a leitura das tabelas:
- 2017–2020: a carteira Momentum com pesos iguais acumula patrimônio muito superior ao GJR e aos índices. A diferença entre as duas versões amplia-se sobretudo ao longo da recuperação posterior ao choque de março de 2020. O CDI segue trajetória de crescimento suave; serve como contraponto de baixo risco, não como uma carteira acionária comparável em volatilidade.
- 2021: as curvas de Momentum com pesos iguais e GJR têm movimentos muito próximos, ambas encerram o ano acima dos índices de ações e da linha do CDI, mas os pesos iguais permanecem à frente. O CDI aparece com crescimento progressivo, enquanto a maior parte dos índices de ações termina abaixo de 100.
Os patrimônios são reiniciados em R$ 100 no começo de cada período e incorporam custos apenas nas carteiras com turnover. As curvas dos índices e do CDI são referências teóricas sem custos; o gráfico não mede ganho líquido acima do CDI por meio de subtração de patrimônios, apenas mostra as trajetórias no mesmo eixo.
5. Exposição ao Ibovespa: beta, correlação e eficiência ativa
Além do Sharpe, o notebook avaliou o comportamento relativo ao IBOV. Essas medidas continuam válidas após incluir o CDI porque usam retorno ativo em relação ao Ibovespa, não retorno excedente à taxa livre de risco.
Período	Estratégia	Beta IBOV	Correlação IBOV	Retorno ativo anualizado (%)	Tracking error (%)	Information Ratio
2017–2020	Momentum igual	1,040	0,805	25,273	21,605	1,170
2017–2020	Momentum GJR	0,958	0,796	16,879	20,529	0,822
2017–2020	Equiponderada 30	0,961	0,967	9,692	7,189	1,348
2021	Momentum igual	1,085	0,678	38,418	24,779	1,550
2021	Momentum GJR	1,083	0,683	36,306	24,330	1,492
2021	Equiponderada 30	0,975	0,967	14,228	5,430	2,620


O Information Ratio anualizado usa o retorno ativo diário da carteira em relação ao Ibovespa, dividido pelo seu tracking error:
\[
IR = \frac{\overline{r_{p,t}-r_{IBOV,t}}}{\operatorname{sd}(r_{p,t}-r_{IBOV,t})}\sqrt{252}.
\]
O retorno ativo da tabela é a diferença média diária anualizada aritmeticamente, não a simples diferença entre os retornos anuais compostos da seção 3.

Interpretação específica do GJR: o beta cai de 1,040 para 0,958 no treinamento, mas permanece praticamente igual em 2021 (1,085 versus 1,083). Logo, reduzir a volatilidade total não necessariamente diminui a exposição sistemática ao mercado. O tracking error cai um pouco em ambos os períodos, porém o retorno ativo também diminui, resultando em IR inferior para o GJR (1,170 → 0,822 no treinamento; 1,550 → 1,492 em 2021).

A Equiponderada 30 apresenta IR maior que ambas as versões de Momentum, especialmente em 2021 (2,620), pois acompanha muito de perto o IBOV (correlação de 0,967) e apresenta tracking error pequeno. Isso não significa maior retorno absoluto ou maior Sharpe: o IR mede retorno ativo por unidade de desvio em relação ao benchmark, enquanto o Sharpe utiliza o CDI como referência de retorno livre de risco.
6. Interpretação econômica: o que pode e o que não pode ser concluído
Achados sustentados pelos resultados
1. O sinal Momentum produziu carteiras com retornos e Sharpes superiores aos quatro índices de ações e à Equiponderada 30 nos dois períodos examinados.
2. O GJR-GARCH(756) diminuiu a volatilidade realizada, mas não melhorou o Sharpe com CDI nem o Information Ratio do Momentum Top 5.
3. A redução de drawdown no treinamento não se repetiu na validação; o GJR apresentou turnover superior nos dois períodos.
4. Os resultados relativos a IBOV sugerem que o Momentum assume um perfil de risco diferente do mercado amplo, mas não demonstram por si só geração de alfa estatisticamente significativo.
Hipóteses ainda não verificadas
- Se a previsão GJR é estatisticamente mais precisa que a volatilidade histórica simples, EWMA ou GARCH simétrico.
- Se a perda de retorno do GJR decorre de menores pesos nas ações vencedoras, de maior custo de giro, de concentração/correlação ou da interação entre esses mecanismos.
- Se a diferença de Sharpe ou retorno entre as duas regras é estatisticamente significativa.
- Se o resultado persistiria em um universo historicamente investível e livre de viés de sobrevivência ou no teste reservado de 2022–2026.
A interpretação adequada é, portanto, restrita à regra de alocação examinada: neste backtest, aplicar pesos inversos à volatilidade prevista pelo GJR não superou manter pesos iguais entre as cinco ações selecionadas por Momentum. Isso é diferente de concluir que o uso de GARCH é improdutivo em geral.
7. Limitações metodológicas
1. Uma especificação GJR específica: apenas Momentum 12–1 / Top 5 / ("gjr", 756) nesta comparação final; resultados não generalizam automaticamente a outras combinações.
2. Seleção retrospectiva do universo: as 30 ações podem introduzir survivorship bias e viés de seleção ex post; a elegibilidade dinâmica de 21 dias não elimina o problema.
3. Validação curta: 2021 contém apenas um ano e já houve exploração de parametrizações em etapas anteriores do projeto. Deve-se evitar otimizar retrospectivamente a estratégia para 2021 e depois chamá-lo de teste independente.
4. Benchmarks sem custos: índices e CDI têm turnover zero; não se consideram despesas e fricções da aplicação efetiva nesses instrumentos.
5. Sem teste formal da diferença de desempenho: resultados de Sharpe, IR e drawdown são descritivos; não há intervalo de confiança nem teste de superioridade estatística.
6. Sem alfa CAPM: beta e correlação foram calculados, mas não há saída de regressão com alfa, p-valor ou HAC no notebook atualizado. O uso do CDI no Sharpe não equivale à estimação de alfa CAPM.
7. Sem avaliação direta da qualidade das previsões: volatilidade realizada menor da carteira não comprova menor erro de previsão do GJR.
8. Cache reutilizado: o notebook informa cache: 1/1 especificações prontas e zero fallback; não comprova reestimação do GJR nessa execução. É necessário auditar o cache para reprodutibilidade plena.
9. Exposição e calendários: a Equiponderada 30 começa a operar após a primeira formação, enquanto os índices e o CDI já apresentam retornos no início de 2017. As datas foram alinhadas na análise, mas não se padronizou o início efetivo de exposição para todos os comparadores.
10. Fonte dos índices: é necessário preservar a exportação Economatica e documentar seus ajustes e convenções de séries (por exemplo, preços versus retorno total), para garantir comparabilidade econômica.
8. Organização dos arquivos e reprodução
Estrutura utilizada pelo código, com o README colocado ao lado do notebook:
TraineeFGVquant/
├── baseDeDados/
│   ├── economatica-3.xlsx
│   ├── indices_benchmark_limpo.xlsx
│   └── cdi_sgs12.csv                  # cache histórico SGS 12
├── cache_vol_mensal.pkl               # cache de previsões do GJR
└── notebooks e resultados/
    ├── momentum com garch/
    │   ├── initial_test.py
    │   └── funcoes_momentum.py
    └── benchmarcks/
        ├── comparacao_benchmarks.ipynb
        └── README.md
Dependências: Python com pandas, numpy, openpyxl, matplotlib, arch e requests, compatíveis com o kernel Jupyter. O notebook encontra a raiz do repositório procurando baseDeDados/economatica-3.xlsx e importa os módulos existentes de notebooks e resultados/momentum com garch/.

Para executar em outra máquina:
- A célula dos índices contém o caminho absoluto C:\Users\julio\Downloads\economatica (1).xlsx. Para reprodução, use a exportação bruta local ou leia diretamente o baseDeDados/indices_benchmark_limpo.xlsx já gerado, via pd.read_excel(..., index_col=0, parse_dates=True). Esse arquivo limpo não deve ser processado novamente com load_data(), que espera o formato de exportação original da Economatica.
- A célula inicial define arquivo dentro do laço de busca da raiz. Para evitar erro caso o diretório de execução já seja a própria raiz, recomenda-se definir arquivo = raiz / "baseDeDados" / "economatica-3.xlsx" depois do laço, incondicionalmente.
- O CDI é carregado pela função já existente baixar_cdi() a partir do cache; se ausente, o notebook recupera o CSV do commit histórico fixado, evitando depender da API do BCB. O CSV deve permanecer disponível para a reprodução offline.
- O GJR exige que o cache de previsões seja compatível com os dados e parâmetros ou que seja possível reestimá-lo com a biblioteca arch.
- Execute as células na ordem. A tabela de Sharpe com CDI está na célula que cria tabelas_finais_cdi; a célula posterior adiciona o CDI ao dicionário de benchmarks e a última gera os dois gráficos com oito curvas.
Estado da verificação
Nesta atualização, foram inspecionadas as 17 células, as saídas numéricas salvas e os dois gráficos finais do notebook atualizado. Em uma verificação anterior da versão original, as métricas da carteira Momentum de pesos iguais e da Equiponderada 30 foram reproduzidas com a base de ações. Não se afirma aqui que o GJR, os índices ou a nova série CDI tenham sido reestimados ou recalculados independentemente nesta revisão. Os números das tabelas com CDI acima foram transcritos das saídas efetivamente registradas no arquivo enviado.
9. Conclusão e próximos testes
A comparação final reforça que o efeito econômico mais relevante foi a seleção por Momentum, enquanto a ponderação por volatilidade prevista via GJR-GARCH(756) reduziu parte do risco, mas não acrescentou eficiência ajustada ao risco segundo Sharpe com CDI e Information Ratio. A proteção de drawdown foi observada em treinamento, mas não em 2021; em contrapartida, o turnover foi sistematicamente maior.

A próxima etapa mais informativa não é apenas reestimar o mesmo GJR: é comparar pesos iguais, volatilidade histórica simples, EWMA, GARCH simétrico e GJR, mantendo idênticos o sinal de Momentum, a seleção, as datas e os custos. Em paralelo, vale decompor retorno e turnover por ação, avaliar a precisão preditiva da volatilidade e examinar a incerteza estatística das diferenças. Por fim, os parâmetros devem ser congelados antes de abrir a amostra reservada de 2022–2026.
Proveniência: comparacao_benchmarks(1).ipynb enviado para atualização do README; resultados extraídos das saídas salvas do notebook. O CDI foi incorporado ao Sharpe e aos gráficos finais. A ausência de CDI como linha das tabelas é consequência da ordem de execução das células, não uma exclusão deliberada da comparação visual.
