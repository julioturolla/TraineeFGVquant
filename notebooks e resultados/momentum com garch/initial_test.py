"""
Momentum 12-1 (Top N / Deadband) com pesos por volatilidade prevista (GARCH).

METODOLOGIA DO MOMENTUM = a do notebook momentums.ipynb, importada de funcoes_momentum.py
(funções extraídas literalmente: preparar_precos, criar_top_n, criar_deadband, criar_pesos,
backtest, aplicar_custos, calcular_sharpe, calcular_metricas). Isso evita divergência:
  - sinal: P[t-21] / P[t-L] - 1, no último pregão do mês (L = 126, 189 ou 252: "6-1","9-1","12-1")
  - seleção: ranking cross-sectional (Top N ou Deadband), carteira só comprada
  - execução: ordem no fechamento do pregão seguinte; pesos "derivam" com os retornos
  - custos: taxa sobre o turnover (compras + vendas); Sharpe com CDI quando fornecido

O QUE ESTE ARQUIVO ACRESCENTA (o GARCH):
  - previsão de volatilidade de cada ativo na data do sinal (GARCH, GJR ou EWMA), usando
    apenas retornos até o fechamento do dia do sinal;
  - pesos da carteira selecionada proporcionais a 1/σ̂ (soma 1), em vez de pesos iguais.
    A seleção dos ativos é IDÊNTICA nos dois esquemas, então a diferença de desempenho
    isola o efeito de dimensionar por volatilidade.
  - Como os pesos somam 1 (sem caixa nem alavancagem), a função backtest do notebook é
    usada sem nenhuma modificação.

PROTOCOLO: por padrão, só dados até 2021-12-31 (treino 2017–2020, validação 2021), como no
notebook. Estender FIM_DADOS usa dados que o notebook reserva como fora da amostra.

Dependências: pip install arch pandas numpy openpyxl matplotlib requests
"""
from __future__ import annotations

import os
import pickle
import re
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model

from funcoes_momentum import (
    aplicar_custos, backtest, calcular_metricas, criar_deadband, criar_pesos,
    criar_top_n, preparar_precos,
)

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------------
# Constantes do notebook
# ----------------------------------------------------------------------------
INICIO_HISTORICO = "2015-01-01"
INICIO_BACKTEST = "2017-01-01"
FIM_DADOS = "2021-12-31"
CUSTOS = (0.0, 0.001, 0.003)
CUSTO_BASE = 0.001
JANELAS = {"6-1": 126, "9-1": 189, "12-1": 252}
SKIP = 21
SELECOES = ("Top 5", "Top 10", "Top 15", "Deadband 7", "Deadband 10")


def definir_periodos(fim_dados: str) -> dict:
    p = {"Treinamento (2017–2020)": ("2017-01-01", "2020-12-31"),
         "Validação (2021)": ("2021-01-01", "2021-12-31")}
    if pd.Timestamp(fim_dados) > pd.Timestamp("2021-12-31"):
        p["Pós-validação (2022+)"] = ("2022-01-01", fim_dados)
    return p


# ----------------------------------------------------------------------------
# 0) Dados: leitura da planilha, CDI
# ----------------------------------------------------------------------------
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{1,9}$")


def localizar_planilha(nome: str = "economatica-3.xlsx") -> Path:
    """Procura 'bases de dados/<nome>' subindo pelas pastas (como no notebook)."""
    p = Path.cwd().resolve()
    while True:
        if (p / "bases de dados" / nome).exists():
            return p / "bases de dados" / nome
        if p == p.parent:
            break
        p = p.parent
    for c in (Path("/mnt/user-data/uploads") / nome, Path(nome)):
        if c.exists():
            return c
    raise FileNotFoundError(f"{nome} não encontrado. Passe o caminho em `path=`.")


