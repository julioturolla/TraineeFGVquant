"""
Testes de heterocedasticidade condicional (efeito ARCH) para justificar o uso do GARCH.

Lógica da justificativa (cada bloco responde a uma pergunta):
  1. A volatilidade varia no tempo?       -> ARCH-LM de Engle (H0: variância constante)
  2. Ela "agrupa" (clustering)?           -> Ljung-Box e ACF de r² vs r (retornos ~ sem
                                             autocorrelação, mas retornos² com autocorrelação)
  3. Faz diferença na prática?            -> AIC/BIC: variância constante vs GARCH vs GJR
  4. O GARCH captura o efeito?            -> ARCH-LM e Ljung-Box nos resíduos padronizados
                                             (esperado: deixam de rejeitar)
  5. Ele é persistente e assimétrico?     -> α+β, meia-vida, γ do GJR (efeito alavancagem)
  6. O efeito é estável no tempo?         -> ARCH-LM em janelas móveis (a mesma janela usada
                                             na reestimação do GARCH na estratégia)

Observações:
  - Os diagnósticos usam a amostra completa (é um teste do fenômeno, não um backtest).
  - Retornos são log-retornos calculados entre observações válidas de cada ativo (em %).
  - Com 30 ativos, reporta-se também a rejeição com correção de Bonferroni (α/30).

Dependências: pip install arch statsmodels pandas numpy openpyxl matplotlib scipy
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.stattools import acf

warnings.filterwarnings("ignore")

PATH = "bases de dados\economatica-3.xlsx"
OUT = "testes"
ALPHA = 0.05
ARCH_LAGS = (1, 5, 10, 20)       # defasagens do ARCH-LM
LB_LAGS = (10, 20)               # defasagens do Ljung-Box
MIN_OBS = 500                    # histórico mínimo por ativo
ROLL_WIN, ROLL_STEP = 756, 63    # janela móvel (~3 anos), passo (~1 trimestre)
DEMO_ASSETS = ("PETR4", "VALE3", "ITUB4", "MGLU3")


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
def load_economatica(path: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=0, header=None)
    tick = [h.strip().split("\n")[-1] for h in raw.iloc[3].astype(str).iloc[1:]]
    df = raw.iloc[4:].copy()
    df.columns = ["Data"] + tick
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).set_index("Data").sort_index()
    df = df.replace("-", np.nan).apply(pd.to_numeric, errors="coerce")
    return df[~df.index.duplicated(keep="last")]


def log_returns_pct(prices: pd.DataFrame) -> dict[str, pd.Series]:
    """Log-retorno (%) entre observações válidas de cada ativo (feriados não viram zero)."""
    out = {}
    for c in prices.columns:
        s = prices[c].dropna()
        s = s[s > 0]
        r = (np.log(s).diff().dropna()) * 100
        if len(r) >= MIN_OBS:
            out[c] = r
        else:
            print(f"[dados] {c}: ignorado ({len(r)} obs)")
    return out


# ----------------------------------------------------------------------------
# Análise por ativo
# ----------------------------------------------------------------------------
def fit(r: pd.Series, kind: str):
    kw = {"CONST": dict(vol="Constant"),
          "GARCH": dict(vol="GARCH", p=1, q=1),
          "GJR": dict(vol="GARCH", p=1, o=1, q=1)}[kind]
    return arch_model(r, mean="Constant", dist="t", **kw).fit(disp="off", show_warning=False)


def diag_tests(z: pd.Series, prefix: str) -> dict:
    z = z.dropna()
    out = {f"{prefix}ARCH-LM(10) p": het_arch(z.values, nlags=10)[1]}
    lb = acorr_ljungbox(z ** 2, lags=list(LB_LAGS))
    out[f"{prefix}LB r²(20) p"] = lb.loc[20, "lb_pvalue"]
    return out


def analyze_asset(r: pd.Series) -> dict:
    e = r - r.mean()
    o = {"n_obs": len(r), "vol_anual_%": r.std() * np.sqrt(252),
         "curtose_exc": stats.kurtosis(r), "assimetria": stats.skew(r),
         "JB p": stats.jarque_bera(r)[1], "retornos_zero_%": (r == 0).mean() * 100}

    # 1) ARCH-LM nos retornos (demeaned)
    for L in ARCH_LAGS:
        o[f"ARCH-LM({L}) p"] = het_arch(e.values, nlags=L)[1]

    # 2) Ljung-Box: retornos vs retornos² (clustering)
    lb_r = acorr_ljungbox(e, lags=list(LB_LAGS))
    lb_r2 = acorr_ljungbox(e ** 2, lags=list(LB_LAGS))
    o["LB r(20) p"] = lb_r.loc[20, "lb_pvalue"]
    o["LB r²(20) p"] = lb_r2.loc[20, "lb_pvalue"]
    a = acf(e ** 2, nlags=20, fft=True)[1:]
    o["ACF r² média(1-20)"] = a.mean()
    o["ACF r média |1-20|"] = np.abs(acf(e, nlags=20, fft=True)[1:]).mean()

    # 3-5) Ajustes: variância constante, GARCH(1,1), GJR(1,1,1), todos com erros t
    res = {k: fit(r, k) for k in ("CONST", "GARCH", "GJR")}
    for k, m in res.items():
        o[f"AIC {k}"], o[f"BIC {k}"] = m.aic, m.bic
    o["melhor AIC"] = min(("CONST", "GARCH", "GJR"), key=lambda k: o[f"AIC {k}"])
    o["melhor BIC"] = min(("CONST", "GARCH", "GJR"), key=lambda k: o[f"BIC {k}"])

    g, j = res["GARCH"], res["GJR"]
    o["alpha"], o["beta"] = g.params["alpha[1]"], g.params["beta[1]"]
    o["persistência α+β"] = o["alpha"] + o["beta"]
    o["meia-vida (dias)"] = (np.log(0.5) / np.log(o["persistência α+β"])
                             if o["persistência α+β"] < 1 else np.inf)
    o["nu (t)"] = g.params["nu"]
    o["gamma GJR"], o["gamma p"] = j.params["gamma[1]"], j.pvalues["gamma[1]"]
    o["conv GARCH"] = g.convergence_flag == 0

    # 4) Resíduos padronizados: o GARCH eliminou o efeito ARCH?
    o.update(diag_tests(g.std_resid, "GARCH: "))
    o.update(diag_tests(j.std_resid, "GJR: "))

    # 6) Estabilidade: % das janelas móveis em que o ARCH-LM(10) rejeita H0
    rej = []
    for s in range(0, len(e) - ROLL_WIN + 1, ROLL_STEP):
        rej.append(het_arch(e.values[s:s + ROLL_WIN], nlags=10)[1] < ALPHA)
    o["% janelas móveis rejeitando"] = np.mean(rej) * 100 if rej else np.nan
    o["_cv"] = g.conditional_volatility * np.sqrt(252)   # para os gráficos
    return o


# ----------------------------------------------------------------------------
# Relatório e gráficos
# ----------------------------------------------------------------------------
def summarize(tab: pd.DataFrame):
    n = len(tab)
    bonf = ALPHA / n
    s = lambda cond: f"{int(cond.sum())}/{n}"
    print("=" * 78)
    print(f"RESUMO ({n} ativos, nível {ALPHA:.0%}; Bonferroni {bonf:.4f})")
    print("=" * 78)
    for L in ARCH_LAGS:
        c = tab[f"ARCH-LM({L}) p"]
        print(f"1. ARCH-LM({L:>2}) rejeita variância constante: {s(c < ALPHA)}"
              f"  | com Bonferroni: {s(c < bonf)}")
    print(f"2. Ljung-Box(20) em r²  rejeita: {s(tab['LB r²(20) p'] < ALPHA)}"
          f"   | em r  rejeita: {s(tab['LB r(20) p'] < ALPHA)}")
    print(f"   ACF média (lags 1-20): r² = {tab['ACF r² média(1-20)'].mean():.3f}"
          f" vs |r| = {tab['ACF r média |1-20|'].mean():.3f}")
    print(f"3. Melhor AIC: " + ", ".join(f"{k}={v}" for k, v in tab['melhor AIC'].value_counts().items())
          + " | Melhor BIC: " + ", ".join(f"{k}={v}" for k, v in tab['melhor BIC'].value_counts().items()))
    print(f"4. Resíduos padronizados (ARCH-LM(10) NÃO rejeita = efeito capturado):")
    print(f"   GARCH: {s(tab['GARCH: ARCH-LM(10) p'] >= ALPHA)} | GJR: {s(tab['GJR: ARCH-LM(10) p'] >= ALPHA)}")
    print(f"   Ljung-Box r² nos resíduos — GARCH: {s(tab['GARCH: LB r²(20) p'] >= ALPHA)}"
          f" | GJR: {s(tab['GJR: LB r²(20) p'] >= ALPHA)}")
    print(f"5. Persistência α+β: mediana {tab['persistência α+β'].median():.3f}"
          f" (mín {tab['persistência α+β'].min():.3f}, máx {tab['persistência α+β'].max():.3f})"
          f" | meia-vida mediana {tab['meia-vida (dias)'].replace(np.inf, np.nan).median():.0f} dias")
    print(f"   γ do GJR significativo (efeito alavancagem): {s(tab['gamma p'] < ALPHA)}"
          f" | γ>0 em {s(tab['gamma GJR'] > 0)}")
    print(f"   Graus de liberdade da t (mediana): {tab['nu (t)'].median():.1f}"
          f" | curtose excessiva mediana: {tab['curtose_exc'].median():.1f}")
    print(f"6. % de janelas móveis (3 anos) com ARCH-LM(10) rejeitando: "
          f"mediana {tab['% janelas móveis rejeitando'].median():.0f}%"
          f" (mín {tab['% janelas móveis rejeitando'].min():.0f}%)")

    exc = tab[(tab["ARCH-LM(10) p"] >= ALPHA) | (tab["persistência α+β"] > 0.995)
              | (tab["persistência α+β"] < 0.8) | (~tab["conv GARCH"])]
    if len(exc):
        print("\nATENÇÃO — ativos com algum sinal de problema:")
        print(exc[["ARCH-LM(10) p", "persistência α+β", "conv GARCH"]].round(4).to_string())
    stale = tab[tab["retornos_zero_%"] > 5]
    if len(stale):
        print("\nAviso de liquidez (>5% de retornos exatamente zero; preços possivelmente 'stale'):")
        print(stale[["retornos_zero_%"]].round(1).to_string())
    print("\nObs.: KLBN3/KLBN11 e SANB3/SANB11 são classes da mesma empresa; não são evidências independentes.")


def make_plots(tab, rets):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    demo = [a for a in DEMO_ASSETS if a in rets]

    # Fig 1: |retorno| e vol condicional do GARCH
    fig, ax = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for a, axx in zip(demo, ax.ravel()):
        r = rets[a]
        axx.vlines(r.index, 0, r.abs() * np.sqrt(252), color="lightgray", lw=0.6, label="|retorno| anualizado")
        cv = tab.loc[a, "_cv"]
        axx.plot(cv.index, cv.values, color="C3", lw=1, label="vol condicional GARCH(1,1)-t")
        axx.set_title(a); axx.set_ylabel("% a.a."); axx.set_ylim(0, tab.loc[a, "_cv"].max() * 1.3)
    ax[0, 0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Volatilidade variável no tempo: períodos calmos e turbulentos se alternam")
    plt.tight_layout(); plt.savefig(f"{OUT}/arch_fig1_volatilidade_condicional.png", dpi=130); plt.close()

    # Fig 2: ACF de r vs r²
    fig, ax = plt.subplots(2, len(demo), figsize=(3.2 * len(demo), 6), sharey="row")
    for k, a in enumerate(demo):
        e = rets[a] - rets[a].mean()
        for row, (x, name) in enumerate([(e, "retornos"), (e ** 2, "retornos²")]):
            ac = acf(x, nlags=40, fft=True)[1:]
            ax[row, k].bar(range(1, 41), ac, color="C0" if row == 0 else "C3")
            band = 1.96 / np.sqrt(len(x))
            ax[row, k].axhline(band, ls="--", c="k", lw=.7); ax[row, k].axhline(-band, ls="--", c="k", lw=.7)
            ax[row, k].set_title(f"{a}: ACF de {name}", fontsize=9)
    fig.suptitle("Retornos quase sem autocorrelação; retornos² fortemente autocorrelacionados (clustering)")
    plt.tight_layout(); plt.savefig(f"{OUT}/arch_fig2_acf_retornos_vs_quadrados.png", dpi=130); plt.close()

    # Fig 3: p-valores antes/depois e persistência
    t = tab.sort_values("persistência α+β")
    fig, ax = plt.subplots(1, 2, figsize=(13, 6))
    y = np.arange(len(t))
    ax[0].scatter(t["ARCH-LM(10) p"].clip(lower=1e-300), y, label="retornos (antes)", color="C3")
    ax[0].scatter(t["GARCH: ARCH-LM(10) p"], y, label="resíduos padronizados do GARCH (depois)", color="C2", marker="s")
    ax[0].axvline(ALPHA, ls="--", c="k", lw=.8); ax[0].set_xscale("log")
    ax[0].set_yticks(y); ax[0].set_yticklabels(t.index, fontsize=8)
    ax[0].set_xlabel("p-valor do ARCH-LM(10) (escala log)"); ax[0].legend(fontsize=8, loc="lower left")
    ax[0].set_title("O GARCH elimina o efeito ARCH (à direita da linha = não rejeita)")
    ax[1].barh(y, t["persistência α+β"], color="C0"); ax[1].set_xlim(0.8, 1.0)
    ax[1].set_yticks(y); ax[1].set_yticklabels(t.index, fontsize=8)
    ax[1].set_xlabel("persistência α+β"); ax[1].set_title("Persistência da volatilidade")
    plt.tight_layout(); plt.savefig(f"{OUT}/arch_fig3_antes_depois_persistencia.png", dpi=130); plt.close()


def main():
    prices = load_economatica(PATH)
    rets = log_returns_pct(prices)
    print(f"[dados] {len(rets)} ativos | {prices.index[0].date()} a {prices.index[-1].date()}")

    rows = {}
    for i, (a, r) in enumerate(rets.items(), 1):
        rows[a] = analyze_asset(r)
        print(f"  {i:>2}/{len(rets)} {a}", end="\r", flush=True)
    tab = pd.DataFrame(rows).T
    num = [c for c in tab.columns if c not in ("melhor AIC", "melhor BIC", "conv GARCH", "_cv")]
    tab[num] = tab[num].astype(float)
    tab["conv GARCH"] = tab["conv GARCH"].astype(bool)

    summarize(tab)
    make_plots(tab, rets)
    tab.drop(columns="_cv").round(5).to_csv(f"{OUT}/arch_test_resultados.csv")
    return tab


if __name__ == "__main__":
    main()