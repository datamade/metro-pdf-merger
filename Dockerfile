FROM python:3.4

LABEL maintainer "DataMade <info@datamade.us>"

RUN apt-get update && \
    apt-get install -y libreoffice

# Inside the container, create an app directory and switch into it
RUN mkdir /app
WORKDIR /app

# Copy the requirements file into the app directory, and install them. Copy
# only the requirements file, so Docker can cache this build step.
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN which unoconv || ( \
    UNOCONV_PATH=/unoconv && \
    wget -P $UNOCONV_PATH https://raw.githubusercontent.com/dagwieers/unoconv/master/unoconv && \
    chmod 755 $UNOCONV_PATH/unoconv && \
    sed -i 's;#!/usr/bin/env python;#!/usr/bin/python3;' $UNOCONV_PATH/unoconv && \
    ln -s $UNOCONV_PATH/unoconv /usr/bin/unoconv \
)

# Copy the contents of the current host directory (i.e., our app code) into
# the container.
COPY . /app
