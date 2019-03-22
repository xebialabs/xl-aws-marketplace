#!/usr/bin/python
import psycopg2
import cfnresponse
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.info("Started Lambda!")
physical_resource_id = "dummy-resource-id"

def fail(reason, physical_resource_id=physical_resource_id):
    logger.error("Failed [%s]: %s" % (physical_resource_id, reason))
    return (cfnresponse.FAILED, physical_resource_id, reason)

def check_props(props, param):
    if param not in props or not props[param]:
        raise Exception('Parameter %s not found.' % param)
    return props[param]

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
                logger.info("Database %s created" % db_name)
            logger.info("All Databases created.")
        except Exception as e:
            return fail(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    logger.info("Done!")
    return (cfnresponse.SUCCESS, physical_resource_id, 'Successfully created databases %s' % db_names)

def handler(event, context):
    logger.info('Received event: %s' % json.dumps(event))
    status = cfnresponse.SUCCESS
    physical_resource_id = None
    data = {}
    reason = None
    try:
        if event['RequestType'] == 'Create':
            status, physical_resource_id, reason = create_database(event, context)
    finally:
        cfnresponse.send(event, context, status, data, physical_resource_id, False, reason)
