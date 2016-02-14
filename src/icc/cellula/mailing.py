import pyramid_mailer.message
# import pyramid_chameleon
from pyramid.renderers import render_to_response

import logging
logger=logging.getLogger('icc.cellula')


class Message(pyramid_mailer.message.Message):
    """Contain common behavior of descendants
    message variants"""

    template=None

    def __init__(self,
                 model=None,
                 view=None,
                 request=None,
                 response=None,
                 **kwargs):
        pyramid_mailer.message.Message.__init__(self, **kwargs)
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

        self.html=render_to_response(template, d, request=self.request)
        print (self.html)
        return True


class RestorePasswordMessage(Message):
    template="templates/email/restore-password.pt"
    def __init__(self, code, **kwargs):
        Message.__init__(self, **kwargs)
        self.code=code
