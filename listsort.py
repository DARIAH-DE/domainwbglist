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

def load_list_from_ldap(ldapdn):
    l = ldap.initialize(app.config['LDAP_URL'])
    l.simple_bind_s(app.config['LDAP_USER'],app.config['LDAP_PASS'])
    obj=l.search_s(ldapdn, ldap.SCOPE_BASE, attrlist=["cNAMERecord"])
    for dn,entry in obj:
        res = entry['cNAMERecord']
    res.sort()
    return res

def add_to_ldap_list(domain,ldapdn):
    l = ldap.initialize(app.config['LDAP_URL'])
    l.simple_bind_s(app.config['LDAP_USER'],app.config['LDAP_PASS'])
    try:
        l.modify_s(ldapdn,[(ldap.MOD_ADD,'cNAMERecord',domain)])
    except ldap.TYPE_OR_VALUE_EXISTS:
        # already there
        pass

def remove_from_ldap_list(domain,ldapdn):
    l = ldap.initialize(app.config['LDAP_URL'])
    l.simple_bind_s(app.config['LDAP_USER'],app.config['LDAP_PASS'])
    try:
        l.modify_s(ldapdn,[(ldap.MOD_DELETE,'cNAMERecord',domain)])
    except ldap.NO_SUCH_ATTRIBUTE:
        # not even on there
        pass

def load_graylist():
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
    openfile = open(os.path.join(os.path.dirname(__file__),'gray.txt'), "w")
    for item in listarray:
        openfile.write("%s\n" % item)
    openfile.close()
    return True

def domain_to_list(domain, listname):
    """Put the domain on the specified list and remove it from all others."""
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
    """Sanitize an entry to a domain name and return as string."""
    stringed_entry = entry.encode('ascii','ignore')
    sanitized_entry = stringed_entry[stringed_entry.find('@')+1:].strip()
    regex = re.compile("^[A-Za-z0-9-.]*$")
    if regex.match(sanitized_entry):
        return sanitized_entry.lower()
    else:
        return ''

@app.route('/api/list/<path:path>', methods=['GET'])
def apilistcall(path):
    if path == 'white':
        return Response(response=json.dumps(load_list_from_ldap(app.config['LDAP_WHITE_DN'])), status=200, mimetype='application/json')
    elif path == 'black':
        return Response(response=json.dumps(load_list_from_ldap(app.config['LDAP_BLACK_DN'])), status=200, mimetype='application/json')
    else:
        return Response(response=json.dumps(load_graylist()), status=200, mimetype='application/json')

@app.route('/api/domain/<path:path>', methods=['GET'])
def apicheckdomain():
    pass


@app.route('/api/')
def edugain_result():
    """Return info on list status of domain or call eduGAIN isFederatedCheck"""
    if 'edugain' in request.args.keys():
        domain = request.args.get('edugain')
        federationhit = '"Federated":true'
        edugainhit = '"eduGAIN-Enabled":true'
        callurl = app.config['RESTURL']+domain
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
        return jsonify(data=domain,
                       edugain=edugainresult,
                       federation=edugainfederationresult)
    elif 'list' in request.args.keys():
        domain = request.args.get('list')
        white = load_list_from_ldap(app.config['LDAP_BLACK_DN'])
        black = load_list_from_ldap(app.config['LDAP_WHITE_DN'])
        gray = load_graylist()
        if domain in white:
            whiteresult = True
        else:
            whiteresult = False
        if domain in black:
            blackresult = True
        else:
            blackresult = False
        if domain in gray:
            grayresult = True
        else:
            grayresult = False
        return jsonify(data=domain,
                       white=whiteresult,
                       black=blackresult,
                       gray=grayresult)


@app.route('/', methods=['GET', 'POST'])
def mainpage():
    """Render the main page."""
    if request.method == 'POST':
        domain_to_list(sanitize_entry(request.form['domain']), request.form['list'])
    return render_template('main.html', edugaincheck=app.config['EDUGAIN_CHECK'])

if __name__ == "__main__":
    app.run()

