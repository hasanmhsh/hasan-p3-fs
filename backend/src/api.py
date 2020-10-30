import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth


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
    drinks = Drink.query.order_by(Drink.id).all()
    if drinks == None:
        abort(404)
    if len(drinks) == 0:
        abort(404)
    return jsonify({
        "success": True,
        "drinks": [drink.short() for drink in drinks]
    })

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
def get_detailed_drink(auth_result):
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
def create_drink(auth_result):
    try:
        body = request.get_json()
        title = body.get('title', None)
        if title == None:
            abort(400)
        recipe = body.get('recipe', None)
        if recipe == None:
            abort(400)
        recipes = []
        if isinstance(recipe, list):
            recipes = recipe
        else:
            recipes.append(recipe)
        recipe_str = json.dumps(recipes)
        drink = Drink(title=title, recipe=recipe_str)
        drink.insert()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except:
        abort(422)


'''
@DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth(['patch:drinks'])
def update_drink(auth_result, drink_id):
    try:
        drink = Drink.query.filter(Drink.id==drink_id).one_or_none()
        if drink == None:
            abort(404)
        body = request.get_json()
        title = body.get('title', None)
        if title:
            drink.title = title
        recipe = body.get('recipe', None)
        if recipe:
            if isinstance(recipe, list):
                drink.recipe = json.dumps(recipe)
            else:
                recipes = []
                recipes.append(recipe)
                drink.recipe = json.dumps(recipes)
        drink.update()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except:
        abort(422)


'''
@DONE implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth(['delete:drinks'])
def delete_drink(auth_result, drink_id):
    try:
        drink = Drink.query.filter(Drink.id==drink_id).one_or_none()
        if drink == None:
            abort(404)
        drink.delete()
        return jsonify({
            "success": True,
            "delete": drink_id
        })
    except:
        abort(422)


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
@DONE implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''


'''
@DONE implement error handler for 404
    error handler should conform to general task above 
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found",
    }), 404

'''
@DONE implement error handler for AuthError
    error handler should conform to general task above 
'''

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized",
    }), 401

@app.errorhandler(403)
def unauthorizable(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "unauthorized",
    }), 403

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request",
    }), 400

@app.errorhandler(401)
def header_error(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized",
    }), 401


