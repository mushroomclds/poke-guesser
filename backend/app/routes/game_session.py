import secrets
from flask import Blueprint, request, jsonify, session
from http import HTTPStatus
from datetime import datetime, timezone, timedelta
import pytz
def _get_cst_tz():
    """Returns the Central Standard Time (CST) timezone object."""
    # CST/CDT (America/Chicago) handles daylight saving automatically
    return pytz.timezone('America/Chicago')


from app.utils.oracle_db import db
from app.config import Config
from app.utils.logger import logger
import threading
import time

game_bp = Blueprint('game', __name__)


def _require_origin():
    """Blocks requests from any domain other than our allowed frontend."""
    origin = request.headers.get('Origin')
    logger.info(f"Origin: {origin} | Allowed: {Config.ALLOWED_ORIGIN}")
    if origin and origin != Config.ALLOWED_ORIGIN:
        return jsonify({'error': 'Invalid origin'}), HTTPStatus.FORBIDDEN
    return None


def _require_token(data, session_key: str):
    """
    Compares the token the client sent in the request body against the one
    Flask stored in the session cookie when the client first asked for a token.
    Deletes it from the session after validation so it can't be reused.
    """
    token = data.get('token')
    if not token or token != session.get(session_key):
        return jsonify({'error': 'Invalid or missing token'}), HTTPStatus.FORBIDDEN
    session.pop(session_key, None)
    return None


def _parse_iso_timestamp(value: str):
    """Converts an ISO-8601 string from the client into a Python datetime object."""
    if isinstance(value, str) and value.endswith('Z'):
        value = value[:-1] + '+00:00'
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Convert to CST
    cst = _get_cst_tz()
    dt_cst = dt.astimezone(cst)
    return dt_cst


def _validate_score(value) -> int:
    """Ensures score is a real integer within a sane range — rejects strings, negatives, absurd values."""
    try:
        score = int(value)
    except (TypeError, ValueError):
        raise ValueError("Score must be an integer.")
    if score < 0:
        raise ValueError("Score cannot be negative.")
    if score > 10_000_000:
        raise ValueError("Score exceeds maximum allowed value.")
    return score


# --- In-memory caches for high scores ---
_all_time_high_score_cache = {
    'score': None,
    'timestamp': 0,
    'lock': threading.Lock(),
}
_daily_high_score_cache = {
    'score': None,
    'date': None,
    'timestamp': 0,
    'lock': threading.Lock(),
}

def _get_high_score_all_time():
    """
    Returns all-time highest score, using cache if recent.
    Cache is refreshed every 60 seconds.
    """
    now = time.time()
    with _all_time_high_score_cache['lock']:
        if (
            _all_time_high_score_cache['score'] is not None
            and now - _all_time_high_score_cache['timestamp'] < 60
        ):
            return _all_time_high_score_cache['score']
        query = (
            "SELECT MAX(final_score) AS high_score "
            "FROM game_sessions "
        )
        try:
            result = db.execute_query(query)
            score = result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.exception('Failed to fetch all-time high score')
            score = 0
        _all_time_high_score_cache['score'] = score
        _all_time_high_score_cache['timestamp'] = now
        return score

def _get_high_score_today():
    """
    Returns today's highest score, using cache if recent.
    Cache is refreshed every 60 seconds or if date changes.
    """
    now = time.time()
    cst = _get_cst_tz()
    today_str = datetime.now(cst).strftime('%Y-%m-%d')
    with _daily_high_score_cache['lock']:
        if (
            _daily_high_score_cache['score'] is not None
            and _daily_high_score_cache['date'] == today_str
            and now - _daily_high_score_cache['timestamp'] < 60
        ):
            return _daily_high_score_cache['score']
        # Oracle: Convert play_started_at to CST for daily comparison
        query = (
            "SELECT MAX(final_score) AS high_score "
            "FROM game_sessions "
            "WHERE TRUNC(CAST(play_started_at AT TIME ZONE 'America/Chicago' AS DATE)) = TRUNC(CAST(SYSTIMESTAMP AT TIME ZONE 'America/Chicago' AS DATE))"
        )
        try:
            result = db.execute_query(query)
            score = result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.exception("Failed to fetch today's high score")
            score = 0
        _daily_high_score_cache['score'] = score
        _daily_high_score_cache['date'] = today_str
        _daily_high_score_cache['timestamp'] = now
        return score


@game_bp.route('/game-session/high-score', methods=['GET'])
def get_high_score():
    """Returns the all-time highest score."""
    err = _require_origin()
    if err:
        return err
    score = _get_high_score_all_time()
    return jsonify({'high_score': score}), HTTPStatus.OK

@game_bp.route('/game-session/high-score-today', methods=['GET'])
def get_high_score_today():
    """Returns the highest score for today (UTC)."""
    err = _require_origin()
    if err:
        return err
    score = _get_high_score_today()
    return jsonify({'high_score_today': score}), HTTPStatus.OK

