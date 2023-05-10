import mimetypes
import os
import smtplib

from channels.consumer import SyncConsumer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

from util.logging_utils import get_request_logger


class EmailConsumer(SyncConsumer):
    """
    A consumer for sending async email messages. Contains two entry points - ``send_text`` and ``send_html`` - which create
    and send email messages given by the ``message`` dictionary, through Django Channels. The message object has
    several properties which are needed and some that are optional:

    * ``'type'``        [required]: The type of message to send, either ``send_text`` or ``send_html``
    * ``'to'``          [required]: The email address to send to
    * ``'from'``        [required]: The email address to send from
    * ``'text'``        [required]: The text content of the email, required no matter if HTML or plaintext is used
    * ``'subject'``     [required]: The subject of the email message
    * ``'html_render'`` [required]: The content for the html render, only used in ``send_html``
    * ``'reply_to'``    [optional]: The content of the reply-to field, needs to be a list or a tuple
    * ``'attachments'`` [optional]: A list of files to attach to the email. Each file is a tuple of the filename, content
      and content type. ``serialize_file`` can be used to create this tuple from a file.

    To send an asynchronous email, use ``async_to_sync(get_channel_layer().send)('email', message)``, where ``message`` is a
    message dictionary as described above. ``async_to_sync`` can be imported from ``asgiref.sync`` and ``get_channel_layer``
    can be imported from ``channels.layers``. The email consumer requires a worker to be run which can be started by the
    command ``python manage.py runworker -v 2 email``. To run the worker, ``redis`` must be installed and running. Requires a
    standard Django setup of email credentials to send emails.
    """

    def send_text(self, message):
        """
        For sending a plaintext message.

        :param message: The message dictionary
        """
        msg = self.create_message(message)
        try:
            msg.send(fail_silently=False)
        except smtplib.SMTPException as e:
            get_request_logger().exception(f"Failed sending plain text email:\n{message}", exc_info=e)

    def send_html(self, message):
        """
        For sending an HTML-rendered message.

        :param message: The message dictionary
        """
        msg = self.create_message(message)
        msg.attach_alternative(message["html_render"], "text/html")
        try:
            msg.send(fail_silently=False)
        except smtplib.SMTPException as e:
            get_request_logger().exception(f"Failed sending HTML email:\n{message}", exc_info=e)

    @staticmethod
    def create_message(message):
        """
        Creates an email message from a message dictionary.

        :param message: The message dictionary
        :return: A email message object
        """
        msg = EmailMultiAlternatives(message["subject"], message["text"], message["from"], [message["to"]])
        if "reply_to" in message:
            msg.reply_to = message["reply_to"]

        # Attach files if any
        if "attachments" in message:
            for filename, file, filetype in message["attachments"]:
                msg.attach(filename, file, filetype)

        return msg


def render_html(request, context: dict, template_name: str):
    """
    Helper for rendering HTML for use in an email. Must be done before sending the message from the thread of a request
    for correct translations.

    :param request: The request object from the view.
    :param context: The context to render the template for.
    :param template_name: The name of the template file
    :return: A string representing the HTML content
    """
    return get_template(template_name).render({
        'request': request,
        **context,
    })


def render_text(request, context: dict, template_name: str, strip=True):
    """
    Helper for rendering text for use in an email. Must be done before sending the message from the thread of a request
    for correct translations.

    :param request: The request object from the view.
    :param context: The context to render the text for if there is a template given
    :param template_name: The name of the template file
    :param strip: If ``True``, the text rendered from the template will have leading and trailing whitespace removed before being returned.
    :return: A string representing the text content
    """
    rendered_text = get_template(template_name).render({
        'request': request,
        **context,
    })
    return rendered_text.strip() if strip else rendered_text


def serialize_file(file):
    """
    Serializes the content of the file so that it can be sent to the email consumer.

    :param file: The file to serialize
    :return: A tuple of the filename, content and content type
    """
    # Django files have content_type specified, while normal Python files don't
    try:
        content_type = file.content_type
    except AttributeError:
        content_type = mimetypes.guess_type(file.name)[0]
    return os.path.basename(file.name), file.read(), content_type
