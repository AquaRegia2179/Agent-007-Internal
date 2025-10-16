import os
import json
from dotenv import load_dotenv

# Import your custom model loaders
from loadModel import loadSmallModel, loadHeavyModel

# Import the high-level functions from your other modules
from .parser import generate_tool_chain
from .argument_filler import fill_arguments_with_context
from hallucination_check import verify_plan

# Load environment variables from your .env file
load_dotenv()

def main():
    """
    Main function to run the multi-step agent planning process.
    """
    # Load the models once at the start
    print("Loading models...")
    try:
        heavy_model = loadHeavyModel() # For plan generation
        small_model = loadSmallModel() # For filling arguments and verification
        print("Models loaded successfully.")
    except Exception as e:
        print(f"Fatal Error loading models: {e}")
        print("Please ensure your .env file is set up correctly and all dependencies are installed.")
        return

    while True:
        user_query = input("\nEnter your query (or type 'exit' to quit): ")

        if user_query.lower() == 'exit':
            break

        if not user_query:
            print("Please enter a valid query.")
            continue

        max_retries = 3
        feedback = None
        last_failed_plan = None
        final_plan = None
        is_valid = False

        for attempt in range(max_retries):
            try:
                current_prompt = user_query
                # If there's feedback from a previous failed attempt, construct a new prompt
                if feedback:
                    print(f"\n--- Retrying plan generation (Attempt {attempt + 1}/{max_retries})... ---")
                    current_prompt = f"""
Original User Query: "{user_query}"

A previous attempt to generate a plan failed. Please create a new plan that corrects the following error.
Error: "{feedback}"
Failed Plan:
{json.dumps(last_failed_plan, indent=2)}

Generate a corrected JSON tool chain based on the original query and the error feedback.
"""

                # --- Step 1: Generate the Skeleton Plan ---
                print("\n--- Step 1: Generating tool chain skeleton... ---")
                skeleton_plan_str = generate_tool_chain(current_prompt)

                if not skeleton_plan_str:
                    print("Error: Failed to generate a skeleton plan.")
                    feedback = "The model failed to generate any output for the skeleton plan."
                    last_failed_plan = {"error": "No output from skeleton generator"}
                    continue # Move to the next attempt

                if skeleton_plan_str.startswith("```json"):
                    skeleton_plan_str = skeleton_plan_str.strip("```json").strip()

                skeleton_plan_obj = json.loads(skeleton_plan_str)

                # --- Step 2: Fill the Argument Values ---
                print("\n--- Step 2: Filling argument values... ---")
                filled_plan = fill_arguments_with_context(skeleton_plan_obj, user_query,)

                # --- Step 3: Hallucination and Correctness Check ---
                print("\n--- Step 3: Verifying correctness of the final plan... ---")
                is_valid, message = verify_plan(filled_plan, user_query, small_model)

                if is_valid:
                    print("\nPlan verified successfully!")
                    final_plan = filled_plan
                    break  # Exit the retry loop on success
                else:
                    print(f"\nValidation Failed: {message}")
                    feedback = message
                    last_failed_plan = filled_plan
                    if attempt == max_retries - 1:
                        print("\nMaximum retries reached. Failed to generate a valid plan for this query.")

            except json.JSONDecodeError:
                print("\nError: The planner failed to return valid JSON.")
                print("Raw output received:", skeleton_plan_str)
                feedback = "The model returned invalid JSON. Please ensure the output is a valid JSON object."
                last_failed_plan = {"raw_output": skeleton_plan_str}
            except Exception as e:
                print(f"\nAn unexpected error occurred during attempt {attempt + 1}: {e}")
                # For unexpected errors, it might be better to stop retrying for this query
                break

        # --- Step 4: Save the Final Result (only if a valid plan was created) ---
        if final_plan:
            output_filename = "filled_output.json"
            with open(output_filename, "w") as f:
                json.dump(final_plan, f, indent=4)

            print(f"\nSuccess! The final, verified plan has been saved to '{output_filename}'")
            print("Final Plan:")
            print(json.dumps(final_plan, indent=4))

if __name__ == "__main__":
    # Note: This script assumes your other functions in 'parser.py' and
    # 'argument_filler.py' are also updated to accept a model instance, like so:
    #   def generate_tool_chain(query, model): ...
    #   def fill_arguments_with_context(skeleton, query, model): ...
    main()

