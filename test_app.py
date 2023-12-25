"""
Unit tests on app.py
(c) 2023-12-25 Marek Ozana
"""

import pytest
import pandas as pd
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

# Define the mock data to return instead of calling download_data
mock_data = pd.DataFrame({
    'Close': [4109.310059, 4169.479980, 4179.830078, 4450.379883, 4588.959961,
              4507.660156, 4288.049805, 4193.799805, 4567.799805, 4754.629883],
}, index=pd.to_datetime([
    '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01', '2023-07-01',
    '2023-08-01', '2023-09-01', '2023-10-01', '2023-11-01', '2023-12-01'
]))

def mock_download_data():
    return mock_data

@pytest.fixture
def app_test():
    with patch('app.download_data', mock_download_data):
        yield AppTest.from_file("app.py", default_timeout=30)

def test_app(app_test):
    app_test.run()

    assert len(app_test.selectbox) == 1, "Problem with select box"

    assert len(app_test.slider) == 1, "INcorrect number of sliders"

    assert len(app_test.number_input) == 1, "INcorrect number inputs"

    
