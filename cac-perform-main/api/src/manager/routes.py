from flask import jsonify, make_response, request
import os
import time
import jwt
from src.model import Manager
from src.manager import manager


@manager.post('/connexion/')
def login():

    data = request.get_json()

    mana = Manager()

    cnx = mana.sign_in(data=data)

    if not cnx:
        return make_response(jsonify({"error": "Identifiants invalides"}), 401)

    # Emettre un JWT simple
    payload = {
        "sub": cnx.get("email"),
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60 * 8  # 8h
    }
    secret = os.getenv('SECRET_KEY', 'change_me')
    token = jwt.encode(payload, secret, algorithm='HS256')

    return make_response(jsonify({"token": token, "user": {"email": cnx.get("email")}}), 200)
