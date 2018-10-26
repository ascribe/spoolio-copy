# -*- coding: utf-8 -*-
import urllib

from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import activate, ugettext as _

from inlinestyler.utils import inline_css

from . import messages
from .utils import get_signup_or_login_link

from util.celery import app
from util.util import send_mail, insert_or_change_subdomain
from whitelabel.models import WhitelabelSettings


@app.task
def send_ascribe_email(*args, **kwargs):
    # TODO The language is activated for translation, no matter what, because
    # errors have been noticed in development, in which when the language is
    # not activated translation "mechanics" will cause an error. This todo note
    # is being written here because the problem is not fully understood, and it
    # is therefore not ruled out that the observed problem could be handled
    # differently.
    language = kwargs.pop('lang', 'en')
    # make sure the language is something, else set to English
    if not language:
        language = 'en'
    activate(language)
    msg_cls = kwargs.pop('msg_cls', messages.AscribeEmailMessage)
    if isinstance(msg_cls, basestring):
        msg_cls = getattr(messages, msg_cls)
    msg_cls(*args, **kwargs).send()


############################################
# Loan
############################################
@app.task
def emailOwnerOnDenyLoanPiece(loanee, piece, subdomain):
    if settings.EMAIL_ENABLED:
        email_to = piece.user_registered.email
        subject = "Loan Request Rejected - " + piece.title
        s = []
        s += ["Hello,"] + [""]
        s += ["The following loan requests have been denied."] + []
        s += ["Ascribe user %s denied loaning ""%s""." %
              (loanee.username, piece.title)] + [""]
        s += [" -%s" % settings.EMAIL_SIGNATURE]
        text_content = "\n".join(s)

        redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND, subdomain)
        d = Context({'owner': piece.user_registered.username, 'piece': piece,
                     'loanee': loanee.username, 'email': email_to,
                     'redirect_url': redirect_url})
        htmly = get_template('emails/owner_ondenyloan.html')
        html_content = htmly.render(d)

        send_mail(subject, text_content, email_to, html_message=html_content)


############################################
# PRIZE
############################################
@app.task
def email_submit_prize(receiver, piece, subdomain):
    subject = u'Thanks for submitting to '
    template_path = 'emails/'
    text_content = u"\n".join([""] + [" -%s" % settings.EMAIL_SIGNATURE])
    redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND, subdomain)
    if subdomain == 'sluice':
        subject += u'Sluice_screens ↄc'
        template_path += 'sluice/email_submit.html'
        d = Context({
            'receiver': receiver,
            'editions': [piece],
            'redirect_url': redirect_url,
            'subject': subject,
        })
        htmly = get_template(template_path)
        html_content = htmly.render(d)
        html_message = inline_css(html_content)
    elif subdomain == 'portfolioreview':
        subject += u'Portfolio Review 2016'
        template_path += 'portfolioreview/email_submit.html'
        d = Context({
            'receiver': receiver,
            'piece': piece,
            'subject': subject,
            'signup_or_login_link': get_signup_or_login_link(receiver.email, subdomain)
        })
        htmly = get_template(template_path)
        html_content = htmly.render(d)
        html_message = inline_css(html_content)
    send_mail(subject, text_content, receiver.email, html_message=html_message)


############################################
# Prize judge email endpoints
############################################
@app.task
def email_signup_judge(user, token, subdomain):
    wl_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    prize_display_name = wl_settings.name
    subject = u'Invitation to judge for %s.' % prize_display_name
    redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND + 'signup', subdomain)

    email_safe = urllib.quote_plus(user.email.encode("utf-8"))

    text_content = u"We would like to invite you to be a jury member for %s\n" % prize_display_name
    text_content += _('Use this link to activate your account:\n')
    text_content += u' %s?token=%s&email=%s&subdomain=%s \n\n' % (redirect_url, token, email_safe, subdomain)
    text_content += _('Thank you and enjoy, \n')
    email_signature = settings.EMAIL_SIGNATURE % {'ascribe_team':
                                                  _('The ascribe Team')}
    text_content += '\n -%s' % email_signature
    context = Context({'username': user.username,
                       'email': user.email,
                       'email_safe': email_safe,
                       'token': token,
                       'subdomain': subdomain,
                       'host': redirect_url})
    if subdomain == 'sluice':
        htmly = get_template('emails/sluice/email_signup_judge.html')
    elif subdomain == 'portfolioreview':
        htmly = get_template('emails/portfolioreview/email_signup_judge.html')
    else:
        htmly = get_template('emails/email_signup_judge.html')

    html_content = inline_css(htmly.render(context))
    send_mail(subject, text_content, user.email, html_message=html_content)


