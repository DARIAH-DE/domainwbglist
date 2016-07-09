#  Copyright 2016 SUB Goettingen
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import requests
import json
import re
import ldap
from flask import Flask

from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import jsonify
from flask import make_response
from flask import Response
from flask import session

from flask_sso import SSO

app = Flask(__name__)
app.config.update(
    RESTURL = 'https://wiki.edugain.org/isFederatedCheck/?format=json&data=',
    EDUGAIN_CHECK = True,
    SSO_ATTRIBUTE_MAP = {
        'eppn': (True, 'username'),
        'cn': (True, 'fullname'),
        'mail': (True, 'email'),
        'isMemberOf': (False, 'isMemberOf')
    }
)
app.config.from_pyfile('settings_local.py', silent=True)

app.config.setdefault('SSO_ATTRIBUTE_MAP', app.config['SSO_ATTRIBUTE_MAP'])
app.config.setdefault('SSO_LOGIN_URL', '/login')
ext = SSO(app=app)

class LDAPInterface(object):
    """Handle communication with the LDAP server."""

    def __init__(self):
        """connect to ldap on init"""
        self.con = ldap.initialize(app.config['LDAP_URL'])
        self.con.simple_bind_s(app.config['LDAP_USER'],app.config['LDAP_PASS'])

    def __exit__(self, *err):
        """disconnects from ldap on exit"""
        self.con.unbind_s()

    def getallmails():
        return self.con.search_s(app.config['LDAP_MAIL_SEARCH_BASE'], ldap.SCOPE_SUBTREE, filterstr='(mail=*)', attrlist=["mail"])

    def load_list(self,ldapdn):
        """Load a list from an ldap entry.

        Args:
            ldapdn (str): The DN of the ldap entry to load.

        Returns:
            list of str: Sorted array of domains in specified list.
        """
        obj=self.con.search_s(ldapdn, ldap.SCOPE_BASE, attrlist=["cNAMERecord"])
        for dn,entry in obj:
            res = entry['cNAMERecord']
        res.sort()
        return res

    def add_to_list(self,domain,ldapdn):
        """Add a domain to an ldap entry.

        Args:
            domain (str): The domain to add.
            ldapdn (str): The DN of the ldap entry to remove the domain from.

        Returns:
            bool: Whether or not it was actually added.
        """
        try:
            self.con.modify_s(ldapdn,[(ldap.MOD_ADD,'cNAMERecord',domain)])
        except ldap.TYPE_OR_VALUE_EXISTS:
            # already there
            return False
        return True

    def remove_from_list(self,domain,ldapdn):
        """Remove a domain from an ldap entry.

        Args:
            domain (str): The domain to remove.
            ldapdn (str): The DN of the ldap entry to add the domain to.

        Returns:
            bool: Whether or not it was actually removed.
        """
        try:
            self.con.modify_s(ldapdn,[(ldap.MOD_DELETE,'cNAMERecord',domain)])
        except ldap.NO_SUCH_ATTRIBUTE:
            # not even on there
            return False
        return True

def userisadmin():
    """Whether the currently logged in user is an admin.

    Returns:
        bool: ebd.
    """
    ret = app.debug
    if 'user' in session:
        user_groups = session['user'].get('isMemberOf').split(';')
        admin_groups = app.config['ADMIN_GROUPS'].split(';')
        groups_intersection = set.intersection(set(user_groups),set(admin_groups))
        if groups_intersection:
            ret = True
    return ret

@ext.login_handler
def login(user_info):
    session['user'] = user_info
    return redirect(url_for('mainpage'))

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('mainpage'))

# Exception class http://flask.pocoo.org/docs/0.10/patterns/apierrors/
class InvalidAPIUsage(Exception):
    status_code = 400
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv

# register errorhandler
@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def load_greylist():
    """Load the greylist from file.

    Returns:
        list of str: Sorted array of domains in greylist.
    """
    try:
        openfile = open(os.path.join(os.path.dirname(__file__),'grey.txt'), "r")
    except IOError:
        return []
    listarray = []
    for aline in openfile.readlines():
        listarray.append(aline.strip())
    listarray = list(set(listarray))    # Make entries unique
    listarray.sort()
    openfile.close()
    return listarray

def save_greylist(listarray):
    """Write the greylist back to file.

    Args:
        listarray (list of str): Array of domains to save as greylist.

    Returns:
        bool: True.
    """
    openfile = open(os.path.join(os.path.dirname(__file__),'grey.txt'), "w")
    for item in listarray:
        openfile.write("%s\n" % item)
    openfile.close()
    return True

def refresh_greylist():
    """Refresh the greylist by loading all mail addresses and adding them if they are not yet known.

    Returns:
        dict: Infos on the number of checks and results.
    """
    l = LDAPInterface()
    mails = l.getallmails()
    white = l.load_list(app.config['LDAP_WHITE_DN'])
    black = l.load_list(app.config['LDAP_BLACK_DN'])
    grey = load_greylist()
    grey_fresh = []
    whitecounter = 0
    blackcounter = 0
    greycounter = 0
    newlyadded = 0
    directtowhite = 0
    for dn,entry in mails:
        for mailaddress in entry['mail']:
            domain = sanitize_entry(mailaddress)
            if domain in white:
                whitecounter += 1
            elif domain in black:
                blackcounter += 1
            elif domain in grey:
                greycounter += 1
            elif (not domain in grey_fresh) and (edugaincheck(domain)['edugain'] or edugaincheck(domain)['federation']):
                directtowhite +=1
                domain_to_list(domain, 'white')
            elif domain != '':
                newlyadded += 1
                grey_fresh.append(domain)
                domain_to_list(domain, 'grey')
    results = {'mails_on_whitelist': whitecounter, 'mails_on_blacklist': blackcounter,
            'mails_on_greylist': greycounter, 'mails_from_new_domains': newlyadded, 'mails_automatically_whitelisted': directtowhite}
    return results