def load_data(path, sheet=0) -> pd.DataFrame:
    """Lê planilha Economatica (cabeçalho na linha 4); ticker = última linha do cabeçalho
    (ou nome da aba, se a coluna não trouxer ticker). Só colunas de fechamento; duplicados
    resolvidos mantendo a coluna de maior cobertura."""
    xl = pd.ExcelFile(path)
    sheet_name = xl.sheet_names[sheet] if isinstance(sheet, int) else sheet
    raw = xl.parse(sheet_name, header=None)
    header = raw.iloc[3].astype(str).tolist()[1:]

    tickers, is_price = [], []
    for h in header:
        lines = [x.strip() for x in h.strip().split("\n") if x.strip()]
        tickers.append(lines[-1] if lines and _TICKER_RE.match(lines[-1]) else str(sheet_name))
        is_price.append("fechamento" in h.lower())

    df = raw.iloc[4:, :].copy()
    df.columns = ["Data"] + tickers
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).set_index("Data").sort_index()
    df = df.replace("-", np.nan).apply(pd.to_numeric, errors="coerce")
    df = df[~df.index.duplicated(keep="last")]

    if any(is_price) and not all(is_price):
        print(f"[dados] colunas que não são fechamento removidas: "
              f"{[t for t, ok in zip(tickers, is_price) if not ok]}")
        df = df.loc[:, is_price]
    cols = list(df.columns)
    if len(set(cols)) < len(cols):
        dups = sorted({c for c in cols if cols.count(c) > 1})
        best = {}
        for i, c in enumerate(cols):
            n = int(df.iloc[:, i].notna().sum())
            if c not in best or n > best[c][1]:
                best[c] = (i, n)
        print(f"[dados] tickers duplicados {dups}: mantida a coluna de maior cobertura de cada um")
        df = df.iloc[:, sorted(i for i, _ in best.values())]
    return df


def baixar_cdi(inicio: str, fim: str, cache: str = "bases de dados/cdi_sgs12.csv") -> pd.Series | None:
    """CDI diário (SGS 12 do BCB, em fração ao dia), como no notebook. Usa cache local;
    devolve None (com aviso) se não houver internet nem cache."""
    ini = pd.Timestamp(inicio) - pd.Timedelta(days=45)
    fim_ts = pd.Timestamp(fim)
    if os.path.exists(cache):
        s = pd.read_csv(cache, index_col=0, parse_dates=True).iloc[:, 0]
        if s.index.min() <= ini + pd.Timedelta(days=10) and s.index.max() >= fim_ts - pd.Timedelta(days=10):
            return s.loc[ini:fim_ts]
    try:
        import requests
        partes, a = [], ini
        while a <= fim_ts:  # janelas de 5 anos (a API limita a extensão das consultas)
            b = min(a + pd.DateOffset(years=5) - pd.Timedelta(days=1), fim_ts)
            r = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados",
                             params={"formato": "json", "dataInicial": a.strftime("%d/%m/%Y"),
                                     "dataFinal": b.strftime("%d/%m/%Y")}, timeout=30)
            r.raise_for_status()
            partes.append(pd.DataFrame(r.json()))
            a = b + pd.Timedelta(days=1)
        d = pd.concat(partes)
        d["data"] = pd.to_datetime(d["data"], format="%d/%m/%Y")
        s = (pd.to_numeric(d["valor"]) / 100).groupby(d["data"]).last().sort_index().rename("cdi")
        s.to_csv(cache)
        return s
    except Exception as e:
        print(f"[cdi] não foi possível obter o CDI ({type(e).__name__}); Sharpe será calculado "
              "sem taxa livre de risco. Passe `cdi=` com a série diária para corrigir.")
        return None


# ----------------------------------------------------------------------------
# 1) Sinais de momentum (idênticos ao notebook)
# ----------------------------------------------------------------------------
def calcular_momentum_mensal(precos, dias, skip=SKIP, inicio_bt=INICIO_BACKTEST, fim=FIM_DADOS):
    indicador = precos.shift(skip) / precos.shift(dias) - 1
    mensal = indicador.groupby(indicador.index.to_period("M")).tail(1)
    return mensal.loc[inicio_bt:fim]


def criar_selecao(momentum_mensal, nome: str):
    """'Top 5' -> criar_top_n(5); 'Deadband 7' -> criar_deadband(7, n=5)."""
    tipo, k = nome.split()
    return criar_top_n(momentum_mensal, int(k)) if tipo == "Top" else criar_deadband(momentum_mensal, int(k))


def preparar_dados(path=None, inicio_hist=INICIO_HISTORICO, inicio_bt=INICIO_BACKTEST,
                   fim=FIM_DADOS, exclude=()):
    path = path or localizar_planilha()
    df = load_data(path).drop(columns=list(exclude), errors="ignore")
    base = df.reset_index().rename(columns={df.index.name or "index": "Data"})
    precos = preparar_precos(base, inicio_hist, fim)           # função do notebook
    retornos = precos.pct_change(fill_method=None)
    momentos = {nome: calcular_momentum_mensal(precos, dias, SKIP, inicio_bt, fim)
                for nome, dias in JANELAS.items()}
    datas = momentos["12-1"].index
    print(f"[dados] {precos.shape[1]} ativos | {precos.index.min().date()} a {precos.index.max().date()}"
          f" | {len(datas)} datas de sinal")
    return precos, retornos, momentos, datas


