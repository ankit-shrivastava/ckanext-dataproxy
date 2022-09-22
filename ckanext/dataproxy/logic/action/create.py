from ckan.logic import get_action
from ckan.common import config
from ckanext.dataproxy.utils.utils import dataproxy_encrypt
from sqlalchemy import *
from ckanext.dataproxy.utils.utils import dataproxy_decrypt
import pandas as pd
import os
from werkzeug.datastructures import FileStorage

orig_resource_create = get_action('resource_create')


def dataproxy_resource_create(context, data_dict=None):
    """
    Intercepts default resource_create action and encrypts password if resource is dataproxy type
    Args:
        context: Request context.
        data_dict: Parsed request parameters.
    Returns:
        see get_action('resource_create').
    Raises:
        Exception: if ckan.dataproxy.secret configuration not set.
    """
    # If not set, default to empty string
    url_type = data_dict.get('url_type')

    if url_type == 'dataproxy':
        secret = config.get('ckan.dataproxy.secret', False)
        if not secret:
            raise Exception(
                'ckan.dataproxy.secret must be defined to encrypt passwords')
        password = data_dict.get('db_password')
        # connstr = data_dict.get('sqlalchemy_uri')

        # replace password with a _password_ placeholder
        data_dict['sqlalchemy_uri'] = data_dict['sqlalchemy_uri'].replace(
            password, '_password_')
        # encrypt db_password
        data_dict['db_password'] = dataproxy_encrypt(password, secret)

        # table_name = data_dict.get('table')
        # database_name = data_dict.get('database')
        # schema_name = None

        # csv_file = f"{database_name}.{schema_name}.{table_name}.out.csv"

        # engine = create_engine(connstr)
        # meta = MetaData(bind=engine)

        # table = Table(table_name, meta, autoload=True, schema=schema_name)

        # conn = engine.connect()
        # select_query = select([table]).limit(100)

        # df = pd.read_sql(select_query, con=conn)
        # df.to_csv(f'/tmp/{csv_file}', index=False)

        # upload = FileStorage(filename=u'')

        # if os.path.exists(f'/tmp/{csv_file}'):
        #     f = open(f'/tmp/{csv_file}', "rb+")
        #     upload = FileStorage(f, csv_file, name=csv_file,
        #                          content_type=u'CSV')
        # data_dict["upload"] = upload

    #f = open("/tmp/demofile2.txt", "a")
    # f.write(data_dict)
    # f.write(url_tye)
    # f.close()

    ret = orig_resource_create(context, data_dict)
    data_dict["url_type"] == "dataproxy"
    # try:
    #     f.close()
    # except:
    #     pass

    return ret
