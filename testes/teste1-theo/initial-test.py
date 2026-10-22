"""
Momentum ajustado à volatilidade + GARCH, aplicado à planilha dados_teste.xlsx.

Base (Economatica, fechamento ajustado a proventos, moeda original):
    PETR4 (BRL) | FXI, EWJ, SPY, USO, VNQ (USD)

Tratamentos específicos desta base:
  - "-" vira NaN (feriados de cada mercado e períodos sem negociação).
  - Retornos são calculados sobre as observações válidas de CADA ativo, então um
    feriado nos EUA não vira "retorno zero" artificial (o que subestimaria a vol).
  - Ativos com cobertura ruim são removidos automaticamente (a FXI tem só 366
    observações esparsas desde 2013 e termina em ago/2026: inviável para GARCH).
  - A amostra começa em `start` (default 1999) para evitar o período de
    hiperinflação do PETR4 (preços ~1e-10 e retornos de +50% ao dia).
  - A planilha NÃO traz CDI nem câmbio. Ambos são opcionais:
        * `fx` (USD/BRL diário) converte os ativos em dólar para reais;
        * `cdi` (retorno diário) rende o caixa; sem ele, usa `cash_rate_anual` fixo.
    Sem `fx`, o PETR4 (BRL) e os demais (USD) ficam em moedas diferentes: o código
    roda, mas a carteira NÃO é uma carteira em reais. Veja o aviso no console.

Dependências: pip install arch statsmodels pandas numpy openpyxl matplotlib
"""
from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
import statsmodels.api as sm
from arch import arch_model

warnings.filterwarnings("ignore")
ANN = 252
PATH_XLSX = "bases de dados\dados_teste.xlsx"


# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Config:
    start: str = "1999-01-01"         # início da amostra (evita hiperinflação do PETR4)
    vol_model: str = "gjr"            # "garch" | "gjr" | "ewma"
    garch_window: int = 756           # janela de estimação (~3 anos)
    refit_every: int = 21             # reestima e rebalanceia a cada ~1 mês
    horizon: int = 21                 # horizonte da previsão de vol (dias)
    min_obs: int = 504                # histórico mínimo antes do primeiro sinal
    min_asset_obs: int = 252          # histórico mínimo por ativo na janela
    min_coverage: float = 0.80        # cobertura mínima para o ativo entrar no universo
    mom_lookbacks: tuple = (21, 63, 126, 252)
    target_vol: float = 0.10          # vol anual alvo da carteira
    max_leverage: float = 1.0         # exposição bruta máxima
    long_only: bool = True            # False => permite vendido
    corr_halflife: int = 63
    corr_shrink: float = 0.2
    cost_bps: float = 5.0             # custo por unidade de turnover
    cash_rate_anual: float = 0.0      # usado só se `cdi` não for fornecido


# ----------------------------------------------------------------------------
# 0) Carga e preparação dos dados
# ----------------------------------------------------------------------------
def load_data(path: str = PATH_XLSX) -> pd.DataFrame:
    """Lê a planilha Economatica (cabeçalho na linha 4; tickers no fim do título)."""
    raw = pd.read_excel(path, sheet_name=0, header=None)
    header = raw.iloc[3].astype(str)
    # 1ª coluna de preço é o PETR4 (sem sufixo); as demais trazem o ticker na última linha
    tickers = ["PETR4"] + [h.strip().split("\n")[-1] for h in header.iloc[2:]]
    df = raw.iloc[4:, :].copy()
    df.columns = ["Data"] + tickers
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).set_index("Data").sort_index()
    df = df.replace("-", np.nan).apply(pd.to_numeric, errors="coerce")
    return df[~df.index.duplicated(keep="last")]


def select_assets(prices: pd.DataFrame, min_coverage: float) -> pd.DataFrame:
    """Remove ativos cuja cobertura (obs válidas / dias úteis entre 1ª e última) é baixa."""
    keep = []
    for c in prices.columns:
        s = prices[c].dropna()
        if len(s) < 500:
            print(f"[universo] {c}: removido ({len(s)} obs)")
            continue
        n_bdays = len(pd.bdate_range(s.index[0], s.index[-1]))
        cov = len(s) / n_bdays
        if cov < min_coverage:
            print(f"[universo] {c}: removido (cobertura {cov:.0%}, {len(s)} obs)")
        else:
            keep.append(c)
    return prices[keep]


