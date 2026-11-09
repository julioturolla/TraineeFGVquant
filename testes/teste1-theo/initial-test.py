"""
Seleção WALK-FORWARD de parâmetros do Momentum-GARCH, COMPARANDO TRÊS MÉTODOS DE VOL
(GARCH, GJR-GARCH e EWMA) sobre exatamente os mesmos ativos, datas e regras.

Para a comparação ser coerente:
  - Cada método tem uma grade do MESMO tamanho (72 configurações = 3 especificações de vol
    x 4 conjuntos de lookbacks x 2 skips x 3 zonas neutras) e é otimizado separadamente.
      GARCH / GJR : janela de estimação 504, 756, 1008 dias (GARCH(1,1) / GJR(1,1,1), erros t)
      EWMA        : lambda 0.90, 0.94, 0.97 (a "memória" do EWMA, análoga à janela)
  - Mesmos ativos, mesmas datas de rebalanceamento, mesma janela de treino, mesmo custo,
    mesma regra de pesos e vol targeting; só muda a previsão de volatilidade.
  - Todos são avaliados no MESMO período fora da amostra.
  - Além do desempenho da carteira, compara-se a qualidade da previsão de vol por ativo (QLIKE).
  - Quando o GARCH não converge, a previsão cai para EWMA(0.94); o número de ocorrências é
    reportado por método, para saber se o GARCH foi de fato avaliado.

Método walk-forward (sem look-ahead): cada configuração é simulada na série inteira; em cada
data de reotimização, escolhe-se a de melhor score nos `train_days` dias anteriores e aplica-se
nos meses seguintes. O custo de trocar de configuração é cobrado.

Requer momentum_garch_dados_teste.py na mesma pasta.
Dependências: pip install arch statsmodels pandas numpy openpyxl matplotlib
"""
from __future__ import annotations

import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np
import pandas as pd

from momentum_garch_dados_teste import (
    ANN, PATH_XLSX, Config, backtest, cash_series, ewma_corr, ewma_vol,
    garch_forecast, load_data, metrics, prepare,
)

# ----------------------------------------------------------------------------
# Grades (mesmo tamanho para os três métodos)
# ----------------------------------------------------------------------------
METHODS = {
    "GARCH": [("garch", 504), ("garch", 756), ("garch", 1008)],
    "GJR":   [("gjr", 504), ("gjr", 756), ("gjr", 1008)],
    "EWMA":  [("ewma", 0.90), ("ewma", 0.94), ("ewma", 0.97)],
}
VOL_SPECS = [s for specs in METHODS.values() for s in specs]
METHOD_OF = {vi: m for m, specs in METHODS.items() for vi in range(len(VOL_SPECS)) if VOL_SPECS[vi] in specs}
DEFAULT_VOL = {m: VOL_SPECS.index(specs[1]) for m, specs in METHODS.items()}  # especificação do meio

LOOKBACKS = [(21, 63, 126), (21, 63, 126, 252), (63, 126, 252), (126, 252)]  # do mais curto ao mais longo
SKIPS = [0, 21]               # 0 = sem skip; 21 = pula o último mês (estilo "12-1")
DEADBANDS = [0.0, 0.25, 0.5]  # zona neutra do t-stat (histerese)
DEFAULT_SIGNAL = (1, 0, 0)    # lookbacks (21,63,126,252), sem skip, sem zona neutra (config "original")


@dataclass(frozen=True)
class OptConfig:
    train_days: int = 1260        # janela de treino (~5 anos)
    reopt_days: int = 252         # reotimiza a cada ~12 meses
    expanding: bool = False       # True => janela expansiva em vez de móvel
    vol_error_lambda: float = 1.0 # peso da penalidade de erro de vol targeting
    neighbor_smoothing: bool = True
    n_workers: int | None = None  # None => os.cpu_count()
    cache_path: str = "cache_vol_forecasts.pkl"


