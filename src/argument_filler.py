# argument_filler_optimized.py
from __future__ import annotations

import json
import os
import re
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
# Model + chain (deterministic & reused)
# ---------------------------
model = loadSmallModel()

_TEMPLATE = """
Fill JSON argument values for ONE tool.

USER: "{user_query}"

STEPS: {step_indexes}
TARGET: [{current_tool_index}] {tool_name}
PREV: [{prev_index}] {prev_name}

ARGS (name:type): {args_brief}

Rules:
- Output ONLY a JSON object mapping argument_name -> value.
- Use "$$PREV[k]" to reference step k.
- Lists must be JSON arrays; unknown => "" (or [] for arrays).
"""

_prompt = ChatPromptTemplate.from_template(_TEMPLATE)
_parser = StrOutputParser()
_chain = _prompt | model | _parser

# ---------------------------
# Helpers
# ---------------------------
_FENCE_JSON_START = "```json"
_FENCE_END = "```"
_JSON_SNIP = re.compile(r"\{.*\}", re.S)

def _clean_fenced_json(s: str) -> str:
    s = s.strip()
    if s.startswith(_FENCE_JSON_START):
        s = s[len(_FENCE_JSON_START):].strip()
    if s.endswith(_FENCE_END):
        s = s[:-len(_FENCE_END)].strip()
    return s

def _parse_json_strict_or_snip(raw: str) -> dict | None:
    s = _clean_fenced_json(raw)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        m = _JSON_SNIP.search(s)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()

def _get_tool_details(tool_name: str) -> dict | None:
    if tool_name == "whoami":
        tool_name = "who_am_i"
    for t in API_LIST:
        if t["name"] == tool_name:
            return t
    return None

def _normalize_against_spec(arg_specs: List[dict], extracted: dict) -> dict:
    """Ensure every arg exists; coerce array types; fill unknown with '' or []"""
    out = {}
    for a in arg_specs:
        aname = a["argument_name"]
        atype = a.get("argument_type", "").lower()
        val = extracted.get(aname, [] if "array" in atype else "")
        if "array" in atype and val != "" and not isinstance(val, list):
            val = [val]
        out[aname] = val
    return out

# ---------------------------
# Rule-based fast paths (0-token)
# ---------------------------
_RX_SEVERITY = re.compile(r"\b(high|medium|low|blocker)\b", re.I)
_RX_PRIORITY = re.compile(r"\b(p0|p1|p2|p3|critical)\b", re.I)
_RX_CHANNEL  = re.compile(r"\b(slack|email|phone|portal|twitter|github)\b", re.I)
_RX_TYPE     = re.compile(r"\b(ticket|issue|task)\b", re.I)
_RX_STAGE    = re.compile(r"\b(triage|backlog|in\s*progress|inprogress|done|closed)\b", re.I)
_RX_CUSTOMER = re.compile(r"\bcust(?:omer)?\s*([A-Za-z0-9_\-]+)|\bfrom\s+([A-Za-z0-9_\-]+)", re.I)
_RX_WORKID   = re.compile(r"([A-Z]+-\d+|[A-Z]+\d+)", re.I)

_PRODUCER_TOOLS = {"works_list", "search_object_by_name"}

def _rule_prefill(tool_name: str, arg_specs: List[dict], user_query: str, step_index: int, plan: List[dict]) -> dict:
    q = user_query
    ql = user_query.lower()
    out = {}
    arg_names = {a["argument_name"] for a in arg_specs}

    def set_if(name, value):
        if name in arg_names and name not in out:
            out[name] = value

    if tool_name in {"summarize_objects", "describe_objects", "prioritize_objects"}:
        if step_index > 0 and plan[step_index - 1].get("tool_name") in _PRODUCER_TOOLS:
            set_if("objects", f"$$PREV[{step_index-1}]")

    if tool_name == "works_list":
        # type (ticket/issue/task)
        m = _RX_TYPE.search(ql)
        if m:
            set_if("type", [m.group(1).lower()])

        # severity
        m = _RX_SEVERITY.search(ql)
        if m:
            sev = m.group(1).lower()
            if sev == "blocker":
                sev = "high"  # map blocker -> high if your backend expects that
            set_if("ticket.severity", [sev])

        # priority
        m = _RX_PRIORITY.search(ql)
        if m:
            p = m.group(1).lower()
            set_if("issue.priority", [p])

        # channel
        m = _RX_CHANNEL.search(ql)
        if m:
            set_if("ticket.source_channel", [m.group(1).lower()])

        # stage
        m = _RX_STAGE.search(ql)
        if m:
            stage = m.group(1).lower().replace(" ", "_")
            set_if("stage.name", [stage])

        # rev_org from previous search or literal
        if step_index > 0 and plan[step_index - 1].get("tool_name") == "search_object_by_name":
            set_if("ticket.rev_org", f"$$PREV[{step_index-1}]")
        else:
            m = _RX_CUSTOMER.search(q)
            if m:
                cust = (m.group(1) or m.group(2))
                set_if("ticket.rev_org", cust)

    if tool_name == "search_object_by_name":
        m = _RX_CUSTOMER.search(q)
        if m:
            cust = (m.group(1) or m.group(2))
            set_if("query", cust)

    if tool_name == "get_similar_work_items":
        m = _RX_WORKID.search(q)
        if m:
            set_if("work_id", m.group(1))

    return out

