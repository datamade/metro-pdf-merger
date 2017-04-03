# Metro PDF Merger

A flask app that listens for requests from [LA Metro Councilmatic](https://github.com/datamade/la-metro-councilmatic). The app consolidates PDFs for Board Reports and Events, stores the merged documents, and provides a route that returns PDFs.

## Set up

Create a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

```bash
mkvirtualenv metro-merger
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The Metro PDF Merger uses [unoconv](https://github.com/dagwieers/unoconv), a CLI tool that performs document conversions; it reads any document type supported by LibreOffice.

Install unoconv with brew:

```bash
brew install unoconv
```

`unoconv` works only with LibreOffice versions 3.6.0.1 - 4.3.x. [Get the DMG file for version 4.3.](https://downloadarchive.documentfoundation.org/libreoffice/old/4.3.7.2/mac/x86_64/LibreOffice_4.3.7.2_MacOS_x86-64.dmg) Or go [visit here](https://downloadarchive.documentfoundation.org/libreoffice/old/4.3.7.2/mac/x86_64/).

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






