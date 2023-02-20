#!/bin/sh
gunicorn app:app --limit-request-line 0 -w 2 --threads 2 -b 0.0.0.0:80
