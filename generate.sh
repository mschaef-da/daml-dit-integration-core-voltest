#!/bin/sh

for ii in $(seq 0 99);
do
    cat dabl-meta.template.yaml | sed s/XYZZY/${ii}/ > dabl-meta.yaml

    ddit clean
    ddit build
    ddit release
done
