import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

from tools import API_LIST

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

contextual_extraction_template = """
You are an AI assistant that determines correct arguments for tools.

User Query: "{user_query}"

Tool: "{tool_name}"
Description: "{tool_desc}"

Arguments to Find:
{arguments_to_find_str}

Output a JSON object with argument names mapped to values.
Use "$$PREV[index]" to reference previous tool outputs.
Format arrays as JSON arrays (e.g., ["value1", "value2"]).
Use empty string "" if value not found.

EXAMPLE:
{{"ticket.rev_org": "$$PREV[0]", "type": ["ticket"]}}
"""

contextual_prompt = ChatPromptTemplate.from_template(contextual_extraction_template)
contextual_extraction_chain = contextual_prompt | model | StrOutputParser()

def get_tool_details(tool_name):
    if tool_name == "whoami":
        tool_name = "who_am_i"
    for tool in API_LIST:
        if tool['name'] == tool_name:
            return tool
    return None

class RuleExtractor:
    PRIORITY_MAP = {
        'p0': ['p0'], 'critical': ['p0'],
        'p1': ['p1'], 'high': ['p1'],
        'p2': ['p2'], 'medium': ['p2'],
        'p3': ['p3'], 'low': ['p3']
    }
    
    SEVERITY_MAP = {
        'blocker': ['blocker'], 'high': ['high'],
        'medium': ['medium'], 'low': ['low']
    }
    
    TYPE_MAP = {
        'issue': ['issue'],
        'ticket': ['ticket'],
        'task': ['task']
    }
    
    STAGE_MAP = {
        'triage': ['triage'], 'backlog': ['backlog'],
        'in progress': ['in_progress'], 'inprogress': ['in_progress'],
        'done': ['done'], 'closed': ['closed']
    }
    
    CHANNEL_MAP = {
        'slack': ['slack'], 'email': ['email'],
        'twitter': ['twitter'], 'github': ['github']
    }

    @staticmethod
    def extract_priority(query_lower):
        for keyword, value in RuleExtractor.PRIORITY_MAP.items():
            if keyword in query_lower:
                return value
        return None

    @staticmethod
    def extract_severity(query_lower):
        for keyword, value in RuleExtractor.SEVERITY_MAP.items():
            if keyword in query_lower:
                return value
        return None

    @staticmethod
    def extract_type(query_lower):
        for keyword, value in RuleExtractor.TYPE_MAP.items():
            if keyword in query_lower:
                return value
        return None

    @staticmethod
    def extract_stage(query_lower):
        for keyword, value in RuleExtractor.STAGE_MAP.items():
            if keyword in query_lower:
                return value
        return None

    @staticmethod
    def extract_channel(query_lower):
        for keyword, value in RuleExtractor.CHANNEL_MAP.items():
            if keyword in query_lower:
                return value
        return None

    @staticmethod
    def extract_work_id(query):
        pattern = r'([A-Z]+-\d+|[A-Z]+\d+)'
        match = re.search(pattern, query, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def extract_customer_name(query):
        patterns = [
            r'customer\s+([A-Za-z0-9_\-]+)',
            r'from\s+([A-Za-z0-9_\-]+)',
            r'cust(?:omer)?\s*([A-Za-z0-9_\-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0).split()[-1]
        return None

def should_skip_llm(tool_name, arguments, plan_index):
    """Check if tool should skip LLM call"""
    # No arguments
    if not arguments:
        return True, "no_args"
    
    # Check if all args already have values ($$PREV or other values)
    all_have_values = all(
        arg.get('argument_value', '').strip() != ''
        for arg in arguments
    )
    if all_have_values:
        return True, "all_have_values"
    
    return False, None

def fill_arguments_with_context(plan: list, user_query: str) -> list:
    filled_plan = plan.copy()
    query_lower = user_query.lower()
    
    # Statistics tracking
    stats = {
        'total_tools': len(filled_plan),
        'llm_calls': 0,
        'rule_extractions': 0,
        'skipped': 0,
        'errors': 0
    }
    
    print(f"\n[DEBUG] Processing query: '{user_query}'")
    print(f"[DEBUG] Plan has {len(filled_plan)} tools")
    
    for i, tool_call in enumerate(filled_plan):
        tool_name = tool_call['tool_name']
        arguments = tool_call.get('arguments', [])
        
        print(f"\n[{i}] [TOOL] Processing: {tool_name}")
        print(f"    [ARGS] Arguments needed: {[arg['argument_name'] for arg in arguments]}")
        
        skip, reason = should_skip_llm(tool_name, arguments, i)
        if skip:
            print(f"    [SKIP] Skipping: {reason}")
            stats['skipped'] += 1
            continue

        tool_details = get_tool_details(tool_name)
        if not tool_details:
            print(f"    [ERROR] No tool details found for: {tool_name}")
            stats['errors'] += 1
            continue

        print(f"    [OK] Tool details found: {tool_details['name']}")
        extracted = {}

        # Rule-based extraction for specific tools
        if tool_name == "works_list":
            priority = RuleExtractor.extract_priority(query_lower)
            if priority:
                extracted['issue.priority'] = priority
            
            severity = RuleExtractor.extract_severity(query_lower)
            if severity:
                extracted['ticket.severity'] = severity
            
            type_val = RuleExtractor.extract_type(query_lower)
            if type_val:
                extracted['type'] = type_val
            
            stage = RuleExtractor.extract_stage(query_lower)
            if stage:
                extracted['stage.name'] = stage
            
            channel = RuleExtractor.extract_channel(query_lower)
            if channel:
                extracted['ticket.source_channel'] = channel
            
            # If we have a previous search result, use it for ticket.rev_org
            if i > 0:
                extracted['ticket.rev_org'] = f"$$PREV[{i - 1}]"

        elif tool_name == "get_similar_work_items":
            work_id = RuleExtractor.extract_work_id(user_query)
            if work_id:
                extracted['work_id'] = work_id

        elif tool_name == "search_object_by_name":
            customer = RuleExtractor.extract_customer_name(user_query)
            if customer:
                extracted['query'] = customer

        elif tool_name == "summarize_objects" and i > 0:
            extracted['objects'] = f"$$PREV[{i - 1}]"

        elif tool_name == "prioritize_objects" and i > 0:
            extracted['objects'] = f"$$PREV[{i - 1}]"

        # If rules extracted values, use them
        if extracted:
            print(f"    [RULE] Rule-based extraction successful: {extracted}")
            stats['rule_extractions'] += 1
            for argument in arguments:
                arg_name = argument['argument_name']
                if arg_name in extracted:
                    argument['argument_value'] = extracted[arg_name]
                    print(f"      [SET] {arg_name} = {extracted[arg_name]}")
            continue

        # Fall back to LLM
        print(f"    [LLM] Using LLM extraction for {tool_name}")
        stats['llm_calls'] += 1
        args_to_find_str = ""
        for arg in tool_details.get('arguments', []):
            args_to_find_str += f"- {arg['argument_name']}: {arg['argument_description']}\n"

        print(f"    [CALL] Calling LLM...")
        response_str = contextual_extraction_chain.invoke({
            "user_query": user_query,
            "tool_name": tool_name,
            "tool_desc": tool_details['description'],
            "arguments_to_find_str": args_to_find_str
        })

        print(f"    [RESPONSE] LLM response: {response_str[:150]}...")
        try:
            extracted_values = json.loads(response_str.strip().strip("```json").strip())
            print(f"    [PARSE] Parsed LLM values: {extracted_values}")
            for argument in arguments:
                arg_name = argument['argument_name']
                if arg_name in extracted_values:
                    value = extracted_values[arg_name]
                    if "$$PREV" in str(value) and isinstance(value, list):
                        argument['argument_value'] = value[0]
                    else:
                        argument['argument_value'] = value
                    print(f"      [SET] {arg_name} = {value}")
        except json.JSONDecodeError as e:
            print(f"    [ERROR] JSON decode error: {e}")
            print(f"    [RAW] Raw response: {response_str}")
            stats['errors'] += 1

    # Print statistics
    print(f"\n[STATISTICS] Processing Summary:")
    print(f"    Total tools: {stats['total_tools']}")
    print(f"    LLM calls: {stats['llm_calls']}")
    print(f"    Rule-based extractions: {stats['rule_extractions']}")
    print(f"    Skipped tools: {stats['skipped']}")
    print(f"    Errors: {stats['errors']}")
    
    # Calculate percentages
    if stats['total_tools'] > 0:
        llm_percentage = (stats['llm_calls'] / stats['total_tools']) * 100
        rule_percentage = (stats['rule_extractions'] / stats['total_tools']) * 100
        skip_percentage = (stats['skipped'] / stats['total_tools']) * 100
        
        print(f"\n[PERCENTAGES]")
        print(f"    LLM usage: {llm_percentage:.1f}%")
        print(f"    Rule usage: {rule_percentage:.1f}%")
        print(f"    Skip rate: {skip_percentage:.1f}%")
    
    print(f"\n[SUMMARY] Processed {len(filled_plan)} tools")
    print(f"[SUMMARY] All arguments filled successfully")
    
    return filled_plan

if __name__ == "__main__":
    user_query = "Summarize high severity tickets from the customer UltimateCustomer"
    
    try:
        with open("output.json", "r") as f:
            skeleton_plan_str = f.read().replace("who_am_i", "whoami")
            skeleton_plan = json.loads(skeleton_plan_str)
        
        filled_plan = fill_arguments_with_context(skeleton_plan, user_query)
        
        with open("filled_output.json", "w") as f:
            json.dump(filled_plan, f, indent=4)
        
        print("\n[SUCCESS] Plan filled and saved to 'filled_output.json'")

    except FileNotFoundError:
        print("[ERROR] 'output.json' not found.")
    except Exception as e:
        print(f"[ERROR] {e}")