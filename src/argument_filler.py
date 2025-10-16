import json
import time
from .loadModel import loadHeavyModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

from .tool_list.usable_tool import API_LIST

load_dotenv()

# --- Load heavy model once ---
model = loadHeavyModel()

# --- Template for SINGLE CALL ---
contextual_extraction_template = """
You are a master AI assistant that analyzes a user query and a multi-step tool plan to determine the correct arguments for each tool.

CRITICAL RULES:
- Output ONLY a JSON array.
- If the plan is [], output [] EXACTLY (no prose).
- Do NOT add/remove/reorder tools or arguments.
- Only edit "argument_value". Leave names/structure untouched.
- If a value depends on a previous tool, write exactly "$$PREV[index]" (index starts at 0).
  - NEVER use property paths with $$PREV (e.g., "$$PREV[0].task_ids" is forbidden).
  - If you believe a field like "task_ids" is needed, still output "$$PREV[index]" only.
- If a value is unknown, leave it as "".

--- CONTEXT ---
User Query: "{user_query}"

--- TOOL DOCUMENTATION (only tools present in the plan) ---
{tool_docs}

--- FULL PLAN (ONLY fill argument_value fields in this structure) ---
{plan_json}

--- NOW FILL THE PLAN BELOW ---
Output the fully filled JSON plan only, nothing else.
"""




contextual_prompt = ChatPromptTemplate.from_template(contextual_extraction_template)
parser = StrOutputParser()
contextual_extraction_chain = contextual_prompt | model | parser


# --- Helper Function to format API docs ---
def format_tool_docs(api_list: list) -> str:
    doc_string = ""
    for tool in api_list:
        doc_string += f"Tool Name: {tool['name']}\nDescription: {tool['description']}\n"
        if tool.get('arguments'):
            doc_string += "Arguments:\n"
            for arg in tool['arguments']:
                doc_string += f"- {arg['argument_name']} ({arg['argument_type']}): {arg['argument_description']}\n"
        doc_string += "---\n"
    return doc_string


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

# --- Main Execution ---
if __name__ == "__main__":
    user_query = input("Enter your query: ")

    try:
        print("Loading skeleton plan from 'output.json'...")
        with open("output.json", "r") as f:
            skeleton_plan_str = f.read().replace("who_am_i", "whoami")
            skeleton_plan = json.loads(skeleton_plan_str)

        filled_plan = fill_arguments_with_context(skeleton_plan, user_query)

        output_filename = "filled_output.json"
        with open(output_filename, "w") as f:
            json.dump(filled_plan, f, indent=4)

        print(f"\nSuccess! The filled plan has been saved to '{output_filename}'")

    except FileNotFoundError:
        print("Error: 'output.json' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")