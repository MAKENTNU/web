import logging
import smtplib

from channels.consumer import SyncConsumer
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import get_template

from web import settings


class EmailConsumer(SyncConsumer):

    def send_text(self, message):
        try:
            send_mail(message["subject"], message["text"], message["from"], [message["to"]], fail_silently=False)
        except smtplib.SMTPException as e:
            logging.error(
                f"Failed sending plain text email from {message['from']} to {message['to']} with exception: {e}")

    def send_html(self, message):
        msg = EmailMultiAlternatives(message["subject"], message["text"], message["from"], [message["to"]])
        msg.attach_alternative(message["html_render"], "text/html")
        try:
            msg.send(fail_silently=False)
        except smtplib.SMTPException as e:
            logging.error(f"Failed sending HTML email from {message['from']} to {message['to']} with exception: {e}")


def render_html(context, html_template_name):
    context.update({"site": settings.EMAIL_SITE_URL})
    return get_template(html_template_name).render(context)


def render_text(context, text="", text_template_name=None):
    if text_template_name is not None:
        context.update({"site": settings.EMAIL_SITE_URL})

        return get_template(text_template_name).render(context)

    # Default to text attribute
    return text
