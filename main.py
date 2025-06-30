import json
import logging

import pyupbit
import ta
from dotenv import load_dotenv
from openai import OpenAI
from pandas import DataFrame
from ta.utils import dropna
from ta.volatility import BollingerBands

import consts

# 로그 설정
logging.basicConfig(filename="bitnari.log", level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# 환경변수 로딩
load_dotenv()


# 업비트 30일봉 차트 조회
def get_daily_charts(coin_ticker):
    return pyupbit.get_ohlcv(coin_ticker, count=30, interval='day')


# 업비트 24시간 거래 데이터 조회
def get_hours_charts(coin_ticker):
    return pyupbit.get_ohlcv(coin_ticker, count=24, interval='minute60')


# 업비트 호가 데이터 조회
def get_orderbook(coin_ticker):
    return pyupbit.get_orderbook(coin_ticker)


# 보조지표 추가
def add_indicators(df: DataFrame):
    # 볼린저 밴드
    indicator_bb = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()
    df['bb_bbn'] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()

    # RSI 지표
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()

    # MACD 지표
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    # 이동평균선
    df['sma_20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()

    return df


def get_answer_of_trade_reason(ohlcv_daily, ohlcv_hours, orderbook_data):
    # OpenAI 비트코인 매매 의사 질의 요청
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are now a Bitcoin trader, and you will use your well-rounded knowledge to identify whether and why to buy, sell, etc. based on the given chart data in order to make the most profit in the shortest possible time.\n\nThe chart data you receive as input is the opening, high, and closing price of Bitcoin for the previous 30 days, and the response is in the form of JSON as shown below.\n\n{\n\t\"decision\": \"buy\",\n\t\"reason\" : \"some reason\"\n},\n{\n\t\"decision\" : \"sell\",\n\t\"reason\" : \"some reason\"\n},\n{\n\t\"decision\" : \"hold\",\n\t\"reason\" : \"some reason\"\n}"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"I'll give you the following data as input between coin buying and selling opinions\nOHLCV daily data for the last 30 days of the coin, including Bollinger Bands, RSI indicator, MACD indicator, and moving average lines: {ohlcv_daily.to_json()}\nOHLCV 60-minute data for the last 24 hours for the coin, including Bollinger Bands, RSI indicator, MACD indicator, and moving average lines: {ohlcv_hours.to_json()}\nOrder Book: {json.dumps(orderbook_data)}"
                    }
                ]
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    return response.choices[0].message.content


# 현재 가격 조회
def get_current_price(coin_ticker):
    return pyupbit.get_current_price(coin_ticker)


def main():
    coin_ticker = "KRW-BTC"

    ohlcv_daily = get_daily_charts(coin_ticker)
    ohlcv_daily = dropna(ohlcv_daily)
    ohlcv_daily = add_indicators(ohlcv_daily)

    ohlcv_hours = get_hours_charts(coin_ticker)
    ohlcv_hours = dropna(ohlcv_hours)
    ohlcv_hours = add_indicators(ohlcv_hours)
    orderbook_data = get_orderbook(coin_ticker)

    ai_result = get_answer_of_trade_reason(ohlcv_daily, ohlcv_hours, orderbook_data)

    logging.info("Response from OpenAI : %s", ai_result)

    json_result = json.loads(ai_result)
    current_price = get_current_price(coin_ticker)

    if json_result["decision"] == consts.BUY:
        logging.info("Buy, current price = %s", current_price)
    elif json_result["decision"] == consts.HOLD:
        logging.info("Hold, current price = %s", current_price)
    elif json_result["decision"] == consts.SELL:
        logging.info("Sell, current price = %s", current_price)
    else:
        logging.info("No decision")


main()
