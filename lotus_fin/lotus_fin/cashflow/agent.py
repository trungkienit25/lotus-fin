import sys
import importlib
_m = importlib.import_module("lotus_fin.modules.f002_cashflow.agent")
sys.modules[__name__] = _m

