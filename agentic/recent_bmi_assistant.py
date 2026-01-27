"""
Example 6: ReCentAutoma - BMI Weight Management Assistant

This example demonstrates how to use ReCentAutoma with custom tools to build
a weight management assistant that calculates BMI and provides personalized
weight management suggestions.

ReCentAutoma is a goal-oriented, guidance-enabled autonomous agent that can
autonomously plan and execute multi-step tasks using tools, with built-in
memory management and goal tracking.
"""
import os
import dotenv

from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.automa import RunningOptions
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition

dotenv.load_dotenv()

# Get the API key and model name from environment variables.
_api_key = os.environ.get("OPENAI_API_KEY")
_api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
_model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Initialize LLM
llm = OpenAILlm(
    api_base=_api_base,
    api_key=_api_key,
    configuration=OpenAIConfiguration(model=_model_name),
    timeout=60,
)


async def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """
    Calculate Body Mass Index (BMI) from weight and height.

    Parameters
    ----------
    weight_kg : float
        Weight in kilograms. Must be a positive number.
    height_m : float
        Height in meters. Must be a positive number.

    Returns
    -------
    str
        A formatted string containing the BMI value and its interpretation. BMI categories:
        - Underweight: < 18.5
        - Normal: 18.5 - 24.9
        - Overweight: 25 - 29.9
        - Obese: >= 30
    """
    if weight_kg <= 0 or height_m <= 0:
        return "Error: Weight and height must be positive numbers."

    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return f"BMI: {bmi:.2f} ({category}). Weight: {weight_kg} kg, Height: {height_m} m."


async def main():
    # Create an agent with the custom tools
    weight_assistant = ReCentAutoma(
        llm=llm,
        tools=[calculate_bmi],
        stop_condition=StopCondition(max_iteration=5, max_consecutive_no_tool_selected=1),
        running_options=RunningOptions(debug=True),
    )

    # Example person data
    person_weight = 82
    person_height = 1.70
    person_name = "John Smith"
    person_gender = "male"

    result = await weight_assistant.arun(
        goal=(
            f"Calculate a person's BMI and provide personalized suggestions for effective weight management."
            f"\n- Name: {person_name}"
            f"\n- Gender: {person_gender}"
            f"\n- Weight: {person_weight} kg"
            f"\n- Height: {person_height} m"
        ),
        guidance=(
            "First calculate the BMI of the person and then give out a suggestion about the weight management."
        ),
    )
    print(result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