def prepare(prices: pd.DataFrame, cfg: Config, fx: pd.Series | None = None,
            brl_assets: tuple = ("PETR4",)):
    """Retorna preços (opcionalmente em BRL), retornos simples e log, e log-preço ffill."""
    prices = prices.loc[cfg.start:]
    prices = select_assets(prices, cfg.min_coverage)

    if fx is not None:
        fx = fx.reindex(prices.index).ffill()
        usd = [c for c in prices.columns if c not in brl_assets]
        prices = prices.copy()
        prices[usd] = prices[usd].mul(fx, axis=0)
    else:
        print("[aviso] sem série de câmbio: PETR4 em BRL e os demais em USD. "
              "Passe `fx` (USD/BRL) para obter uma carteira em reais.")

    simple = pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)
    for c in prices.columns:  # retorno entre observações válidas do próprio ativo
        simple[c] = prices[c].dropna().pct_change().reindex(prices.index)
    logr = np.log1p(simple)
    logp = np.log(prices).ffill(limit=5)  # só para o momentum (atravessa feriados)
    return prices, simple, logr, logp


# ----------------------------------------------------------------------------
# 1) Previsão de volatilidade
# ----------------------------------------------------------------------------
def ewma_vol(r: pd.DataFrame, lam: float = 0.94) -> pd.DataFrame:
    """Vol diária EWMA (benchmark e fallback). Ignora NaN dos feriados."""
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
        am = arch_model(x, mean="Zero", vol="GARCH", p=1,
                        o=1 if model == "gjr" else 0, q=1, dist="t", rescale=False)
        res = am.fit(disp="off", show_warning=False)
        if res.convergence_flag != 0:
            return np.nan
        var_path = res.forecast(horizon=horizon, reindex=False).variance.values[-1]
        return float(np.sqrt(var_path.mean()) / 100)
    except Exception:
        return np.nan


