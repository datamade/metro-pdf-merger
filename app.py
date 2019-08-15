from flask import Flask, request, make_response, abort, Response
from flask_cors import cross_origin

import json
from redis import Redis

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

import boto3
import botocore

from config import SENTRY_DSN, S3_BUCKET
from tasks import makePacket

app = Flask(__name__)
app.config.from_object('config')

redis = Redis()

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FlaskIntegration()]
)


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

    client = boto3.client('s3')

    try:
        document = client.get_object(Bucket=S3_BUCKET,
                                     Key='{}.pdf'.format(ocd_id))
    except botocore.exceptions.ClientError:
        response = make_response('Document not found', 404)
    else:
        # This closure just iterates the streaming response from S3 into a
        # streaming response from this route. That way we don't have to read
        # anything into memory
        def generate_response(doc):
            while True:
                yield doc.read(4096)

        response = Response(generate_response(document['Body']))
        response.headers["Content-Disposition"] = 'attachment; filename={}.pdf'.format(ocd_id)
        response.headers['Content-Length'] = document['ContentLength']

    return response


if __name__ == "__main__":

    app.run(host='0.0.0.0', debug=True)
