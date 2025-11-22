import asyncio

from app.workers.aqi_agent import run_aqi_agent


if __name__ == "__main__":
    asyncio.run(run_aqi_agent())
