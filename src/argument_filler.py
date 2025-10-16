import json
import time
from loadModel import loadSmallModel, loadHeavyModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

from tool_list.usable_tool import API_LIST

load_dotenv()

# --- Load heavy model once ---
model = loadHeavyModel("llama70b")

# --- Template for SINGLE CALL ---
contextual_extraction_template = """
You are a master AI assistant that analyzes a user query and a multi-step tool plan to determine the correct arguments for each tool.

```json
--- CONTEXT ---
User Query: "{user_query}"

--- TOOL DOCUMENTATION ---
{tool_docs}

--- FULL PLAN ---
The plan is a JSON array of steps. Each step has:
- tool_name
- arguments (each with argument_name and argument_value = "")

{plan_json}

--- TASK ---
Your job is to fill in *all* argument_value fields for each step in the plan, using the user query and context.
If a value depends on the output of a previous tool, write "$$PREV[index]" (where index is that tool's number starting from 0).

- Keep the same JSON structure.
- Only replace empty argument_value fields.
- Do NOT add or remove tools or arguments.
- If you cannot determine a value, leave it as "".

--- EXAMPLE FORMAT ---
Input:
[
  {{
    "tool_name": "search_object_by_name",
    "arguments": [{{"argument_name": "query", "argument_value": ""}}]
  }},
  {{
    "tool_name": "works_list",
    "arguments": [
      {{"argument_name": "ticket.rev_org", "argument_value": ""}},
      {{"argument_name": "type", "argument_value": ""}}
    ]
  }}
]

Output:
[
  {{
    "tool_name": "search_object_by_name",
    "arguments": [{{"argument_name": "query", "argument_value": "Contoso"}}]
  }},
  {{
    "tool_name": "works_list",
    "arguments": [
      {{"argument_name": "ticket.rev_org", "argument_value": "$$PREV[0]"}},
      {{"argument_name": "type", "argument_value": ["ticket"]}}
    ]
  }}
]

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
    tool_docs = format_tool_docs(API_LIST)
    plan_json = json.dumps(plan, indent=4)

    print("Sending single LLM request to fill all arguments...")
    response_str = contextual_extraction_chain.invoke({
        "user_query": user_query,
        "tool_docs": tool_docs,
        "plan_json": plan_json
    })

    response_str = response_str.strip().replace("```json", "").replace("```", "").strip()

    try:
        filled_plan = json.loads(response_str)
        print("Successfully parsed LLM response into JSON")
        return filled_plan
    except json.JSONDecodeError:
        print("Failed to decode LLM output. Raw response:")
        print(response_str)
        return plan


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