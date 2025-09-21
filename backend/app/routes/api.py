from flask import Blueprint, request, jsonify, session
# from app.services.user_service import UserService
# from app.utils.auth_decorator import require_auth
import secrets
from app.utils.oracle_db import db
import html, re
from http import HTTPStatus
import requests, random, json, threading, time
from app.utils.logger import logger
import queue
from app.config import Config
import os

api = Blueprint('api', __name__) # Blueprint for API routes, imported in init.py
# user_service = UserService()

API_BASE = "https://api.pokemontcg.io/v2"
headers = {"X-Api-Key": Config.POKEMON_API_KEY}
logger.info(Config.POKEMON_API_KEY)

CACHE_SIZE = 10
card_cache = queue.Queue(maxsize=CACHE_SIZE)  # Pre-loaded cards using Queue

def fetchPokemonSetData():

    global cachePokemonSetData
    headers = {"X-Api-Key": Config.POKEMON_API_KEY}

    pokemonSetData = requests.get(f"{API_BASE}/sets", headers=headers)
    if pokemonSetData.status_code != 200:
        return jsonify({"error", "pokemon data set couldnt be retrieved"}), 400
    cachePokemonSetData = pokemonSetData.json().get("data", [])

    with open('./pokemonSetData.txt', 'w') as a: 
        json.dump(cachePokemonSetData, a)
    logger.info(cachePokemonSetData)

# fetchPokemonSetData()
# Determine the correct path for pokemonSetData.txt
local_path = os.path.join(os.path.dirname(__file__), "pokemonSetData.txt")
docker_path = "/usr/local/app/backend/app/routes/pokemonSetData.txt"

# Use docker_path if it exists, otherwise fallback to local_path
data_file_path = docker_path if os.path.exists(docker_path) else local_path

with open(data_file_path, 'r') as f:
    cachePokemonSetData = json.load(f)
    logger.info(f'cachePokemonSetData successfully loaded')

def fetch_card_from_api():
    # logger.info(Config.POKEMON_API_KEY)
    headers = {"X-Api-Key": Config.POKEMON_API_KEY}
    # Select a random set
    chosen_set = random.choice(cachePokemonSetData)
    set_id = chosen_set.get("id")
    total_cards = chosen_set.get("total")
    if not set_id or not total_cards:
        return jsonify({"error": "Invalid set data"}), 500
    # Generate a random card number
    card_number = random.randint(1, total_cards)
    # Construct the card ID
    card_id = f"{set_id}-{card_number}"

    # pokemonName = request.args.get("name")
    # if not pokemonName: 
    #     return jsonify({'error': 'empty pokemon name'}), HTTPStatus.BAD_REQUEST #400

    try:
        card_response = requests.get(
            f"{API_BASE}/cards/{card_id}?select=name,images,tcgplayer",
            headers=headers,
            timeout=120
        )
        # logger.info(f'{card_id} + {card_response.json()}')
        # call = requests.get(f"https://api.pokemontcg.io/v2/cards?q=name:{pokemonName}&page=1&pageSize=5", headers=headers)
        if card_response.status_code == 200:
            # card_data = card_response.json().get("data")
            return card_response.json()
            # if card_data:
            #     return jsonify(card_data)
            # else:
            #     return jsonify({"error": "Card data not found"}), 404
    except requests.Timeout:
        logger.info("Timeout occurred while fetching card data")
        return None
    except Exception as e:
        logger.info(f"Exception occurred: {e}")
        return None

def queue_worker():
    """Background worker to keep queue filled"""
    while True:
        if card_cache.qsize() < CACHE_SIZE:
            try:
                card = fetch_card_from_api()
                if card:
                    card_cache.put(card)
                    logger.info(f"Card added\tcache size: {card_cache.qsize()}")
                else:
                    logger.info("No card fetched, skipping add")
            except Exception as e:
                logger.info(f"Error in queue_worker: {e}")
        time.sleep(1)

MAX_THREADS_FOR_CARD_FETCH = 5
worker_threads = []
for _ in range(MAX_THREADS_FOR_CARD_FETCH):
    t = threading.Thread(target=queue_worker, daemon=True)
    t.start()
    worker_threads.append(t)

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

@api.route('/get-card-data', methods=['GET'])
def get_card_data():

    logger.info(f'trying to get card...')

    # Block until a card is available
    card = card_cache.get(block=True)
    logger.info(f'card retrieved, current cache size: {card_cache.qsize()}')
    return jsonify(card)

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