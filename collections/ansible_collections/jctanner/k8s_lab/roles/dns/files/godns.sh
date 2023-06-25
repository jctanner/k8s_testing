#!/bin/bash

cd /opt/godns

if [ ! -d cache ]; then
    mkdir -p cache
fi

export GOCACHE=/opt/godns/cache

go run godns.go | tee -a /var/log/godns.log
