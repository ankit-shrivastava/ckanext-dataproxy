import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import json
from ckanext.dataproxy.logic.action.create import dataproxy_resource_create
from ckanext.dataproxy.logic.action.update import dataproxy_resource_update
from ckanext.reclineview.plugin import ReclineViewBase, ReclineView
from ckan.lib.helpers import resource_view_get_fields
import os

from ckanext.dataproxy.utils.utils import dataproxy_decrypt
from ckan.common import config
from sqlalchemy import *
import pandas as pd
import numpy as np
from flask import Blueprint

import logging

log = logging.getLogger(__name__)


class DataproxyView(plugins.SingletonPlugin):
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    # plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'ckanext-dataproxy')

    def _resource_view_get_fields(self, resource):
        # Skip filter fields lookup for dataproxy resources
        url_type = resource.get('url_type', '')
        sqlalchemy_uri = False
        if "sqlalchemy_uri" in resource:
            sqlalchemy_uri = True
        if url_type == 'dataproxy' or sqlalchemy_uri:
            return []
        return resource_view_get_fields(resource)

    def get_helpers(self):
        ret = {}
        # ret = super().get_helpers()
        # ret["get_dataproxy_url"] = my_get_dataproxy_url
        ret.update({'resource_view_get_fields': self._resource_view_get_fields})
        return ret

    def info(self):
        ''' IResourceView '''
        return {'name': 'dataproxy_view',
                'title': plugins.toolkit._('Database Proxy Explorer'),
                'icon': 'table',
                'default_title': plugins.toolkit._('Database Proxy Explorer'),
                }

    def can_view(self, data_dict):
        ''' IResourceView '''
        resource = data_dict['resource']
        return resource.get('url_type', '') == 'dataproxy'

    def view_template(self, context, data_dict):
        return 'dataproxy_view.html'

    def form_template(self, context, data_dict):
        return 'dataproxy_form.html'

    def setup_template_variables(self, context, data_dict):
        # we add datastore_active as json value so recline would request datastore api endpoint,
        # but ckan itself knows it's not datastore therefore ckan won't offer recline views to dataproxy resources
        # data_dict['resource']['datastore_active'] = True

        resource = data_dict.get("resource", None)
        if resource:
            url_type = resource.get('url_type', '')

            sqlalchemy_uri = False
            if "sqlalchemy_uri" in resource:
                sqlalchemy_uri = True
            if url_type == 'dataproxy' or sqlalchemy_uri:
                data_dict['resource']['myitem'] = True
                data_dict['resource']['yupee'] = "hgadas"

                table_name = resource.get('table')
                database_name = resource.get('database')
                schema_name = None
                connstr = resource.get('sqlalchemy_uri')
                secret = config.get('ckan.dataproxy.secret', False)

                password = resource.get('db_password')
                password = dataproxy_decrypt(password, secret)
                connstr = connstr.replace('_password_', password)

                engine = create_engine(connstr)
                meta = MetaData(bind=engine)
                table = Table(table_name, meta, autoload=True,
                              schema=schema_name)
                select_query = select([table]).limit(100)

                conn = engine.connect()
                df = pd.read_sql(select_query, con=conn)
                df.replace({np.nan: None}, None, inplace=True)
                lst = df.values.tolist()
                data_dict['resource']['preview'] = lst

        return {'resource_json': json.dumps(data_dict['resource']),
                'resource_view_json': json.dumps(data_dict['resource_view'])}


def hello_plugin():
    u'''A simple view function'''

    return {
        "help": "http://192.168.0.111:5000/api/3/action/help_show?name=datastore_search",
        "success": True,
        "result": {
            "filters": {

            },
            "include_total": True,
            "limit": 10,
            "offset": 0,
            "records_format": "objects",
            "resource_id": "bb6a7675-6781-4fb6-b2ec-bd5519428530",
            "total_estimation_threshold": 1000,
            "records": [
                {
                    "_id": 1,
                    "SUM(DAILYCOST)": 16.439751,
                    "INVOICEDATE": "2022-08-09T00:00:00",
                    "SERVICE": "AWS"
                },
                {
                    "_id": 2,
                    "SUM(DAILYCOST)": 3.778264164,
                    "INVOICEDATE": "2022-08-07T00:00:00",
                    "SERVICE": "Snowflake"
                }
            ],
            "fields": [
                {
                    "id": "_id",
                    "type": "int"
                },
                {
                    "id": "\ufeffSUM(DAILYCOST)",
                    "type": "numeric"
                },
                {
                    "id": "INVOICEDATE",
                    "type": "timestamp"
                },
                {
                    "id": "SERVICE",
                    "type": "text"
                }
            ],
            "_links": {
                "start": "/api/3/action/datastore_search",
                "next": "/api/3/action/datastore_search?offset=10"
            },
            "total": 28,
            "total_was_estimated": False
        }
    }


class DataproxyPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'ckanext-dataproxy')

    # def before_show(self, resource_dict):
    #     if not plugins.toolkit.check_ckan_version(min_version='2.3.0') and resource_dict.get('url_type') == 'dataproxy':
    #         # Mask dataproxy resources as datastore ones for recline to render
    #         resource_dict['datastore_active'] = True
    #     return resource_dict

    def get_actions(self):
        ''' IActions '''
        return {'resource_create': dataproxy_resource_create,
                'resource_update': dataproxy_resource_update}

    # def before_map(self, map):
    #     ''' IRoutes '''
    #     # Override API mapping on controller level to intercept dataproxy calls
    #     search_ctrl = 'ckanext.dataproxy.controllers.search:SearchController'
    #     map.connect('dataproxy', '/api/3/action/datastore_search',
    #                 controller=search_ctrl, action='search_action')
    #     map.connect('dataproxy', '/api/3/action/datastore_search_sql',
    #                 controller=search_ctrl, action='search_sql_action')
    #     return map

    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''

        # Create Blueprint for plugin
        blueprint = Blueprint("dataproxy", self.__module__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        rules = [
            (u'/api/3/dataproxy_search', u'hello_plugin', hello_plugin)
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)
        return blueprint
