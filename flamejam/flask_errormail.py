"""
    flask_errormail
    ~~~~~~~~~~~~~~~

    Flask extension for sending emails to administrators when 500 Internal 
    Server Errors occur.

    :copyright: (c) 2012 by Jason Wyatt Feinstein.
    :license: MIT, see LICENSE.txt for more details.
    
"""
import traceback

def mail_on_500(app, recipients):
    '''Main function for setting up Flask-ErrorMail to send e-mails when 500 
    errors occur.

    :param app: Flask Application Object
    :type app: flask.Flask
    :param recipients: List of recipient email addresses.
    :type recipients: list or tuple
    :param sender: Email address that should be listed as the sender. Defaults 
        to 'noreply@localhost'
    :type sender: string

    '''

    #importing locally, so that the dependencies are only required if 
    # mail_on_500 is used.
    from flask import request as __request
    from flask import url_for as __url_for
    from flask import redirect as __redirect
    from flask_mail import Mail as __Mail
    from flask_mail import Message as __Message

    mail = __Mail(app)

    # create a closure to track the recipients
    def email_exception(exception):
        '''Handles the exception message from Flask by sending an email to the
        recipients defined in the call to mail_on_500.

        '''

        msg = __Message("[Flask|ErrorMail] Exception Detected: %s" % exception.message,
                        recipients=recipients)
        msg_contents = [
            'Traceback:',
            '='*80,
            traceback.format_exc(),
        ]
        msg_contents.append('\n')
        msg_contents.append('Request Information:')
        msg_contents.append('='*80)
        environ = __request.environ
        environkeys = sorted(environ.keys())
        for key in environkeys:
            msg_contents.append('%s: %s' % (key, environ.get(key)))

        msg.body = '\n'.join(msg_contents) + '\n'

        mail.send(msg)
        import flamejam.views.account
        return flamejam.views.account.error(exception)

    app.register_error_handler(500, email_exception)

__all__ = ['mail_on_500']
