"""
Unit tests on app.py
(c) 2023-12-25 Marek Ozana
"""

import pytest
import pandas as pd
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import app

# Define the mock data to return instead of calling download_data
mock_data = pd.DataFrame(
    {
        "Close": [
            3226.0,
            2954.0,
            2585.0,
            2912.0,
            3044.0,
            3100.0,
            3271.0,
            3500.0,
            3363.0,
            3270.0,
            3622.0,
            3756.0,
            3714.0,
            3811.0,
            3973.0,
            4181.0,
            4204.0,
            4298.0,
            4395.0,
            4523.0,
            4308.0,
            4605.0,
            4567.0,
            4766.0,
            4516.0,
            4374.0,
            4530.0,
            4132.0,
            4132.0,
            3785.0,
            4130.0,
            3955.0,
            3586.0,
            3872.0,
            4080.0,
            3840.0,
            4077.0,
            3970.0,
            4109.0,
            4169.0,
            4180.0,
            4450.0,
            4589.0,
            4508.0,
            4288.0,
            4194.0,
            4568.0,
            4755.0,
        ],
    },
    index=pd.to_datetime(
        [
            "2020-01-01",
            "2020-02-01",
            "2020-03-01",
            "2020-04-01",
            "2020-05-01",
            "2020-06-01",
            "2020-07-01",
            "2020-08-01",
            "2020-09-01",
            "2020-10-01",
            "2020-11-01",
            "2020-12-01",
            "2021-01-01",
            "2021-02-01",
            "2021-03-01",
            "2021-04-01",
            "2021-05-01",
            "2021-06-01",
            "2021-07-01",
            "2021-08-01",
            "2021-09-01",
            "2021-10-01",
            "2021-11-01",
            "2021-12-01",
            "2022-01-01",
            "2022-02-01",
            "2022-03-01",
            "2022-04-01",
            "2022-05-01",
            "2022-06-01",
            "2022-07-01",
            "2022-08-01",
            "2022-09-01",
            "2022-10-01",
            "2022-11-01",
            "2022-12-01",
            "2023-01-01",
            "2023-02-01",
            "2023-03-01",
            "2023-04-01",
            "2023-05-01",
            "2023-06-01",
            "2023-07-01",
            "2023-08-01",
            "2023-09-01",
            "2023-10-01",
            "2023-11-01",
            "2023-12-01",
        ]
    ),
)


def mock_download_data():
    return mock_data


@pytest.fixture
def app_test():
    with patch("app.download_data", mock_download_data):
        yield AppTest.from_file("app.py")


def test_app(app_test):
    app_test.run()

    assert len(app_test.selectbox) == 1, "Problem with select box"

    assert len(app_test.slider) == 1, "INcorrect number of sliders"

    assert len(app_test.number_input) == 1, "Incorrect number inputs"


def test_back_test():
    """Unit test on app.back_test function"""
    bt = app.back_test(mock_data, start_year=2021, n_sma=10)
    assert bt.index[0] == pd.Timestamp("2020-12-01")
    assert bt.columns.tolist() == [
        "Close",
        "sma",
        "pos",
        "trade",
        "ret",
        "ret_strat",
        "bh",
        "bh_dd",
        "strat",
        "strat_dd",
    ]
    assert bt.loc["2022-11-01", "trade"] == 1
    assert bt.loc["2022-12-01", "trade"] == -1
    assert bt.loc["2023-01-01", "trade"] == 1
    assert bt.loc["2023-02-01", "trade"] == 0
    assert bt.iloc[-2].round(2).to_dict() == {
        "Close": 4568.0,
        "sma": 4302.5,
        "pos": 0.0,
        "trade": 1.0,
        "ret": 0.09,
        "ret_strat": 0.0,
        "bh": 0.22,
        "bh_dd": -0.04,
        "strat": 0.03,
        "strat_dd": -0.19,
    }