@game_bp.route('/game-session/token', methods=['GET'])
def get_game_session_token():
    """
    Issues a one-time token when the player clicks Play.

    Generates a random unguessable string, stores it in Flask's encrypted session
    cookie (server-side), and returns the value to the client. The client holds
    onto it and sends it back with the game result. Flask then compares both copies
    to prove the POST came from the same browser that started the game.
    """
    _require_origin()

    # Generate a cryptographically random 64-char hex string
    token = secrets.token_hex(32)

    # Store it server-side in the encrypted session cookie tied to this browser
    session['game_session_token'] = token

    # Send the value to the client — they'll include it in the POST body later
    return jsonify({'token': token}), HTTPStatus.OK


@game_bp.route('/game-session', methods=['POST'])
def store_game_session():
    """
    Stores a completed game session (start time + final score) in the database.

    Security: validates origin, then validates the one-time token by comparing
    what the client sent in the body against what Flask stored in the session
    cookie when the token was issued. Both must match — this proves the POST
    came from the same browser that started the game and prevents CSRF/replay attacks.

    Expected JSON body:
    {
        "play_started_at": "2025-04-30T14:22:00Z",
        "final_score":     4200,
        "token":           "<token from /game-session/token>"
    }
    """
    # Block requests from unknown origins (not our frontend)
    err = _require_origin()
    if err:
        return err

    # Reject empty or malformed request bodies
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be valid JSON.'}), HTTPStatus.BAD_REQUEST

    # Compare body token vs session token — deletes it from session on success
    err = _require_token(data, session_key='game_session_token')
    if err:
        return err

    # Parse and validate the timestamp the client recorded when Play was clicked
    raw_ts = data.get('play_started_at')
    if not raw_ts:
        return jsonify({'error': 'play_started_at is required.'}), HTTPStatus.BAD_REQUEST
    try:
        play_started_at = _parse_iso_timestamp(raw_ts)
    except (ValueError, TypeError):
        return (
            jsonify({'error': 'play_started_at must be a valid ISO-8601 timestamp (e.g. 2025-04-30T14:22:00Z).'}),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    # Validate the final score — must be a non-negative integer
    raw_score = data.get('final_score')
    if raw_score is None:
        return jsonify({'error': 'final_score is required.'}), HTTPStatus.BAD_REQUEST
    try:
        final_score = _validate_score(raw_score)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), HTTPStatus.UNPROCESSABLE_ENTITY

    # Write the session record to Oracle
    insert_query = """
        INSERT INTO game_sessions (play_started_at, final_score)
        VALUES (:play_started_at, :final_score)
    """
    try:
        db.execute_query(insert_query, {
            'play_started_at': play_started_at,
            'final_score':     final_score,
        }
        , "POST")
        logger.info(f"game_session stored | started={play_started_at} (CST) score={final_score}")
        return jsonify({'message': 'Game session stored successfully.'}), HTTPStatus.CREATED

    except Exception:
        logger.exception("Failed to insert game_session")
        return jsonify({'error': 'Could not store game session. Please try again.'}), HTTPStatus.INTERNAL_SERVER_ERROR

'''
Browser                          Flask
  │                                │
  │  GET /api/game-session/token   │
  │ ─────────────────────────────► │  secrets.token_hex(32) generates random token "a3f9b2..."
  │                                │  
  │                                │  //stores token "a3f9b2..." — session data lives in the browser as cookie, Flask just owns the key to read it (stateless)
  │                                │  session['game_session_token'] = "a3f9b2..." 
  │                                │  
  │                                │  //1.Flask encrypts ENTIRE session dict, sends to browser as cookie 2. also sends raw token
  │                                │  1. Sets-Cookie: session=<encrypted_blob>
  │ ◄───────────────────────────── │  2. returns { token: "a3f9b2..." } //also sends the raw token value in the response body for JS to store
  │                                │
  │  stores "a3f9b2..." in         │
  │  this.gameSessionToken         │
  │                                │
  │  POST /api/game-session        │
  │1. body: { token: "a3f9b2..."}  │
  │2. Cookie: session=<blob> ────► │  decrypts cookie → finds "a3f9b2..."
  │                                │  compares body token == session token ✓
  │                                │  deletes token from session (one-time use)

    A cookie is literally just a header field — Cookie: key=value — the browser automatically attaches it to every request to that 
    domain. 
    - **Cookie** = proves identity ("same browser that got the token") — Flask reads this server-side, JS can't use it
    - **Raw token in body** = the value JS stores and sends back in the POST body for Flask to compare against

    Flask can only decrypt the cookie and check what's inside. So the flow is:

    Flask app →  cookie →  browser
    1. Browser w/ coookie → Flask  →  Flask decrypts cookie →  finds "a3f9..."
    2. Browser w/ return header data too → Flask →  raw data : { token: "a3f9..." }
    Flask compares both  ✓

    Without the raw token in the body there's nothing to compare against. Without the cookie Flask has no server-side record to compare to.
'''