Domain List sorter
==================


Setup
-----

Install python dependencies on Ubuntu:
````
apt-get install python-pip python-virtualenv python-dev build-essential libffi-dev python-ldap libldap2-dev libsasl2-dev libssl-dev
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

Install flask with its components from `reqirements.txt` into a virtualenv namend `venv`.

Enforce Shibboleth authentication at `/login`.

Make sure the server can write to `gray.txt`.

The following options must be set in `settings_local.py`:
````
SECRET_KEY = '*************'

LDAP_URL = 'ldap://mu.ldap.vm'
LDAP_USER = 'uid=user,dc=example,dc=com'
LDAP_PASS = '**************'

LDAP_WHITE_DN = 'dc=whitelist,dc=example,dc=com'
LDAP_BLACK_DN = 'dc=blacklist,dc=example,dc=com'

LDAP_MAIL_SEARCH_BASE = 'dc=example,dc=com'

ADMIN_GROUPS = 'admin'

SSO_ATTRIBUTE_MAP = {
    'eppn': (True, 'username'),
    'cn': (True, 'fullname'),
    'mail': (True, 'email'),
    'isMemberOf': (False, 'isMemberOf')
}
````

To enable debugging add
````
DEBUG=True
````
If you want to enable the use of eduGAIN's isFederatedCheck, add
````
EDUGAIN_CHECK=True
````

