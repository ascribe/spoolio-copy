###########
Whitelabels
###########

To create a whitelabel, the command ``createwhitelabel`` can be used.

.. code-block:: bash

    python manage.py createwhitelabel \
        --user-email alice@wonderland.xyz \
        --subdomain xyz \
        --whitelabel-name wonderland

Using the short form:
        
.. code-block:: bash

    python manage.py createwhitelabel -u sylvain@ascribe.io -s xyz -n wonderland

.. note::
    
    On heroku, the ``-s`` flag will not work as it is a heroku flag for dyno sizes, so unless you find a way to indicate that the flag is for the ``manage.py`` command, you can use ``--subdomain``.

Getting help:

.. code-block:: bash

    python manage.py createwhitelabel --help
