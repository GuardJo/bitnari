import json
import logging

import pyupbit
from dotenv import load_dotenv
from openai import OpenAI

import consts

# 로그 설정
logging.basicConfig(filename="bitnari.log", level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# 환경변수 로딩
load_dotenv()


# 업비트 30일봉 차트 조회
def get_month_charts(coin_ticker):
    return pyupbit.get_ohlcv(coin_ticker, count=30, interval='day')


# 업비트 24시간 거래 데이터 조회
def get_daily_charts(coin_ticker):
    return pyupbit.get_ohlcv(coin_ticker, count=24, interval='minute60')


# 업비트 호가 데이터 조회
def get_orderbook(coin_ticker):
    return pyupbit.get_orderbook(coin_ticker)


def get_answer_of_trade_reason(ohlcv_month, ohlcv_daily, orderbook_data):
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
                        "text": f"I'll give you the following data as input between coin buying and selling opinions\nOHLCV daily data for the last 30 days of the coin: {ohlcv_month.to_json()}\nOHLCV 60-minute data for the last 24 hours of the coin: {ohlcv_daily.to_json()}\nOrder Book: {json.dumps(orderbook_data)}"
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

    ohlcv_daily = get_month_charts(coin_ticker)
    ohlcv_month = get_daily_charts(coin_ticker)
    orderbook_data = get_orderbook(coin_ticker)
    ai_result = get_answer_of_trade_reason(ohlcv_month, ohlcv_daily, orderbook_data)

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
