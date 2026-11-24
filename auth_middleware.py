import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4
from flask import request, jsonify, g, current_app
from models import db, RevokedToken, User

def generate_token(user):
    issued_at = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'jti': str(uuid4()),
        'iat': issued_at,
        'exp': issued_at + timedelta(days=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_DAYS', 7))
    }
    secret = current_app.config['JWT_SECRET_KEY']
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token


def _get_token_user(token):
    data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    token_id = data.get('jti')
    if not token_id or db.session.get(RevokedToken, token_id):
        raise jwt.InvalidTokenError('Invalid or revoked token')

    try:
        user_id = int(data['sub'])
    except (KeyError, TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError('Invalid token subject') from exc

    g.current_token_id = token_id
    g.current_token_expiration = datetime.fromtimestamp(data['exp'], timezone.utc).replace(tzinfo=None)
    return db.session.get(User, user_id)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
        if not token:
            return jsonify({'success': False, 'message': 'Authentication token is missing. Please log in.'}), 401
            
        try:
            user = _get_token_user(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token. Please authenticate again.'}), 401

        if not user:
            return jsonify({'success': False, 'message': 'User no longer exists.'}), 401
        if user.status == 'suspended':
            return jsonify({'success': False, 'message': 'This account has been suspended. Please contact support.'}), 403
        g.current_user = user
            
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
        if not token:
            return jsonify({'success': False, 'message': 'Authentication token is missing.'}), 401
            
        try:
            user = _get_token_user(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Unauthorized access.'}), 401

        if not user or user.role != 'admin':
            return jsonify({'success': False, 'message': 'Administrator privileges required to access this resource.'}), 403
        if user.status == 'suspended':
            return jsonify({'success': False, 'message': 'Account is suspended.'}), 403
        g.current_user = user
            
        return f(*args, **kwargs)
    return decorated


def optional_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                try:
                    user = _get_token_user(parts[1])
                    if user and user.status != 'suspended':
                        g.current_user = user
                except jwt.InvalidTokenError:
                    pass
                    
        return f(*args, **kwargs)
    return decorated
