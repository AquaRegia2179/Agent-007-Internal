import random
import pandas as pd

# --- Base templates from PS ---
templates = {
    "similar_summary": [
        "Summarize work items similar to {}",
        "Show me a summary of work items related to {}",
        "Find and summarize all items similar to {}",
        "Get similar work items for {} and summarize them",
        "List all tasks related to {} and summarize them",
        "Summarize similar work items like {}",
        "Give a summary of items similar to {}",
        "Find all related work items for {}"
    ],
    "meaningless": [
        "What is the meaning of life?",
        "Can you tell me the secret of existence?",
        "Why are we here?",
        "Explain the purpose of life",
        "Give me life advice",
        "Tell me something philosophical",
        "What’s the ultimate goal of life?",
        "Share a deep thought"
    ],
    "p0_sprint": [
        "Prioritize my P0 issues and add them to the current sprint",
        "Add all my P0 issues to this sprint after prioritizing them",
        "Fetch P0 issues I own and add them to sprint",
        "Take my top-priority (P0) issues and push to sprint",
        "Organize urgent issues into the sprint list",
        "Add critical P0 issues to sprint",
        "Get P0 issues and add them to my current sprint",
        "List my urgent issues and include them in sprint"
    ],
    "high_sev_customer": [
        "Summarize high severity tickets from the customer {}",
        "Show me a summary of high-severity tickets for {}",
        "List all critical tickets related to {} and summarize them",
        "Summarize all high priority tickets belonging to {}",
        "Get me all severe tickets for {} and give a short summary",
        "Provide a summary of critical tickets for {}",
        "Show severe issues from customer {}",
        "Summarize major tickets linked with {}"
    ],
    "triage_part": [
        "What are my issues in triage under part {}? Summarize them.",
        "List and summarize all triage issues for part {}",
        "Show me issues currently in triage for {}",
        "Summarize my triage issues linked to {}",
        "Get all issues in triage stage related to {}",
        "Summarize all triaged issues under {}",
        "Display issues in triage for {}",
        "List triage-stage issues belonging to {}"
    ],
    "slack_tickets": [
        "List all high severity tickets from {} coming via Slack and summarize them",
        "Summarize high-priority Slack tickets for {}",
        "Get Slack tickets from {} with high severity and summarize them",
        "Summarize all critical Slack issues linked to {}",
        "Fetch and summarize all high-severity Slack tickets for {}",
        "List critical Slack tickets from {}",
        "Summarize Slack-origin issues for {}",
        "Show me high severity Slack tickets belonging to {}"
    ],
    "meeting_tasks": [
        "Given meeting transcript {}, create action items and add them to my sprint",
        "From transcript {}, generate tasks and include them in my sprint",
        "Use meeting notes {} to create tasks and push to sprint",
        "Extract action points from {} and add to sprint",
        "Make sprint tasks from transcript {}",
        "Convert meeting {} into sprint tasks",
        "Generate tasks from {} and add them to sprint",
        "Take {} and create actionable tasks for sprint"
    ],
    "similar_create_prioritize": [
        "Get work items similar to {}, summarize, create issues, and prioritize them",
        "Find similar tasks for {}, summarize, and make new prioritized issues",
        "Generate issues from summary of similar items to {}",
        "Summarize and prioritize all related work items to {}",
        "Create prioritized issues from summary of work items like {}",
        "Find all related items for {} and create prioritized issues",
        "Make prioritized issues from similar work to {}",
        "Summarize similar items for {} and rank them by priority"
    ]
}

# --- Example placeholders ---
work_ids = [f"TKT-{i}" for i in range(100, 200)]
customers = [f"Cust{i}" for i in range(100, 140)]
parts = [f"FEAT-{i}" for i in range(100, 140)]
transcripts = [f"Transcript {chr(65+i)}" for i in range(26)]

# --- Build query list ---
queries = []
categories = list(templates.keys())

# Generate enough unique queries
while len(queries) < 200:
    cat = random.choice(categories)
    template = random.choice(templates[cat])

    if "{}" in template:
        if cat in ["similar_summary", "similar_create_prioritize"]:
            value = random.choice(work_ids)
        elif cat in ["high_sev_customer", "slack_tickets"]:
            value = random.choice(customers)
        elif cat == "triage_part":
            value = random.choice(parts)
        elif cat == "meeting_tasks":
            value = random.choice(transcripts)
        else:
            value = "UNKNOWN"
        query = template.format(value)
    else:
        query = template

    if query not in queries:
        queries.append(query)

# Save as CSV
df = pd.DataFrame({"query": queries})
df.to_csv("queries.csv", index=False)

print(f"✅ Generated exactly {len(queries)} unique queries and saved to queries.csv")