@app.task
def email_invite_judge(user, subdomain):
    wl_settings = WhitelabelSettings.objects.get(subdomain=subdomain)
    prize_display_name = wl_settings.name
    subject = u'Invitation to judge for %s' % prize_display_name
    redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND + 'login', subdomain)

    email_safe = urllib.quote_plus(user.email.encode("utf-8"))

    text_content = u"We would like to invite you to be a jury member for %s.\n" % prize_display_name
    text_content += u"Use this link to log in:\n"
    text_content += u' %s?&email=%s&subdomain=%s \n\n' % (redirect_url, email_safe, subdomain)
    text_content += _('Thank you and enjoy, \n')
    email_signature = settings.EMAIL_SIGNATURE % {'ascribe_team': _('The ascribe Team')}
    text_content += '\n -%s' % email_signature

    context = Context({'username': user.username,
                       'email': user.email,
                       'email_safe': email_safe,
                       'subdomain': subdomain,
                       'host': redirect_url})
    if subdomain == 'sluice':
        htmly = get_template('emails/sluice/email_invite_judge.html')
    elif subdomain == 'portfolioreview':
        htmly = get_template('emails/portfolioreview/email_invite_judge.html')
    html_content = inline_css(htmly.render(context))
    send_mail(subject, text_content, user.email, html_message=html_content)


############################################
# Contract
############################################
@app.task
def email_contract_agreement_decision(contract_agreement, accepted=True):
    issuer = contract_agreement.contract.issuer
    email_to = issuer.email
    issuer_username = issuer.username
    signee = contract_agreement.signee

    if accepted:
        html_template_path = 'emails/contract_agreement_accepted.html'
        subject = 'Contract accepted'
        TEMPLATE = u"""Hi {issuer_username},
        We are glad to inform you that {signee} accepted the contract."""
    else:
        html_template_path = 'emails/contract_agreement_rejected.html'
        subject = 'Contract declined'
        TEMPLATE = u"""Hi {issuer_username},
        We are sorry to inform you that {signee} rejected the contract."""

    email_text = TEMPLATE.format(signee=signee, issuer_username=issuer_username)
    context = Context({
        'issuer': issuer_username.encode('ascii'),
        'signee': signee.email.encode('ascii'),
        'contract_url': contract_agreement.contract.blob.url_safe,
        'contract_name': contract_agreement.contract.name,
        'appendix_default': contract_agreement.appendix.get('default', None) if contract_agreement.appendix else None,
    })
    email_html = get_template(html_template_path).render(context)
    send_mail(subject, email_text, email_to, email_html)


############################################
# Ikonotv
############################################
@app.task
def email_send_contract_agreement(user, subdomain):
    if subdomain == 'ikonotv':
        html_template_path = 'emails/ikonotv/ikonotv_contract_agreement.html'
        subject = u'IkonoTV contract agreement'
        issuer = 'IkonoTV'
    else:
        raise NotImplementedError
    email_to = user.email
    email_safe = urllib.quote_plus(email_to.encode('ascii'))
    username = user.username
    link = get_signup_or_login_link(email_to, subdomain)
    TEMPLATE = u"""Hi {username},
    {issuer} would like you to review the contract agreement, please click on the link below:
    {link}

    Thank you and hope to hear from you,
    -{issuer}"""
    email_text = TEMPLATE.format(username=username, link=link, issuer=issuer)
    context = Context({
        'username': username.encode('ascii'),
        'email': email_to.encode('ascii'),
        'email_safe': email_safe.encode('ascii'),
        'link': link.encode('ascii'),
    })
    email_html = get_template(html_template_path).render(context)
    send_mail(subject, email_text, email_to, email_html)
