"""
Busca de parâmetros do Momentum 12-1 + GARCH, com o PROTOCOLO DO NOTEBOOK momentums.ipynb:
  - parâmetros escolhidos SÓ no treino (2017–2020); a validação (2021) apenas reporta;
  - sinal, seleção, execução, custos e métricas = funções do notebook (funcoes_momentum.py).

Grade (cada configuração é um backtest completo):
  janela do momentum   : 6-1, 9-1, 12-1                       (3)
  seleção              : Top 5/10/15, Deadband 7/10           (5)
  esquema de pesos     : iguais (notebook)  +  1/σ̂ com σ̂ de   (1 + 9)
                         GARCH(504/756/1008), GJR(504/756/1008), EWMA(λ 0.90/0.94/0.97)
  => 150 backtests (15 com pesos iguais e 45 por método de vol).

Comparação coerente entre métodos de vol: mesma seleção de ativos, mesmas datas, mesmo custo,
grades do mesmo tamanho (3 especificações por método). Só muda a previsão de σ̂ que
dimensiona os pesos. A seleção por ranking não usa σ̂, então a vol só afeta o tamanho.

Relatórios:
  1. melhor configuração de cada família escolhida no TREINO e seu resultado na VALIDAÇÃO;
  2. efeito do dimensionamento por vol: Δ Sharpe (pesos por vol − pesos iguais) com a MESMA
     seleção, por método e período;
  3. qualidade da previsão de vol (QLIKE) nas datas de sinal.

Requer funcoes_momentum.py e momentum_garch_dados_teste.py na mesma pasta.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from funcoes_momentum import aplicar_custos
from initial_test import (
    CUSTO_BASE, FIM_DADOS, INICIO_BACKTEST, JANELAS, SELECOES, baixar_cdi,
    definir_periodos, executar_backtests, nome_esquema, preparar_dados, prever_vol,
    tabela_metricas,
)

METHODS = {
    "GARCH": [("garch", 504), ("garch", 756), ("garch", 1008)],
    "GJR":   [("gjr", 504), ("gjr", 756), ("gjr", 1008)],
    "EWMA":  [("ewma", 0.90), ("ewma", 0.94), ("ewma", 0.97)],
}
VOL_SPECS = [s for specs in METHODS.values() for s in specs]
FAMILIA = {nome_esquema(s): m for m, specs in METHODS.items() for s in specs}
FAMILIA["igual"] = "Pesos iguais"
ORDEM_FAMILIAS = ["Pesos iguais", "GARCH", "GJR", "EWMA"]


# ----------------------------------------------------------------------------
# Grade de resultados
# ----------------------------------------------------------------------------
def montar_grade(resultados, periodos, cdi) -> pd.DataFrame:
    """Linhas = (janela, seleção, esquema); colunas = (período, métrica)."""
    tabs = tabela_metricas(resultados, periodos, cdi, CUSTO_BASE)
    grade = pd.concat(tabs, axis=1)            # colunas MultiIndex (período, métrica)
    grade.index = pd.MultiIndex.from_tuples(grade.index, names=["janela", "seleção", "esquema"])
    grade["família"] = [FAMILIA[e] for e in grade.index.get_level_values("esquema")]
    return grade


def melhores_por_familia(grade, p_treino, p_valid):
    """Escolhe, em cada família, a configuração de maior Sharpe no TREINO e mostra a validação."""
    linhas = {}
    for fam in ORDEM_FAMILIAS:
        g = grade[grade["família"] == fam]
        melhor = g[(p_treino, "Sharpe")].idxmax()
        linhas[fam] = {
            "configuração": " | ".join(map(str, melhor)),
            "Sharpe treino": g.loc[melhor, (p_treino, "Sharpe")],
            "Sharpe validação": g.loc[melhor, (p_valid, "Sharpe")],
            "Retorno val. (%)": g.loc[melhor, (p_valid, "Retorno anual (%)")],
            "Vol val. (%)": g.loc[melhor, (p_valid, "Volatilidade (%)")],
            "MaxDD val. (%)": g.loc[melhor, (p_valid, "Max Drawdown (%)")],
            "Sharpe grade (mediana) treino": g[(p_treino, "Sharpe")].median(),
            "Sharpe grade (mediana) val.": g[(p_valid, "Sharpe")].median(),
            "nº configs": len(g),
        }
    return pd.DataFrame(linhas).T, {f: grade[grade["família"] == f][(p_treino, "Sharpe")].idxmax()
                                    for f in ORDEM_FAMILIAS}


def efeito_do_dimensionamento(grade, periodos):
    """Δ Sharpe = Sharpe(pesos por vol) − Sharpe(pesos iguais), mesma (janela, seleção)."""
    sh = {per: grade[(per, "Sharpe")].unstack("esquema") for per in periodos}
    linhas = {}
    for fam, specs in METHODS.items():
        cols = [nome_esquema(s) for s in specs]
        linha = {}
        for per in periodos:
            d = sh[per][cols].sub(sh[per]["igual"], axis=0).stack()
            linha[f"mediana Δ {per.split()[0]}"] = d.median()
            linha[f"% Δ>0 {per.split()[0]}"] = (d > 0).mean() * 100
        linhas[fam] = linha
    return pd.DataFrame(linhas).T


def qlike_por_spec(retornos, sigmas, datas, horizonte=21):
    logr = np.log1p(retornos)
    rv = (logr ** 2).rolling(horizonte, min_periods=horizonte // 2).mean().shift(-horizonte).reindex(datas)
    out = {}
    for spec, sg in sigmas.items():
        fc = sg ** 2
        m = (rv > 0) & (fc > 0)
        ratio = (rv / fc).where(m)
        out[nome_esquema(spec)] = float((ratio - np.log(ratio) - 1).stack().mean())
    return pd.Series(out, name="QLIKE (menor = melhor)")


def plot_melhores(resultados, escolhidos, periodos, caminho):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, len(periodos), figsize=(7 * len(periodos), 5))
    ax = np.atleast_1d(ax)
    for a, (per, (ini, fim)) in zip(ax, periodos.items()):
        for fam, chave in escolhidos.items():
            pat = (1 + aplicar_custos(resultados[chave].loc[ini:fim], CUSTO_BASE)).cumprod()
            a.plot(pat.index, pat.values, label=f"{fam}: {' | '.join(map(str, chave))}",
                   ls="--" if fam == "Pesos iguais" else "-")
        a.set_title(f"{per}\n(configurações escolhidas no treino)"); a.grid(alpha=.3)
        a.set_ylabel("Patrimônio (base 1)")
    ax[0].legend(fontsize=7)
    plt.tight_layout(); plt.savefig(caminho, dpi=130); plt.close()


# ----------------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------------
def run_optimization(path=None, cdi="auto", exclude=(), fim=FIM_DADOS, workers=None,
                     cache_path="cache_vol_mensal.pkl", saida_prefixo="otimizacao"):
    precos, retornos, momentos, datas = preparar_dados(path, exclude=exclude, fim=fim)
    periodos = definir_periodos(fim)
    p_treino, p_valid = list(periodos)[:2]
    if isinstance(cdi, str) and cdi == "auto":
        cdi = baixar_cdi(INICIO_BACKTEST, fim)
    sem_cdi = "" if cdi is not None else "  [Sharpe sem CDI]"

    sigmas, fallbacks = prever_vol(retornos, datas, VOL_SPECS, workers=workers, cache_path=cache_path)
    print("[vol] previsões GARCH/GJR que caíram para EWMA:",
          {nome_esquema(s): fallbacks[s] for s in VOL_SPECS if s[0] != "ewma"})

    resultados, _ = executar_backtests(retornos, momentos, sigmas, JANELAS, SELECOES,
                                       [None] + VOL_SPECS, INICIO_BACKTEST, fim)
    print(f"[grade] {len(resultados)} backtests executados")
    grade = montar_grade(resultados, periodos, cdi)

    tab, escolhidos_idx = melhores_por_familia(grade, p_treino, p_valid)
    print(f"\n1) Melhor configuração de cada família (escolhida no treino){sem_cdi}")
    print(tab.drop(columns=["configuração"]).round(3).to_string())
    print("   configurações:", {f: tab.loc[f, "configuração"] for f in ORDEM_FAMILIAS})

    efeito = efeito_do_dimensionamento(grade, periodos)
    print(f"\n2) Efeito de dimensionar por vol (Δ Sharpe vs pesos iguais, mesma seleção; "
          f"{len(JANELAS) * len(SELECOES) * 3} pares por método){sem_cdi}")
    print(efeito.round(3).to_string())

    ql = qlike_por_spec(retornos, sigmas, datas)
    print("\n3) Qualidade da previsão de vol nas datas de sinal (QLIKE)")
    print(ql.round(4).to_string())

    plot_melhores(resultados, escolhidos_idx, periodos, f"{saida_prefixo}_melhores.png")
    g = grade.copy(); g.columns = [" | ".join(c) if isinstance(c, tuple) and c[1] else c[0] for c in g.columns]
    g.round(4).to_csv(f"{saida_prefixo}_grade.csv")
    tab.round(4).to_csv(f"{saida_prefixo}_familias.csv")
    return {"grade": grade, "familias": tab, "efeito": efeito, "qlike": ql, "resultados": resultados}


if __name__ == "__main__":
    # A primeira execução ajusta ~9 especificações de vol (alguns minutos); depois usa o cache.
    out = run_optimization()