from flask import Flask, request

from PyPDF2 import PdfFileMerger, PdfFileReader
from urllib.request import urlopen
from io import StringIO, BytesIO
from subprocess import call
import signal
import sys
# # import logging
import requests
import json

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

# @app.route('/<slug>', methods=['POST'])
@app.route('/merge_pdfs/<slug>', methods=['POST'])
def merge_pdfs(slug):

    file_urls = json.loads(request.data.decode())

    makePacket(slug, file_urls)

    # Do not return untl makePacket finishes. DO this in a separate "thread" or in a redis-q.

    # It should return a response almost immediately.

    # Add some logic to check if the file already exists.

    # Also make a route that returns the file.

    return request.data

def makePacket(merged_id, filenames_collection):

    # Set a custom timeout: 2 minutes.
    # signal.signal(signal.SIGALRM)
    # signal.alarm(120)

    merger = PdfFileMerger(strict=False)

    # if any('.ppt' in string for string in filenames_collection):
    for filename in filenames_collection:
        # Run this up to two times, in the event of a timeout, libreoffice RunTimeError ('Office probably died'), or other exception.
        attempts = 0
        while attempts < 2:
            try:
                if filename.lower().endswith(('.xlsx', '.doc', '.docx', '.ppt', '.pptx', '.rtf')):
                    call(['unoconv', '-f', 'pdf', filename])
                    path, keyword, exact_file = filename.partition('attachments/')
                    new_file = exact_file.split('.')[0] + '.pdf'
                    f = open(new_file, 'rb')
                    merger.append(PdfFileReader(f))
                    call(['rm', new_file])
                else:
                    opened_url = urlopen(filename).read()
                    merger.append(BytesIO(opened_url), import_bookmarks=False)

                if attempts >= 1:
                    #LOGGER.info("Phew! It worked on the second try.")
                    #LOGGER.info("\n")
                    print("Fail!")

                break
            except Exception as err:
                attempts += 1
                #LOGGER.info("\n")
                #LOGGER.info(("{} caused the following error: ").format(filename))
                #LOGGER.info(err)
                if attempts < 2:
                    print("GEAT!")
                    #LOGGER.info(self.style.WARNING("Trying again...."))
                else:
                    print("AHHHHH!!")
                    #LOGGER.info(("Something went wrong. Please look at {}.").format(filename))
                    #LOGGER.info("\n")
            except:
                attempts += 1
                #LOGGER.info("\n")
                #LOGGER.info(("Unexpected error: {}").format(sys.exc_info()[0]))

    # 'merger' is a PdfFileMerger object, which can be written to a new file like so:
    try:
        merger.write('merged_pdfs/' + merged_id + '.pdf')
        #LOGGER.info(("Successful merge! {}").format(merged_id))
    except:
        #LOGGER.info(("{0} caused the failure of writing {1} as a PDF").format(sys.exc_info()[0], merged_id))
        #LOGGER.info(("We could not merge this file collection: {}").format(filenames_collection))
        print("FAIL!")

    # merger.write('merged_pdfs/' + merged_id + '.pdf')

    return merger

# def timeout_handler(signum, frame):
#     raise Exception("ERROR: Timeout")


if __name__ == "__main__":
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)