from urllib.request import urlopen
from urllib.error import HTTPError
from io import BytesIO
from subprocess import call
import threading
import multiprocessing
import signal
import sys
from uuid import uuid4
from pickle import loads, dumps
import logging
import logging.config

from redis import Redis

from PyPDF2 import PdfFileMerger, PdfFileReader

from sentry_sdk import capture_exception

from subprocess import check_output, CalledProcessError

import boto3

from config import REDIS_QUEUE_KEY, LOGGING, SENTRY_DSN, S3_BUCKET

redis = Redis()

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


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
    merger = PdfFileMerger(strict=False)

    for filename in filenames_collection:
        # Run this up to two times, in the event of a timeout, libreoffice RunTimeError ('Office probably died'), or other exception.
        attempts = 0
        while attempts < 2:
            try:
                if filename.lower().endswith(('.xlsx', '.doc', '.docx', '.ppt', '.pptx', '.rtf')) or filename in ['http://metro.legistar1.com/metro/attachments/6aaadb7d-4c9a-429b-a499-2107bc9d031e.pdf', 'http://metro.legistar1.com/metro/attachments/2146cf74-8a70-4d48-8a73-94f21a40106d.pdf', 'http://metro.legistar1.com/metro/attachments/c1fae640-108f-411d-9790-204eb7b9efbb.pdf']:
                    try:
                        logger.info('Unoconv conversion underway...')
                        check_output(['unoconv', '-f', 'pdf', filename])
                        logger.info('Successful conversion!')
                    except CalledProcessError as call_err:
                        logger.info('Unsuccessful conversion. We had some difficulty with {}'.format(filename))
                        logger.info(call_err)

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
            except HTTPError as err:
                attempts += 1
                logger.error(("\n {0} caused the following error: \n {1}").format(filename, err))
                error_logging(attempts, filename)
            except FileNotFoundError as err:
                attempts += 1
                logger.error(("\n {0} caused the following error: \n {1}").format(filename, err))
                error_logging(attempts, filename)

    # 'merger' is a PdfFileMerger object, which can be written to a new file like so:
    try:
        merged = BytesIO()
        merger.write(merged)
        merged.seek(0)

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(S3_BUCKET)
        s3_key = bucket.Object('{id}.pdf'.format(id=merged_id))
        s3_key.upload_fileobj(merged)
        s3_key.Acl().put(ACL='public-read')

        logger.info(("Successful merge! {}").format(merged_id))
    except:
        logger.error(("{0} caused the failure of writing {1} as a PDF, and we could not merge this file collection: \n {2}").format(sys.exc_info()[0], merged_id, filenames_collection))
        capture_exception()

    return merger


class ChildProcessor(multiprocessing.Process):
    def __init__(self, msg, **kwargs):
        super().__init__(**kwargs)
        self.msg = msg

    def run(self):
        func, key, args, kwargs = loads(self.msg)
        func(*args, **kwargs)


class ParentProcessor(threading.Thread):
    def __init__(self, stopper, **kwargs):
        super().__init__(**kwargs)

        self.stopper = stopper

    def run(self):
        logger.info('Listening for messages...')
        while not self.stopper.is_set():
            self.doWork()

    def doWork(self):
        msg = redis.blpop(REDIS_QUEUE_KEY)

        child = ChildProcessor(msg[1])
        child.start()
        exited = child.join(timeout=120)

        if exited is None:
            child.terminate()

        if redis.llen(REDIS_QUEUE_KEY) == 0:
            logger.info("Hurrah! Done merging Metro PDFs.")


def queue_daemon():
    try:
        # This is really only needed for deployments
        # There might be a better way of doing this
        from deployment import DEPLOYMENT_ID

        with open('/tmp/worker_running.txt', 'w') as f:
            f.write(DEPLOYMENT_ID)
    except ImportError:
        pass

    stopper = threading.Event()
    worker = ParentProcessor(stopper)

    def signalHandler(signum, frame):
        stopper.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, signalHandler)
    signal.signal(signal.SIGTERM, signalHandler)

    logger.info('Starting worker')
    worker.start()


def error_logging(attempts, filename):
    if attempts < 2:
        logger.info('Trying again...')
    else:
        logger.error(("Something went wrong. Please look at {}. \n").format(filename))
        capture_exception()
