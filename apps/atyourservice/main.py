# Click library has some problems with python3 when it comes to unicode: http://click.pocoo.org/5/python3/#python3-surrogates
# to fix this we need to set the environ variables to export the locales
import os
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

import click
import logging
from JumpScale import j
import asyncio

try:
    import jsonschema
except:
    j.do.execute("pip3 install jsonschema")
    import jsonschema

try:
    from JumpScale.baselib.atyourservice81.server.app import app as sanic_app
except:
    print("needs:\npip3 install sanic==0.3.0")
    j.do.execute("pip3 install sanic==0.3.0")
    from JumpScale.baselib.atyourservice81.server.app import app as sanic_app

print("to see api:http://localhost:5000/")

# configure asyncio logger
asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.handlers = []
asyncio_logger.addHandler(j.logger.handlers.consoleHandler)
asyncio_logger.addHandler(j.logger.handlers.fileRotateHandler)
asyncio_logger.setLevel(logging.DEBUG)


@click.command()
@click.option('--host', '-h', default='127.0.0.1', help='listening address')
@click.option('--port', '-p', default=5000, help='listening port')
@click.option('--debug', default=False, is_flag=True, help='enable debug logging')
def main(host, port, debug=False):
    # load the app
    async def init_ays(sanic, loop):
        if debug:
            loop.set_debug(True)
        j.atyourservice.debug = debug
        j.atyourservice._start(loop=loop)

    # start server
    sanic_app.run(debug=debug, host=host, port=port, workers=1, before_start=init_ays)


if __name__ == '__main__':
    main()
