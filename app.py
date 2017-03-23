from flask import Flask, request, make_response, send_from_directory
from flask import send_file, current_app as app
from flask_cors import cross_origin

from io import BytesIO
import json
from redis import Redis

from tasks import makePacket

app = Flask(__name__)
app.config.from_object('config')

redis = Redis()


@app.route('/')
def index():
    return 'A flask app that listens for requests from <a href="https://boardagendas.metro.net/" target="_blank">LA Metro Councilmatic</a>. The app consolidates PDFs for Board Reports and Events, stores the merged documents, and provides a route that returns PDFs.'


@app.route('/merge_pdfs/<slug>', methods=['POST'])
def merge_pdfs(slug):

    file_urls = json.loads(request.data.decode())

    makePacket.delay(slug, file_urls)

    return json.dumps({'success': True})


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


if __name__ == "__main__":

    app.run(host='0.0.0.0', debug=True)