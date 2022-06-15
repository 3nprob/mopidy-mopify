from __future__ import unicode_literals

import logging
import os
import tornado.web

from . import mem

from .services.sync import sync
from .services.autoupdate import update

from .services.queuemanager import core as QueueManagerCore
from .services.queuemanager import frontend
from .services.queuemanager import requesthandler as QueueManagerRequestHandler

from mopidy import config, ext

__version__ = '1.7.4-rc0'
__ext_name__ = 'mopify'
__verbosemode__ = False

logger = logging.getLogger(__ext_name__)


class MopifyExtension(ext.Extension):
    dist_name = 'Mopidy-Mopify'
    ext_name = __ext_name__
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(MopifyExtension, self).get_config_schema()
        schema['debug'] = config.Boolean()
        schema['facebook_auth_frame'] = config.String()
        schema['spotify_auth_callback'] = config.String()
        schema['spotify_auth_frame'] = config.String()
        schema['spotify_auth_refresh'] = config.String()
        schema['spotify_client_id'] = config.String()

        return schema

    def setup(self, registry):
        sync.Sync();

        # Create instances
        mem.queuemanager = QueueManagerCore.QueueManager()

        # Add Queuemanager Frontend class
        registry.add('frontend', frontend.QueueManagerFrontend)

        # Add web extension
        registry.add('http:app', {
            'name': self.ext_name,
            'factory': mopify_client_factory
        })

        logger.info('Setup Mopify')


class ConfigHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config
    def get(self):
        self.write(self.config)


def mopify_client_factory(config, core):
    directory = 'debug' if config.get(__ext_name__)['debug'] is True else 'min'
    mopifypath = os.path.join(os.path.dirname(__file__), 'static', directory)

    return [
        ('/sync/(.*)', sync.RootRequestHandler, {'core': core, 'config': config}),
        ('/queuemanager/(.*)', QueueManagerRequestHandler.RequestHandler, {'core': core, 'config': config}),
        ('/update', update.UpdateRequestHandler, {'core': core, 'config': config}),
	('/config', ConfigHandler, {'config': dict(config.get(__ext_name__))}),
        (r'/(.*)', tornado.web.StaticFileHandler, {
            "path": mopifypath,
            "default_filename": "index.html"
        })
    ]
