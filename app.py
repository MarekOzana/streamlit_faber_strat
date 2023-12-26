"""
Streamlit interface to Faber's trend following strategy
Based on
Faber 2007: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461

BUY RULE
Buy when monthly price > 10-month SMA.
SELL RULE
Sell and move to cash when monthly price < 10-month SMA

(c) 2023-12-23 Marek Ozana
"""
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf
import charts

st.set_page_config(layout="wide", page_title="Faber's Trend-Following Strategy")

TICKER2NAME: dict[str, str] = {
    "S&P 500": "^GSPC",
    "EuroStoxx 600": "^STOXX",
    "DAX": "^GDAXI",
    "CAC40": "^FCHI",
    "FTSE 100": "^FTSE",
    "Nikkey 225": "^N225",
    "NASDAQ Composite": "^IXIC",
    "OMX Stockholm 30": "^OMX",
    "Russel 2000": "^RUT",
    "Amazon": "AMZN",
    "Bitcoin": "BTC-USD",
    " USD/SEK": "SEK=X",
}


@st.cache_data
def download_data(ticker: str) -> pd.DataFrame:
    """Fetch monthly data for given ticker"""
    data = (
        yf.Ticker(ticker)
        .history(period="max", interval="1mo")[["Close"]]
        .tz_localize(None)
    )
    return data


def _calc_cum_ret(series: pd.Series, start_dt: pd.Timestamp) -> pd.Series:
    """
    Calculate the cumulative return of a time series starting from a specific date.

    :param series: Time series of returns.
    :param start_dt: Start date for cumulative calculation.
    :return: Series of cumulative returns.
    """
    return series.multiply(series.index >= start_dt).add(1).cumprod().sub(1)


def _calc_drawdowns(r_cum: pd.Series) -> pd.Series:
    """Calculate drawdowns from cumulative returns"""
    prev_peaks = (1 + r_cum).cummax()
    dd = ((1 + r_cum) - prev_peaks) / prev_peaks
    return dd


def _calc_ann_ret(rets: pd.Series) -> float:
    """Calculate annualized return based on monthly returns"""
    r_ann = (1 + rets).prod() ** (12 / len(rets)) - 1
    return r_ann


def _calc_ann_vol(rets: pd.Series) -> float:
    """Calculate annualized volatility based on monthly returns"""
    vol_ann = rets.std() * np.sqrt(12)
    return vol_ann


