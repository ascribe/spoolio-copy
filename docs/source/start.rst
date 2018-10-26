Getting started
===============
The recommended setup is via ``docker`` and ``saltstack``. For other ways see
the :ref:`legacy` setup.


Preliminaries
-------------

.. note:: Environment Variables

    Yau need to have a file:

        * ``/opt/spool_secrets.local.env``

    containing various environment variables that the ``spool`` project relies
    on.Some of these environment variables are meant to be kept secret, and
    consequently are not included in the repository. ``saltstack`` and
    ``ionics`` make it convenient to get these environment variables.


1. Setup ``saltstack`` and the required ``state`` files by following the
   instructions under `ionics`_.
2. Ask a fellow developer for the keyring.
3. Run:

    .. code-block:: bash

        $ sudo salt-call --local -l debug state.highstate

4. Install recenet versions of `docker`_ and `docker-compose`_, if you don't
   have them already.
5. If you have not done so already, clone spoolio:

    .. code-block:: bash

        $ git clone git@github.com:ascribe/spoolio.git

7. ``cd`` into ``spoolio``
8. Under ``spoolio``, buidl the ``db`` and ``spool`` services:

    .. code-block:: bash

        $ docker-compose build db spool

9. Start the ``db`` in the background:

    .. code-block:: bash

        $ docker-compose up -d db

10. Setting up the database:

.. code-block:: bash

    $ docker-compose run --rm spool python manage.py migrate
    $ docker-compose run --rm spool python manage.py loaddata ownership/fixtures/licenses.json
    $ docker-compose run --rm spool python manage.py migrate

.. note:: If you wonder: "Why all these steps?" Yes, it could be
    simplified. See `issue #335`_


Running the tests
-----------------
To run all tests (this may take quite soem time):

.. code-block:: bash

    $ docker-compose run --rm spool py.test -v

The run the tests under an app (e.g.: ``users``):

.. code-block:: bash

    $ docker-compose run --rm spool py.test -v users


Running the interactive python + django shell
---------------------------------------------

.. code-block:: bash

    $ docker-compose run --rm spool django-admin shell

.. code-block:: python

    In [1]: from ownership.models import Ownership




.. _ionics: https://github.com/ascribe/ionics
.. _docker: https://docs.docker.com/engine/installation/
.. _docker-compose: https://docs.docker.com/compose/install/
.. _issue #335: https://github.com/ascribe/spoolio/issues/335
