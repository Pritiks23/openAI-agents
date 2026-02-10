import asyncio
from pydantic import BaseModel
from agents import Agent, Runner, trace
from examples.auto_mode import input_with_fallback

"""
This example demonstrates a deterministic flow for a code generation pipeline:
1. The first agent generates a small code snippet based on user requirements
2. The second agent validates the snippet for correctness and coding best practices
3. If the snippet fails validation, we stop here
4. If it passes, the third agent generates unit tests for the code
5. The fourth agent creates a deployment-ready version of the code with tests included
"""

code_gen_agent = Agent(
    name="code_gen_agent",
    instructions="Generate a small Python function or snippet based on the user's requirements.",
)

class CodeValidatorOutput(BaseModel):
    correct: bool
    follows_best_practices: bool

code_validator_agent = Agent(
    name="code_validator_agent",
    instructions="Validate the given Python code snippet. Check if it is correct and follows coding best practices.",
    output_type=CodeValidatorOutput,
)

unit_test_agent = Agent(
    name="unit_test_agent",
    instructions="Write unit tests for the provided Python code snippet.",
    output_type=str,
)

deployment_agent = Agent(
    name="deployment_agent",
    instructions="Create a deployment-ready Python file including the code snippet and its unit tests.",
    output_type=str,
)

async def main():
    input_prompt = input_with_fallback(
        "Describe the functionality you want the code to implement: ",
        "Write a Python function that calculates the factorial of a number.",
    )

    with trace("Deterministic code generation flow"):
        # 1. Generate code
        code_result = await Runner.run(
            code_gen_agent,
            input_prompt,
        )
        print("Code snippet generated")

        # 2. Validate code
        validation_result = await Runner.run(
            code_validator_agent,
            code_result.final_output,
        )

        assert isinstance(validation_result.final_output, CodeValidatorOutput)
        if not validation_result.final_output.correct:
            print("Code snippet is incorrect. Stopping here.")
            exit(0)

        if not validation_result.final_output.follows_best_practices:
            print("Code snippet does not follow best practices. Stopping here.")
            exit(0)

        print("Code snippet is correct and follows best practices. Generating unit tests...")

        # 3. Generate unit tests
        tests_result = await Runner.run(
            unit_test_agent,
            code_result.final_output,
        )
        print("Unit tests generated")

        # 4. Create deployment-ready package
        deployment_result = await Runner.run(
            deployment_agent,
            f"{code_result.final_output}\n\n{tests_result.final_output}",
        )
        print(f"Deployment-ready code:\n{deployment_result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())