# ----------------------------------------------------------------------------
# 1) Previsões de vol de todas as especificações (cache incremental e paralelismo)
# ----------------------------------------------------------------------------
def _worker(args):
    a, r, ew_fb, ew_spec, pos, model, param, horizon, min_asset_obs = args
    out = np.full(len(pos), np.nan)
    n_fb = 0
    w = int(param) if model != "ewma" else 756   # EWMA usa a mesma regra de disponibilidade do GARCH
    for k, p in enumerate(pos):
        x = r[max(0, p + 1 - w): p + 1]
        if np.isfinite(x).sum() < min_asset_obs:
            continue
        if model == "ewma":
            out[k] = ew_spec[p]
            continue
        s = garch_forecast(pd.Series(x), model, horizon, min_asset_obs)
        if np.isfinite(s):
            out[k] = s
        else:
            out[k] = ew_fb[p]; n_fb += 1       # fallback EWMA(0.94)
    return a, out, n_fb


def get_vol_forecasts(logr: pd.DataFrame, cfg: Config, ocfg: OptConfig):
    reb = logr.index[cfg.min_obs :: cfg.refit_every]
    pos = [logr.index.get_loc(t) for t in reb]
    fingerprint = (list(logr.columns), str(logr.index[0]), str(logr.index[-1]),
                   cfg.horizon, cfg.refit_every, cfg.min_obs, cfg.min_asset_obs)

    cache = {}  # {(modelo, parametro): (DataFrame, n_fallbacks)}
    if os.path.exists(ocfg.cache_path):
        with open(ocfg.cache_path, "rb") as f:
            c = pickle.load(f)
        if c.get("fingerprint") == fingerprint:
            cache = c["specs"]
            print(f"[vol] cache: {sum(s in cache for s in VOL_SPECS)}/{len(VOL_SPECS)} especificações prontas")

    ew_fb = ewma_vol(logr, 0.94)
    n = ocfg.n_workers or os.cpu_count() or 1
    for spec in VOL_SPECS:
        if spec in cache:
            continue
        model, param = spec
        t0 = time.time()
        ew_spec = ewma_vol(logr, param) if model == "ewma" else ew_fb
        tasks = [(a, logr[a].values, ew_fb[a].values, ew_spec[a].values, pos, model, param,
                  cfg.horizon, cfg.min_asset_obs) for a in logr.columns]
        if n > 1:
            with ProcessPoolExecutor(min(n, len(tasks))) as ex:
                res = list(ex.map(_worker, tasks))
        else:
            res = [_worker(t) for t in tasks]
        df = pd.DataFrame(index=reb, columns=logr.columns, dtype=float)
        for a, arr, _ in res:
            df[a] = arr
        cache[spec] = (df, sum(r[2] for r in res))
        with open(ocfg.cache_path, "wb") as f:     # salva a cada especificação (retomável)
            pickle.dump({"fingerprint": fingerprint, "specs": cache}, f)
        print(f"[vol] {model}-{param} pronto em {time.time() - t0:.0f}s", flush=True)

    sigmas = {vi: cache[s][0] for vi, s in enumerate(VOL_SPECS)}
    fallbacks = {vi: cache[s][1] for vi, s in enumerate(VOL_SPECS)}
    return reb, sigmas, fallbacks


# ----------------------------------------------------------------------------
# 2) Pesos por configuração (correlações e retornos acumulados em cache)
# ----------------------------------------------------------------------------
def precompute_corr(logr, reb, cfg: Config):
    Rs = []
    for t in reb:
        i = logr.index.get_loc(t)
        win = logr.iloc[max(0, i + 1 - 4 * cfg.corr_halflife): i + 1]
        Rs.append(ewma_corr(win, cfg.corr_halflife, cfg.corr_shrink))
    return Rs


def precompute_cum(logp, reb):
    cum = {}
    for L in {L for lb in LOOKBACKS for L in lb}:
        for sk in SKIPS:
            cum[(L, sk)] = (logp.shift(sk) - logp.shift(L + sk)).reindex(reb).values
    return cum


