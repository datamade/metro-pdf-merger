from flask import Flask, request, make_response, abort
from flask_cors import cross_origin

from io import BytesIO
import json
from redis import Redis
from raven.contrib.flask import Sentry

from config import SENTRY_DSN
from tasks import makePacket

app = Flask(__name__)
app.config.from_object('config')

redis = Redis()
sentry = Sentry(app, dsn=SENTRY_DSN)


@app.route('/')
def index():
    return 'A flask app that listens for requests from <a href="https://boardagendas.metro.net/" target="_blank">LA Metro Councilmatic</a>. The app consolidates PDFs for Board Reports and Events, stores the merged documents, and provides a route that returns PDFs.'


@app.route('/pong/')
def pong():

    try:
        from deployment import DEPLOYMENT_ID
    except ImportError:
        abort(401)

    return DEPLOYMENT_ID


@app.route('/merge_pdfs/<slug>', methods=['POST'])
def merge_pdfs(slug):

    file_urls = json.loads(request.data.decode())

    makePacket.delay(slug, file_urls)

    return json.dumps({'success': True})


@app.route('/document/<ocd_id>')
@cross_origin()
def document(ocd_id):
    file_path = 'merged_pdfs/' + ocd_id + '.pdf'

    try:
        pdfFileObj = open(file_path, 'rb')
        readFile = pdfFileObj.read()
        output = BytesIO(readFile)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = 'attachment; filename=%s' % file_path
    except FileNotFoundError:
        response = make_response('Document not found', 404)

    return response


if __name__ == "__main__":

    app.run(host='0.0.0.0', debug=True)
