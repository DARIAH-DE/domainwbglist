Domain List sorter
==================


Setup
-----

Install python dependencies on Ubuntu:
```
apt-get install python-pip python-virtualenv python-dev build-essential libffi-dev python-ldap libldap2-dev libsasl2-dev libssl-dev
```

Start by creating a virtualenv
```
virtualenv venv
source venv/bin/activate
```
than install the dependencies
```
pip install -r requirements.txt
```

Config
------

Install flask with its components from `reqirements.txt` into a virtualenv namend `venv`.

Enforce Shibboleth authentication at `/login`.

Make sure the server can write to `grey.txt`.

The following options must be set in `settings_local.py`:
```python
SECRET_KEY = '*************'

LDAP_URL = 'ldap://mu.ldap.vm'
LDAP_USER = 'uid=user,dc=example,dc=com'
LDAP_PASS = '**************'

LDAP_WHITE_DN = 'dc=whitelist,dc=example,dc=com'
LDAP_BLACK_DN = 'dc=blacklist,dc=example,dc=com'

LDAP_MAIL_SEARCH_BASE = 'dc=example,dc=com'

ADMIN_GROUPS = 'admin'
```
If needed, you can overwrite `SSO_ATTRIBUTE_MAP`.

To enable debugging add
```python
DEBUG = True
```
If you want to enable the use of eduGAIN's isFederatedCheck, add
```python
EDUGAIN_CHECK = True
```

