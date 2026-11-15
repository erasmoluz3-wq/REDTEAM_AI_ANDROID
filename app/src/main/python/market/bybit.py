from pybit.unified_trading import HTTP

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def ema(values, period):
    if len(values) < period:
        return None

    result = sum(values[:period]) / period
    alpha = 2 / (period + 1)

    for value in values[period:]:
        result = value * alpha + result * (1 - alpha)

    return result


def rsi(values, period=14):
    if len(values) <= period:
        return None

    changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]

    gains = [max(x, 0) for x in changes]
    losses = [max(-x, 0) for x in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    return 100 - (100 / (1 + avg_gain / avg_loss))


def atr(highs, lows, closes, period=14):
    if len(closes) <= period:
        return None

    true_ranges = []

    for i in range(1, len(closes)):
        true_ranges.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        ))

    value = sum(true_ranges[:period]) / period

    for current in true_ranges[period:]:
        value = (value * (period - 1) + current) / period

    return value


def analyze_symbol(api, symbol):
    ticker_response = api.get_tickers(
        category="spot",
        symbol=symbol
    )

    if ticker_response["retCode"] != 0:
        raise RuntimeError(ticker_response["retMsg"])

    ticker = ticker_response["result"]["list"][0]
    price = float(ticker["lastPrice"])

    candle_response = api.get_kline(
        category="spot",
        symbol=symbol,
        interval="15",
        limit=200
    )

    if candle_response["retCode"] != 0:
        raise RuntimeError(candle_response["retMsg"])

    candles = sorted(
        candle_response["result"]["list"],
        key=lambda candle: int(candle[0])
    )

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    volumes = [float(c[5]) for c in candles]

    if len(closes) < 50:
        raise RuntimeError("Histórico insuficiente")

    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    rsi14 = rsi(closes)
    atr14 = atr(highs, lows, closes)

    average_volume = sum(volumes[-21:-1]) / 20
    volume_ratio = (
        volumes[-1] / average_volume
        if average_volume > 0 else 0
    )

    if ema9 > ema21 and 50 <= rsi14 <= 68 and price > ema9:
        signal = "COMPRA EM AVALIAÇÃO"
    elif ema9 < ema21 or rsi14 > 70:
        signal = "VENDA/EVITAR NOVA COMPRA"
    else:
        signal = "AGUARDAR"

    return {
        "symbol": symbol,
        "price": price,
        "ema9": ema9,
        "ema21": ema21,
        "rsi14": rsi14,
        "atr14": atr14,
        "volume_ratio": volume_ratio,
        "signal": signal,
    }


def market_report(symbols=SYMBOLS):
    api = HTTP(testnet=False)
    reports = [
        "DADOS PÚBLICOS DA BYBIT MAINNET",
        "Mercado Spot, candles de 15 minutos.",
        "Análise técnica informativa. Nenhuma ordem foi enviada.",
    ]

    for symbol in symbols:
        try:
            data = analyze_symbol(api, symbol)

            reports.append(
                f"\n{symbol}\n"
                f"Preço: {data['price']}\n"
                f"EMA 9: {data['ema9']:.8f}\n"
                f"EMA 21: {data['ema21']:.8f}\n"
                f"RSI 14: {data['rsi14']:.2f}\n"
                f"ATR 14: {data['atr14']:.8f}\n"
                f"Volume relativo: {data['volume_ratio']:.2f}x\n"
                f"Sinal técnico inicial: {data['signal']}"
            )

        except Exception as error:
            reports.append(
                f"\n{symbol}: ERRO - {type(error).__name__}: {error}"
            )

    return "\n".join(reports)
