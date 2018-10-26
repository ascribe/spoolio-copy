.. _osx_setup:

Setting up on OSX
=================

Setup system dependencies
-------------------------
Install `homebrew <http://brew.sh/>`_

Install system depdendencies:

.. code-block:: bash

    $ brew install python
    $ brew install libevent
    $ brew install postgresql
    $ brew install rabbitmq
    $ brew install libxml2 libxslt
    $ brew install heroku-toolbelt
    $ brew install mailhog
    $ sudo gem install foreman

(Optional) Launch postgresql and rabbitmq at launch:

.. code-block:: bash

    $ launchctl load ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist
    $ launchctl load ~/Library/LaunchAgents/homebrew.mxcl.rabbitmq.plist

If pip is not already available, install it:

.. code-block:: bash

    $ sudo easy_install pip

Install python utilities:

.. code-block:: bash

    $ sudo pip install virtualenv

Set up DB:

.. code-block:: bash

    $ createdb mysite_db
    $ createuser mysite_user
    $ psql -U <username> -d mysite_db
    # Create extensions and grant privileges as in 'Getting Started'

Set env variables and hosts, see `Getting Started`_

Install repo
------------
OSX's file system is by default case-sensitive, which causes problems. To get
around this, let's set up a disk image with a case sensitive file system and
use that to run spool:

* Open Disk Utility
* Make a new image using `New Image` in the top toolbar
* Select the following options:
    * Name: your choice, say `atomicsylv`
    * Size: `500MB` (don't worry about this, sparse disk images
      grow as necessary)
    * Format: `Mac OS Extended (Case-sensitive, Journaled)`
    * Encryption: your choice
    * Partitions: `Single partition - GUID Partition Map`
    * Image Format: `sparse disk image`
* Save the image somewhere, say `~/dmgs`

Let's mount this image so we can install spool on it:

.. code-block:: bash

    $ mkdir ~/volumes
    $ hdiutil attach -mountroot ~/volumes/ ~/dmgs/atomicsylv.sparseimage
    $ cd ~/volumes/atomicsylv

Install spool: see ``install repo`` section of `Getting Started`_

If installing local requirements fails, try this workaround first:

* Open requirements/common.txt
* Comment out ``gevent`` requirement
* ``$ sudo pip install gevent``
* ``$ sudo pip install -r requirements/local.txt``

Run:

.. code-block:: bash

    $ foreman start #run both web and celery worker

Load data in DB
---------------
See `Load data in DB <../README.md#load-data-in-db>`_


Running the project normally
----------------------------
See `Run project <../README.md#run-project>`_


.. _Getting Started: ../README.md#getting-started
