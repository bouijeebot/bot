import pandas as pd

def convert_m1_to_1h(input_path, output_path):
    df = pd.read_csv(input_path, sep=';', header=None)
    df.columns = ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]

    # Kombinera till datetime
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%Y%m%d %H%M%S')
    df.set_index('datetime', inplace=True)

    # Skapa 1H OHLCV genom resampling
    ohlcv = df.resample('1H').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()

    ohlcv.reset_index(inplace=True)
    ohlcv.to_csv(output_path, index=False)
    print(f"✅ Sparade 1H-data till {output_path}")
