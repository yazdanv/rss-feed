from app.reader.tasks import feed_distributor
from celery import current_app as current_celery_app

from app.core.config import settings


celery_app = current_celery_app
celery_app.config_from_object(settings, namespace="CELERY")

celery_app.autodiscover_tasks()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        1 * 60, feed_distributor.s(0), name='priority_0_tasks')
    sender.add_periodic_task(
        3 * 60, feed_distributor.s(1), name='priority_1_tasks')
    sender.add_periodic_task(
        5 * 60, feed_distributor.s(2), name='priority_2_tasks')
    sender.add_periodic_task(
        10 * 60, feed_distributor.s(3), name='priority_3_or_more_tasks')
