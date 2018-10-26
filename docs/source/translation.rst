***********
Translation
***********

Some simple notes on how to add support for a new language, and update an existing one.

For complete documentation on Django's translation mechanisms see 
`Translation <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/>`_



Quick reminder
==============
As an example, imagine we have the file ``quotes/leonardo.py`` with the following content:

.. code-block:: python

   quote = 'Where the spirit does not work with the hand, there is no art.'

Also assume, we are in the root of the project and ``LOCALE_PATHS`` is set to 

.. code-block:: python
   
   BASE_DIR = os.path.dirname(os.path.dirname(__file__)) 
   LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

In simpler words, ``LOCALE_PATHS`` points to a single directory, ``locale``,
under the project root. For more details on the role of ``LOCALE_PATHS``, see
`How Django discovers translations`_


How do we mark the text for translation?
----------------------------------------
Edit the python file ``quotes/leonardo.py`` like so:

.. code-block:: python

   # -*- coding: utf-8 -*-
   from django.utils.translation import ugettext as _

   msg = _('Where the spirit does not work with the hand, there is no art.')

Rwference: `Standard translation`_


How do we create or update a message file (``*.po``)?
-----------------------------------------------------
If we wish to translate the text in Italian ...

.. code-block:: bash

   django-admin makemessages -l it

Reference: `Localization: how to create language files <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#localization-how-to-create-language-files>`_


How do we add the translation? 
------------------------------
We need to edit the created ``*.po`` file.

.. code-block:: po

   #: quotes/leonardo.py:4
   msgid "Where the spirit does not work with the hand, there is no art."
   msgstr "Quando lo spirito non collabora con le mani non c'è arte."

Reference: `Message files <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#message-files>`_


How do we compile the message file? 
-----------------------------------
Create a ``*.mo`` file by running the following command:

.. code-block:: bash
   
   django-admin compilemessages

Reference: `Compiling message files <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#compiling-message-files>`_

That's it! 

*Bravissimo!*

.. _Standard translation: https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#standard-translation
.. _How Django discovers translations: https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#how-django-discovers-translations


Internalization in template code
================================

See `django's docs <shttps://docs.djangoproject.com/en/1.8/topics/i18n/translation/#internationalization-in-template-code>`_.