def make_weights(sigma, cum, Rs, lookbacks, skip, deadband, cfg: Config, use_momentum=True):
    S = sigma.values
    with np.errstate(invalid="ignore", divide="ignore"):
        M = np.mean([cum[(L, skip)] / (S * np.sqrt(L)) for L in lookbacks], axis=0)
    T, N = S.shape
    W = np.zeros((T, N))
    state = np.zeros(N)
    started = np.zeros(N, dtype=bool)

    for k in range(T):
        s, m = S[k], M[k]
        ok = np.isfinite(s) & np.isfinite(m)
        if not ok.any():
            continue
        new = ok & ~started
        state[new] = np.sign(m[new])
        started |= new
        state[ok & (m > deadband)] = 1.0     # histerese: só muda de lado ao cruzar a zona neutra
        state[ok & (m < -deadband)] = -1.0

        d = np.where(ok, state if use_momentum else 1.0, 0.0)
        if cfg.long_only:
            d = np.clip(d, 0.0, None)
        if not d.any():
            continue

        idx = np.where(ok)[0]
        sg = s[idx]
        r = d[idx] / sg
        cov = Rs[k][np.ix_(idx, idx)] * np.outer(sg, sg) * ANN
        pv = np.sqrt(r @ cov @ r)
        if pv <= 0:
            continue
        w = r * cfg.target_vol / pv
        gross = np.abs(w).sum()
        if gross > cfg.max_leverage:
            w *= cfg.max_leverage / gross
        W[k, idx] = w
    return pd.DataFrame(W, index=sigma.index, columns=sigma.columns)


# ----------------------------------------------------------------------------
# 3) Simula as três grades
# ----------------------------------------------------------------------------
def simulate_grid(simple, logr, logp, cash, cfg: Config, ocfg: OptConfig):
    reb, sigmas, fallbacks = get_vol_forecasts(logr, cfg, ocfg)
    Rs = precompute_corr(logr, reb, cfg)
    cum = precompute_cum(logp, reb)

    keys, rets, turns, wds = [], [], [], []
    t0 = time.time()
    for vi in range(len(VOL_SPECS)):
        for li, lb in enumerate(LOOKBACKS):
            for si, sk in enumerate(SKIPS):
                for di, db in enumerate(DEADBANDS):
                    W = make_weights(sigmas[vi], cum, Rs, lb, sk, db, cfg)
                    r, tr, Wd = backtest(simple, W, cash, cfg)
                    keys.append((vi, li, si, di)); rets.append(r); turns.append(tr); wds.append(Wd.values)
    print(f"[grade] {len(keys)} configurações simuladas em {time.time() - t0:.0f}s")

    naive = {}
    for m, vi in DEFAULT_VOL.items():   # carteira sem momentum, com a vol de cada método
        Wn = make_weights(sigmas[vi], cum, Rs, LOOKBACKS[1], 0, 0.0, cfg, use_momentum=False)
        naive[m] = backtest(simple, Wn, cash, cfg)[0]

    R = pd.concat(rets, axis=1, keys=range(len(keys)))
    TR = pd.concat(turns, axis=1, keys=range(len(keys)))
    return R, TR, wds, keys, naive, sigmas, fallbacks, reb


# ----------------------------------------------------------------------------
# 4) Seleção walk-forward (um método por vez)
# ----------------------------------------------------------------------------
def neighbor_lists(subkeys):
    """Vizinhos: mesma especificação de vol, diferindo ±1 em exatamente um eixo do sinal."""
    pos = {k: i for i, k in enumerate(subkeys)}
    nb = []
    for k in subkeys:
        lst = [pos[k]]
        for ax in (1, 2, 3):
            for step in (-1, 1):
                c = list(k); c[ax] += step
                if tuple(c) in pos:
                    lst.append(pos[tuple(c)])
        nb.append(lst)
    return nb


