from flask import Flask, request, jsonify
from kipy import KiCad
from kipy.board_types import BoardLayer, Zone, Track
from kipy.common_types import PolygonWithHoles
from kipy.geometry import PolyLine, PolyLineNode, Vector2
from kipy.util import from_mm

app = Flask(__name__)

# --- Tool Implementation ---

# REVISED: Updated to handle a flat list of numbers for points.
def create_copper_zone(layer_name, points):
    """Creates a copper zone from a flat list of points [x1, y1, x2, y2, ...]."""
    try:
        kicad = KiCad()
        board = kicad.get_board()
        outline = PolyLine()

        # Check if the list has an even number of points
        if len(points) % 2 != 0:
            return {"status": "error", "message": "Invalid points list. Must contain an even number of coordinates."}

        # Iterate through the flat list two at a time
        point_pairs = []
        for i in range(0, len(points), 2):
            x, y = points[i], points[i+1]
            point_pairs.append((x, y))
            outline.append(PolyLineNode.from_xy(from_mm(x), from_mm(y)))
        
        # Close the polygon by adding the first point again at the end
        if point_pairs:
            first_x, first_y = point_pairs[0]
            outline.append(PolyLineNode.from_xy(from_mm(first_x), from_mm(first_y)))

        polygon = PolygonWithHoles()
        polygon.outline = outline
        zone = Zone()
        zone.layers = [BoardLayer.Value(layer_name)]
        zone.outline = polygon
        created_items = board.create_items(zone)

        return {"status": "success", "message": f"Created zone with {len(created_items)} item(s) on layer {layer_name}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_track(layer_name, start_point, end_point, width_mm):
    """Creates a track on the specified layer."""
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

    id, method, params = data.get('id'), data.get('method'), data.get('params', {})
    tools = {"create_copper_zone": create_copper_zone, "create_track": create_track}

    if method in tools:
        try:
            result = tools[method](**params)
            return jsonify({"jsonrpc": "2.0", "result": result, "id": id})
        except TypeError as e:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32602, "message": f"Invalid params: {e}"}, "id": id}), 400
        except Exception as e:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {e}"}, "id": id}), 500
    else:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": id}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
