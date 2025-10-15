import json
from loadModel import loadHeavyModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Assuming usable_tool.py is in a subdirectory called 'tool_list' as per parser.py
# If it's in the same directory, change the import to: from usable_tool import API_LIST
from tool_list.usable_tool import API_LIST

load_dotenv()

def format_tool_docs(api_list: list) -> str:
    """
    Formats the tool documentation into a single string for the prompt.
    This function is consistent with the one in parser.py.
    """
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

def fill_arguments_with_context(skeleton_plan: list, query: str) -> dict:
    """
    Takes a skeleton plan (JSON with empty argument values) and the user query,
    then uses an LLM to fill in the argument values.

    Args:
        skeleton_plan: The list of tool calls with empty argument values.
        query: The original user query string.

    Returns:
        A dictionary representing the final, filled-out plan.
    """
    model = loadHeavyModel()  # Use a more capable model for this nuanced task
    formatted_tools = format_tool_docs(API_LIST)
    skeleton_plan_str = json.dumps(skeleton_plan, indent=4)

    prompt_template = """
    You are an expert AI agent. Your task is to intelligently fill in the 'argument_value' for a given JSON plan based on a user's query and the provided tool documentation.

    You must carefully analyze the user's query to extract the correct values. For tool outputs that feed into subsequent tools, you must use the '$$PREV[i]' syntax.

    ---
    CONTEXT:
    1. User Query: "{user_query}"

    2. Tool Documentation:
    {tools}

    3. Skeleton JSON Plan (to be filled):
    {skeleton_plan}
    ---

    INSTRUCTIONS:
    - Fill in the `argument_value` for each argument in the "Skeleton JSON Plan".
    - The values must be extracted or inferred from the "User Query".
    - If an argument's value should be the output of a previous step, use `$$PREV[i]`, where `i` is the 0-based index of the previous tool in the chain.
    - Ensure the data types of the values match the "Tool Documentation" (e.g., return a list of strings for 'array of strings').
    - Your output MUST BE ONLY the completed JSON object. Do not include any explanations, comments, or markdown formatting like ```json.

    FILLED JSON PLAN:
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    parser = StrOutputParser()
    chain = prompt | model | parser

    # Invoke the chain to get the filled JSON string
    response_str = chain.invoke({
        "tools": formatted_tools,
        "user_query": query,
        "skeleton_plan": skeleton_plan_str
    })
    
    # Clean up the string in case the LLM wraps it in markdown
    if response_str.startswith("```json"):
        response_str = response_str.strip("```json").strip()

    # Parse the final string into a Python dictionary and return it
    try:
        filled_json = json.loads(response_str)
        return filled_json
    except json.JSONDecodeError:
        print("Error: Failed to decode the argument filler LLM output into valid JSON.")
        print("Raw output received:", response_str)
        # Return the original skeleton to avoid a crash, though it will be incomplete
        return skeleton_plan