def walk_forward(R, TR, wds, cash, keys, sub, cfg: Config, ocfg: OptConfig):
    idx = R.index
    Rsub = R.iloc[:, sub]
    ex = Rsub.sub(cash.reindex(idx), axis=0)
    verr = ((Rsub.rolling(63).std() * np.sqrt(ANN)) - cfg.target_vol).abs()
    nb = neighbor_lists([keys[i] for i in sub])
    cost = cfg.cost_bps / 1e4

    first = ocfg.train_days
    reopt = list(range(first, len(idx), ocfg.reopt_days))
    out = pd.Series(np.nan, index=idx[first:])
    chosen, prev = [], None

    for j, p in enumerate(reopt):
        lo = 0 if ocfg.expanding else p - ocfg.train_days
        sh = (ex.iloc[lo:p].mean() / ex.iloc[lo:p].std() * np.sqrt(ANN)).values
        sc = sh - ocfg.vol_error_lambda * verr.iloc[lo:p].mean().values / cfg.target_vol
        if ocfg.neighbor_smoothing:
            sc = np.array([sc[n].mean() for n in nb])
        best = sub[int(np.nanargmax(sc))]
        end = reopt[j + 1] if j + 1 < len(reopt) else len(idx)

        seg = R[best].iloc[p:end].copy()
        if prev is not None and prev != best:      # custo de trocar de configuração
            real = np.abs(wds[best][p] - wds[prev][p - 1]).sum()
            seg.iloc[0] += cost * TR[best].iloc[p] - cost * real
        out.iloc[p - first: end - first] = seg.values
        k = keys[best]
        chosen.append({"data": idx[p], "vol": VOL_SPECS[k[0]][1], "lookbacks": LOOKBACKS[k[1]],
                       "skip": SKIPS[k[2]], "deadband": DEADBANDS[k[3]],
                       "score_suavizado": float(np.nanmax(sc)), "col": best})
        prev = best
    return out, pd.DataFrame(chosen)


# ----------------------------------------------------------------------------
# 5) Qualidade da previsão de vol por ativo (QLIKE, menor = melhor)
# ----------------------------------------------------------------------------
def qlike_by_asset(logr, sigmas, reb, cfg: Config, start):
    rv = (logr ** 2).rolling(cfg.horizon, min_periods=cfg.horizon // 2).mean().shift(-cfg.horizon).reindex(reb)
    rows = {}
    for vi, sg in sigmas.items():
        fc = sg ** 2
        m = (rv > 0) & (fc > 0)
        ratio = (rv / fc).where(m)
        ql = (ratio - np.log(ratio) - 1).loc[start:]
        rows[vi] = ql.mean()
    return rows


# ----------------------------------------------------------------------------
# 6) Relatório comparativo
# ----------------------------------------------------------------------------
def report(results, R, TR, naive, cash, cfg, logr, sigmas, fallbacks, reb, keys, plot_path=None):
    oos = results["GARCH"][0].index
    assert all(results[m][0].index.equals(oos) for m in results), "períodos fora da amostra diferentes"
    print(f"\nPeríodo fora da amostra (igual para os 3 métodos): {oos[0].date()} a {oos[-1].date()}\n")

    # --- Desempenho da carteira
    perf = {}
    for m, (wf, chosen, sub) in results.items():
        perf[f"{m} (walk-forward)"] = metrics(wf, cash, cfg.target_vol)
    perf["Ingênua (EWMA, sem momentum)"] = metrics(naive["EWMA"].loc[oos], cash, cfg.target_vol)
    print(pd.DataFrame(perf).round(4).to_string())

    # --- Diagnóstico por método
    ex = R.loc[oos].sub(cash.reindex(oos), axis=0)
    sharpes = ex.mean() / ex.std() * np.sqrt(ANN)
    diag = {}
    for m, (wf, chosen, sub) in results.items():
        sh_sub = sharpes.iloc[sub]
        wf_sh = metrics(wf, cash)["sharpe"]
        fixed = [i for i in sub if keys[i] == (DEFAULT_VOL[m],) + DEFAULT_SIGNAL][0]
        diag[m] = {
            "Sharpe walk-forward": wf_sh,
            "Sharpe config fixa (meio da grade)": sharpes.iloc[fixed],
            "Sharpe grade: mín": sh_sub.min(), "Sharpe grade: mediana": sh_sub.median(),
            "Sharpe grade: máx (look-ahead)": sh_sub.max(),
            "% da grade superada pelo walk-forward": (sh_sub < wf_sh).mean(),
            "trocas de config (em %d reotimizações)" % len(chosen):
                int((chosen["col"] != chosen["col"].shift()).sum() - 1),
            "previsões GARCH que caíram p/ EWMA": sum(fallbacks[vi] for vi in range(len(VOL_SPECS))
                                                    if METHOD_OF[vi] == m and m != "EWMA"),
        }
    print("\nDiagnóstico por método (mesma grade de 72 configurações cada):")
    print(pd.DataFrame(diag).round(3).to_string())

    # --- QLIKE por ativo
    ql = qlike_by_asset(logr, sigmas, reb, cfg, oos[0])
    tab = pd.DataFrame({m: ql[DEFAULT_VOL[m]] for m in METHODS})
    tab.loc["MÉDIA"] = tab.mean()
    best_spec = {m: min((vi for vi in range(len(VOL_SPECS)) if METHOD_OF[vi] == m),
                        key=lambda vi: ql[vi].mean()) for m in METHODS}
    tab.loc["MÉDIA (melhor das 3 espec.)"] = [ql[best_spec[m]].mean() for m in METHODS]
    print("\nQLIKE da previsão de vol por ativo (menor = melhor; especificação do meio da grade):")
    print(tab.round(4).to_string())
    print("Melhor especificação por método:", {m: VOL_SPECS[best_spec[m]] for m in METHODS})

    # --- Parâmetros escolhidos
    print("\nFrequência dos parâmetros escolhidos:")
    for m, (wf, chosen, sub) in results.items():
        print(f" [{m}]")
        for col in ("vol", "lookbacks", "skip", "deadband"):
            print(f"   {col}: " + ", ".join(f"{k}={v}" for k, v in chosen[col].astype(str).value_counts().items()))

    if plot_path:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5.5))
        for m, (wf, _, _) in results.items():
            (1 + wf).cumprod().plot(ax=ax, label=f"{m} walk-forward")
        (1 + naive["EWMA"].loc[oos]).cumprod().plot(ax=ax, label="Ingênua (EWMA)", color="gray", ls="--")
        ax.set_yscale("log"); ax.legend(); ax.set_title("Crescimento de 1 fora da amostra, por método de vol (escala log)")
        plt.tight_layout(); plt.savefig(plot_path, dpi=130)
    return pd.DataFrame(perf), pd.DataFrame(diag), tab


