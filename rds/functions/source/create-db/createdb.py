#!/usr/bin/python
import psycopg2
import cfn_resource
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.info("Started Lambda!")
handler = cfn_resource.Resource()
physical_resource_id = "dummy-resource-id"

def fail(reason, physical_resource_id=physical_resource_id):
    return {
        'Status': cfn_resource.FAILED,
        'Reason': reason,
        'PhysicalResourceId': physical_resource_id
    }

def check_props(props, param):
    if param not in props or not props[param]:
        raise Exception('Parameter %s not found.' % param)
    return props[param]

@handler.create
def create_database(event, context):
    props = event['ResourceProperties']
    logger.info('Got event: %s' % event)
    try:
        db_names = check_props(props, 'DBNames')
        db_user = check_props(props, 'DBUser')
        db_password = check_props(props, 'DBPassword')
        db_host = check_props(props, 'DBHost')
        if 'PhysicalResourceId' in event:
            physical_resource_id = event['PhysicalResourceId']
        else:
            physical_resource_id = "%s_%s" % (db_host, db_names[0])
    except Exception as e:
        return fail(str(e), physical_resource_id="parameters-not-set")
    
    logger.info("Pre-connect to %s via Psycopg2" % db_host)
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(database='postgres', user=db_user, host=db_host, password=db_password)
        logger.info("Connected to Database %s" % db_host)
    except Exception as e:
        return fail('Could not connect to the Postgres DB: %s' % str(e))
    else:
        try:
            conn.set_session(autocommit=True)
            cursor = conn.cursor()
            for db_name in db_names:
                logger.info("Creating database %s on %s" % (db_name, db_host))
                cursor.execute("CREATE DATABASE %s WITH OWNER %s" % (db_name, db_user))
            logger.info("Database created")
        except Exception as e:
            return fail(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    logger.info("Done!")
    return {
        'Status': 'SUCCESS',
        'PhysicalResourceId': physical_resource_id,
        'Reason': 'Successfully created databases %s' % db_names
    }