from flask import jsonify

def api_response(success: bool, message: str, data=None, status_code: int = 200):
    """
    Standard API response wrapper.
    Format:
    {
        "success": True/False,
        "message": "...",
        "data": { ... } # Optional
    }
    """
    payload = {
        'success': success,
        'message': message
    }
    if data is not None:
        payload['data'] = data
    return jsonify(payload), status_code
