from app.reader.tasks import feed_indexer_coordinator
from celery import current_app as current_celery_app

from app.core.config import settings


celery_app = current_celery_app
celery_app.config_from_object(settings, namespace="CELERY")

celery_app.autodiscover_tasks()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        1 * 60, feed_indexer_coordinator.s("HIGH"), name='high_priority_tasks')
    sender.add_periodic_task(
        3 * 60, feed_indexer_coordinator.s("MEDIUM"), name='medium_priority_tasks')
    sender.add_periodic_task(
        5 * 60, feed_indexer_coordinator.s("LOW"), name='low_priority_tasks')
