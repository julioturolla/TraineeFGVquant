import numpy as np
import pandas as pd


def preparar_precos(base, inicio, fim):
    precos = base.copy()
    precos.columns = ['Data'] + [str(c).strip().split('\n')[-1].strip()
                                for c in precos.columns[1:]]
    if precos.columns.duplicated().any():
        raise ValueError('Tickers duplicados após normalização do cabeçalho.')
    precos['Data'] = pd.to_datetime(precos['Data'], errors='coerce')
    precos = precos.dropna(subset=['Data']).set_index('Data').sort_index()
    precos = precos.loc[inicio:fim]
    if precos.index.has_duplicates:
        raise ValueError('Datas duplicadas na planilha.')
    precos = precos.replace('-', np.nan).apply(pd.to_numeric, errors='coerce')
    precos = precos.dropna(how='all').ffill(limit=1)
    if precos.empty or (precos <= 0).any().any() or np.isinf(precos.to_numpy()).any():
        raise ValueError('Base vazia ou com preços não positivos/infinitos.')
    return precos


def criar_top_n(momentum_mensal, n):
    if not isinstance(n, int) or n < 1:
        raise ValueError('n deve ser inteiro positivo.')
    historico = {}
    for data, linha in momentum_mensal.iterrows():
        ranking = linha.dropna().sort_values(ascending=False, kind='stable')
        if len(ranking) >= n:
            historico[data] = ranking.head(n).index.tolist()
    return pd.DataFrame.from_dict(historico, orient='index',
                                  columns=[f'Ativo {i}' for i in range(1, n + 1)])


def criar_deadband(momentum_mensal, limite, n=5):
    if not isinstance(n, int) or not isinstance(limite, int) or n < 1 or limite < n:
        raise ValueError('Use limite inteiro >= n >= 1.')
    carteira, historico = [], {}
    for data, linha in momentum_mensal.iterrows():
        ranking = linha.dropna().sort_values(ascending=False, kind='stable')
        if len(ranking) < n:
            continue
        permitidos = ranking.head(limite).index
        carteira = [ativo for ativo in carteira if ativo in permitidos]
        for ativo in ranking.index:
            if len(carteira) == n:
                break
            if ativo not in carteira:
                carteira.append(ativo)
        historico[data] = carteira.copy()
    return pd.DataFrame.from_dict(historico, orient='index',
                                  columns=[f'Ativo {i}' for i in range(1, n + 1)])


def criar_pesos(carteira, universo):
    pesos = pd.DataFrame(0.0, index=carteira.index, columns=universo)
    for data, linha in carteira.iterrows():
        ativos = linha.dropna().tolist()
        if not ativos or len(set(ativos)) != len(ativos):
            raise ValueError(f'Carteira vazia ou com duplicatas em {data}.')
        if not set(ativos).issubset(pesos.columns):
            raise ValueError(f'Ativo fora do universo em {data}.')
        pesos.loc[data, ativos] = 1.0 / len(ativos)
    return pesos


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
        faltantes = r.index[(pesos_atuais > 0) & r.isna()].tolist()
        if faltantes:
            raise ValueError(f'Retorno ausente em {data.date()}: {faltantes}')
        r = r.fillna(0.0)
        if not np.isfinite(r.to_numpy()).all() or (r < -1).any():
            raise ValueError(f'Retorno inválido em {data}.')
        retorno_dia = float((pesos_atuais * r).sum())
        if retorno_dia <= -1:
            raise ValueError(f'Patrimônio esgotado em {data}.')
        pesos_atuais = pesos_atuais * (1 + r) / (1 + retorno_dia)
        turnover = 0.0
        if ordens.loc[data].notna().all():
            novos_pesos = ordens.loc[data]
            turnover = float((novos_pesos - pesos_atuais).abs().sum())
            pesos_atuais = novos_pesos.copy()
        historico.append({'Data': data, 'Retorno': retorno_dia, 'Turnover': turnover})
    return pd.DataFrame(historico).set_index('Data')


def aplicar_custos(resultado, custo):
    if not np.isfinite(custo) or custo < 0 or (custo * resultado['Turnover'] >= 1).any():
        raise ValueError('Custo inválido ou superior ao patrimônio.')
    return (1 + resultado['Retorno']) * (1 - custo * resultado['Turnover']) - 1


def calcular_sharpe(retornos, pregoes_ano=252):
    volatilidade = retornos.std(ddof=1)
    if not np.isfinite(volatilidade) or volatilidade <= 1e-15:
        return np.nan
    return retornos.mean() / volatilidade * np.sqrt(pregoes_ano)


def calcular_metricas(resultado, custo=0.001, pregoes_ano=252):
    if resultado.empty or resultado[['Retorno', 'Turnover']].isna().any().any():
        raise ValueError('Resultado vazio ou com valores ausentes.')
    r = aplicar_custos(resultado, custo)
    patrimonio = (1 + r).cumprod()
    retorno_anual = patrimonio.iloc[-1] ** (pregoes_ano / len(r)) - 1
    pico = patrimonio.cummax().clip(lower=1.0)
    return {'Retorno anual (%)': retorno_anual * 100,
            'Volatilidade (%)': r.std(ddof=1) * np.sqrt(pregoes_ano) * 100,
            'Sharpe': calcular_sharpe(r, pregoes_ano),
            'Max Drawdown (%)': (patrimonio / pico - 1).min() * 100,
            'Turnover anual': resultado['Turnover'].sum() * pregoes_ano / len(r)}
