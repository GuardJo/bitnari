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


def get_answer_of_trade_reason(df):
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
                        "text": df.to_json()
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

    chart_data = get_month_charts(coin_ticker)
    ai_result = get_answer_of_trade_reason(chart_data)

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
