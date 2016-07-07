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

from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.update(
    BOOTSTRAP_SERVE_LOCAL='True',
    RESTURL='https://wiki.edugain.org/isFederatedCheck/?format=json&data=',
    LISTFILES={"white" : "white.txt", "gray":"gray.txt", "black":"black.txt"},
    EDUGAIN_CHECK=True
)
app.config.from_pyfile('settings_local.py', silent=True)
Bootstrap(app)

l = ldap.initialize(app.config['LDAP_URL'])
l.simple_bind_s(app.config['LDAP_USER'],app.config['LDAP_PASS'])

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

def load_list_from_ldap(ldapdn):
    """Load a list from an ldap entry.

    Args:
        ldapdn (str): The DN of the ldap entry to load.

    Returns:
        list of str: Sorted array of domains in specified list.
    """
    obj=l.search_s(ldapdn, ldap.SCOPE_BASE, attrlist=["cNAMERecord"])
    for dn,entry in obj:
        res = entry['cNAMERecord']
    res.sort()
    return res

def add_to_ldap_list(domain,ldapdn):
    """Add a domain to an ldap entry.

    Args:
        domain (str): The domain to add.
        ldapdn (str): The DN of the ldap entry to remove the domain from.
    """
    try:
        l.modify_s(ldapdn,[(ldap.MOD_ADD,'cNAMERecord',domain)])
    except ldap.TYPE_OR_VALUE_EXISTS:
        # already there
        pass

def remove_from_ldap_list(domain,ldapdn):
    """Remove a domain from an ldap entry.

    Args:
        domain (str): The domain to remove.
        ldapdn (str): The DN of the ldap entry to add the domain to.
    """
    try:
        l.modify_s(ldapdn,[(ldap.MOD_DELETE,'cNAMERecord',domain)])
    except ldap.NO_SUCH_ATTRIBUTE:
        # not even on there
        pass

def load_graylist():
    """Load the graylist from file.

    Returns:
        list of str: Sorted array of domains in graylist.
    """
    try:
        openfile = open(os.path.join(os.path.dirname(__file__),'gray.txt'), "r")
    except IOError:
        return []
    listarray = []
    for aline in openfile.readlines():
        listarray.append(aline.strip())
    listarray = list(set(listarray))    # Make entries unique
    listarray.sort()
    openfile.close()
    return listarray

def save_graylist(listarray):
    """Write the graylist back to file.

    Args:
        listarray (list of str): Array of domains to save as graylist.

    Returns:
        bool: True.
    """
    openfile = open(os.path.join(os.path.dirname(__file__),'gray.txt'), "w")
    for item in listarray:
        openfile.write("%s\n" % item)
    openfile.close()
    return True

def refresh_graylist():
    """Refresh the graylist by loading all mail addresses and adding them if they are not yet known.

    Returns:
        dict: Infos on the number of checks and results.
    """
    mails = l.search_s(app.config['LDAP_MAIL_SEARCH_BASE'], ldap.SCOPE_SUBTREE, filterstr='(mail=*)', attrlist=["mail"])
    white = load_list_from_ldap(app.config['LDAP_WHITE_DN'])
    black = load_list_from_ldap(app.config['LDAP_BLACK_DN'])
    gray = load_graylist()
    whitecounter = 0
    blackcounter = 0
    graycounter = 0
    newlyadded = 0
    for dn,entry in mails:
        for mailaddress in entry['mail']:
            domain = sanitize_entry(mailaddress)
            if domain in white:
                whitecounter += 1
            elif domain in black:
                blackcounter += 1
            elif domain in gray:
                graycounter += 1
            elif domain != '':
                newlyadded += 1
                domain_to_list(domain, 'gray')
    results = {'mails_on_whitelist': whitecounter, 'mails_on_blacklist': blackcounter,
            'mails_on_graylist': graycounter, 'mails_from_new_domains': newlyadded}
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
        graylistarray = load_graylist()
        try:
            graylistarray.remove(domain)
        except ValueError:
            pass
        if listname == 'white':
            add_to_ldap_list(domain,app.config['LDAP_WHITE_DN'])
            remove_from_ldap_list(domain,app.config['LDAP_BLACK_DN'])
        elif listname == 'black':
            add_to_ldap_list(domain,app.config['LDAP_BLACK_DN'])
            remove_from_ldap_list(domain,app.config['LDAP_WHITE_DN'])
        else:
            remove_from_ldap_list(domain,app.config['LDAP_WHITE_DN'])
            remove_from_ldap_list(domain,app.config['LDAP_BLACK_DN'])
            graylistarray.append(domain)
        save_graylist(graylistarray)
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
    if listname == 'white':
        return Response(response=json.dumps(load_list_from_ldap(app.config['LDAP_WHITE_DN'])), status=200, mimetype='application/json')
    elif listname == 'black':
        return Response(response=json.dumps(load_list_from_ldap(app.config['LDAP_BLACK_DN'])), status=200, mimetype='application/json')
    else:
        return Response(response=json.dumps(load_graylist()), status=200, mimetype='application/json')

@app.route('/api/refresh', methods=['GET'])
def apirefreshcall():
    """API Call to refresh the graylist.

    Returns:
        json: Infos on the number of checks and results.
    """
    return jsonify(refresh_graylist())

@app.route('/api/edugain/<checkaddress>', methods=['GET'])
def edugaincheck(checkaddress):
    """API Call to check the edugain status of a domain.

    Args:
        checkaddress (str): The address to check for edugain support.

    Returns:
        json: The edugain and federation statuses as booleans.
    """
    if not app.config['EDUGAIN_CHECK']:
        raise InvalidAPIUsage('Not available.', status_code=500)
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
    return jsonify(edugain=edugainresult,
                   federation=edugainfederationresult)

@app.route('/api/domain/<address>', methods=['GET'])
def apicheckdomain(address):
    """API Call to check on which list a domain is.

    Args:
        address (str): The address to check for list containment.

    Returns:
        json: The list the address' domain is on.
    """
    domain = sanitize_entry(address)
    if domain in load_list_from_ldap(app.config['LDAP_WHITE_DN']):
        return jsonify(listed='white')
    elif domain in load_list_from_ldap(app.config['LDAP_BLACK_DN']):
        return jsonify(listed='black')
    elif domain in load_graylist():
        return jsonify(listed='gray')
    else:
        return jsonify(listed=None)

@app.route('/', methods=['GET', 'POST'])
def mainpage():
    """Render the page."""
    if request.method == 'POST':
        domain_to_list(sanitize_entry(request.form['domain']), request.form['list'])
    return render_template('main.html', edugaincheck=app.config['EDUGAIN_CHECK'])

if __name__ == "__main__":
    app.run()

