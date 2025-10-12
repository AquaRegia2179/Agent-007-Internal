from loadModel import loadHeavyModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import json
import re

from tool_list.usable_tool import API_LIST

load_dotenv()

def format_tool_docs(api_list: list) -> str:
    doc_string = ""
    for tool in api_list:
        doc_string += f"Tool Name: {tool['name']}\n"
        doc_string += f"Description: {tool['description']}\n"
        if tool.get('arguments'):
            doc_string += "Arguments:\n"
            for arg in tool['arguments']:
                doc_string += f"- {arg['argument_name']} ({arg['argument_type']}): {arg['argument_description']}\n"
        doc_string += "---\n"
    return doc_string

def generate_tool_chain(query: str) -> str:
    model = loadHeavyModel()
    formatted_tools = format_tool_docs(API_LIST)


    prompt_template = """
    You are a specialized AI that converts user queries into valid JSON tool plans.
    Your ONLY output must be a raw JSON array, without any other text, explanations, or markdown formatting.

    --- AVAILABLE TOOLS ---
    {tools}
    --- END TOOLS ---

    --- EXAMPLE ---
    User Query: "Find the account owner for Contoso and then list their open tickets."
    JSON Output:
    [
        {{
            "tool_name": "search_object_by_name",
            "arguments": [
                {{
                    "argument_name": "name",
                    "argument_value": ""
                }}
            ]
        }},
        {{
            "tool_name": "works_list",
            "arguments": [
                {{
                    "argument_name": "ticket.rev_org",
                    "argument_value": ""
                }},
                {{
                    "argument_name": "ticket.state",
                    "argument_value": ""
                }}
            ]
        }}
    ]
    --- END EXAMPLE ---

    Now, based on the available tools and the example, process the following query.

    User Query: "{user_query}"

    CRITICAL: Your response must be only the JSON array, starting with `[` and ending with `]`.
    JSON Output:
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    parser = StrOutputParser()
    chain = prompt | model | parser

    response = chain.invoke({
        "tools": formatted_tools,
        "user_query": query
    })
    pattern = r"<think>.*?</think>"
    response = re.sub(pattern, "", response, flags=re.DOTALL).strip()
    return response

if __name__ == "__main__":
    while True:
        # 1. Ask the user for a query
        user_query = input("Enter your query (or type 'exit' to quit): ")
        
        if user_query.lower() == 'exit':
            break
            
        if not user_query:
            print("Please enter a valid query.")
            continue

        # Generate the tool chain string from the LLM
        json_string_output = generate_tool_chain(user_query)
        
        # Clean up the string in case the LLM wraps it in markdown
        if json_string_output.startswith("```json"):
            json_string_output = json_string_output.strip("```json").strip()
        
        try:
            # 2. Save the output to a JSON file
            parsed_json = json.loads(json_string_output)
            with open("output.json", "w") as f:
                json.dump(parsed_json, f, indent=4)
            
            print(f"Success! Output saved to output.json")

        except json.JSONDecodeError:
            print("Error: Failed to decode the LLM output into valid JSON.")
            print("Raw output received:", json_string_output)