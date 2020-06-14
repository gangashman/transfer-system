#!/usr/bin/env python3

from datetime import timedelta
from logging.config import dictConfig
from socket import gaierror

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

import settings
from databases import Database
from sanic import Sanic
from sanic_session import InMemorySessionInterface, Session

dictConfig(settings.LOGGER_SETTINGS)

app = Sanic(__name__)

session = Session(app, interface=InMemorySessionInterface())

if not settings.SECRET_KEY:
    raise Exception('ERROR: SECRET_KEY is None')

app.config['SECRET_KEY'] = settings.SECRET_KEY

mainmetatadata = MetaData()
Base = declarative_base(metadata=mainmetatadata)


@app.listener('before_server_start')
async def connect_db(app, loop):
    app.config['database'] = Database(app.config['CONNECTION'])
    try:
        await app.config['database'].connect()

    except gaierror:
        raise gaierror(f"Can't connect to {app.config['CONNECTION']}")


@app.listener('before_server_stop')
async def disconnect_db(app, loop):
    await app.config['database'].disconnect()


def create_app(connection, run=True):

    app.config['CONNECTION'] = connection

    from transfers.views import transfers_blueprint
    from users.views import users_blueprint

    # Register views
    app.blueprint(users_blueprint)
    app.blueprint(transfers_blueprint)

    if run:
        app.run(
            settings.HOST_IP, int(settings.HOST_PORT),
            debug=bool(settings.DEBUG),
            auto_reload=bool(settings.DEBUG)
        )
    return app


if __name__ == '__main__':
    create_app(settings.connection)
