import requests
import json

def call_mcp_kicad_server(method, params):
    """
    Sends a JSON-RPC request to the MCP KiCad server.
    """
    url = "http://localhost:5000/mcp"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

if __name__ == '__main__':
    # --- Example 1: Create a rectangular copper zone ---
    print("--- Creating a rectangular copper zone ---")
    zone_params = {
        "layer_name": "BL_F_Cu",
        "points": [
            [10, 10],  # Top-left
            [30, 10],  # Top-right
            [30, 40],  # Bottom-right
            [10, 40],  # Bottom-left
        ]
    }
    response = call_mcp_kicad_server("create_copper_zone", zone_params)
    print("Server Response:", json.dumps(response, indent=2))

    print("\n" + "="*40 + "\n")

    # --- Example 2: Create a track ---
    print("--- Creating a track ---")
    track_params = {
        "layer_name": "BL_B_Cu",
        "start_point": [5, 5],
        "end_point": [50, 25],
        "width_mm": 0.5
    }
    response = call_mcp_kicad_server("create_track", track_params)
    print("Server Response:", json.dumps(response, indent=2))
