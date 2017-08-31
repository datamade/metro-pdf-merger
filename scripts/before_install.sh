#!/bin/bash
set -euo pipefail

# Make directory for project
rm -Rf /home/datamade/metro-pdf-merger
mkdir -p /home/datamade/metro-pdf-merger

cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown -R datamade.datamade . && sudo -H -u datamade blackbox_postdeploy
