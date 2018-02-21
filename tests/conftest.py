import pytest
from sanic import Sanic, Blueprint
from sanic.response import json

from sanic_jwt import exceptions, Initialize
from sanic_jwt.decorators import protected


class User(object):

    def __init__(self, id, username, password):
        self.user_id = id
        self.username = username
        self.password = password

    def to_dict(self):
        properties = [
            'user_id',
            'username',
        ]
        return {prop: getattr(self, prop, None) for prop in properties}


@pytest.yield_fixture
def users():
    yield [
        User(1, 'user1', 'abcxyz'),
        User(2, 'user2', 'abcxyz'),
    ]


@pytest.yield_fixture
def username_table(users):
    yield {u.username: u for u in users}


@pytest.yield_fixture
def authenticate(username_table):
    async def authenticate(request, *args, **kwargs):
        username = request.json.get('username', None)
        password = request.json.get('password', None)

        if not username or not password:
            raise exceptions.AuthenticationFailed(
                "Missing username or password.")

        user = username_table.get(username, None)
        if user is None:
            raise exceptions.AuthenticationFailed("User not found.")

        if password != user.password:
            raise exceptions.AuthenticationFailed("Password is incorrect.")

        return user

    yield authenticate


@pytest.yield_fixture
def app(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app,
        authenticate=authenticate,
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_url_prefix(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt = Initialize(
        sanic_app,
        authenticate=authenticate,
        url_prefix='/somethingelse'
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt)


@pytest.yield_fixture
def app_with_bp(username_table, authenticate):

    sanic_app = Sanic()
    sanic_jwt_init = Initialize(
        sanic_app,
        authenticate=authenticate,
    )

    @sanic_app.route("/")
    async def helloworld(request):
        return json({"hello": "world"})

    @sanic_app.route("/protected")
    @protected()
    async def protected_request(request):
        return json({"protected": True})

    sanic_bp = Blueprint('bp', url_prefix='/bp')
    sanic_app.blueprint(sanic_bp)

    sanic_jwt_init_bp = Initialize(
        sanic_bp,
        app=sanic_app,
        authenticate=authenticate,
    )
    print('sanic_bp', sanic_bp.url_prefix)
    print('sanic_jwt_init_bp', sanic_jwt_init_bp._get_url_prefix())
    print('sanic_bp', sanic_bp.routes)

    @sanic_bp.route("/")
    async def bp_helloworld(request):
        return json({"hello": "world"})

    @sanic_bp.route("/protected")
    @protected()
    async def bp_protected_request(request):
        return json({"protected": True})

    yield (sanic_app, sanic_jwt_init, sanic_bp, sanic_jwt_init_bp)
