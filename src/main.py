import os
import json
from dotenv import load_dotenv

# Import the high-level functions from your other modules
from .parser import generate_tool_chain
from .argument_filler import fill_arguments_with_context

# Load environment variables from your .env file
load_dotenv()

def main():
    """
    Main function to run the two-step agent planning process.
    """
    while True:
        user_query = input("\nEnter your query (or type 'exit' to quit): ")

        if user_query.lower() == 'exit':
            break

        if not user_query:
            print("Please enter a valid query.")
            continue

        try:
            # --- Step 1: Generate the Skeleton Plan ---
            print("Step 1: Generating tool chain skeleton...")
            skeleton_plan_str = generate_tool_chain(user_query)

            # Clean the raw string output from the LLM
            if skeleton_plan_str.startswith("```json"):
                skeleton_plan_str = skeleton_plan_str.strip("```json").strip()

            # Parse the skeleton string into a Python object
            skeleton_plan_obj = json.loads(skeleton_plan_str)

            # --- Step 2: Fill the Argument Values ---
            print("\nStep 2: Filling argument values based on the skeleton...")
            filled_plan = fill_arguments_with_context(skeleton_plan_obj, user_query)

            # --- Step 3: Save the Final Result ---
            output_filename = "filled_output.json"
            with open(output_filename, "w") as f:
                json.dump(filled_plan, f, indent=4)

            print(f"\nSuccess! The final plan has been saved to '{output_filename}'")

        except json.JSONDecodeError:
            print("\nError: The planner failed to return valid JSON.")
            print("Raw output received:", skeleton_plan_str)
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()