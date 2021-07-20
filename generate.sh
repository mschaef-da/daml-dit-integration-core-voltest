#!/bin/sh

for ii in $(seq 0 10);
do
    cat dabl-meta.template.yaml | sed s/XYZZY/${ii}/
done
