from flask import jsonify,request,g,url_for
from flask.views import MethodView
from test import app,db
from test.auth import auth_required, generate_token
from test.errors import api_abort, ValidationError
from test.schemas import user_schema, item_schema, items_schema

from test.models import User, Item

class AuthTokenAPI(MethodView):
    def post(self):
        grant_type = request.form.get('grant_type')
        username = request.form.get('username')
        password = request.form.get('password')

        if grant_type is None or grant_type.lower() != 'password':
            return api_abort(code=400, message='The grant type must be password.')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.validate_password(password):
            return api_abort(code=400, message='Either the username or password was invalid.')

        token, expiration = generate_token(user)

        response = jsonify({
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': expiration
        })
        
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response
app.add_url_rule('/oauth/token', view_func=AuthTokenAPI.as_view('token'), methods=['POST'])


class UserAPI(MethodView):
    decorators = [auth_required]
    def get(self):
        return jsonify(user_schema(g.current_user))
app.add_url_rule('/user', view_func=UserAPI.as_view('user'), methods=['GET'])

class ItemAPI(MethodView):
    decorators = [auth_required]

    def get(self, item_id):
        
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        return jsonify(item_schema(item))

    def put(self, item_id):
        
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        item.body = get_item_body()
        db.session.commit()
        return '', 204

    def patch(self, item_id):
        
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        item.done = not item.done
        db.session.commit()
        return '', 204

    def delete(self, item_id):
        
        item = Item.query.get_or_404(item_id)
        if g.current_user != item.author:
            return api_abort(403)
        db.session.delete(item)
        db.session.commit()
        return '', 204
app.add_url_rule('/user/items/<int:item_id>', view_func=ItemAPI.as_view('item'),
                    methods=['GET', 'PUT', 'PATCH', 'DELETE'])

class ItemsAPI(MethodView):
    decorators = [auth_required]

    def get(self):

        page = request.args.get('page', 1, type=int)
        per_page = app.config['TODOISM_ITEM_PER_PAGE']
        pagination = Item.query.with_parent(g.current_user).paginate(page, per_page)
        items = pagination.items
        current = url_for('.items', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.items', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.items', page=page + 1, _external=True)
        return jsonify(items_schema(items, current, prev, next, pagination))


    def post(self):
        item = Item(body=get_item_body(), author=g.current_user)
        db.session.add(item)
        db.session.commit()
        response = jsonify(item_schema(item))
        response.status_code = 201
        response.headers['Location'] = url_for('.item', item_id=item.id, _external=True)
        return response
app.add_url_rule('/user/items', view_func=ItemsAPI.as_view('items'), methods=['GET', 'POST'])


def get_item_body():
    data = request.get_json()
    body = data.get('body')
    if body is None or str(body).strip() == '':
        raise ValidationError('The item body was empty or invalid.')
    return body


class IndexAPI(MethodView):

    def get(self):
        return jsonify({
            "api_version": "1.0",
            "api_base_url": "http://127.0.0.1:5000/",
            "current_user_url": "http://127.0.0.1:5000/user",
            "authentication_url": "http://127.0.0.1:5000/oauth/token",
            "item_url": "http://127.0.0.1:5000/items/{item_id }",
            "current_user_items_url": "http://127.0.0.1:5000/user/items{?page,per_page}",
            "current_user_active_items_url": "http://127.0.0.1:5000/user/items/active{?page,per_page}",
            "current_user_completed_items_url": "http://127.0.0.1:5000/user/items/completed{?page,per_page}",
        })
app.add_url_rule('/', view_func=IndexAPI.as_view('index'), methods=['GET'])


class ActiveItemsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        pagination = Item.query.with_parent(g.current_user).filter_by(done=False).paginate(
            page, per_page=app.config['TODOISM_ITEM_PER_PAGE'])
        items = pagination.items
        current = url_for('.items', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.active_items', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.active_items', page=page + 1, _external=True)
        return jsonify(items_schema(items, current, prev, next, pagination))


class CompletedItemsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        pagination = Item.query.with_parent(g.current_user).filter_by(done=True).paginate(
            page, per_page=app.config['TODOISM_ITEM_PER_PAGE'])
        items = pagination.items
        current = url_for('.items', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.completed_items', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.completed_items', page=page + 1, _external=True)
        return jsonify(items_schema(items, current, prev, next, pagination))

    def delete(self):
        Item.query.with_parent(g.current_user).filter_by(done=True).delete()
        db.session.commit() 
        return '', 204

app.add_url_rule('/user/items/active', view_func=ActiveItemsAPI.as_view('active_items'), methods=['GET'])
app.add_url_rule('/user/items/completed', view_func=CompletedItemsAPI.as_view('completed_items'),
                    methods=['GET', 'DELETE'])