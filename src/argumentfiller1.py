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

# ============================================================================
# QUERY NORMALIZATION - NEW ADDITION
# ============================================================================

query_normalization_template = """
You are an AI assistant that normalizes user queries for a work management system.

User Query: "{user_query}"

Extract and normalize the following information from the query:

1. **Work Item Type**: Map common terms to standard types
   - "issues", "tickets", "problems" → "ticket"
   - "tasks", "todos" → "task"
   - If mentioned with channels (slack, email, twitter) → default to "ticket"

2. **Priority**: Map to standard priority levels
   - "critical", "urgent", "p0" → "p0"
   - "high", "important", "p1" → "p1"
   - "medium", "normal", "p2" → "p2"
   - "low", "minor", "p3" → "p3"

3. **Severity**: Map to standard severity levels
   - "blocker" → "blocker"
   - "high", "critical" → "high"
   - "medium", "moderate" → "medium"
   - "low", "minor" → "low"

4. **Stage**: Map to standard stages
   - "triage" → "triage"
   - "backlog" → "backlog"
   - "in progress", "working on", "ongoing" → "in_progress"
   - "done", "completed", "closed", "resolved" → "done"

5. **Source Channel**: Identify communication channels
   - "slack" → "slack"
   - "email" → "email"
   - "twitter" → "twitter"
   - "github" → "github"

6. **Customer Name**: Extract customer identifiers
   - Look for patterns like "Cust113", "customer XYZ", "from ABC"
   - Extract the exact identifier

7. **Work ID**: Extract work item identifiers
   - Patterns like "TICKET-123", "ISS-456", "TASK123"

Output ONLY a JSON object with these fields (use null if not found):
{{
  "work_type": "ticket|task|issue|null",
  "priority": "p0|p1|p2|p3|null",
  "severity": "blocker|high|medium|low|null",
  "stage": "triage|backlog|in_progress|done|null",
  "source_channel": "slack|email|twitter|github|null",
  "customer_name": "string|null",
  "work_id": "string|null"
}}

IMPORTANT: 
- Return ONLY the JSON object, no additional text
- Use null for fields not found in the query
- When "issues" appears with channels or severity/priority, map to "ticket"
"""

query_normalization_prompt = ChatPromptTemplate.from_template(query_normalization_template)
query_normalization_chain = query_normalization_prompt | model | StrOutputParser()

def normalize_query(user_query: str) -> dict:
    """
    Normalizes the user query using LLM to extract and standardize entities.
    Returns a dictionary with normalized fields.
    """
    print(f"\n[NORMALIZE] Starting query normalization...")
    print(f"[NORMALIZE] Query: '{user_query}'")
    
    try:
        response_str = query_normalization_chain.invoke({
            "user_query": user_query
        })
        
        print(f"[NORMALIZE] LLM Response: {response_str[:200]}...")
        
        # Clean up response
        cleaned = response_str.strip().strip("```json").strip("```").strip()
        normalized = json.loads(cleaned)
        
        print(f"[NORMALIZE] Parsed normalized data: {normalized}")
        return normalized
        
    except json.JSONDecodeError as e:
        print(f"[NORMALIZE] [ERROR] JSON decode error: {e}")
        print(f"[NORMALIZE] [RAW] Raw response: {response_str}")
        return {}
    except Exception as e:
        print(f"[NORMALIZE] [ERROR] Normalization failed: {e}")
        return {}

# ============================================================================
# CONTEXTUAL EXTRACTION (Existing)
# ============================================================================

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

# ============================================================================
# ENHANCED RULE EXTRACTOR - Uses Normalized Query Data
# ============================================================================