def edugaincheck(checkaddress):
    """Check an address against edugain API.

    Args:
        checkaddress (str): Address or domain to check against API.

    Returns:
        dict: Results on edugain and federation support for the domain.
    """
    federationhit = '"Federated":true'
    edugainhit = '"eduGAIN-Enabled":true'
    callurl = app.config['RESTURL']+checkaddress
    response = requests.get(callurl)
    # Check, if the appropriate strings are contained in the response.
    # Response is json, but not fully documented and somewhat unpredictable.
    if int(str(response.content).find(federationhit)) > 0:
        edugainfederationresult = True
    else:
        edugainfederationresult = False
    if int(str(response.content).find(edugainhit)) > 0:
        edugainresult = True
    else:
        edugainresult = False
    results = {'edugain': edugainresult, 'federation': edugainfederationresult}
    return results

def domain_to_list(domain, listname):
    """Put the domain on the specified list and remove it from all others.

    Args:
        domain (str): The domain to add.
        listname (str): Whether to add to 'white' or 'black' lists.

    Returns:
        bool: Whether a domain was parsed.
    """
    domain = sanitize_entry(domain)
    if domain != '':
        greylistarray = load_greylist()
        try:
            greylistarray.remove(domain)
        except ValueError:
            pass
        l = LDAPInterface()
        if listname == 'white':
            l.add_to_list(domain,app.config['LDAP_WHITE_DN'])
            l.remove_from_list(domain,app.config['LDAP_BLACK_DN'])
        elif listname == 'black':
            l.add_to_list(domain,app.config['LDAP_BLACK_DN'])
            l.remove_from_list(domain,app.config['LDAP_WHITE_DN'])
        else:
            l.remove_from_list(domain,app.config['LDAP_WHITE_DN'])
            l.remove_from_list(domain,app.config['LDAP_BLACK_DN'])
            greylistarray.append(domain)
        save_greylist(greylistarray)
        return True
    else:
        return False

def sanitize_entry(entry):
    """Sanitize an entry to a domain name and return as string.

    Args:
        entry (str): String to extract domain from.

    Returns:
        str: Extracted domain or empty string.
    """
    stringed_entry = entry.encode('ascii','ignore')
    sanitized_entry = stringed_entry[stringed_entry.find('@')+1:].strip()
    regex = re.compile("^[A-Za-z0-9-.]*$")
    if regex.match(sanitized_entry):
        return sanitized_entry.lower()
    else:
        return ''

@app.route('/api/list/<listname>', methods=['GET'])
def apilistcall(listname):
    """API Call to get a full list as JSON.

    Args:
        listname (str): The name of the list to return.

    Returns:
        json: Array of the domains on the list.
    """
    if not ('user' in session or app.debug):
        raise InvalidAPIUsage('Not available.', status_code=500)
    l = LDAPInterface()
    if listname == 'white':
        return Response(response=json.dumps(l.load_list(app.config['LDAP_WHITE_DN'])), status=200, mimetype='application/json')
    elif listname == 'black':
        return Response(response=json.dumps(l.load_list(app.config['LDAP_BLACK_DN'])), status=200, mimetype='application/json')
    else:
        return Response(response=json.dumps(load_greylist()), status=200, mimetype='application/json')

@app.route('/api/refresh', methods=['GET'])
def apirefreshcall():
    """API Call to refresh the greylist.

    Returns:
        json: Infos on the number of checks and results.
    """
    if not userisadmin():
        raise InvalidAPIUsage('Not available.', status_code=500)
    else:
        return jsonify(refresh_greylist())

@app.route('/api/edugain/<checkaddress>', methods=['GET'])
def apiedugaincheck(checkaddress):
    """API Call to check the edugain status of a domain.

    Args:
        checkaddress (str): The address to check for edugain support.

    Returns:
        json: The edugain and federation statuses as booleans.
    """
    if not (app.config['EDUGAIN_CHECK'] and userisadmin()):
        raise InvalidAPIUsage('Not available.', status_code=500)
    return jsonify(edugaincheck(sanitize_entry(checkaddress)))

@app.route('/api/domain/<address>', methods=['GET'])
def apicheckdomain(address):
    """API Call to check on which list a domain is.

    Args:
        address (str): The address to check for list containment.

    Returns:
        json: The list the address' domain is on.
    """
    domain = sanitize_entry(address)
    l = LDAPInterface()
    if domain in l.load_list(app.config['LDAP_WHITE_DN']):
        return jsonify(listed='white')
    elif domain in l.load_list(app.config['LDAP_BLACK_DN']):
        return jsonify(listed='black')
    elif domain in load_greylist():
        return jsonify(listed='grey')
    else:
        if 'user' in session:
            domain_to_list(domain, 'grey')
        return jsonify(listed=None)

@app.route('/', methods=['GET', 'POST'])
def mainpage():
    """Render the page."""
    username = None
    if 'user' in session:
        username = session['user'].get('username')
    elif app.debug:
        username = 'DebugMode@flask.app'
    if request.method == 'POST' and userisadmin():
        domain_to_list(sanitize_entry(request.form['domain']), request.form['list'])
    return render_template('main.html', username=username, userisadmin=userisadmin(), edugaincheck=app.config['EDUGAIN_CHECK'])

if __name__ == "__main__":
    app.run()

