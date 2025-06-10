from flask import Flask, request, jsonify
from kipy import KiCad
from kipy.board_types import (
    BoardLayer,
    Zone,
    Track
)
from kipy.common_types import PolygonWithHoles
from kipy.geometry import PolyLine, PolyLineNode, Vector2
from kipy.util import from_mm
import json

app = Flask(__name__)

# --- Tool Implementation ---

def create_copper_zone(layer_name, points):
    """
    Creates a copper zone on the specified layer with the given outline.
    """
    try:
        kicad = KiCad()
        board = kicad.get_board()

        outline = PolyLine()
        for point in points:
            outline.append(PolyLineNode.from_xy(from_mm(point[0]), from_mm(point[1])))
        # Close the polygon
        outline.append(PolyLineNode.from_xy(from_mm(points[0][0]), from_mm(points[0][1])))

        polygon = PolygonWithHoles()
        polygon.outline = outline
        zone = Zone()
        zone.layers = [BoardLayer.Value(layer_name)]
        zone.outline = polygon
        created_items = board.create_items(zone)

        return {"status": "success", "message": f"Created zone with {len(created_items)} item(s)."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_track(layer_name, start_point, end_point, width_mm):
    """
    Creates a track on the specified layer.
    """
    try:
        kicad = KiCad()
        board = kicad.get_board()

        track = Track()
        track.layer = BoardLayer.Value(layer_name)
        track.start = Vector2.from_xy_mm(start_point[0], start_point[1])
        track.end = Vector2.from_xy_mm(end_point[0], end_point[1])
        track.width = from_mm(width_mm)
        created_items = board.create_items(track)

        return {"status": "success", "message": f"Created track with {len(created_items)} item(s)."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- JSON-RPC Endpoint ---

@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}), 400

    id = data.get('id')
    method = data.get('method')
    params = data.get('params', {})

    tools = {
        "create_copper_zone": create_copper_zone,
        "create_track": create_track,
        # Add more tools here as needed
    }

    if method in tools:
        try:
            result = tools[method](**params)
            return jsonify({"jsonrpc": "2.0", "result": result, "id": id})
        except Exception as e:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {e}"}, "id": id}), 500
    else:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": id}), 404

if __name__ == '__main__':
    # Run the server on localhost, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
