import sys

from celery import Celery


app = Celery("config")

if sys.platform == "win32":
    app.conf.worker_pool = "solo"  # Windows: prefork часто падає (WinError 5 / semlock).

app.autodiscover_tasks()