# ---------------------------
# Two-level cache (memory + disk)
# ---------------------------
_CACHE: Dict[str, Dict] = {}                 # payloads for chain
_CACHE_FILE = ".filler_cache.json"
try:
    with open(_CACHE_FILE, "r", encoding="utf-8") as _f:
        _RESP_CACHE: Dict[str, str] = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError):
    _RESP_CACHE = {}

def _save_resp_cache():
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_RESP_CACHE, f)
    except Exception:
        pass

@lru_cache(maxsize=512)
def _invoke_cached(fp: str) -> str:
    return _chain.invoke(_CACHE[fp])

# ---------------------------
# Core logic
# ---------------------------
def fill_arguments_with_context(plan: List[dict], user_query: str, verbose: bool = True) -> List[dict]:
    filled_plan = json.loads(json.dumps(plan))  # deep copy

    for i, tool_call in enumerate(filled_plan):
        tool_name = tool_call.get("tool_name", "")
        args = tool_call.get("arguments") or []

        if verbose:
            print(f"\n[{i}] Tool: {tool_name}")
            print("     needs:", [a["argument_name"] for a in args])

        if not args:
            if verbose:
                print("     skip: no arguments")
            continue

        # already filled?
        if all(a.get("argument_value") not in ("", []) for a in args):
            if verbose:
                print("     skip: already filled")
            continue

        tool_details = _get_tool_details(tool_name)
        if not tool_details:
            if verbose:
                print("     warn: tool spec not found")
            continue

        arg_specs = tool_details.get("arguments", [])
        args_brief = ", ".join(f"{a['argument_name']}:{a['argument_type']}" for a in arg_specs)

        # ---------- Rule-based prefill (0-token) ----------
        prefill = _rule_prefill(tool_name, arg_specs, user_query, i, plan)
        if prefill and verbose:
            print("     rule:", prefill)

        # apply prefill
        for a in args:
            if a["argument_name"] in prefill:
                a["argument_value"] = prefill[a["argument_name"]]

        # done after prefill?
        if all(a.get("argument_value") not in ("", []) for a in args):
            if verbose:
                print("     skip: rule-prefilled")
            continue

        # ---------- LLM path ----------
        step_indexes = ",".join(f"[{k}]" for k in range(len(plan)))
        prev_index = max(0, i - 1)
        prev_name = plan[prev_index].get("tool_name", "") if i > 0 else ""

        payload = {
            "user_query": user_query,
            "current_tool_index": i,
            "tool_name": tool_name,
            "args_brief": args_brief,
            "step_indexes": step_indexes,
            "prev_index": prev_index,
            "prev_name": prev_name,
        }

        # cache key
        fp_src = json.dumps(
            {"u": _norm(user_query), "i": i, "t": tool_name, "ab": args_brief, "si": step_indexes, "pi": prev_index, "pn": prev_name},
            ensure_ascii=False,
        )
        fp = hashlib.sha1(fp_src.encode("utf-8")).hexdigest()
        _CACHE[fp] = payload

        if fp in _RESP_CACHE:
            raw = _RESP_CACHE[fp]
            if verbose:
                print("     cache: disk hit")
        else:
            if verbose:
                print("     llm: invoke")
            raw = _invoke_cached(fp)
            _RESP_CACHE[fp] = raw
            _save_resp_cache()

        extracted = _parse_json_strict_or_snip(raw)
        if extracted is None:
            if verbose:
                print("     error: could not parse LLM JSON")
            continue

        # spec-aware normalization
        extracted = _normalize_against_spec(arg_specs, extracted)

        # assign
        for a in args:
            aname = a["argument_name"]
            a["argument_value"] = extracted.get(aname, a.get("argument_value", ""))
            if verbose:
                print(f"     set: {aname} = {a['argument_value']}")

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
            skeleton_plan = json.loads(f.read())

        filled_plan = fill_arguments_with_context(skeleton_plan, user_query, verbose=True)

        out = "filled_output.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(filled_plan, f, indent=4, ensure_ascii=False)

        print(f"\nSuccess! The corrected filled plan has been saved to '{out}'")

    except FileNotFoundError:
        print("Error: 'output.json' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
