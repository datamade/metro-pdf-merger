from urllib.request import urlopen
from io import BytesIO
from subprocess import call
import signal
import sys
from uuid import uuid4
from pickle import loads, dumps
import logging
import logging.config
import traceback

from redis import Redis

from PyPDF2 import PdfFileMerger, PdfFileReader

from raven import Client

from subprocess import check_output, CalledProcessError

import boto3

from config import REDIS_QUEUE_KEY, LOGGING, SENTRY_DSN, S3_BUCKET

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
            rv = redis.get(self.key)  # Return the value at the given key
            if rv is not None:
                self._rv = loads(rv)  # Reads the pickled object
        return self._rv


def queuefunc(f):
    def delay(*args, **kwargs):
        qkey = REDIS_QUEUE_KEY
        key = '%s:result:%s' % (qkey, str(uuid4()))  # Creates a key with the REDIS_QUEUE_KEY and a randomly generated UUID.
        s = dumps((f, key, args, kwargs))  # Pickles together the function and parameters; returns the pickled representation as a string.
        redis.rpush(REDIS_QUEUE_KEY, s)  # Push (append) values to the tail of the stored list.
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
                if filename.lower().endswith(('.xlsx', '.doc', '.docx', '.ppt', '.pptx', '.rtf')) or filename in ['http://metro.legistar1.com/metro/attachments/6aaadb7d-4c9a-429b-a499-2107bc9d031e.pdf', 'http://metro.legistar1.com/metro/attachments/2146cf74-8a70-4d48-8a73-94f21a40106d.pdf', 'http://metro.legistar1.com/metro/attachments/c1fae640-108f-411d-9790-204eb7b9efbb.pdf']:
                    # call(['unoconv', '-f', 'pdf', filename])
                    try:
                        logger.info('Unoconv conversion underway...')
                        check_output(['unoconv', '-f', 'pdf', filename])
                        logger.info('Successful conversion!')
                    except CalledProcessError as call_err:
                        logger.info('Unsuccessful conversion. We had some difficulty with {}'.format(filename))
                        logger.info(call_err)
                        # logger.info(call_err.output) No output....

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
                break
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
        merged = BytesIO()
        merger.write(merged)
        merged.seek(0)

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(S3_BUCKET)
        s3_key = bucket.Object('{id}.pdf'.format(id=merged_id))
        s3_key.upload_fileobj(merged)

        logger.info(("Successful merge! {}").format(merged_id))
    except:
        logger.error(("{0} caused the failure of writing {1} as a PDF, and we could not merge this file collection: \n {2}").format(sys.exc_info()[0], merged_id, filenames_collection))
        client.captureException()

    return merger


def queue_daemon():

    from deployment import DEPLOYMENT_ID

    with open('/tmp/worker_running.txt', 'w') as f:
        f.write(DEPLOYMENT_ID)

    while 1:

        msg = redis.blpop(REDIS_QUEUE_KEY)
        func, key, args, kwargs = loads(msg[1])
        try:
            func(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logger.info(tb)
            client.captureException()

        if redis.llen(REDIS_QUEUE_KEY) == 0:
            logger.info("Hurrah! Done merging Metro PDFs.")


def timeout_handler(signum, frame):
    raise Exception("ERROR: Timeout")
