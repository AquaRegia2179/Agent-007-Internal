from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import json

from tools import API_LIST # Assuming tools.py is in the same directory

load_dotenv()

# Create a single LLM chain instance to be reused
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", # Use a powerful model for extraction
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# A specialized prompt for extracting a single argument value
extraction_prompt_template = """
You are an expert at extracting specific information from a user's query.
Your task is to find the value for a single argument based on the user's request.

--- CONTEXT ---
User Query: "{user_query}"
Tool Name: "{tool_name}"
Argument Name: "{arg_name}"
Argument Description: "{arg_desc}"
Argument Type: "{arg_type}"
---

Based on the context above, what is the value for the "{arg_name}" argument?

- If the argument's value comes from the output of a previous tool (like a list of objects to be summarized), respond with "$$PREV[index]". For example, if summarizing the output of the first tool (index 0), respond with "$$PREV[0]".
- If the value is explicitly in the user query, extract it.
- Format list or array values as a JSON array (e.g., ["p0", "p1"]).
- Format boolean values as "true" or "false".
- If no suitable value can be found in the query, respond with an empty string "".

Your response should ONLY be the extracted value and nothing else.
"""

extraction_prompt = ChatPromptTemplate.from_template(extraction_prompt_template)
parser = StrOutputParser()
extraction_chain = extraction_prompt | model | parser

# Function to get the details of a tool and its argument from API_LIST
def get_arg_details(tool_name, arg_name):
    for tool in API_LIST:
        if tool['name'] == tool_name:
            if tool.get('arguments'):
                for arg in tool['arguments']:
                    if arg['argument_name'] == arg_name:
                        return tool['description'], arg['argument_description'], arg['argument_type']
    return None, None, None

def fill_argument_values(plan: list, user_query: str) -> list:
    """
    Takes a skeleton JSON plan and a user query, and fills in the argument_values.
    """
    filled_plan = plan.copy()
    
    for i, tool_call in enumerate(filled_plan):
        tool_name = tool_call['tool_name']
        if not tool_call.get('arguments'):
            continue

        for argument in tool_call['arguments']:
            arg_name = argument['argument_name']
            
            # Get context for the prompt
            tool_desc, arg_desc, arg_type = get_arg_details(tool_name, arg_name)
            
            if not arg_desc:
                print(f"Warning: Could not find details for {tool_name}.{arg_name}")
                continue

            # Invoke the LLM to find the value
            print(f"Finding value for: {tool_name} -> {arg_name}...")
            value = extraction_chain.invoke({
                "user_query": user_query,
                "tool_name": tool_name,
                "arg_name": arg_name,
                "arg_desc": arg_desc,
                "arg_type": arg_type,
            })
            
            # Clean up the response from the LLM
            value = value.strip().strip('`"\'')
            
            # Update the argument_value in the plan
            argument['argument_value'] = value

    return filled_plan
  
if __name__ == "__main__":
    # 1. Get the original user query from the user
    user_query = input("Enter the original user query that generated the skeleton: ")
    
    if not user_query:
        print("Error: The user query cannot be empty.")
    else:
        try:
            # 2. Load the skeleton plan from the existing output.json file
            print("Loading skeleton plan from 'output.json'...")
            with open("output.json", "r") as f:
                skeleton_plan = json.load(f)
            
            # 3. Call the main function to process and fill the values
            print("Processing and filling argument values...")
            filled_plan = fill_argument_values(skeleton_plan, user_query)
            
            # 4. Save the result to a new file
            output_filename = "filled_output.json"
            with open(output_filename, "w") as f:
                json.dump(filled_plan, f, indent=4)
            
            print(f"\nSuccess! The filled plan has been saved to '{output_filename}'")

        except FileNotFoundError:
            print("Error: 'output.json' not found. Make sure the file exists.")
        except json.JSONDecodeError:
            print("Error: 'output.json' contains invalid JSON. Please check the file.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