def build_vol_forecasts(logr: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    dates = logr.index
    reb = dates[cfg.min_obs :: cfg.refit_every]
    ew = ewma_vol(logr)
    out = pd.DataFrame(index=reb, columns=logr.columns, dtype=float)
    n_fallback = 0

    for t in reb:
        i = dates.get_loc(t)
        win = logr.iloc[max(0, i + 1 - cfg.garch_window) : i + 1]
        for c in logr.columns:
            s = np.nan
            if cfg.vol_model != "ewma":
                s = garch_forecast(win[c], cfg.vol_model, cfg.horizon, cfg.min_asset_obs)
            if np.isnan(s) and win[c].notna().sum() >= cfg.min_asset_obs:
                s = ew.loc[t, c]
                n_fallback += cfg.vol_model != "ewma"
            out.loc[t, c] = s
    if cfg.vol_model != "ewma":
        print(f"[vol] fallback para EWMA em {n_fallback} de {out.notna().sum().sum()} previsões")
    return out


# ----------------------------------------------------------------------------
# 2) Momentum ajustado à vol (t-stat), vários lookbacks
# ----------------------------------------------------------------------------
def momentum_tstat(logp: pd.DataFrame, sigma: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    scores = []
    for L in cfg.mom_lookbacks:
        cum = (logp - logp.shift(L)).reindex(sigma.index)
        scores.append(cum / (sigma * np.sqrt(L)))
    return sum(scores) / len(scores)


# ----------------------------------------------------------------------------
# 3) Pesos: momentum = direção, vol = tamanho
# ----------------------------------------------------------------------------
def ewma_corr(win: pd.DataFrame, halflife: int, shrink: float) -> np.ndarray:
    n = len(win)
    w = 0.5 ** (np.arange(n)[::-1] / halflife)
    C = np.atleast_2d(np.cov(win.fillna(0).values.T, aweights=w))
    d = np.sqrt(np.diag(C))
    d[d == 0] = 1.0
    R = C / np.outer(d, d)
    return (1 - shrink) * R + shrink * np.eye(len(R))


def build_weights(logr, logp, sigma, cfg: Config, use_momentum: bool = True) -> pd.DataFrame:
    mom = momentum_tstat(logp, sigma, cfg)
    W = pd.DataFrame(0.0, index=sigma.index, columns=sigma.columns)

    for t in sigma.index:
        s, m = sigma.loc[t], mom.loc[t]
        ok = s.notna() & m.notna()
        if ok.sum() == 0:
            continue
        cols = ok[ok].index

        direction = np.sign(m[cols]) if use_momentum else pd.Series(1.0, index=cols)
        if cfg.long_only:
            direction = direction.clip(lower=0)
        if (direction != 0).sum() == 0:
            continue

        raw = (direction / s[cols]).values
        i = logr.index.get_loc(t)
        win = logr[cols].iloc[max(0, i + 1 - 4 * cfg.corr_halflife) : i + 1]
        R = ewma_corr(win, cfg.corr_halflife, cfg.corr_shrink)
        sig = s[cols].values
        cov = R * np.outer(sig, sig) * ANN
        port_vol = np.sqrt(raw @ cov @ raw)
        if port_vol <= 0:
            continue

        w = raw * cfg.target_vol / port_vol
        gross = np.abs(w).sum()
        if gross > cfg.max_leverage:
            w *= cfg.max_leverage / gross
        W.loc[t, cols] = w
    return W


# ----------------------------------------------------------------------------
# 4) Backtest (pesos em t valem a partir de t+1)
# ----------------------------------------------------------------------------
def cash_series(index: pd.DatetimeIndex, cfg: Config, cdi: pd.Series | None) -> pd.Series:
    if cdi is not None:
        return cdi.reindex(index).fillna(0.0)
    return pd.Series((1 + cfg.cash_rate_anual) ** (1 / ANN) - 1, index=index)


def backtest(simple, W, cash, cfg: Config):
    Wd = W.reindex(simple.index).ffill().shift(1).loc[W.index[0]:].fillna(0.0)
    r = simple.loc[Wd.index].fillna(0.0)   # feriado do ativo => sem retorno no dia
    c = cash.reindex(Wd.index)
    turnover = Wd.diff().abs().sum(axis=1).fillna(0.0)
    ret = (Wd * r).sum(axis=1) + (1.0 - Wd.sum(axis=1)) * c - turnover * cfg.cost_bps / 1e4
    return ret, turnover, Wd


# ----------------------------------------------------------------------------
# 5) Métricas e regressão
# ----------------------------------------------------------------------------
def metrics(ret, cash, target_vol=None, turnover=None) -> dict:
    c = cash.reindex(ret.index).fillna(0.0)
    ex = ret - c
    eq = (1 + ret).cumprod()
    out = {
        "ret_anual": eq.iloc[-1] ** (ANN / len(ret)) - 1,
        "vol_anual": ret.std() * np.sqrt(ANN),
        "sharpe": ex.mean() / ex.std() * np.sqrt(ANN) if ex.std() > 0 else np.nan,
        "max_drawdown": (eq / eq.cummax() - 1).min(),
    }
    if target_vol is not None:
        out["erro_vol_target"] = ((ret.rolling(63).std() * np.sqrt(ANN)) - target_vol).abs().mean()
    if turnover is not None:
        out["turnover_anual"] = turnover.mean() * ANN
    return out


def factor_regression(ret, cash, factors: pd.DataFrame):
    c = cash.reindex(ret.index).fillna(0.0)
    X = sm.add_constant(factors.reindex(ret.index).fillna(0.0).sub(c, axis=0))
    res = sm.OLS(ret - c, X, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    print(f"alpha anualizado: {res.params['const'] * ANN:.2%} (t={res.tvalues['const']:.2f})")
    print(res.params.drop("const").rename("beta").round(3).to_string())
    return res


# ----------------------------------------------------------------------------
# 6) Escolha de modelo/janela por QLIKE (walk-forward)
# ----------------------------------------------------------------------------
def qlike(rv: pd.DataFrame, fc_var: pd.DataFrame) -> float:
    rv, fc_var = rv.where(rv > 0), fc_var.where(fc_var > 0)
    ratio = rv / fc_var
    return float((ratio - np.log(ratio) - 1).stack().mean())


def evaluate_vol_models(logr, cfg, models=("garch", "gjr", "ewma"), windows=(504, 756, 1008)):
    """Proxy de variância realizada: média de r² nos `horizon` dias seguintes."""
    rv = (logr ** 2).rolling(cfg.horizon, min_periods=cfg.horizon // 2).mean().shift(-cfg.horizon)
    rows = []
    for m in models:
        for w in (windows if m != "ewma" else (0,)):
            c = replace(cfg, vol_model=m, garch_window=w or cfg.garch_window)
            fc = build_vol_forecasts(logr, c)
            rows.append({"modelo": m, "janela": w, "qlike": qlike(rv.reindex(fc.index), fc ** 2)})
    return pd.DataFrame(rows).sort_values("qlike").reset_index(drop=True)


# ----------------------------------------------------------------------------
# 7) Execução
# ----------------------------------------------------------------------------
def run(prices_raw: pd.DataFrame, cfg: Config = Config(), fx=None, cdi=None,
        factor_cols=("SPY",), plot_path: str | None = None):
    prices, simple, logr, logp = prepare(prices_raw, cfg, fx)
    print(f"[universo] {list(prices.columns)} | {prices.index[0].date()} a {prices.index[-1].date()}")

    t0 = time.time()
    sigma = build_vol_forecasts(logr, cfg)
    print(f"[vol] {len(sigma)} rebalanceamentos em {time.time() - t0:.0f}s")

    cash = cash_series(prices.index, cfg, cdi)

    W = build_weights(logr, logp, sigma, cfg, use_momentum=True)
    strat, turn, Wd = backtest(simple, W, cash, cfg)

    W_naive = build_weights(logr, logp, sigma, cfg, use_momentum=False)
    naive, turn_n, _ = backtest(simple, W_naive, cash, cfg)

    cash_ret = cash.reindex(strat.index)
    table = pd.DataFrame({
        "Estratégia": metrics(strat, cash, cfg.target_vol, turn),
        "Ingênua (sem momentum)": metrics(naive, cash, cfg.target_vol, turn_n),
        "Caixa": metrics(cash_ret, cash),
    })
    print("\n" + table.round(4).to_string())

    print("\nRegressão da estratégia contra fatores:")
    factor_regression(strat, cash, simple[list(factor_cols)])

    if plot_path:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                               gridspec_kw={"height_ratios": [3, 2]})
        (1 + strat).cumprod().plot(ax=ax[0], label="Estratégia")
        (1 + naive).cumprod().plot(ax=ax[0], label="Ingênua")
        ax[0].set_yscale("log"); ax[0].legend(); ax[0].set_title("Crescimento de 1 (escala log)")
        Wd.plot.area(ax=ax[1], linewidth=0); ax[1].set_title("Pesos"); ax[1].legend(loc="upper left", ncol=5)
        plt.tight_layout(); plt.savefig(plot_path, dpi=130)

    return {"weights": W, "sigma": sigma, "strategy": strat, "naive": naive,
            "turnover": turn, "table": table, "prices": prices}


if __name__ == "__main__":
    prices_raw = load_data(PATH_XLSX)
    cfg = Config(long_only=True, target_vol=0.10, max_leverage=1.0)

    # fx  = pd.read_..."USDBRL"  # Series diária USD/BRL  -> carteira em reais
    # cdi = pd.read_..."CDI"     # Series diária do retorno do CDI
    # print(evaluate_vol_models(prepare(prices_raw, cfg)[2], cfg))  # escolher modelo/janela

    out = run(prices_raw, cfg, fx=None, cdi=None,
              plot_path="momentum_garch_resultado.png")


