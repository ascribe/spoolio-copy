***************************
Bitcoin Management Commands
***************************


Check wallet status

.. code-block:: bash

    $ heroku run python manage.py wallet_status --remote live

Refill federation wallet

It is better not to create transactions with more then 200 outputs

.. code-block:: bash

    $ heroku run python manage.py refill <num_fees> <num_tokens> --remote live
    $ heroky run python manage.py refill 50 150 --remote live