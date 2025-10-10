import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

from tools import API_LIST

load_dotenv()

# --- LLM and Chain Setup ---
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

contextual_extraction_template = """
You are a master AI assistant that analyzes a user query and a multi-step tool plan to determine the correct arguments for each tool.

--- CONTEXT ---
User Query: "{user_query}"

--- THE FULL PLAN ---
You are currently filling in the arguments for the tool at index {current_tool_index}.
Here are all the steps in the plan:
{full_plan_str}

--- YOUR TASK ---
Your job is to determine the values for all arguments of the tool: "{tool_name}".
Tool Description: "{tool_desc}"

Arguments to Find:
{arguments_to_find_str}

--- INSTRUCTIONS ---
- Your output MUST be a single, valid JSON object mapping each argument_name to its extracted value.
- **CRITICAL**: To set an argument's value from a previous step, look at the plan and use "$$PREV[index]". For example, if the value for 'objects' should be the output of the tool at index 1 ('works_list'), the value should be "$$PREV[1]".
- Use the User Query to extract explicit values (e.g., "p0", "issue").
- Format list/array values as a JSON array (e.g., ["p0"]).
- If a value cannot be found in the query or from a previous step, use an empty string "".

EXAMPLE OUTPUT:
{{
  "work_ids": "$$PREV[2]",
  "sprint_id": "$$PREV[3]"
}}
"""

contextual_prompt = ChatPromptTemplate.from_template(contextual_extraction_template)
parser = StrOutputParser()
contextual_extraction_chain = contextual_prompt | model | parser

# --- Helper Function ---
def get_tool_details(tool_name):
    # Fix for who_am_i vs whoami inconsistency
    if tool_name == "whoami":
        tool_name = "who_am_i"
    for tool in API_LIST:
        if tool['name'] == tool_name:
            return tool
    return None

# --- Core Logic ---
def fill_arguments_with_context(plan: list, user_query: str) -> list:
    filled_plan = plan.copy()

    # Create a simple string representation of the full plan for context
    full_plan_str = ""
    for idx, step in enumerate(plan):
        full_plan_str += f"[{idx}] {step['tool_name']}\n"

    for i, tool_call in enumerate(filled_plan):
        tool_name = tool_call['tool_name']
        
        if not tool_call.get('arguments'):
            print(f"Skipping '{tool_name}' as it has no arguments.")
            continue

        tool_details = get_tool_details(tool_name)
        if not tool_details:
            print(f"Warning: Could not find details for tool '{tool_name}'")
            continue

        args_to_find_str = ""
        for arg in tool_details.get('arguments', []):
            args_to_find_str += f"- Name: {arg['argument_name']}, Description: {arg['argument_description']}\n"
        
        print(f"\nProcessing tool [{i}]: '{tool_name}'...")
        
        response_str = contextual_extraction_chain.invoke({
            "user_query": user_query,
            "current_tool_index": i,
            "full_plan_str": full_plan_str,
            "tool_name": tool_name,
            "tool_desc": tool_details['description'],
            "arguments_to_find_str": args_to_find_str
        })
        
        try:
            extracted_values = json.loads(response_str.strip().strip("```json").strip())
            
            for argument in tool_call['arguments']:
                arg_name = argument['argument_name']
                if arg_name in extracted_values:
                    # Special handling for array values that the LLM might return as a string
                    value = extracted_values[arg_name]
                    if "PREV" in str(value) and isinstance(value, list):
                        argument['argument_value'] = value[0] # Take the string out of the list
                    else:
                        argument['argument_value'] = value
                    print(f"  - Filled '{arg_name}': {argument['argument_value']}")

        except json.JSONDecodeError:
            print(f"  - Error: Failed to decode JSON for tool '{tool_name}'. Raw response: {response_str}")
            
    return filled_plan

# --- Main Execution Block ---
if __name__ == "__main__":
    user_query = "Summarize high severity tickets from the customer UltimateCustomer" # Example Query
    print(f"Using Query: \"{user_query}\"")
    
    try:
        print("Loading skeleton plan from 'output.json'...")
        with open("output.json", "r") as f:
            skeleton_plan_str = f.read().replace("who_am_i", "whoami")
            skeleton_plan = json.loads(skeleton_plan_str)
        
        filled_plan = fill_arguments_with_context(skeleton_plan, user_query)
        
        output_filename = "filled_output.json"
        with open(output_filename, "w") as f:
            json.dump(filled_plan, f, indent=4)
        
        print(f"\nSuccess! The corrected filled plan has been saved to '{output_filename}'")

    except FileNotFoundError:
        print("Error: 'output.json' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")