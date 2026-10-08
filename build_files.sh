#!/bin/bash
echo "--- Installing Python dependencies ---"
python3 -m pip install -r requirements.txt

echo "--- Collecting static files ---"
python3 ivatio/manage.py collectstatic --noinput --clear

echo "--- Preparing static files for Vercel CDN ---"
mkdir -p staticfiles_build
cp -r ivatio/staticfiles/* staticfiles_build/
echo "--- Build completed successfully ---"
