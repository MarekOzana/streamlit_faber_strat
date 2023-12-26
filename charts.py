"""
Faber Strategy CHarts
(c) 2023-12-25 Marek Ozana
"""
import pandas as pd
import altair as alt


def chart_cumul_ret(bt_data: pd.DataFrame, ix_name: str) -> alt.Chart:
    g_data = (
        bt_data[["bh", "strat", "pos", "bh_dd", "strat_dd"]]
        .reset_index(names=["date"])
        .rename(columns={"bh": ix_name, "strat": "Strategy"})
    )
    title = f"{ix_name}: Buy&Hold vs. Trend Strategy"
    fig_rets = (
        alt.Chart(g_data, title=title)
        .transform_fold([ix_name, "Strategy"])
        .mark_line()
        .encode(
            x=alt.X("date:T").title(None),
            y=alt.Y("value:Q").axis(format="%").title("Cumulative Return"),
            color=alt.Color("key:N").legend(title=None),
            tooltip=[
                "date:T",
                alt.Tooltip("value:Q", format="0.1%", title="Cumulative Ret"),
                "key:N",
            ],
        )
    )
    fig_dd = (
        alt.Chart(
            g_data[["date", "bh_dd", "strat_dd"]].rename(
                columns={"bh_dd": ix_name, "strat_dd": "Strategy"}
            )
        )
        .transform_fold([ix_name, "Strategy"])
        .mark_area(opacity=0.8)
        .encode(
            x=alt.X("date:T").title(None),
            y=alt.Y("value:Q").axis(format="%").title("DrawDowns"),
            color=alt.Color("key:N"),
            tooltip=[
                "date:T",
                alt.Tooltip("value:Q", format="0.1%", title="DrawDown"),
                "key:N",
            ],
        )
    )
    fig = (fig_rets + fig_dd).resolve_scale(color="shared").interactive()
    return fig


def chart_ix_and_SMA(bt_data: pd.DataFrame, ix_name: str, n_sma: int):
    g_data = (
        bt_data[["Close", "sma", "pos", "trade"]]
        .reset_index(names=["date"])
        .rename(columns={"Close": ix_name, "sma": f"SMA{n_sma}"})
        .assign(trade=lambda x: x["trade"].map({-1: "Sell", 1: "Buy", 0: None}))
    )
    base = alt.Chart(g_data, title=f"{ix_name} and signal {n_sma}-months SMA").encode(
        x=alt.X("date:T").title(None)
    )
    line = (
        base.transform_fold(fold=[ix_name, f"SMA{n_sma}"])
        .mark_line()
        .encode(
            y=alt.Y("value:Q").title("Index Level"),
            color=alt.Color("key:N").legend(title=None),
        )
    )
    trade = (
        alt.Chart(g_data.dropna(subset=["trade"]))
        .mark_point()
        .encode(
            x=alt.X("date:T"),
            y=alt.Y(f"{ix_name}:Q"),
            color=alt.Color("trade:N")
            .scale(domain=["Buy", "Sell"], range=["forestgreen", "firebrick"])
            .legend(None),
            shape=alt.Shape("trade:N").scale(
                domain=["Buy", "Sell"], range=["triangle-up", "square"]
            ),
            tooltip=[
                "yearmonth(date)",
                "trade:N",
                alt.Tooltip(f"{ix_name}:Q", format="0.1f"),
            ],
        )
    )

    chart = (line + trade).resolve_scale(color="independent").interactive()
    return chart
