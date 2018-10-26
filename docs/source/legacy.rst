.. _legacy:

Legacy docs
===========

**The following applies setting up on Ubuntu Linux.**
If using OSX, follow :ref:`osx_setup`

.. code-block:: bash

    # setup DB
    sudo apt-get install postgresql postgresql-contrib
    sudo apt-get install libpq-dev
    sudo apt-get install python-dev
    sudo apt-get install -y python-pip
    sudo pip install psycopg2
    sudo su - postgres
    postgres@dimi-ascribe:~$ /etc/init.d/postgresql start
    postgres@dimi-ascribe:~$ createdb mysite_db
    postgres@dimi-ascribe:~$ createuser mysite_user
    postgres@dimi-ascribe:~$ psql mysite_db -c 'create extension if not exists hstore;'
    postgres@dimi-ascribe:~$ psql template1 -c 'create extension if not exists hstore;'	# for tests
    postgres@dimi-ascribe:~$ psql
    postgres=# GRANT ALL PRIVILEGES ON DATABASE mysite_db to mysite_user;
    postgres=# ALTER USER mysite_user PASSWORD '123';
    postgres=# ALTER USER mysite_user CREATEDB;
    
    # preliminaries
    wget -qO- https://toolbelt.heroku.com/install-ubuntu.sh | sh
    sudo apt-get install rabbitmq-server
    sudo apt-get install libjpeg-dev
    sudo apt-get install zlib1g-dev
    sudo apt-get install libpng12-dev
    sudo apt-get install libxml2-dev libxslt1-dev
    sudo apt-get install mailhog	# (local mail server)
    
    # install repo
    mkdir code_ascribe
    cd code_ascribe
    git clone git@github.com:ascribe/spoolio.git
    cd spool
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements/local.txt
    git remote add live git@heroku.com:warm-hamlet-6893.git
    git remote add staging git@heroku.com:ci-ascribe.git
    git config heroku.remote staging
    heroku keys:add
    
    # set your env variables :: ask someone
    
    # set the hosts
    sudo nano /etc/hosts
    # add following entries
    127.0.0.1       localhost.com
    127.0.0.1       cc.localhost.com
    127.0.0.1       www.localhost.com
    
    # load the fixtures
    ./python manage.py loaddata web/fixtures/sites.json
    ./python manage.py loaddata ownership/fixtures/licenses.json
    ./python manage.py loaddata whitelabel/fixtures/settings.json

Load data in DB
---------------

.. code-block:: bash

    # load latest dump from live db
    heroku pg:backups public-url --remote live #gives you <dump_url>
    sudo su - postgres
    postgres@dimi-ascribe:~$ wget <dump_url> #gives you <dump-file> (use quotes to surround url)
    postgres@dimi-ascribe:~$ dropdb mysite_db && createdb mysite_db && pg_restore --verbose --clean --no-acl --no-owner -h localhost -U mysite_user -d mysite_db <dump-file>
    postgres@dimi-ascribe:~$ psql mysite_db -c 'create extension hstore;'
    # migrate database
    source venv/bin/activate
    ./manage.py migrate


Run project
-----------
.. code-block:: bash

    source venv/bin/activate
    foreman start #run both web and celery worker (see Procfile)
    ./manage.py runserver #run only web
    ./manage.py shell #run IPython
    ./manage.py celery purge #remove all celery messages


Running a local mail server for development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When developing, if you need to have emails sent, you need to run
`Mailhog <https://github.com/mailhog/MailHog>`_.

.. code-block:: bash
    
    $ mailhog

Sent emails can then be seen at ``localhost:8025``

You are encouraged to consult
`Mailhog's documentation <https://github.com/mailhog/MailHog>`_ for more
information on using, and configuring Mailhog.


Requirements Files
------------------
Depending on which environment you are setting up, you can use the relevant
requirements file found under :file:`requirements/`:

* :file:`common.txt` for packages common to all environments -- *(e.g.: django)*
* :file:`heroku.txt`: for packages specific to heroku (live & staging) -- *(e.g.: newrelic)*
* :file:`travis.txt`: for packages specific to travis -- *(e.g.: coverage)*
* :file:`local.txt`: for packages specific to a local development environment -- *(e.g.: ipython)*

**IMPORTANT**: :file:`requirements.txt` is meant to be used for heroku deployments,
as heroku looks for a :file:`requirements.txt` under the project root. You do not
need to edit it though. For heorku requirements, you can edit
:file:`requirements/heroku.txt`.

Docker Setup
------------
An alternative setup using docker is documentated under :ref:`docker_setup`