# ----------------------------------------------------------------------------
# 2) Previsão de volatilidade nas datas de sinal (GARCH / GJR / EWMA)
# ----------------------------------------------------------------------------
def ewma_vol(r: pd.DataFrame, lam: float = 0.94) -> pd.DataFrame:
    out = {}
    for c in r.columns:
        x = r[c].dropna()
        out[c] = np.sqrt((x ** 2).ewm(alpha=1 - lam, adjust=False).mean())
    return pd.DataFrame(out).reindex(r.index).ffill(limit=5)


def garch_forecast(x: pd.Series, model: str, horizon: int, min_obs: int) -> float:
    x = x.dropna() * 100
    if len(x) < min_obs:
        return np.nan
    try:
        am = arch_model(x, mean="Zero", vol="GARCH", p=1, o=1 if model == "gjr" else 0, q=1,
                        dist="t", rescale=False)
        res = am.fit(disp="off", show_warning=False)
        if res.convergence_flag != 0:
            return np.nan
        var_path = res.forecast(horizon=horizon, reindex=False).variance.values[-1]
        return float(np.sqrt(var_path.mean()) / 100)
    except Exception:
        return np.nan


def _worker(args):
    a, r, ew_fb, ew_spec, pos, model, param, horizon, min_asset_obs = args
    out = np.full(len(pos), np.nan)
    n_fb = 0
    w = int(param) if model != "ewma" else 756
    for k, p in enumerate(pos):
        x = r[max(0, p + 1 - w): p + 1]                 # só dados até a data do sinal
        if np.isfinite(x).sum() < min_asset_obs:
            continue
        if model == "ewma":
            out[k] = ew_spec[p]
            continue
        s = garch_forecast(pd.Series(x), model, horizon, min_asset_obs)
        if np.isfinite(s):
            out[k] = s
        else:
            out[k] = ew_fb[p]; n_fb += 1                 # fallback EWMA(0.94)
    return a, out, n_fb


def prever_vol(retornos, datas, specs, horizonte=21, min_obs_ativo=252, workers=None,
               cache_path="notebooks e resultados\momentum com garch\cache_vol_mensal.pkl"):
    """Vol diária prevista (média do horizonte) nas `datas`, para cada especificação em `specs`
    (lista de (modelo, parâmetro): ('gjr', 756), ('garch', 504), ('ewma', 0.94)).
    Retorna ({spec: DataFrame[datas x ativos]}, {spec: nº de fallbacks p/ EWMA}).
    Cache incremental em disco (retomável)."""
    logr = np.log1p(retornos)
    pos = [logr.index.get_loc(t) for t in datas]
    fp = (tuple(logr.columns), str(logr.index[0]), str(logr.index[-1]),
          len(datas), str(datas[0]), str(datas[-1]), horizonte, min_obs_ativo)

    cache = {}
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            c = pickle.load(f)
        if c.get("fingerprint") == fp:
            cache = c["specs"]
            print(f"[vol] cache: {sum(s in cache for s in specs)}/{len(specs)} especificações prontas")

    ew_fb = ewma_vol(logr, 0.94)
    n = workers or os.cpu_count() or 1
    for spec in specs:
        if spec in cache:
            continue
        model, param = spec
        t0 = time.time()
        ew_spec = ewma_vol(logr, param) if model == "ewma" else ew_fb
        tasks = [(a, logr[a].values, ew_fb[a].values, ew_spec[a].values, pos, model, param,
                  horizonte, min_obs_ativo) for a in logr.columns]
        if n > 1:
            with ProcessPoolExecutor(min(n, len(tasks))) as ex:
                res = list(ex.map(_worker, tasks))
        else:
            res = [_worker(t) for t in tasks]
        df = pd.DataFrame(index=datas, columns=logr.columns, dtype=float)
        for a, arr, _ in res:
            df[a] = arr
        cache[spec] = (df, sum(r[2] for r in res))
        if cache_path:
            with open(cache_path, "wb") as f:
                pickle.dump({"fingerprint": fp, "specs": cache}, f)
        print(f"[vol] {model}-{param} pronto em {time.time() - t0:.0f}s", flush=True)
    return {s: cache[s][0] for s in specs}, {s: cache[s][1] for s in specs}


# ----------------------------------------------------------------------------
# 3) Pesos: iguais (notebook) vs inverso da vol prevista (GARCH)
# ----------------------------------------------------------------------------
def criar_pesos_vol(carteira, sigma, universo):
    """Mesmos ativos de `carteira`, com peso ∝ 1/σ̂ (som a 1). Se algum σ̂ faltar, usa a mediana
    dos σ̂ disponíveis da carteira (ou pesos iguais se nenhum existir)."""
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
        print(f"[pesos] {n_faltas} σ̂ ausentes substituídos pela mediana da carteira")
    return pesos


def nome_esquema(spec) -> str:
    return "igual" if spec is None else f"{spec[0]}-{spec[1]}"


