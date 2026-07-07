import json
import requests

# Load Data
with open("towers_inventory.json", "r") as f:
    inventory_data = json.load(f)

with open("regional_policies.txt", "r") as f:
    regional_text = f.read()

# print("Towers loaded:", len(inventory_data))
# print("Policies loaded:", len(regional_text))

# --------------------------------------------

# Tool look 1


def tool_lookup_tower(tower_id):
    for tower in inventory_data:
        if tower["tower_id"] == tower_id:
            return tower
    return None

# Tool Policy


def tool_get_policies(region):
    lines = regional_text.split("\n")
    result = []
    capture = False
    for line in lines:
        if region in line:
            capture = True
        if capture and line.strip() == "" and result:
            break
        if capture:
            result.append(line)
    return "\n".join(result)


# --------------------------------------------

# Ollama CALL
def extract_from_request(user_input):
    prompt = f"""
    Extract the following fields from this lease request and return ONLY valid JSON:
    - operator (string)
    - tower_id (string)
    - weight_kg (number)
    - height_m (number)

    Request: "{user_input}"
    Return only JSON, no explanation, no markdown.
"""
    response = requests.post(
        "http://localhost:11434/api/generate", json={
            "model": "llama3.1:latest",
            "prompt": prompt,
            "stream": False,
        })

    raw = json.loads(response.text)
    text = raw["response"].strip().removeprefix(
        "```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


# --------------------------------------------

# Orchestration

def run_agent(user_input):

    # Step 1: Extract data from user input
    extracted = extract_from_request(user_input)
    # print("Extracted:", extracted)

    # Tool 1 - tower lookup
    tower = tool_lookup_tower(extracted["tower_id"])
    if tower is None:
        return {"status": "Rejected", "reason": f"Tower ID {extracted['tower_id']} not found"}
    # print("Tower found:", tower)

    # Tool 2 - policy based on region
    policies = tool_get_policies(tower["region"])
    # print("Policies found:", policies)

    # Step 3: Sending to LLM
    judgment = get_judgment(extracted, tower, policies)
    return judgment

# --------------------------------------------

# LLM JUDGMENT


def get_judgment(extracted, tower, policies):
    prompt = f"""
You are a telecom tower lease vetting agent. Follow these steps carefully:

STEP 1 - Check tower weight capacity:
- Current weight: {tower['current_weight_kg']}kg
- New equipment weight: {extracted['weight_kg']}kg
- Total if approved: {tower['current_weight_kg'] + extracted['weight_kg']}kg
- Max allowed: {tower['max_allowed_weight_kg']}kg
- PASS if total <= max, FAIL if total > max

STEP 2 - Check single asset weight limit from policy:
{policies}
- Equipment weight is {extracted['weight_kg']}kg
- Find the single asset limit for {tower['region']} and compare

STEP 3 - Check height limit from policy:
- Equipment height is {extracted['height_m']}m
- Find the height limit for {tower['region']} and compare
- PASS if equipment height <= limit, FAIL if equipment height > limit

STEP 4 - Final judgment:
- If ALL steps pass → APPROVED
- If ANY step fails → REJECTED

Return ONLY valid JSON:
{{
  "status": "APPROVED" or "REJECTED",
  "reason": [
    "STEP 1: <explain result>",
    "STEP 2: <explain result>", 
    "STEP 3: <explain result>"
  ]
}}

No explanation, no markdown.
"""
    response = requests.post(
        "http://localhost:11434/api/generate", json={
            "model": "llama3.1:latest",
            "prompt": prompt,
            "stream": False,
        })
    raw = json.loads(response.text)
    text = raw["response"].strip().removeprefix(
        "```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)

# --------------------------------------------
# Test


# Positive Case
user_input = "Operator Du wants to mount a 15kg 5G antenna at a height of 40 meters on Tower TWR-101 "
result = run_agent(user_input)
print(json.dumps(result, indent=2))
# Negative Case
user_input = "Operator Etisalat wants to mount a 50kg antenna at a height of 50 meters on Tower TWR-101."
result = run_agent(user_input)
print(json.dumps(result, indent=2))