def run_optimization(prices_raw, cfg: Config = Config(), ocfg: OptConfig = OptConfig(),
                     fx=None, cdi=None, plot_path=None):
    prices, simple, logr, logp = prepare(prices_raw, cfg, fx)
    print(f"[universo] {list(prices.columns)} | {prices.index[0].date()} a {prices.index[-1].date()}")
    cash = cash_series(prices.index, cfg, cdi)

    R, TR, wds, keys, naive, sigmas, fallbacks, reb = simulate_grid(simple, logr, logp, cash, cfg, ocfg)

    results = {}
    for m in METHODS:
        sub = [i for i, k in enumerate(keys) if METHOD_OF[k[0]] == m]
        wf, chosen = walk_forward(R, TR, wds, cash, keys, sub, cfg, ocfg)
        results[m] = (wf, chosen, sub)

    perf, diag, qtab = report(results, R, TR, naive, cash, cfg, logr, sigmas, fallbacks, reb, keys, plot_path)
    return {"results": results, "perf": perf, "diag": diag, "qlike": qtab, "grid_returns": R}


if __name__ == "__main__":
    prices_raw = load_data(PATH_XLSX)
    cfg = Config(long_only=True, target_vol=0.10, max_leverage=1.0)
    ocfg = OptConfig(train_days=1260, reopt_days=252)

    out = run_optimization(prices_raw, cfg, ocfg, fx=None, cdi=None,
                           plot_path="/mnt/user-data/outputs/comparacao_metodos_vol.png")
    allc = pd.concat([c.drop(columns="col").assign(metodo=m) for m, (_, c, _) in out["results"].items()])
    allc.to_csv("parametros_escolhidos_por_metodo.csv", index=False)