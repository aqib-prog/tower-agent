# Tower Lease Vetting Agent

An autonomous AI agent that vets incoming telecom tower lease requests from mobile operators.

## How It Works
1. User Request (plain text)
          
2. Ollama (llama3.1) extracts structured data

 3.1 Tool 1: Lookup tower  towers_inventory.json
 
 3.2 Tool 2: Get policies  regional_policies.txt

4. Ollama judges using Chain-of-Thought prompting

5. Structured JSON output: APPROVED / REJECTED + reasons

## Tech Stack
- Python 3.13
- Ollama (llama3.1)
- Chain-of-Thought prompting
- No external AI APIs — fully local
