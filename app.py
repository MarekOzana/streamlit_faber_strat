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
import streamlit as st
import yfinance as yf
import pandas as pd
from typing import Literal
import altair as alt
import calendar

st.set_page_config(layout="wide")


@st.cache_data
def download_data(ticker: Literal["^GSPC", "^OMX"]) -> pd.DataFrame:
    # Fetch monthly data
    data = yf.Ticker(ticker).history(period="max", interval="1mo")[["Close"]]
    data = data.assign(
        sma=lambda x: x["Close"].rolling(window=10).mean(),
        pos=lambda x: (x["Close"].gt(x["sma"])).astype(int).shift(1),
        ret=lambda x: x["Close"].pct_change(),
        ret_strat=lambda x: x["ret"].mul(x["pos"]),
    )
    return data


@st.cache_data
def back_test(data: pd.DataFrame, start_year: int = 2010) -> pd.DataFrame:
    """
    Perform a back test on financial data.

    :param data: DataFrame containing financial data.
    :param start_year: The year from which to start the back test.
    :return: DataFrame with cumulative returns.
    """

    def _calc_cum_ret(series: pd.Series, start_dt: pd.Timestamp) -> pd.Series:
        """
        Calculate the cumulative return of a time series starting from a specific date.

        :param series: Time series of returns.
        :param start_dt: Start date for cumulative calculation.
        :return: Series of cumulative returns.
        """
        return series.multiply(series.index >= start_dt).add(1).cumprod().sub(1)

    start_dt = pd.Timestamp(year=start_year, month=1, day=1)
    # Calculate the first business day of the previous month
    first_prev_month_day = start_dt - pd.offsets.BMonthBegin(1)

    tbl = (
        data.tz_convert(None)
        .loc[first_prev_month_day:]
        .assign(
            bh=lambda df: _calc_cum_ret(df["ret"], start_dt),
            strat=lambda df: _calc_cum_ret(df["ret_strat"], start_dt),
        )
    )
    return tbl


def create_cum_ret_chart(back_tested_data: pd.DataFrame, ticker: str) -> alt.Chart:
    chart_data = back_tested_data[["bh", "strat", "pos"]].reset_index()
    title = f"{ticker}: Strategy Positions and Cumulative Return"
    chart = (
        alt.Chart(chart_data, title=title)
        .mark_point()
        .encode(
            x=alt.X("Date:T").title(None),
            y=alt.Y("strat:Q").title("Cumulative Returns").axis(format="%"),
            color=alt.Color("pos_status:N"),
            shape=alt.Shape("pos_status:N"),
            tooltip=[
                alt.Tooltip("yearmonth(Date)", title="date"),
                "pos_status:N",
                alt.Tooltip("strat:Q", title="Strategy Return", format="%"),
            ],
        )
        .transform_calculate(pos_status="datum.pos == 1 ? 'LONG' : 'NEUTRAL'")
        .interactive()
    )
    return chart


def create_monthly_table(ts_monthly: pd.Series) -> pd.DataFrame:
    """Create monthly performance table based on pandas.Series

    It compounds (Daily) returns into monthly and creates monthly performance table.

    Parameters
    ----------
    ts_monthly: pd.Series
        monthly time series of returns in decimal format i.e. 0.01 = 1%

    Returns
    -------
    tbl: pd.DataFrame
        Calendar table with monthly and total returns

    Examples
    --------
    >>> tbl = create_monthly_table(r)
    >>> tbl.style.format("{:0.2%}", na_rep='').background_gradient(vmin=-1, vmax=1, cmap='RdBu', axis=None)  # noqa
    """
    monthly: pd.DataFrame = pd.DataFrame(
        {
            "ret": ts_monthly,
            "Month": ts_monthly.index.month,
            "Year": ts_monthly.index.year,
        },
        index=ts_monthly.index,
    )
    tbl = pd.pivot_table(monthly, values="ret", index=["Year"], columns=["Month"])
    tbl["YTD"] = (1 + tbl).prod(axis=1) - 1
    tbl = tbl.rename(columns=dict([(i, calendar.month_abbr[i]) for i in range(1, 13)]))
    tbl.index = tbl.index.astype(str)
    return tbl


def main():
    st.sidebar.title("Parameters")
    ticker = st.sidebar.selectbox("Select Ticker", ["^GSPC", "^OMX", "^RUT"])
    data = download_data(ticker)

    start_year = st.sidebar.slider("Select Start Year", data.index[0].year, 2021, 2008)
    back_tested_data = back_test(data, start_year)

    chart = create_cum_ret_chart(back_tested_data, ticker)
    st.altair_chart(chart, use_container_width=True, theme=None)

    tbl_perf = create_monthly_table(ts_monthly=back_tested_data["ret_strat"])
    st.dataframe(tbl_perf.style.format("{:0.2%}", na_rep=""), use_container_width=True)


if __name__ == "__main__":
    main()
