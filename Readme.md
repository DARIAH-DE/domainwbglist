Domain List sorter
==================


Setup
-----

Install python dependencies on Ubuntu:
````
apt-get install python-pip python-virtualenv
````

Start by creating a virtualenv
````
virtualenv venv
source venv/bin/activate
````
than install the dependencies
````
pip install -r requirements.txt
````

Config
------

Create the files `white.txt`, `gray.txt` and `black.txt` with domain lists of the form `@domain.tld`, one per line.

Optionally create `settings_local.py` and add 
````
DEBUG=True
````
If you want to enable eduGain checks, add
````
EDUGAIN_CHECK=True
````
