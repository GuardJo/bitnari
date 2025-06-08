import os

import dotenv

# TODO 추후 제거
dotenv.load_dotenv()
print(os.getenv("OPEN_AI_API_KEY"))
print(os.getenv("UPBIT_API_KEY"))
