import pyupbit
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

df = pyupbit.get_ohlcv('KRW-BTC', count=30, interval='day')
print(df)

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

print(response.choices[0].message.content)
