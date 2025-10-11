# argument_filler_optimized.py
from __future__ import annotations

import json
import os
import hashlib
from functools import lru_cache
from typing import Dict, List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from loadModel import loadSmallModel
from usable_tool import API_LIST

load_dotenv()

# ---------------------------
# Model + chain (deterministic)
# ---------------------------
model = loadSmallModel()  # keep your lightweight model

# Ultra-compact prompt
_TEMPLATE = """
Fill argument values for ONE tool in a multi-step plan.

USER: "{user_query}"

PLAN (index:name):
{plan_brief}

TARGET: step [{current_tool_index}] -> {tool_name}

ARGS (name:type):
{args_brief}

Rules:
- Return ONLY a JSON object mapping argument_name -> value.
- Use "$$PREV[k]" to reference the output of step k.
- Lists must be JSON arrays. If unknown, use "" (or [] for arrays).
"""

_prompt = ChatPromptTemplate.from_template(_TEMPLATE)
_parser = StrOutputParser()
_chain = _prompt | model | _parser

# ---------------------------
# Helpers
# ---------------------------
def _clean_fenced_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```json"):
        s = s[len("```json"):].strip()
    if s.endswith("```"):
        s = s[:-3].strip()
    return s

def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()

def _get_tool_details(tool_name: str) -> dict | None:
    # handle alias only at lookup-time; do NOT mutate file contents
    if tool_name == "whoami":
        tool_name = "who_am_i"
    for t in API_LIST:
        if t["name"] == tool_name:
            return t
    return None

# Small memo cache for identical fills (query+plan+tool+args)
_CACHE: Dict[str, Dict] = {}

@lru_cache(maxsize=512)
def _invoke_cached(fp: str) -> str:
    return _chain.invoke(_CACHE[fp])

# ---------------------------
# Core logic
# ---------------------------
def fill_arguments_with_context(plan: List[dict], user_query: str, verbose: bool = True) -> List[dict]:
    # deep copy via JSON to avoid mutating caller data
    filled_plan = json.loads(json.dumps(plan))

    # minimal plan outline to save tokens
    plan_brief = "\n".join(f"[{idx}] {step.get('tool_name','')}" for idx, step in enumerate(plan))

    for i, tool_call in enumerate(filled_plan):
        tool_name = tool_call.get("tool_name", "")

        # Skip tools without arguments
        args = tool_call.get("arguments") or []
        if not args:
            if verbose:
                print(f"Skipping '{tool_name}' as it has no arguments.")
            continue

        # If everything is already filled (non-empty), skip LLM call
        if all(a.get("argument_value") not in ("", []) for a in args):
            if verbose:
                print(f"Skipping '{tool_name}' — arguments already filled.")
            continue

        tool_details = _get_tool_details(tool_name)
        if not tool_details:
            if verbose:
                print(f"Warning: Could not find details for tool '{tool_name}'")
            continue

        arg_specs = tool_details.get("arguments", [])
        args_brief = ", ".join(f"{a['argument_name']}:{a['argument_type']}" for a in arg_specs)
        arg_type_map = {a["argument_name"]: a.get("argument_type", "").lower() for a in arg_specs}

        if verbose:
            print(f"\nProcessing tool [{i}]: '{tool_name}'...")

        payload = {
            "user_query": user_query,
            "current_tool_index": i,
            "plan_brief": plan_brief,
            "tool_name": tool_name,
            "args_brief": args_brief,
        }

        # Fingerprint for cache key (stable + short)
        fp_src = json.dumps(
            {"u": _norm(user_query), "i": i, "t": tool_name, "p": plan_brief, "a": args_brief},
            ensure_ascii=False,
        )
        fp = hashlib.sha1(fp_src.encode("utf-8")).hexdigest()
        _CACHE[fp] = payload

        # Invoke LLM (cached)
        raw = _invoke_cached(fp)

        try:
            resp = _clean_fenced_json(raw)
            extracted = json.loads(resp)
        except json.JSONDecodeError:
            if verbose:
                print(f"  - Error: Failed to decode JSON for tool '{tool_name}'. Raw: {raw}")
            continue

        # Assign values with type-aware array coercion
        for a in tool_call["arguments"]:
            aname = a["argument_name"]
            if aname in extracted:
                val = extracted[aname]
                atype = arg_type_map.get(aname, "")
                if "array" in atype and val != "" and not isinstance(val, list):
                    val = [val]
                a["argument_value"] = val
                if verbose:
                    print(f"  - Filled '{aname}': {a['argument_value']}")

    return filled_plan

# ---------------------------
# Main (example run)
# ---------------------------
if __name__ == "__main__":
    user_query = "Summarize high severity tickets from the customer UltimateCustomer"
    print(f"Using Query: \"{user_query}\"")

    try:
        print("Loading skeleton plan from 'output.json'...")
        with open("output.json", "r", encoding="utf-8") as f:
            skeleton_plan_str = f.read()             # no risky replaces
            skeleton_plan = json.loads(skeleton_plan_str)

        filled_plan = fill_arguments_with_context(skeleton_plan, user_query, verbose=True)

        out = "filled_output.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(filled_plan, f, indent=4, ensure_ascii=False)

        print(f"\nSuccess! The corrected filled plan has been saved to '{out}'")

    except FileNotFoundError:
        print("Error: 'output.json' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
