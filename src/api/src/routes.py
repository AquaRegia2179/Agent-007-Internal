from flask import jsonify, request
import json
from . import app
from ...parser import generate_tool_chain
from ...argument_filler import fill_arguments_with_context
import os

def clean_json_output(output: str) -> str:
    cleaned = output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned
    
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({ "message": "API is live!" })

@app.route('/respond', methods=['POST'])
def respond():
    user_query = request.json.get('query', '')
    raw_output = generate_tool_chain(user_query)
    json_string_output = clean_json_output(raw_output)
    plan = json.loads(json_string_output)
    filled_plan = fill_arguments_with_context(plan, user_query)

    response = jsonify({ "reply":  filled_plan})

    return response