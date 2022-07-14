web: gunicorn image_upload.wsgi
worker: celery -A image_upload worker -l info