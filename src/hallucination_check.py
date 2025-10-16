import json

def get_verification_prompt(plan_obj, user_query):
    """
    Creates a prompt for the LLM to verify the generated plan.
    """
    plan_str = json.dumps(plan_obj, indent=4)
    prompt = f"""
You are an expert plan verifier. Your task is to determine if a generated plan is a correct and logical way to fulfill a user's query.

Analyze the following:
1. Original User Query: "{user_query}"
2. Generated Plan:
```json
{plan_str}
```

Does the generated plan accurately and logically address the user's query?
- Check if the tools chosen are appropriate for the query.
- Check if the arguments for each tool are correct and relevant based on the query.
- Check if the sequence of tools makes sense to achieve the user's goal.

Respond with only "YES" if the plan is correct, logical, and directly addresses the query.
Respond with "NO" followed by a concise, one-sentence explanation if the plan is incorrect, illogical, or hallucinated.
"""
    return prompt

def verify_plan(filled_plan, user_query, llm_instance):
    """
    Checks if the generated plan is a hallucination or incorrect using a LangChain model.

    Args:
        filled_plan (dict): The final plan with all arguments filled.
        user_query (str): The original query from the user.
        llm_instance: An instantiated LangChain chat model.

    Returns:
        tuple[bool, str]: A tuple containing a boolean (True if valid, False if not)
                           and a message string.
    """
    print("\nVerifying the plan against the user query...")
    verification_prompt = get_verification_prompt(filled_plan, user_query)

    try:
        # Use the passed-in LangChain model instance
        response = llm_instance.invoke(verification_prompt)
        llm_response = response.content.strip()

        print(f"Verifier LLM response: '{llm_response}'")

        if llm_response.upper().startswith("YES"):
            return True, "Plan verified successfully."
        elif llm_response.upper().startswith("NO"):
            # Extract the reason after the "NO"
            reason = llm_response[2:].strip(": ").strip()
            return False, f"Plan rejected. Reason: {reason}"
        else:
            # Handle cases where the model doesn't follow instructions
            return False, f"Verifier response was not in the expected 'YES' or 'NO' format. Full response: {llm_response}"

    except Exception as e:
        print(f"Error during verification LLM call: {e}")
        return False, "Failed to get a response from the verifier LLM."

