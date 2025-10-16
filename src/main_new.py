import json
from dotenv import load_dotenv
from .parser import generate_tool_chain
from .argument_filler import fill_arguments_with_context
from .hallucination_check import verify_plan
from .loadModel import loadHeavyModel

def clean_json_output(output: str) -> str:
    cleaned = output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned

def main():
    load_dotenv()

    query = input("Enter your query: ").strip()
    if not query:
        print("Please enter a valid query.")
        return

    print("\n[1/2] Generating tool chain with parser.py...")
    raw_output = generate_tool_chain(query)

    # Clean up LLM markdown wrapping
    json_string_output = clean_json_output(raw_output)

    try:
        plan = json.loads(json_string_output)
    except json.JSONDecodeError:
        print("Parser returned invalid JSON after cleaning. Raw output:")
        print(raw_output)
        return

    with open("output.json", "w") as f:
        json.dump(plan, f, indent=4)
    print("Parsed skeleton plan and saved to output.json")

    print("\n[2/2] Filling argument values with argument_filler.py...")
    filled_plan = fill_arguments_with_context(plan, query)

    verifier_model  = loadHeavyModel()
    tries = 4
    for i in range(tries):
        flag , err = verify_plan(filled_plan, query, verifier_model)
        if not flag:
            print("Reprompting\n")
            filled_plan = fill_arguments_with_context(plan, query, err)


    final_path = "final_output.json"
    with open(final_path, "w") as f:
        json.dump(filled_plan, f, indent=4)

    print(f"\nSuccess — filled plan saved to '{final_path}'")
    print(json.dumps(filled_plan, indent=4))

if __name__ == "__main__":
    main()
