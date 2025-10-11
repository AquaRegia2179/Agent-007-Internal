from loadModel import loadModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import json

from tools import API_LIST

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
    model = loadModel()
    formatted_tools = format_tool_docs(API_LIST)

    prompt_template = """
    Generate a JSON tool-call plan for the user's query.
    Output a JSON array where each object has a `tool_name` and `arguments`. For each argument, provide the `argument_name` but leave `argument_value` as an empty string ("").
    Schema:
    ```json
    [{{"tool_name":"name_of_the_tool","arguments":[{{"argument_name":"name_of_the_argument","argument_value":""}}]}}]
    ```
    Tool List: {tools}
    User Query: "{user_query}"
    Your output should only be the JSON array, with no other text or formatting.
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    parser = StrOutputParser()
    chain = prompt | model | parser

    response = chain.invoke({
        "tools": formatted_tools,
        "user_query": query
    })
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