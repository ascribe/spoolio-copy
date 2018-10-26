.. _docker_setup:

Working with Docker
===================
Simple help on how to work with docker for development.


tl;dr
-----
For Ubuntu. See documentation below for other systems.

Install `docker engine <https://docs.docker.com/installation/ubuntulinux/>`_:
 
.. code-block:: bash
    
    $ sudo apt-get update
    $ sudo apt-get install docker-engine
    $ sudo docker run hello-world   # this should work

Install `docker-compose <https://docs.docker.com/compose/install/>`_:

.. code-block:: bash

    $ curl -L https://github.com/docker/compose/releases/download/VERSION_NUM/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
    $ chmod +x /usr/local/bin/docker-compose

Clone spool and start the services:

.. code-block:: bash

    $ git clone git@github.com:ascribe/spoolio.git
    $ cd spool
    $ docker-compose build
    $ docker-compose run --rm spool sh deploy.local.sh
    $ docker-compose up

If everything went well, you should now be running:

* ``spool`` - web server - django/rest-framework based api
* ``db`` - postgresql database
* ``nginx`` - proxy server
* ``rabbitmq`` - amqp broker for celery tasks
* ``celeryworker`` - worker process for celery tasks
* ``celerybeat`` - beat process for periodic tasks


Scope
-----
Have an environment that allows one to work on the code of spool, and test it.
More precisely, this means that one can run the postgres database, run
migrations, load fixtures, run the shell, run tests, and various other django
commands, via ``django-admin`` or ``python manage.py``.

Moreover, the source code is mounted in the containers from the developer's
host machine so that running containers will run the modified code. 

On the roadmap, but not yet ready
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Being able to run an integrated environment involving both the frontend and
backend, i.e.: onion & spool.


.. _prerequisites:

Prerequisites
-------------

* `Docker Engine aka Docker <https://docs.docker.com/installation/ubuntulinux/>`_
* `Docker Compose <https://docs.docker.com/compose/install/>`_
* `Docker Machine <https://docs.docker.com/machine/install-machine/>`_ (*optional*)  

Please refer to the hyperlinked documentation for setup instructions.


Quick start
-----------
If you're not using ``docker-machine`` just go directly to the
:ref:`docker_compose` section.

docker-machine
^^^^^^^^^^^^^^
Create a local virtual machine, which will act as the "docker host".
That is, it will be the machine on which the containers run.

.. code-block:: bash

    $ docker-machine create -d virtualbox spoolbox

Point your docker client to the newly created machine:

.. code-block:: bash

    $ eval $(docker-machine env spoolbox)


.. _docker_compose:

docker-compose
^^^^^^^^^^^^^^
Build the spool and database services. The first time, it may take a few
(~10-15) minutes.

.. code-block:: bash

    $ docker-compose build

Now, running ``docker-compuse up`` creates and starts all the container-based
services (i.e. ``spool``, ``db``, etc). Because the database service takes longer
to be created and started, the spool service will fail, when running
``docker-compose up`` for the first time. There's an
`open issue <https://github.com/docker/compose/issues/374>`_ regarding this
problem. In the meantime, you need to first create and start the database
service. You can do so in various ways.

Create and start the database service first, stop it, and start the spool
service:

.. code-block:: bash

    $ docker-compose up db
    # crtl-c
    $ docker-compose up spool

In one line:

.. code-block:: bash

    $ docker-compose up -d db && docker-compose stop db && docker-compose up spool

Simpler form:

.. code-block:: bash

    $ docker-compose up -d db && docker-compose up spool

