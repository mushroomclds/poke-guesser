from flask import Blueprint, request, jsonify, session
# from app.services.user_service import UserService
# from app.utils.auth_decorator import require_auth
import secrets
from app.utils.oracle_db import db
import html, re
from http import HTTPStatus

api = Blueprint('api', __name__) # Blueprint for API routes, imported in init.py
# user_service = UserService()

# @api.route('/users', methods=['GET'])
# @require_auth
# def get_users():
#     """Get all users (protected route)"""
#     users = user_service.get_all_users()
#     return jsonify({'users': users}), 200

# @api.route('/profile', methods=['GET'])
# @require_auth
# def get_profile(current_user):
#     """Get current user profile"""
#     return jsonify({
#         'username': current_user.username,
#         'email': current_user.email
#     }), 200

# @api.route('/health', methods=['GET'])
# def health_check():
#     """API health check endpoint"""
#     return jsonify({'status': 'healthy', 'service': 'flask-api'}), 200

@api.route('/game-state-user-input', methods=['POST'])
def get_game_state_user_input():

    data = request.get_json()
    # print(data)
    # print(type(data))
    # print(data.get("price1"))
    # print(data["price2"])
    # print(data.get("hasBothCards"))

    isCorrect = data.get("price2") >= data.get("price1") if data.get("answer") else data.get("price2") <= data.get("price1")
    
    returnVal = True if (data.get("hasBothCards") and isCorrect) else False
    return jsonify({ 'result' : returnVal }) # return a tuple of (response_body, status_code)
    
@api.route('/get-token', methods=['GET'])
def get_token():
    """Generate a one-time token and store it in the session."""
    token = secrets.token_urlsafe(32)
    session['user_input_token'] = token
    return jsonify({'token': token}) # returns 200 status code by default

@api.route('/user-input', methods=['POST'])
def store_user_input():
    allowed_origin = "https://mushroom-clouds.com"  # Change to your deployed frontend domain
    origin = request.headers.get('Origin')
    if origin != allowed_origin:
        return jsonify({'error': 'Invalid origin'}), HTTPStatus.FORBIDDEN #403 

    """
    Store user input in the userInput table.
    Expects JSON: { "input": "user input sanitized" }
    Requires JWT in Authorization header.
    """
    data = request.get_json()
    user_input = data.get('input')
    
    token = data.get('token')
    if not user_input:
        return jsonify({'error': 'Input is required'}), HTTPStatus.BAD_REQUEST #400
    if not token or token != session.get('user_input_token'):
        return jsonify({'error': 'Invalid or missing token'}), HTTPStatus.FORBIDDEN #403 
    # Optionally, remove the token after use to make it one-time
    session.pop('user_input_token', None)

    # Sanitize user input
    user_input = html.escape(user_input.strip())
    if len(user_input) > 15:  # Adjust max length as needed
        return jsonify({'error': 'Input too long'}), HTTPStatus.BAD_REQUEST #400
    user_input = re.sub(r'[<>"\']', '', user_input)


    insert_query = """
        INSERT INTO userInput (text_data, date_time)
        VALUES (:input_value, SYS_EXTRACT_UTC(SYSTIMESTAMP) AT TIME ZONE 'America/Chicago')
    """
    try:
        db.execute_query(insert_query, {'input_value': user_input})
        return jsonify({'message': 'Input stored successfully'}), HTTPStatus.CREATED #201
    except Exception as e:
        return jsonify({'error': "error in route "}), HTTPStatus.INTERNAL_SERVER_ERROR #500 