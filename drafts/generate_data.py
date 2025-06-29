import random
import json

# Define roles and some example prompts
roles = {
    "PARAMEDIC": [
        "Unconscious male, visible bleeding from head, rapid pulse.",
        "Elderly woman with chest pain and shortness of breath.",
        "Teenager with broken leg, alert and responsive.",
    ],
    "NURSE": [
        "Update vitals for patient 204: BP 120/80, HR 95.",
        "Patient 331 now stable, request physician check.",
        "Log administration of morphine to patient 112.",
    ],
    "PHYSICIAN": [
        "Review status of all red-tagged patients.",
        "Request medevac for critical burn patient.",
        "Approve discharge for patient 109, green tag.",
    ],
    "REUNIFICATION_COORDINATOR": [
        "Search for Maya Thompson, age 10.",
        "Check if John Smith is registered in the system.",
        "Log family contact for patient 118.",
    ],
    "LOGISTICS": [
        "Request 5 IV kits at triage tent A.",
        "Check oxygen tank availability.",
        "Restock morphine supply for unit B.",
    ],
    "MEDICAL_ASSISTANT": [
        "Take notes on patient 223: severe asthma attack.",
        "Summarize the past 3 entries for patient 318.",
        "Help nurse in Triage Zone B update logs.",
    ],
    "TRANSFER_AGENT": [
        "Prepare ambulance for patient 102, status red.",
        "Confirm transport vehicle ETA for Zone C.",
        "Update patient 202 transfer status to complete.",
    ]
}

# Template for message formatting
def create_instruction(role, input_text):
    return {
        "messages": [
            {"role": "system", "content": f"You are a {role.lower()} responding to MCI-related instructions."},
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": generate_response(role, input_text)}
        ]
    }

# Simulated assistant response generator
def generate_response(role, input_text):
    if "triage" in input_text.lower() or "unconscious" in input_text.lower():
        return "Triage: Red. Notify physician and initiate emergency care protocol."
    elif "update vitals" in input_text.lower():
        return "Vitals updated. Patient log refreshed and timestamped."
    elif "review" in input_text.lower():
        return "All red-tagged patients reviewed. Three require immediate evacuation."
    elif "search" in input_text.lower():
        return "Match found: Maya Thompson, stable in Triage Zone C."
    elif "request" in input_text.lower():
        return "Supply request logged. Delivery estimated in 5 minutes."
    elif "take notes" in input_text.lower():
        return "Notes recorded and attached to patient 223’s chart."
    elif "prepare ambulance" in input_text.lower():
        return "Ambulance assigned. Dispatch confirmed for patient 102."
    else:
        return "Instruction received. Action logged and queued."

# Generate dataset
samples = []
for role, prompts in roles.items():
    for _ in range(150):  # Generate ~150 samples per role
        input_text = random.choice(prompts)
        samples.append(create_instruction(role, input_text))

# Shuffle for variety
random.shuffle(samples)

# Optionally save to JSON
with open("mci_gemma_instructions.json", "w") as f:
    json.dump(samples, f, indent=2)

# Preview first few entries
for sample in samples[:3]:
    print(json.dumps(sample, indent=2))
