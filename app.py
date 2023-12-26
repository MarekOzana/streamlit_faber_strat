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
from typing import Literal

import pandas as pd
import streamlit as st
import yfinance as yf
import charts

st.set_page_config(layout="wide", page_title="Faber's Trend-Following Strategy")

TICKER2NAME: dict[str, str] = {
    "S&P 500": "^GSPC",
    "OMXS Stockholm 30": "^OMX",
    "Russell 2000": "^RUT",
}


@st.cache_data
def download_data(ticker: Literal["^GSPC", "^OMX", "^RUT"]) -> pd.DataFrame:
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

        start_year = st.sidebar.slider(
            "Start Year", data.index[0].year, 2021, data.index[0].year + 1
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

        - Buy when monthly price > 10-month SMA
        - Sell and move to cash when monthly price < 10-month SMA
        """
    )

    chart_ix = charts.chart_ix_and_SMA(bt_data, ix_name, n_sma)
    st.altair_chart(chart_ix, use_container_width=True, theme=None)
    chart_cr = charts.chart_cumul_ret(bt_data, ix_name=ix_name)
    st.altair_chart(chart_cr, use_container_width=True, theme=None)


if __name__ == "__main__":
    main()
