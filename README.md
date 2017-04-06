# Metro PDF Merger

A flask app that listens for requests from [LA Metro Councilmatic](https://github.com/datamade/la-metro-councilmatic). The app consolidates PDFs for Board Reports and Events, stores the merged documents, and provides a route that returns PDFs.

## Set up

Copy the config.py.example file. It has everything you need to run the app. If you want to configure the app with Sentry, then find your DSN Client key and assign its value to SENTRY_DSN.

```bash
cp config.py.example config.py
```

Create a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

```bash
mkvirtualenv metro-merger
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The Metro PDF Merger uses [unoconv](https://github.com/dagwieers/unoconv), a CLI tool that performs document conversions; it reads any document type supported by LibreOffice.

#### Mac OS

Install unoconv with brew:

```bash
brew install unoconv
```

The brew installation comes with a caveat: `unoconv` works only with LibreOffice versions 3.6.0.1 - 4.3.x. [Get the DMG file for version 4.3.](https://downloadarchive.documentfoundation.org/libreoffice/old/4.3.7.2/mac/x86_64/LibreOffice_4.3.7.2_MacOS_x86-64.dmg) Or [visit here](https://downloadarchive.documentfoundation.org/libreoffice/old/4.3.7.2/mac/x86_64/).


#### Ubuntu

On Linux, but also on any operting system, you may chose to partially install LibreOffice, which helps to keep your server safe from attacks (smaller surface area for potential invasion) and free of the heavy-weight packaging in the full LibreOffice suite.

Install libreoffice-script-provider-python and the necessary packages from LibreOffice:

```bash
apt-get install libreoffice-script-provider-python
apt-get install libreoffice-writer
apt-get install libreoffice-calc
apt-get install libreoffice-impress
```

Then, install unoconv from source:

```bash
mkdir unoconv
cd unoconv
wget https://raw.githubusercontent.com/dagwieers/unoconv/master/unoconv
# Make a symbolic link
sudo ln -s /home/ubuntu/unoconv/unoconv /usr/bin/unoconv
```

In the unoconv file, specify the location of Python:

```
#!/usr/bin/python3
```

## Get started

Run the app locally:

```bash
python app.py
```

This app uses [Redis](https://redis.io/), a data store that brokers messages between a sender and receiver. You need to [download Redis](https://redis.io/download), first. Then, you can put Redis to "work." In a new terminal tab, run:

```bash
python run_worker.py
```

This module calls `queue_daemon`, a while loop that processes entries in the Redis queue, or in other words, runs the `makePacket` function, which merges and saves the newly consolidated PDFs.

This app serves the needs of LA Metro Councilmatic. Learn about setting up an instance of [LA Metro Councilmatic](https://github.com/datamade/la-metro-councilmatic). LA Metro comes with a management command that queries the Metro database and sends post requests. Each request carries a JSON object, which contains URLs that point to bill documents on Legistar (i.e., the documents that metro-pdf-merger consolidates).

In the LA Metro repo, find `settings.py` and change MERGER_BASE_URL. It should point to your flask app, for instance:

```
MERGER_BASE_URL = 'http://0.0.0.0:5000'
```

Then, run the management command in your LA Metro repo:

```bash
# Grab all documents
python manage.py compile_pdfs --all_documents

# Grab only the most recently added documents
python manage.py compile_pdfs
```

## Team

* Regina Compton, DataMade - developer

## Errors / Bugs

If something is not behaving intuitively, it is a bug, and should be reported.
Report it here: https://github.com/datamade/nyc-councilmatic/issues

## Note on Patches/Pull Requests

* Fork the project.
* Make your feature addition or bug fix.
* Commit, do not mess with rakefile, version, or history.
* Send a pull request. Bonus points for topic branches.

## Copyright

Copyright (c) 2017 DataMade. Released under the [MIT License](https://github.com/datamade/nyc-councilmatic/blob/master/LICENSE).




