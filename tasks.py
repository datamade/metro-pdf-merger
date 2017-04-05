from flask import Flask, request, make_response, send_from_directory
from flask import send_file, current_app as app
from flask_cors import cross_origin

from PyPDF2 import PdfFileMerger, PdfFileReader
from urllib.request import urlopen
from io import BytesIO
from subprocess import call, check_output, CalledProcessError
import signal
import sys
import requests
import json
from redis import Redis
from uuid import uuid4
from pickle import loads, dumps
import logging
import logging.config
import traceback
import os
from raven import Client

from config import REDIS_QUEUE_KEY, LOGGING, SENTRY_DSN

redis = Redis()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)
client = Client(SENTRY_DSN)


class DelayedResult(object):
    def __init__(self, key):
        self.key = key
        self._rv = None

    @property
    def return_value(self):
        if self._rv is None:
            rv = redis.get(self.key) # Return the value at the given key
            if rv is not None:
                self._rv = loads(rv) # Reads the pickled object
        return self._rv


def queuefunc(f):
    def delay(*args, **kwargs):
        qkey = REDIS_QUEUE_KEY
        key = '%s:result:%s' % (qkey, str(uuid4())) # Creates a key with the REDIS_QUEUE_KEY and a randomly generated UUID.
        s = dumps((f, key, args, kwargs)) # Pickles together the function and parameters; returns the pickled representation as a string.
        redis.rpush(REDIS_QUEUE_KEY, s) # Push (append) values to the tail of the stored list.
        return DelayedResult(key)
    f.delay = delay
    return f


@queuefunc
def makePacket(merged_id, filenames_collection):
    # Custom Timeout error: 2 minutes.
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)

    merger = PdfFileMerger(strict=False)

    for filename in filenames_collection:
        # Run this up to two times, in the event of a timeout, libreoffice RunTimeError ('Office probably died'), or other exception.
        attempts = 0
        while attempts < 2:
            try:
                if filename.lower().endswith(('.xlsx', '.doc', '.docx', '.ppt', '.pptx', '.rtf')):
                    # call(['unoconv', '-f', 'pdf', filename])
                    try:
                        check_output(['unoconv', '-f', 'pdf', filename])
                        logger.error('Success!!')
                    except CalledProcessError as call_err:
                        logger.error("CalledProcessError")
                        logger.error(call_err.output, call_err.return_code)
                    path, keyword, exact_file = filename.partition('attachments/')
                    new_file = exact_file.split('.')[0] + '.pdf'
                    f = open(new_file, 'rb')
                    merger.append(PdfFileReader(f))
                    call(['rm', new_file])
                else:
                    opened_url = urlopen(filename).read()
                    try:
                        merger.append(BytesIO(opened_url), import_bookmarks=False)
                    except:
                        # For PDFs with a little extra garbage, we need to open, save, and re-convert them.
                        call(['unoconv', '-f', 'pdf', filename])
                        path, keyword, exact_file = filename.partition('attachments/')
                        new_file = exact_file.split('.')[0] + '.pdf'
                        f = open(new_file, 'rb')
                        merger.append(PdfFileReader(f))
                        call(['rm', new_file])
                if attempts >= 1:
                    logger.info('Phew! It worked on the second try.')
                    logger.info('\n')
            except Exception as err:
                attempts += 1
                logger.error(("\n {0} caused the following error: \n {1}").format(filename, err))
                if attempts < 2:
                    logger.info('Trying again...')
                else:
                    logger.error(("Something went wrong. Please look at {}. \n").format(filename))
                    client.captureException()
            except:
                attempts += 1
                logger.error(("\n Unexpected error: {}").format(sys.exc_info()[0]))
                client.captureException()

    # 'merger' is a PdfFileMerger object, which can be written to a new file like so:
    try:
        merger.write('merged_pdfs/' + merged_id + '.pdf')
        logger.info(("Successful merge! {}").format(merged_id))
    except:
        logger.error(("{0} caused the failure of writing {1} as a PDF, and we could not merge this file collection: \n {2}").format(sys.exc_info()[0], merged_id, filenames_collection))
        client.captureException()

    return merger


def queue_daemon():
    while 1:

        msg = redis.blpop(REDIS_QUEUE_KEY)
        func, key, args, kwargs = loads(msg[1])
        try:
            rv = func(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logger.info(tb)
            client.captureException()

        if redis.llen(REDIS_QUEUE_KEY) == 0:
            logger.info("Hurrah! Done merging Metro PDFs.")


def timeout_handler(signum, frame):
    raise Exception("ERROR: Timeout")
