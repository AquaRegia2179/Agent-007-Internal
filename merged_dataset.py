import json

# --- Step 1: Load dataset_empty.json (list of dicts) ---
with open("dataset_empty.json", "r") as f:
    empty_data = json.load(f)

# --- Step 2: Load dataset.jsonl (one JSON per line) ---
dataset_data = []
with open("dataset.jsonl", "r") as f:
    for line in f:
        dataset_data.append(json.loads(line.strip()))

# --- Step 3: Merge them ---
merged = dataset_data + empty_data

# --- Step 4: Save merged data as JSONL (recommended format) ---
with open("merged_dataset.jsonl", "w") as f:
    for item in merged:
        json.dump(item, f)
        f.write("\n")

print(f"✅ Successfully merged {len(dataset_data)} + {len(empty_data)} = {len(merged)} entries into merged_dataset.jsonl")