def calc_stats(bt_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate Back-test statistics"""
    stats = pd.DataFrame(
        {
            "Return (annual)": {
                "Buy & Hold": _calc_ann_ret(rets=bt_data["ret"]),
                "Strategy": _calc_ann_ret(rets=bt_data["ret_strat"]),
            },
            "Volatility": {
                "Buy & Hold": _calc_ann_vol(bt_data["ret"]),
                "Strategy": _calc_ann_vol(bt_data["ret_strat"]),
            },
            "Max DrawDown": {
                "Buy & Hold": bt_data["bh_dd"].min(),
                "Strategy": bt_data["strat_dd"].min(),
            },
        }
    )
    stats["Ret / Vol"] = stats["Return (annual)"] / stats["Volatility"]
    return stats


@st.cache_data
def back_test(
    data: pd.DataFrame, start_year: int = 2010, n_sma: int = 10
) -> pd.DataFrame:
    """
    Perform a back test on financial data.

    :param data: DataFrame with close of an equity index
    :param start_year: The year from which to start the back test.
    :param n_sma: The Simple Moving Average Period
    :return: DataFrame with cumulative returns.
    """
    start_dt = pd.Timestamp(year=start_year, month=1, day=1)
    first_prev_month_day = start_dt - pd.offsets.BMonthBegin(1)

    tbl = (
        data.assign(
            sma=lambda x: x["Close"].rolling(window=n_sma).mean(),
            pos=lambda x: (x["Close"].gt(x["sma"])).astype(int).shift(1),
            trade=lambda x: x["pos"].diff().shift(-1).fillna(0),
            ret=lambda x: x["Close"].pct_change(),
            ret_strat=lambda x: x["ret"].mul(x["pos"]),
        )
        .loc[first_prev_month_day:]
        .assign(
            bh=lambda df: _calc_cum_ret(df["ret"], start_dt),
            bh_dd=lambda x: _calc_drawdowns(x["bh"]),
            strat=lambda df: _calc_cum_ret(df["ret_strat"], start_dt),
            strat_dd=lambda x: _calc_drawdowns(x["strat"]),
        )
    )
    return tbl


def main():
    with st.sidebar:
        st.title("Parameters")
        ix_name = st.sidebar.selectbox("Index Name", TICKER2NAME.keys())
        ticker = TICKER2NAME[ix_name]
        data = download_data(ticker)

        start_year = max(data.index[0].year + 1, 2000)
        start_year = st.sidebar.slider(
            "Start Year", data.index[0].year, 2022, start_year
        )
        n_sma = st.sidebar.number_input(
            "SMA Period", min_value=2, max_value=24, value=10
        )
        bt_data = back_test(data, start_year, n_sma)

    st.markdown(
        """
    ## Faber's Trend-Following Strategy

    Discover the potential of a simple trend-following strategy, based on
    [Faber's 2006 academic research](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461):

        - Buy when the monthly price is above the 10-month SMA
        - Sell and switch to cash when the monthly price falls below the 10-month SMA

    Since its publication in 2006, the strategy's performance beyond that year stands
    as a real-world test. It aims to provide returns similar to stocks but with less
    volatility and drawdowns. Give it a try!
    """
    )

    st.subheader("Back Test")
    chart_cr = charts.chart_cumul_ret(bt_data, ix_name=ix_name)
    st.altair_chart(chart_cr, use_container_width=True, theme=None)

    st.subheader("Statistics")
    stats = calc_stats(bt_data)
    stats.index.name = ix_name
    stats_styled = (
        stats.style.format(
            "{:0.1%}", subset=["Return (annual)", "Max DrawDown", "Volatility"]
        )
        .format("{:0.2f}", subset=["Ret / Vol"])
        .background_gradient(subset=["Return (annual)", "Max DrawDown", "Ret / Vol"])
        .background_gradient(subset=["Volatility"], cmap="PuBu_r")
    )
    st.dataframe(stats_styled, use_container_width=True)

    st.subheader("Signal")
    chart_ix = charts.chart_ix_and_SMA(bt_data, ix_name, n_sma)
    st.altair_chart(chart_ix, use_container_width=True, theme=None)

    st.divider()
    st.caption(
        "## Disclaimer:\n"
        "Back-Test Results Are Not Indicative of Future Performance.\n"
        "This document presents the results of back-tests conducted on various "
        "financial time series using a specific investment strategy. It is crucial "
        "to understand that back-testing involves the application of a strategy to "
        "historical data, and past performance in these tests is not indicative of "
        "future results.\n"
        "The outcomes derived from these back-tests are hypothetical and are "
        "intended for illustrative purposes only. They do not represent actual "
        "trading or investment, nor do they account for the impact of market "
        "liquidity, transaction costs, or other external factors that can affect "
        "real-world performance.\n"
        "Investors should be cautious in interpreting back-test results as these "
        "do not guarantee future returns and do not reflect the potential for loss "
        "in actual trading. Market conditions, economic factors, and investment "
        "strategies are subject to change, which can significantly affect the "
        "performance of any investment approach.\n"
        "Before making investment decisions, investors are encouraged to consider "
        "their own financial circumstances, investment objectives, and risk "
        "tolerance. These back-tests should not be construed as financial advice, "
        "and investors should engage with financial advisors for personalized "
        "investment strategies tailored to their specific needs and goals."
    )


if __name__ == "__main__":
    main()
