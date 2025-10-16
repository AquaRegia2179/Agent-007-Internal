from flask import jsonify, request
import json
from . import app
from ...parser import generate_tool_chain
from ...argument_filler import fill_arguments_with_context
from ...loadModel import loadHeavyModel
from ...hallucination_check import verify_plan
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
    query = request.json.get('query', '')
    raw_output = generate_tool_chain(query)
    json_string_output = clean_json_output(raw_output)
    plan = json.loads(json_string_output)
    filled_plan = fill_arguments_with_context(plan, query)
    verifier_model  = loadHeavyModel()
    tries = 0
    for i in range(tries):
        flag , err = verify_plan(filled_plan, query, verifier_model)
        if not flag:
            print("Reprompting\n")
            filled_plan = fill_arguments_with_context(plan, query, err)
    response = jsonify({ "reply":  filled_plan})

    return response