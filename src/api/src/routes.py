from flask import jsonify, request
import json
from . import app
from ...parser import generate_tool_chain
from ...argument_filler import fill_arguments_with_context
import os

@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({ "message": "API is live!" })

@app.route('/respond', methods=['POST'])
def respond():
    user_query = request.json.get('query', '')
    skeleton_plan_str = generate_tool_chain(user_query)
    if skeleton_plan_str.startswith("```json"):
        skeleton_plan_str = skeleton_plan_str.strip("```json").strip()
    skeleton_plan_obj = json.loads(skeleton_plan_str)
    filled_plan = fill_arguments_with_context(skeleton_plan_obj, user_query)

    response = jsonify({ "reply":  filled_plan})

    return response