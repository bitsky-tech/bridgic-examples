"""
This example demonstrates how to trace a ReAct application using `langwatch`
in `bridgic`.

Set up the environment variables:

```shell
export LANGWATCH_API_KEY="<your_langwatch_api_key>"
```

Run this example with uv:

```shell
uv run trace/react_tracing.py
```
"""

import os
import asyncio
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.traces.langwatch import start_langwatch_trace
from bridgic.core.agentic import ReActAutoma

# Get the API base, API key and model name.
_api_key = os.environ.get("OPENAI_API_KEY")
_api_base = os.environ.get("OPENAI_API_BASE")
_model_name = os.environ.get("OPENAI_MODEL_NAME")


# Configure tracing with `langwatch` in `bridgic`.
start_langwatch_trace()

llm = OpenAILlm(  # the llm instance
    api_base=_api_base,
    api_key=_api_key,
    configuration=OpenAIConfiguration(model=_model_name),
    timeout=20,
)

# Three mock tools defined as async functions.

async def get_weather(city: str, days: int):
    """
    Get the weather forecast for the next few days in a specified city.

    Parameters
    ----------
    city : str
        The city to get the weather of, e.g. New York.
    days : int
        The number of days to get the weather forecast for.
    
    Returns
    -------
    str
        The weather forecast for the next few days in the specified city.
    """
    await asyncio.sleep(0.1)
    return f"The weather in {city} will be mostly sunny for the next {days} days."

async def get_flight_price(origin_city: str, destination_city: str):
    """
    Get the average round-trip flight price from one city to another.

    Parameters
    ----------
    origin_city : str
        The origin city of the flight.
    destination_city : str
        The destination city of the flight.
    
    Returns
    -------
    str
        The average round-trip flight price from the origin city to the destination city.
    """
    await asyncio.sleep(0.1)
    return f"The average round-trip flight from {origin_city} to {destination_city} is about $850."

async def get_hotel_price(city: str, nights: int):
    """
    Get the average price of a hotel stay in a specified city for a given number of nights.

    Parameters
    ----------
    city : str
        The city to get the hotel price of, e.g. New York.
    nights : int
        The number of nights to get the hotel price for.
    
    Returns
    -------
    str
        The average price of a hotel stay in the specified city for the given number of nights.
    """
    await asyncio.sleep(0.1)
    return f"A 3-star hotel in {city} costs about $120 per night for {nights} nights."


#Create an agent for planning a trip.
travel_planner_agent = ReActAutoma(
    llm=llm,
    system_prompt="You are a travel planner. You are given a city and a number of days. You need to plan a trip to the city for the given number of days.",
    tools=[get_weather, get_flight_price, get_hotel_price],
)

async def main():
    await travel_planner_agent.arun(
        user_msg="Plan a 3-day trip to Tokyo. Check the weather forecast, estimate the flight price from San Francisco, and the hotel cost for 3 nights."
    )

if __name__ == "__main__":
    asyncio.run(main())