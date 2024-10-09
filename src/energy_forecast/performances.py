from joblib import Memory, expires_after

memory = Memory("/tmp/cache/energy_forecast", verbose=0)
