#!/bin/bash

for i in $(seq $1)
do
	python3 gen.py
	sleep 2
done