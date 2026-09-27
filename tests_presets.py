from src.screener.engine import ScreenerEngine
from src.screener.presets import ScreenerPresets

engine = ScreenerEngine("config/screener_config.yaml")
presets = ScreenerPresets("config/screener_config.yaml")

df = engine.load_data("nifty100.db")

result = presets.run_preset(
    "Quality Compounder",
    df
)

print(result.head())

print()

print("Companies Selected:", len(result))