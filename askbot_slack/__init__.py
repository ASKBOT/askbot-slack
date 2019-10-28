"""Posts messages to a Slack channel when new posts appear on Askbot"""
import json
import logging
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from askbot_slack import conf #register slack settings
from askbot.conf import settings as askbot_settings
from askbot.models import Post


def get_url(model_instance):
    """
    Returns the URL for the model instance.  Dependent on Site Domain name being set.
    """
    return "http://%s%s" % (Site.objects.get_current().domain, model_instance.get_absolute_url())


def post_msg(msg):
    """
    Post message to specific slack channel defined in config.
    """
    payload = {
        "text": msg,
        "username": askbot_settings.SLACK_USERNAME,
        "channel": askbot_settings.SLACK_CHANNEL
    }
    try:
        requests.post(askbot_settings.SLACK_WEBHOOK_URL, data=json.dumps(payload))
    except Exception as error: #pylint: disable=broad-except
        message = unicode(error).encode('utf-8')
        logging.critical('Cannot post to slack channel: %s', message)



@receiver(post_save, sender=Post)
def notify_post_created(sender, instance, created, raw, using, **kwargs):
    """
    Post message when Askbot Post is created.  A Post includes Questions, Comments and Answers.
    """
    if created and askbot_settings.SLACK_ENABLED:
        params = {
            'user': instance.author,
            'title': instance.thread.title,
            'url': get_url(instance)
        }
        if instance.is_question():
            msg = _('%(user)s asked "%(title)s": %(url)s') % params
        elif instance.is_answer():
            msg = _('%(user)s answered "%(title)s": %(url)s') % params
        elif instance.is_comment():
            msg = _('%(user)s commented on "%(title)s": %(url)s') % params
        post_msg(msg)


class SlackMiddleware(object):
    """
    A NO-OP middleware class to ensure our receiver gets registered early on.
    From the django 1.5 docs on signals
    'make sure that the module it's in gets imported early on so that the signal
    handling gets registered before any signals need to be sent'.
    Registering as a no-op middleware class ensures that
    this is 'imported early on'.  In later versions of django we can use the App#register method.
    """
    pass
