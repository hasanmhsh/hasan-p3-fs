import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from functools import wraps
from jose import jwt
from urllib.request import urlopen

from .database.models import db_drop_and_create_all, setup_db, Drink
# from .auth.auth import AuthError, requires_auth

# Configuration
# AUTH0 ACCOUNT
AUTH0_DOMAIN = 'dev-tv8ilm54.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'cafee'
API_CLIENT_ID = 'c7JLjTI1xwXnM2dR1Lu2tTjlN8C9RPbe'


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

## Auth Header
def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    
    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)
    
    # CHOOSE OUR KEY
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    # Finally, verify!!!
    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            # print('successful')
            # print(payload)
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

def get_token_auth_header():
    #check if http request has 'Authorization' header
    if 'Authorization' not in request.headers:
        abort(401)

    # auth header example -> 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ2FiZSIsInNjaG9vbCI6InVkYWNpdHkiLCJyb2xlIjoiaW5zdHJ1Y3RvciJ9.T9hKh61bM-lFqvntAWrqPLWxAH-Ig0usQVwiVcJ1g5g'
    auth_header = request.headers['Authorization']
    # we don't wand 'Bearer' word we just want the jwt
    header_parts = auth_header.split(' ')

    # check if the authentication type is 'Bearer'
    if len(header_parts) != 2:
        abort(401)
    elif header_parts[0].lower() != 'bearer':
        abort(401)

    return header_parts[1]

def requires_auth(permissions=[]):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            jwt = get_token_auth_header()
            try:
                payload = verify_decode_jwt(jwt)
            except:
                abort(403)
            if permissions != None:
                if len(permissions) > 0:
                    for permission in permissions:
                        check_permissions(permission, payload)
                else:
                    check_permissions('', payload)
            else:
                check_permissions('', payload)
            return f(payload,*args, **kwargs)
        return wrapper
    return requires_auth_decorator

def check_permissions(permission, payload):
    if 'permissions' not in payload:
                        raise AuthError({
                            'code': 'invalid_claims',
                            'description': 'Permissions not included in JWT.'
                        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True

app = Flask(__name__)
setup_db(app)
CORS(app)


@app.route('/seed-database')
def seed_database():
    recipe1 = '[{"color": "#334455", "name":"latte", "parts":2}]'
    drink1 = Drink(title='coffe1', recipe=recipe1)
    drink1.insert()

'''
@DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

## ROUTES
'''
@DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_abstract_drinks():
    # try:
        drinks = Drink.query.order_by(Drink.id).all()
        return jsonify({
            "success": True, 
            "drinks": [drink.short() for drink in drinks]
        })
    # except:
        # abort(404)

'''
@DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail')
@requires_auth(['get:drinks-detail'])
def get_detailed_drink(jwt):
    try:
        drinks = Drink.query.order_by(Drink.id)
        return jsonify({
            "success": True,
            "drinks": [drink.long() for drink in drinks]
        })
    except:
        abort(404)

'''
@DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth(['post:drinks'])
def create_drink(jwt):
    try:
        body = request.get_json()
        title = body['title']
        recipe = json.dumps(body['recipe'])
        drink = Drink(title=title, recipe=recipe)
        drink.insert()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except:
        abort(422)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''
