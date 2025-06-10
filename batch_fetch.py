from fetch_ohlcv_data import download_ohlcv

pairs = ["EURUSD", "USDCHF", "EURCHF", "USDJPY", "EURJPY", "GBPUSD", "XAUUSD", "GBPJPY"]
years = [2020, 2021, 2022, 2023, 2024]

for pair in pairs:
    for year in years:
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        filename = f"data/{pair.lower()}_{year}.csv"
        print(f"\n🔄 Hämtar {pair} för {year}...")
        try:
            download_ohlcv(pair, start, end, save_as=filename)
        except Exception as e:
            print(f"❌ Fel vid {pair} {year}: {e}")
