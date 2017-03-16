from flask import Flask, request, make_response, send_from_directory
from flask import send_file, current_app as app
from flask_cors import cross_origin

from PyPDF2 import PdfFileMerger, PdfFileReader
from urllib.request import urlopen
from io import StringIO, BytesIO
from subprocess import call
import signal
import sys
import requests
import json

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)


@app.route('/')
def index():
    return 'The place to find great PDFs.'


@app.route('/merge_pdfs/<slug>', methods=['POST'])
def merge_pdfs(slug):

    file_urls = json.loads(request.data.decode())

    makePacket(slug, file_urls)

    # Do not return until makePacket finishes. Do this in a separate "thread" or in a redis-q. It should return a response almost immediately.

    return request.data


@app.route('/document/<ocd_id>')
@cross_origin()
def document(ocd_id):
    file_path = 'merged_pdfs/' + ocd_id + '.pdf'
    pdfFileObj = open(file_path, 'rb')
    readFile = pdfFileObj.read()
    output = BytesIO(readFile)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = 'attachment; filename=%s' % file_path

    return response


def makePacket(merged_id, filenames_collection):

    merger = PdfFileMerger(strict=False)

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
                    app.logger.info('Phew! It worked on the second try.')
                    app.logger.info('\n')
                break
            except Exception as err:
                attempts += 1
                app.logger.error(("\n {0} caused the following error: \n {1}").format(filename, err))
                if attempts < 2:
                    app.logger.info('Trying again...')
                else:
                    app.logger.error(("Something went wrong. Please look at {}. \n").format(filename))
            except:
                attempts += 1
                app.logger.error(("\n Unexpected error: {}").format(sys.exc_info()[0]))

    # 'merger' is a PdfFileMerger object, which can be written to a new file like so:
    try:
        merger.write('merged_pdfs/' + merged_id + '.pdf')
        app.logger.info(("Successful merge! {}").format(merged_id))
    except:
        app.logger.error(("{0} caused the failure of writing {1} as a PDF, and we could not merge this file collection: \n {2}").format(sys.exc_info()[0], merged_id, filenames_collection))

    return merger


if __name__ == "__main__":
    import os
    handler = RotatingFileHandler('debug.log', maxBytes=100000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)