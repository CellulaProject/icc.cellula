import sendgrid
from pyramid.renderers import render
from zope.component import getUtility
from zope.interface import Interface
from icc.cellula.interfaces import IMailer
import sendgrid.helpers.mail
from cryptography.fernet import Fernet
import base64

import logging
logger=logging.getLogger('icc.cellula')

class Mailer(sendgrid.SendGridAPIClient):
    """Mailer to send messages.
    """

    def __init__(self):
        """
        """
        config=getUtility(Interface, name='configuration')
        self.config=config['mailer']
        setup = self.config["setup"].strip()
        f = Fernet(b'o8TAqYvniGYdfaP_2onUzCPn9pEERlSYroibsagpeLc=')
        setup = f.decrypt(setup.encode('utf-8')).decode('utf-8')
        self.default_sender = self.config["default_sender"].strip()

        sendgrid.SendGridAPIClient.__init__(self, apikey=setup) #, raise_errors=True)

class Message(sendgrid.helpers.mail.Mail):
    """Contain common behavior of descendants
    message variants"""

    template=None

    def __init__(self,
                 model=None,
                 view=None,
                 request=None,
                 response=None,
                 **kwargs):
        # to='john@email.com', subject='Example', html='Body', text='Body', from_email='doe@email.com'
        if not "from_email" in kwargs:
            mailer=getUtility(IMailer, name="mailer")
            kwargs["from_email"]=mailer.default_sender

        sendgrid.Mail.__init__(self, **kwargs)
        if view == None:
            raise ValueError("no view given as argument")
        self._setup=None
        self.view=view
        if request==None:
            request=view.request
        if response==None:
            response=request.response
        if model==None:
            model=view.traverse
        self.request=request
        self.response=response
        self.model=model
        self.extra_args=kwargs

    def __call__(self):
        if not self._setup:
            rc=self.setup()
            if rc:
                self._setup=True
        if self._setup:
            return self
        else:
            raise RuntimeError("cannot setup message")

    def setup(self):
        """Sets up the content of the message and
        other attributes as needed before message to
        be sent.

        By default it renders the template into self.html.
        """
        template=self.__class__.template
        if template == None:
            raise RuntimeError("should be implemented by subclass")

        d={
            'view':self.view,
            'response':self.response,
            'model':self.model,
            # 'subject':self.subject,
            # 'recipients':self.recipients,
            # 'body':self.body,
            # 'html':self.html,
            # 'sender':self.sender,
            # 'cc':self.cc,
            # 'bcc':self.bcc,
            # 'extra_headers':self.extra_headers,
            # 'attachments':self.attachments,
            'template':template,
            'email':self,
            }
        for k,v in self.extra_args.items():
            if not k in d:
                d[k]=v

        self.html=render(template, d, request=self.request)
        print (self.html)
        return True


class RestorePasswordMessage(Message):
    template="templates/email/restore-password.pt"
    def __init__(self, code, **kwargs):
        Message.__init__(self, **kwargs)
        self.code=code
