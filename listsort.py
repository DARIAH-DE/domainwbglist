import os
import requests
from flask import Flask

from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import jsonify
from flask import make_response
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.update(
    BOOTSTRAP_SERVE_LOCAL='True',
    RESTURL='https://wiki.edugain.org/isFederatedCheck/?format=json&data=',
    LISTFILES={"white" : "white.txt", "gray":"gray.txt", "black":"black.txt"},
    EDUGAIN_CHECK=False
)
app.config.from_pyfile('settings_local.py', silent=True)
Bootstrap(app)

def list_as_array(listname):
    """Returns the specified list as array."""
    if not listname in app.config['LISTFILES'].iterkeys():
        raise NameError('invalid list name')
    try:
        openfile = open(os.path.join(os.path.dirname(__file__),
                        app.config['LISTFILES'][listname]), "r")
    except IOError:
        return []
    listarray = []
    for aline in openfile.readlines():
        listarray.append(aline.strip())
    listarray = list(set(listarray))    # Make entries unique
    listarray.sort()
    openfile.close()
    return listarray

def save_array_as_list(array, listname):
    """Save a given array as specified listname."""
    if not listname in app.config['LISTFILES'].iterkeys():
        raise NameError('invalid list name')
    openfile = open(os.path.join(os.path.dirname(__file__),
                    app.config['LISTFILES'][listname]), "w")
    for item in array:
        openfile.write("%s\n" % item)
    openfile.close()
    return True

def list_to_htmlstring(listarray):
    """Renders the HTML code for listing the given listarray on the page."""
    liststring = '<div class="list-group">'
    for element in listarray:
        liststring += ('<a href="'+url_for('decidepage')+element+'" '
                       'class="list-group-item">'+element+'</a>')
    liststring += '</div>'
    return liststring

def domain_to_list(domain, listname):
    """Put the domain on the specified list and remove it from all others."""
    for eachlist in app.config['LISTFILES'].iterkeys():
        listarray = list_as_array(eachlist)
        if listname == eachlist:
            listarray.append(domain)
        else:
            try:
                listarray.remove(domain)
            except ValueError:
                pass
        save_array_as_list(listarray, eachlist)
    return True

def sanitize_entry(entry):
    """Sanitize an entry to a domain name."""
    sanitized_entry = entry[entry.find('@'):].strip()
    return sanitized_entry.lower()

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
        white = list_as_array('white')
        black = list_as_array('black')
        gray = list_as_array('gray')
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


@app.route('/decide/')
@app.route('/decide/<name>', methods=['GET', 'POST'])
def decidepage(name=None):
    """Render and process the decision page.

    If a POST is received, the approriate list changes are called.
    Otherwise the page for deciding the list to put it on it rendered.
    """
    if request.method == 'POST':
        domain_to_list(name, request.form['list'])
        return redirect(url_for('mainpage'))
    else:
        return render_template('decide.html',
                               name=name,
                               url='http://'+name.strip('@'),
                               edugaincheck=app.config['EDUGAIN_CHECK'])

@app.route('/download/')
@app.route('/download/<name>', methods=['GET', 'POST'])
def downloadfile(name=None):
    """Download lists."""
    if name == 'white.ldif':
        DC = 'dn: dc=whitelist,dc=dariah,dc=eu'
        array = list_as_array('white')
    elif name == 'black.ldif':
        DC = 'dn: dc=blacklist,dc=dariah,dc=eu'
        array = list_as_array('black') 
    else:
        return false
    arraystring = DC+"\nchangetype: modify\nreplace: cNAMERecord\n"
    for line in array:
        arraystring += "cNAMERecord: "+line[1:]+"\n"
    arraystring += "\n"
    response = make_response(arraystring)
    response.headers["Content-Disposition"] = "attachment; filename="+name
    return response

@app.route('/', methods=['GET', 'POST'])
def mainpage():
    """Render the main page with all three lists."""
    whitelistarray = list_as_array('white')
    blacklistarray = list_as_array('black')
    graylistarray = list_as_array('gray')
    whiteliststring = list_to_htmlstring(whitelistarray)
    blackliststring = list_to_htmlstring(blacklistarray)
    grayliststring = list_to_htmlstring(graylistarray)
    counter_all = 0
    counter_white = 0
    counter_black = 0
    counter_added_to_graylist = 0
    if request.method == 'POST':
        mailfile = request.files['mailfile']
        for aline in mailfile.readlines():
            checkline = sanitize_entry(aline)
            if checkline in whitelistarray:
                counter_white += 1
            elif checkline in blacklistarray:
                counter_black += 1
            elif checkline not in graylistarray:
                domain_to_list(checkline,'gray')
                counter_added_to_graylist += 1
                graylistarray = list_as_array('gray')
                grayliststring = list_to_htmlstring(graylistarray)
            counter_all += 1
    return render_template('main.html',
                           whiteliststring=whiteliststring,
                           blackliststring=blackliststring,
                           grayliststring=grayliststring,
                           whitenumber=len(whitelistarray),
                           blacknumber=len(blacklistarray),
                           graynumber=len(graylistarray),
                           counter_all=counter_all,
                           counter_white=counter_white,
                           counter_black=counter_black,
                           counter_added_to_graylist=counter_added_to_graylist)

if __name__ == "__main__":
    app.run()

