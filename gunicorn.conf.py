import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
accesslog = "-"
errorlog = "-"
