from celery import Celery
from urllib.parse import quote

password = "$2a$12$sDztpY8S1HX0NhnNNDcctezevP95TjwYJMkjHsA9anKzL7u92vUV2"
safe_password = quote(password)
# Create a Celery app
celery_app = Celery(
    'tasks', 
    broker=f'redis://:{safe_password}@157.173.199.49:6379/0',
    backend=f'redis://:{safe_password}@157.173.199.49:6379/0'
)

# Configure Celery (optional)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
