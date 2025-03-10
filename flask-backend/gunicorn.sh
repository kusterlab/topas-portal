#!/bin/sh
gunicorn app:app -w 4 --threads 10 -b  0.0.0.0:3832 --timeout 4000
