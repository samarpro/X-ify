from openai import OpenAI
import dotenv
import os
import json
from pathlib import Path

dotenv.load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

json_path = Path(__file__).parent / "output" / "x_scrape.json"

if not json_path.exists():
    raise FileNotFoundError(f"Could not find scrape file: {json_path}")

with json_path.open("r", encoding="utf-8") as f:
    scrape_data = json.load(f)

prompt = (
    "Analyze the following X/Twitter scrape data. "
    "Summarize the key posts and identify major trends, themes, and sentiment. "
    "Also call out any notable accounts or recurring topics.\n\n"
    f"Data:\n{json.dumps(scrape_data, ensure_ascii=False)}"
)

completion = client.chat.completions.create(
    model="tencent/hy3-preview:free",
    messages=[
        {"role": "user", "content": prompt},
    ],
    stream=False,
)


print(completion.choices[0].message.content)