def executar_backtests(retornos, momentos, sigmas, janelas, selecoes, esquemas,
                       inicio_bt=INICIO_BACKTEST, fim=FIM_DADOS):
    """esquemas: lista com None (pesos iguais, notebook) e/ou specs de vol.
    Retorna {(janela, seleção, esquema): DataFrame[Retorno, Turnover]} e as carteiras."""
    resultados, carteiras = {}, {}
    for jn in janelas:
        for sel in selecoes:
            carteira = criar_selecao(momentos[jn], sel)
            carteiras[(jn, sel)] = carteira
            for esq in esquemas:
                pesos = (criar_pesos(carteira, retornos.columns) if esq is None
                         else criar_pesos_vol(carteira, sigmas[esq], retornos.columns))
                resultados[(jn, sel, nome_esquema(esq))] = backtest(pesos, retornos, inicio_bt, fim)
    return resultados, carteiras


# ----------------------------------------------------------------------------
# 4) Relatório (mesmas métricas do notebook)
# ----------------------------------------------------------------------------
def tabela_metricas(resultados, periodos, cdi=None, custo=CUSTO_BASE):
    tabs = {}
    for per, (ini, fim) in periodos.items():
        tabs[per] = pd.DataFrame({k: calcular_metricas(r.loc[ini:fim], custo, cdi=cdi)
                                  for k, r in resultados.items()}).T
    return tabs


def plot_patrimonio(resultados, periodos, caminho, janela):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cores = {s: f"C{i}" for i, s in enumerate(SELECOES)}
    fig, ax = plt.subplots(1, len(periodos), figsize=(7 * len(periodos), 5))
    ax = np.atleast_1d(ax)
    for a, (per, (ini, fim)) in zip(ax, periodos.items()):
        for (jn, sel, esq), r in resultados.items():
            pat = (1 + aplicar_custos(r.loc[ini:fim], CUSTO_BASE)).cumprod()
            a.plot(pat.index, pat.values, color=cores[sel], ls="--" if esq == "igual" else "-",
                   lw=1.2, label=f"{sel} | {esq}")
        a.set_title(f"{per} — janela {janela}, custo {CUSTO_BASE:.2%}")
        a.set_ylabel("Patrimônio (base 1)"); a.grid(alpha=.3)
    ax[0].legend(fontsize=7, ncol=2)
    plt.tight_layout(); plt.savefig(caminho, dpi=130); plt.close()


def run(path=None, janela="12-1", vol=("gjr", 756), cdi="auto", exclude=(),
        fim=FIM_DADOS, plot_path=None, workers=None, cache_path="cache_vol_mensal.pkl"):
    precos, retornos, momentos, datas = preparar_dados(path, INICIO_HISTORICO, INICIO_BACKTEST, fim, exclude)
    periodos = definir_periodos(fim)
    if isinstance(cdi, str) and cdi == "auto":
        cdi = baixar_cdi(INICIO_BACKTEST, fim)

    sigmas, fb = prever_vol(retornos, datas, [vol], workers=workers, cache_path=cache_path)
    print(f"[vol] {nome_esquema(vol)}: {fb[vol]} previsões caíram para EWMA")

    resultados, carteiras = executar_backtests(retornos, momentos, sigmas, [janela], SELECOES,
                                               [None, vol], INICIO_BACKTEST, fim)
    tabs = tabela_metricas(resultados, periodos, cdi)
    for per, t in tabs.items():
        print(f"\n{per} — custo {CUSTO_BASE:.2%}" + ("" if cdi is not None else "  [Sharpe sem CDI]"))
        print(t.round(3).to_string())

    print("\nΔ Sharpe (pesos por vol − pesos iguais), mesma seleção:")
    for per, t in tabs.items():
        d = {sel: t.loc[(janela, sel, nome_esquema(vol)), "Sharpe"] - t.loc[(janela, sel, "igual"), "Sharpe"]
             for sel in SELECOES}
        print(f"  {per}: " + " | ".join(f"{k}: {v:+.2f}" for k, v in d.items()))
    if plot_path:
        plot_patrimonio(resultados, periodos, plot_path, janela)
    return {"resultados": resultados, "carteiras": carteiras, "metricas": tabs,
            "sigmas": sigmas, "precos": precos, "retornos": retornos}


if __name__ == "__main__":
    # Planilha: procura 'bases de dados/economatica-3.xlsx' nas pastas acima (como no notebook).
    # Ou passe o caminho:  run(path=r"bases de dados\economatica-3.xlsx")
    out = run(janela="12-1", vol=("gjr", 756), plot_path="notebooks e resultados\momentum com garch\momentum_garch_resultado.png")