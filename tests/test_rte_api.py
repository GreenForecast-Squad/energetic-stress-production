from energy_forecast.rte_api_core import RTEAPROAuth2
import pytest

class TestRTEAPROAuth2:
    
    def test_init(self, ):
        my_api = RTEAPROAuth2()
        assert my_api.secret
        assert my_api.token
        assert my_api.token_type
        assert my_api.token_expires_in
        assert my_api.token_expires_at
        assert my_api.headers
    
    def test_get_token(self, ):
        my_api = RTEAPROAuth2()
        older_token = my_api.token
        my_api.get_token()
        assert my_api.token != older_token
        assert my_api.token_type
        assert my_api.token_expires_in
        assert my_api.token_expires_at
        assert my_api.headers
    
    def test_check_token(self, ):
        my_api = RTEAPROAuth2()
        my_api.get_token()
        my_api.check_token()
    
    def test_format_date(self):
        import pandas as pd
        ts = pd.Timestamp("2021-01-01")
        formated = RTEAPROAuth2.format_date(ts)
        assert formated == "2021-01-01T00:00:00+02:00"
    
    def test_fetch_response(self, ):
        my_api = RTEAPROAuth2()
        my_api.get_token()
        params = {}
        with pytest.raises(AttributeError):
            my_api.fetch_response(params)
        
    def test_check_start_end_dates(self):
        import pandas as pd
        start_date = "2021-01-01"
        end_date = "2021-01-02"
        checked_start, checked_end = RTEAPROAuth2.check_start_end_dates(start_date, end_date)
        
        assert checked_start == pd.Timestamp("2021-01-01")
        assert checked_end == pd.Timestamp("2021-01-02")
        
        start_date = "2021-01-01"
        end_date = None
        checked_start, checked_end = RTEAPROAuth2.check_start_end_dates(start_date, end_date, horizon="1D")
        
        assert checked_start == pd.Timestamp("2021-01-01")
        assert checked_end == pd.Timestamp("2021-01-02")
        
        start_date = None
        end_date = None
        checked_start, checked_end = RTEAPROAuth2.check_start_end_dates(start_date, end_date, horizon="1D")
        # round to the day as "now" changes quickly
        assert checked_start.date() == pd.Timestamp("now").date()
        assert checked_end.date() == pd.Timestamp("now").date() + pd.Timedelta("1D")
