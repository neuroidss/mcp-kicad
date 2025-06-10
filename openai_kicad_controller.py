import os
import json
import requests
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: 'openai' library not installed. Please run 'pip install openai'")
    exit()

# --- Configuration from Environment Variables ---
OPENAI_API_BASE_URL = os.environ.get("OPENAI_API_BASE_URL")
OPENAI_LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- Sanity Checks ---
if not OPENAI_API_BASE_URL or not OPENAI_LLM_MODEL:
    print("FATAL ERROR: Environment variables are not set.")
    exit()

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=OPENAI_API_BASE_URL, api_key=OPENAI_API_KEY)
MCP_KICAD_URL = "http://localhost:5000/mcp"

# --- MCP Client Function ---
def call_mcp_kicad_server(method, params):
    headers = {'Content-Type': 'application/json'}
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    print(f"\n-> Sending to MCP KiCad Server:\n{json.dumps(payload, indent=2)}")
    try:
        response = requests.post(MCP_KICAD_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# --- Tool Definitions (Unchanged) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_copper_zone",
            "description": "Creates a copper zone on a layer with a polygonal outline. For rectangles, provide all 4 corner points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {"type": "string", "description": "Layer name, e.g., 'BL_F_Cu' or 'BL_B_Cu'."},
                    "points": {
                        "type": "array",
                        "description": "A flat list of coordinates [x1, y1, x2, y2, ...].",
                        "items": {"type": "number"}
                    }
                },
                "required": ["layer_name", "points"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_track",
            "description": "Creates a straight track segment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {"type": "string", "description": "Layer name, e.g., 'BL_F_Cu'."},
                    "start_point": {"type": "array", "description": "[x, y] in mm.", "items": {"type": "number"}},
                    "end_point": {"type": "array", "description": "[x, y] in mm.", "items": {"type": "number"}},
                    "width_mm": {"type": "number", "description": "Track width in mm."}
                },
                "required": ["layer_name", "start_point", "end_point", "width_mm"]
            }
        }
    }
]

# --- Main Application Logic ---
def main():
    messages = [{"role": "system", "content": "You are a helpful assistant that controls KiCad. For rectangles, provide all 4 corner points."}]
    print("KiCad AI Controller (via OpenAI-compatible endpoint).")
    print(f"Endpoint: {OPENAI_API_BASE_URL}")
    print(f"Model: {OPENAI_LLM_MODEL}")
    print("Type your commands or 'quit' to exit.")

    while True:
        try:
            prompt = input("\n> ")
        except EOFError:
            break
        if prompt.lower() in ['quit', 'exit']:
            break

        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(model=OPENAI_LLM_MODEL, messages=messages, tools=tools, tool_choice="auto")
            response_message = response.choices[0].message
            
            if response_message.tool_calls:
                messages.append(response_message)
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    print(f"\nModel wants to call tool: '{tool_name}'")
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    server_response = call_mcp_kicad_server(tool_name, tool_args)
                    print(f"\n<- MCP Server Response:\n{json.dumps(server_response, indent=2)}")
                    
                    # --- THIS IS THE FIX ---
                    # Instead of sending the whole JSON object, send only the simple message string.
                    tool_content = "Tool execution failed." # Default message
                    if server_response:
                        if "result" in server_response and "message" in server_response.get("result", {}):
                            tool_content = server_response["result"]["message"]
                        elif "error" in server_response and "message" in server_response.get("error", {}):
                             tool_content = f"Error from server: {server_response['error']['message']}"
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": tool_content # Pass the simplified string here
                    })
                    # --- END OF FIX ---

                final_response = client.chat.completions.create(model=OPENAI_LLM_MODEL, messages=messages)
                print(f"\nAI: {final_response.choices[0].message.content}")
                messages.append(final_response.choices[0].message)
            else:
                print(f"\nAI: {response_message.content}")
                messages.append({"role": "assistant", "content": response_message.content})
        
        except Exception as e:
            print(f"An error occurred: {e}")
            messages.pop()

if __name__ == "__main__":
    main()
