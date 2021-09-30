# Metro PDF Merger

A flask app that listens for requests from [LA Metro Councilmatic](https://github.com/datamade/la-metro-councilmatic). The app consolidates PDFs for Board Reports and Events, stores the merged documents, and provides a route that returns PDFs.

## Working with a local instance of LA Metro Councilmatic

This app serves the needs of LA Metro Councilmatic. Learn about setting up an instance of [LA Metro Councilmatic](https://github.com/datamade/la-metro-councilmatic). LA Metro comes with a management command that queries the Metro database and sends post requests. Each request carries a JSON object, which contains URLs that point to bill documents on Legistar (i.e., the documents that metro-pdf-merger consolidates).

First, run the merger as described in **Development**, below.

Then, in your LA Metro directory, find `settings.py` and update `MERGER_BASE_URL` to point at your Flask app.

```
MERGER_BASE_URL = 'http://host.docker.internal:5000'
```

Finally, run the management command in your LA Metro directory:

```bash
# Grab all documents
docker-compose run --rm app python manage.py compile_pdfs --all_documents

# Grab only the most recently added documents
docker-compose run --rm app python manage.py compile_pdfs
```

## Development

### With Docker

Copy the example `.env` file, then add credentials for an AWS user with access
to your configured S3 bucket.

```bash
cp .env.example .env
```

Next, start the app:

```bash
docker-compose up
```

The merger app will be available at http://localhost:5000.

### Without Docker

#### Install system dependencies

##### 1. Unoconv 

The Metro PDF Merger uses [unoconv](https://github.com/dagwieers/unoconv), a CLI tool that performs document conversions; it reads any document type supported by LibreOffice.

##### Mac OS

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
# Do the following as the datamade user:
mkdir unoconv
cd unoconv
wget https://raw.githubusercontent.com/dagwieers/unoconv/master/unoconv
# Assign read, write, and execute permissions to unoconv source file
chmod 755 unoconv
# Make a symbolic link
sudo ln -s /home/datamade/unoconv/unoconv /usr/bin/unoconv
```

In the unoconv file, specify the location of Python:

```
#!/usr/bin/python3
```

##### 2. Redis

This app also uses [Redis](https://redis.io/), a data store that brokers messages between a sender and receiver. You need to [download Redis](https://redis.io/download), first. Then, you can put Redis to "work." In a new terminal tab, run:

```bash
redis-server
```

#### Install app dependencies and configure the app

Create a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

```bash
mkvirtualenv metro-merger
```

Install app dependencies:

```bash
pip install -r requirements.txt
```

Copy the config.py.example file.

```bash
cp config.py.example config.py
```

It has almost everything you need to run the app, with two exceptions.

##### 1. Sentry

If you want to configure the
app with Sentry, then find your DSN Client key and assign its value to SENTRY_DSN.

##### 2. S3

We store the merged PDF packets in an AWS S3 bucket. You may want to test this tool locally, but still send PDFs to AWS. To so, you need to have the right credentials, and you need to tell your app to send PDFs to our test S3 bucket.

* Go to [https://console.aws.amazon.com/iam/](https://console.aws.amazon.com/iam/), and select your user name.
* Select "Create Access Key," and download the relevant `.csv` file.
* At the root of your local machine (e.g., `~`), add an AWS directory and create two files:

```
mkdir ~/.aws
touch ~/.aws/credentials
touch ~/.aws/config
```

* Then, add the following:

```
# ~/.aws/credentials
[default]
aws_access_key_id = ****
aws_secret_access_key = ****

# ~/.aws/config
[default]
region = us-east-1
```

Credentials set!

#### Run the app

Run the app locally:

```bash
python app.py
```

And in another tab, run:

```bash
python run_worker.py
```

This module calls `queue_daemon`, a while loop that processes entries in the Redis queue, or in other words, runs the `makePacket` function, which merges and saves the newly consolidated PDFs.

## Team

* Regina Compton, DataMade - developer
* Eric van Zanten, DataMade - developer

## Errors / Bugs

If something is not behaving intuitively, it is a bug, and should be reported.
Report it here: https://github.com/datamade/nyc-councilmatic/issues

## Note on Patches/Pull Requests

* Fork the project.
* Make your feature addition or bug fix.
* Commit, do not mess with rakefile, version, or history.
* Send a pull request. Bonus points for topic branches.

## Copyright

Copyright (c) 2021 DataMade. Released under the [MIT License](https://github.com/datamade/nyc-councilmatic/blob/master/LICENSE).
