#!/usr/bin/python
''' Script to poll SQS queue '''

import json
import time
import sys
import socket
import ConfigParser
import logging
from datetime import datetime
import boto
from boto.sqs.message import RawMessage

def setup_logger(name, config, level=logging.INFO):
    """ Function to set up logging handlers """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if config.getboolean('file_logger', 'enabled'):
        logpath = config.get('file_logger', 'logpath')
        filehdlr = logging.FileHandler(logpath + name + '.log')
        logger.addHandler(filehdlr)

    if config.getboolean('console', 'enabled'):
        consolehdlr = logging.StreamHandler(sys.stdout)
        consolehdlr.setLevel(logging.DEBUG)
        logger.addHandler(consolehdlr)

    if config.getboolean('syslog', 'enabled'):
        host = config.get('syslog', 'host')
        port = config.getint('syslog', 'port')
        sysloghdlr = logging.handlers.SysLogHandler(address=(host, port),
                                                    socktype=socket.SOCK_DGRAM)
        sysloghdlr.setLevel(logging.INFO)
        logger.addHandler(sysloghdlr)

    return logger

def get_queue(config):
    ''' Get AWS SQS from config '''
    # Init AWS SQS
    awskey = config.get('aws', 'key')
    awssecret = config.get('aws', 'secret')
    queuename = config.get('aws', 'queue_name')
    region = config.get('aws', 'region')
    sqs = boto.sqs.connect_to_region(region, aws_access_key_id=awskey,
                                     aws_secret_access_key=awssecret)
    sqsqueue = sqs.get_queue(queuename)
    return sqsqueue

def process_msg(result, event_logger, compliance_logger):
    ''' Process log message '''
    try:
        msg = json.loads(result.get_body())
        if "Dome9 Continuous compliance" in msg["Subject"]:
            compliance_logger.info(json.dumps(msg))
        else:
            event_logger.info(json.dumps(msg))
            # result.delete()
    except:
        event_logger.exception("Error while handling messge:\n %s'",
                               (result.get_body()))
    finally:
        result.delete()
        ### this will delete all messages even if their handling failed.
        ### For additional reliability you can move this to the try block.
        ### (and then configure dead letter queue to handle 'poisonous messages')

def run():
    ''' Main loop '''
    print "starting SQS poller script"
    forever = any("forever" in s for s in sys.argv)
    if forever:
        print "running forever..."

    start = datetime.now()

    max_uptime = 60 #when not running forever...

    ### load config file
    config = ConfigParser.ConfigParser()
    config.read("./poller.conf")

    ### Create event logging handler
    event_logger = setup_logger('event', config)

    ### Create compliance logging handler
    compliance_logger = setup_logger('compliance', config)

    try:
        queue = get_queue(config)
        queue.set_message_class(RawMessage)
    except Exception as error_msg:
        event_logger.error("Error getting SQS queue: %s", error_msg)
        sys.exit(1)

    # Poll messages loop
    while True:
        result_count = 0
        try:
            results = queue.get_messages(10, wait_time_seconds=20)
            result_count = len(results)
            event_logger.debug("Got %s result(s) this time.", result_count)

            for result in results:
                process_msg(result, event_logger, compliance_logger)

        except:
            event_logger.exception("Unexpected error. Will retry in 60 seconds")
            time.sleep(60)

        finally:
            if not forever:
                if (datetime.now()-start).total_seconds() > max_uptime:
                    event_logger.debug("Worker uptime exceeded. exiting.")
                    sys.exit(0)
                if result_count == 0:
                    event_logger.debug("Queue is empty. exiting.")
                    sys.exit(0)

if __name__ == '__main__':
    run()