At the moment of this writing the command executed when running the spool
container is: `uwsgi --socket :8000 --module web.wsgi`` (See the file
``docker-compose.yml``)

You can overwrite this behavior. For instance:

.. code-block:: bash

    $ docker-compose run --rm spool python manage.py test --nomigrations bitcoin

would run the tests for the ``bitcoin`` app.


Setting up the database "mysite_db"
"""""""""""""""""""""""""""""""""""

.. code-block:: bash

    $ docker-compose run --rm spool python manage.py migrate
    $ docker-compose run --rm spool python manage.py loaddata ownership/fixtures/licenses.json
    $ docker-compose run --rm spool python manage.py migrate

You can now start a shell:

.. code-block:: bash

    $ docker-compose run --rm spool python manage.py shell

.. code-block:: python

    In [1]: from users.models import User

    In [2]: User.objects.all()
    Out[2]: [<User: admin>]

    In [3]: User.objects.get()
    Out[3]: <User: admin>

    In [4]: User.objects.get().check_password('admin')
    Out[4]: True


Running the server
""""""""""""""""""
Although the information therein may be of some use, it should be noted that
the ``docker-compose.yml`` now runs the web server by default, via nginx. The
instructions that follow are concerned with running the web server via the
``manage.py`` command.

To run the server:

.. code-block:: bash

    $ docker-compose run --rm --service-ports spool python manage.py runserver 0.0.0.0:8000


You should be able to access the ascribe landing page in your browser at
``<docker_host_ip>:<mapped_port``.

The value of ``docker_host_ip`` depends on how you run docker. if you are running
on linux, then it is probably simply ``localhost``. If you are using docker-machine, then

.. code-block:: bash

    $ docker-machine ip spoolbox

will give you the ip.

If you are using boot2docker:

.. code-block:: bash

    $ boot2docker ip

As for the mapped port, you may get it by running:

.. code-block:: bash

    $ docker-compose ps
        Name                     Command               State            Ports
    ------------------------------------------------------------------------------------
    spool_db_1          /docker-entrypoint.sh postgres   Up      5432/tcp
    spool_spool_run_1   python manage.py runserver ...   Up      0.0.0.0:32793->8000/tcp

If you look under the ``Ports`` column, for the service ``spool_spool_run_1``,
the mapping is shown to be:

.. code-block:: bash

    0.0.0.0:32793->8000/tcp

which means that the private port ``8000`` is mapped to ``32793``.

One reason for not simply pinning the port to ``8000``, is that we can run
multiple containers at the same time.

Example:

Let's start the server 3 times, in silent mode. That is, let's launch
three containers running the server.

.. code-block:: bash

    $ docker-compose run -d --rm --service-ports spool python manage.py runserver 0.0.0.0:8000
    $ docker-compose run -d --rm --service-ports spool python manage.py runserver 0.0.0.0:8000
    $ docker-compose run -d --rm --service-ports spool python manage.py runserver 0.0.0.0:8000

Then if you list the containers:

.. code-block:: bash

    $ docker-compose ps

         Name                     Command               State            Ports
    ------------------------------------------------------------------------------------
    spool_db_1          /docker-entrypoint.sh postgres   Up      5432/tcp
    spool_spool_run_1   python manage.py runserver ...   Up      0.0.0.0:32794->8000/tcp
    spool_spool_run_2   python manage.py runserver ...   Up      0.0.0.0:32795->8000/tcp
    spool_spool_run_3   python manage.py runserver ...   Up      0.0.0.0:32796->8000/tcp

you can see three servers running. Each one of them can be accessed
simultaneously in a browser, at their respective port.

To stop the containers:

.. code-block:: bash

    $ docker stop spool_spool_run_1 spool_spool_run_2 spool_spool_run_3


.. _dbbackup_docker:

Gettting a Database Backup into a Container
-------------------------------------------

.. code-block:: bash
    
    $ mkdir -p ~/dbdumps
   
If somehow the directory has been created by ``docker``, chances are that ``user:group`` are set ``root:root``. Set the
file permission:

.. code-block:: bash
    
    $ sudo chown -R `id -un`:`id -gn` ~/dbdumps
    
Get the backup:
    
    $ URL=`heroku pg:backups public-url --remote live`
    $ wget -O ~/dbdumps/db.sql $URL
    
Make sure the db container is running:

.. code-block:: bash
    
    $ docker-compose ps
       Name                     Command                 State       Ports   
    ---------------------------------------------------------------------------
    spoolio_db_1         /docker-entrypoint.sh postgres   Up           5432/tcp 

If it is not running:

.. code-block:: bash
    
    $ docker-compose up -d db

Enter the container, as user ``postgres``: 

.. code-block:: bash

    $ docker exec -it -u postgres spoolio_db_1 bash

Drop the db

.. code-block:: bash

    postgres@bdf8ad9b6b48:/$ dropdb mysite_db

.. code-block:: bash

    postgres@bdf8ad9b6b48:/$ createdb mysite_db                                                                                
    
.. code-block:: bash

    postgres@bdf8ad9b6b48:/$  pg_restore -v -c --no-acl -O -h localhost -U mysite_user -d mysite_db /tmp/dbdumps/db.sql

If you wonder what the various flags (e.g.: ``-c``) stand for, run ``pg_restore --help``!


Useful commands
---------------
Command help:

.. code-block:: bash

    $ docker-compose --help

Listing containers:

.. code-block:: bash

    $ docker-compose ps

Stopping all services:

.. code-block:: bash

    $ docker-compose stop

Stopping one service:

.. code-block:: bash

    $ docker-compose spool

Removing stopped service containers:

.. code-block:: bash

    $ docker-compose rm

You can force this command if you don't want to be prompted every time.

.. code-block:: bash

    $ docker-compose rm -f

Removing a stopped service container:

.. code-block:: bash

    $ docker-compose rm spool


Resources
---------

* `Docker Docs <https://docs.docker.com/>`_
* `Overview of Docker Compose <https://docs.docker.com/compose/>`_
* `Quickstart Guide: Compose and Django <https://docs.docker.com/compose/django/>`_
* `Compose CLI reference <https://docs.docker.com/compose/cli/>`_
* `docker-compose.yml reference <https://docs.docker.com/compose/yml/>`_
* `Managing data in containers <https://docs.docker.com/userguide/dockervolumes/>`_
* `dockerizing-django <https://github.com/realpython/dockerizing-django>`_