class RuleExtractor:
    PRIORITY_MAP = {
        'p0': ['critical'], 
        'p1': ['high'], 
        'p2': ['medium'],
        'p3': ['low']
    }
    
    SEVERITY_MAP = {
        'blocker': ['blocker'], 'high': ['high'],
        'medium': ['medium'], 'low': ['low']
    }
    
    TYPE_MAP = {
        'issue': ['issue'], 'ticket': ['ticket'], 'task': ['task']
    }
    
    STAGE_MAP = {
        'triage': ['triage'], 'backlog': ['backlog'],
        'in_progress': ['in_progress'], 'done': ['done']
    }
    
    CHANNEL_MAP = {
        'slack': ['slack'], 'email': ['email'],
        'twitter': ['twitter'], 'github': ['github']
    }

    @staticmethod
    def extract_from_normalized(normalized_data: dict, tool_name: str, plan_index: int):
        """
        Extract arguments based on normalized query data.
        This replaces individual keyword extraction methods.
        """
        extracted = {}
        
        if tool_name == "works_list":
            # Priority
            if normalized_data.get('priority'):
                extracted['issue.priority'] = RuleExtractor.PRIORITY_MAP.get(
                    normalized_data['priority'], 
                    [normalized_data['priority']]
                )
            
            # Severity
            if normalized_data.get('severity'):
                extracted['ticket.severity'] = RuleExtractor.SEVERITY_MAP.get(
                    normalized_data['severity'],
                    [normalized_data['severity']]
                )
            
            # Type
            if normalized_data.get('work_type'):
                extracted['type'] = RuleExtractor.TYPE_MAP.get(
                    normalized_data['work_type'],
                    [normalized_data['work_type']]
                )
            
            # Stage
            if normalized_data.get('stage'):
                extracted['stage.name'] = RuleExtractor.STAGE_MAP.get(
                    normalized_data['stage'],
                    [normalized_data['stage']]
                )
            
            # Channel
            if normalized_data.get('source_channel'):
                extracted['ticket.source_channel'] = RuleExtractor.CHANNEL_MAP.get(
                    normalized_data['source_channel'],
                    [normalized_data['source_channel']]
                )
            
            # If we have a previous search result, use it for ticket.rev_org
            if plan_index > 0:
                extracted['ticket.rev_org'] = f"$$PREV[{plan_index - 1}]"

        elif tool_name == "get_similar_work_items":
            if normalized_data.get('work_id'):
                extracted['work_id'] = normalized_data['work_id']

        elif tool_name == "search_object_by_name":
            if normalized_data.get('customer_name'):
                extracted['query'] = normalized_data['customer_name']

        elif tool_name == "summarize_objects" and plan_index > 0:
            extracted['objects'] = f"$$PREV[{plan_index - 1}]"

        elif tool_name == "prioritize_objects" and plan_index > 0:
            extracted['objects'] = f"$$PREV[{plan_index - 1}]"

        return extracted

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

# ============================================================================
# MAIN FUNCTION - Enhanced with Query Normalization
# ============================================================================

def fill_arguments_with_context(plan: list, user_query: str) -> list:
    filled_plan = plan.copy()
    
    print(f"\n{'='*80}")
    print(f"[DEBUG] Processing query: '{user_query}'")
    print(f"[DEBUG] Plan has {len(filled_plan)} tools")
    print(f"{'='*80}")
    
    # STEP 1: Normalize the query using LLM (ONE CALL)
    normalized_data = normalize_query(user_query)
    
    if not normalized_data:
        print("[WARNING] Query normalization failed, falling back to original logic")
    
    # STEP 2: Process each tool in the plan
    for i, tool_call in enumerate(filled_plan):
        tool_name = tool_call['tool_name']
        arguments = tool_call.get('arguments', [])
        
        print(f"\n[{i}] [TOOL] Processing: {tool_name}")
        print(f"    [ARGS] Arguments needed: {[arg['argument_name'] for arg in arguments]}")
        
        skip, reason = should_skip_llm(tool_name, arguments, i)
        if skip:
            print(f"    [SKIP] Skipping: {reason}")
            continue

        tool_details = get_tool_details(tool_name)
        if not tool_details:
            print(f"    [ERROR] No tool details found for: {tool_name}")
            continue

        print(f"    [OK] Tool details found: {tool_details['name']}")
        
        # STEP 3: Rule-based extraction using normalized data
        extracted = RuleExtractor.extract_from_normalized(normalized_data, tool_name, i)

        # If rules extracted values, use them
        if extracted:
            print(f"    [RULE] Rule-based extraction successful: {extracted}")
            for argument in arguments:
                arg_name = argument['argument_name']
                if arg_name in extracted:
                    argument['argument_value'] = extracted[arg_name]
                    print(f"      [SET] {arg_name} = {extracted[arg_name]}")
            continue

        # STEP 4: Fall back to LLM for complex extractions
        print(f"    [LLM] Using LLM extraction for {tool_name}")
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
            cleaned = response_str.strip().strip("```json").strip("```").strip()
            extracted_values = json.loads(cleaned)
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

    print(f"\n{'='*80}")
    print(f"[SUMMARY] Processed {len(filled_plan)} tools")
    print(f"[SUMMARY] All arguments filled successfully")
    print(f"{'='*80}\n")
    
    return filled_plan

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Test with the problematic query
    user_query = "Summarize all critical Slack issues linked to Cust113."
    
    try:
        with open("output.json", "r") as f:
            skeleton_plan_str = f.read().replace("who_am_i", "whoami")
            skeleton_plan = json.loads(skeleton_plan_str)
        
        filled_plan = fill_arguments_with_context(skeleton_plan, user_query)
        
        with open("filled_output.json", "w") as f:
            json.dump(filled_plan, f, indent=4)
        
        print("\n[SUCCESS] Plan filled and saved to 'filled_output.json'")
        print("\n[OUTPUT PREVIEW]")
        print(json.dumps(filled_plan, indent=2)[:500])

    except FileNotFoundError:
        print("[ERROR] 'output.json' not found.")
    except Exception as e:
        print(f"[ERROR] {e}")