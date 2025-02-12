import asyncio
import json
from rush_fetch import benchmark_submission

async def main():

    response = await benchmark_submission("b11071e7-4662-4a0f-8579-815febd1f514", "0d2723d5-674e-430c-90be-7784d068247f")
    print(json.dumps(response, indent=1))  # Print the API response


if __name__ == "__main__":
    asyncio.run(main())

