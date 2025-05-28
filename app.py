
from flask import Flask, render_template_string
import threading
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

app = Flask(__name__)

sinais = []
nativos = {
    "BTC-USD": "Bitcoin",
    "EURJPY=X": "EUR/JPY"
}

modo_agressivo = True

TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Sinais do Robô</title></head>
<body>
    <h1>Sinais Gerados</h1>
    <pre>{{ sinais }}</pre>
</body>
</html>
"""

def gerar_sinais():
    global sinais
    while True:
        for codigo, nome in nativos.items():
            try:
                dados = yf.download(codigo, period='2d', interval='1m', progress=False)
                dados.dropna(inplace=True)

                dados["MM20"] = dados["Close"].rolling(window=20).mean()
                exp1 = dados["Close"].ewm(span=12, adjust=False).mean()
                exp2 = dados["Close"].ewm(span=26, adjust=False).mean()
                dados["MACD"] = exp1 - exp2
                dados["Signal"] = dados["MACD"].ewm(span=9, adjust=False).mean()

                delta = dados["Close"].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / loss
                dados["RSI"] = 100 - (100 / (1 + rs))

                dados["VolumeM10"] = dados["Volume"].rolling(10).mean()
                dados["VolumeSTD"] = dados["Volume"].rolling(10).std()

                ultimo = dados.iloc[-1]
                anterior = dados.iloc[-2]

                try:
                    preco = float(ultimo["Close"])
                    macd = float(ultimo["MACD"])
                    signal = float(ultimo["Signal"])
                    rsi = float(ultimo["RSI"])
                    mm20 = float(ultimo["MM20"])
                    volume = float(ultimo["Volume"])
                    volume_medio = float(ultimo["VolumeM10"])
                    volume_desvio = float(ultimo["VolumeSTD"])
                    corpo = abs(anterior["Close"] - anterior["Open"])
                    sombra = abs(anterior["High"] - anterior["Low"])
                except:
                    continue

                hora = datetime.now().strftime('%H:%M:%S')
                if corpo < sombra * 0.5:
                    continue
                elif abs(macd - signal) < 0.00005:
                    continue
                elif volume < volume_medio:
                    continue
                elif macd > signal and rsi < (85 if modo_agressivo else 70) and preco > mm20:
                    sinal = f"[{hora}] [{nome}] COMPRA | Preco: {preco:.2f}"
                elif macd < signal and rsi > (15 if modo_agressivo else 30) and preco < mm20:
                    sinal = f"[{hora}] [{nome}] VENDA | Preco: {preco:.2f}"
                else:
                    continue

                sinais.append(sinal)
                with open("sinais.txt", "a") as f:
                    f.write(sinal + "\n")

            except Exception as e:
                continue

        time.sleep(15)

@app.route("/")
def index():
    return render_template_string(TEMPLATE, sinais="\n".join(sinais[-50:]))

if __name__ == "__main__":
    threading.Thread(target=gerar_sinais, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
