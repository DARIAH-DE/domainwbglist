import os
import requests
from flask import Flask

from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import send_from_directory
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

def edugain_check(domain):
    """Call the eduGAIN isFederatedCheck to identify institutional domains."""
    federationhit = '"Federated":true'
    edugainhit = '"eduGAIN-Enabled":true'
    callurl = app.config['RESTURL']+domain
    response = requests.get(callurl)
    # Check, if the appropriate strings are contained in the response.
    # Response is json, but not fully documented and somewhat unpredictable.
    if (int(str(response.content).find(edugainhit)) > 0 or
            int(str(response.content).find(federationhit)) > 0):
        edugainresult = True
    else:
        edugainresult = False
    return edugainresult

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
        liststring += ('<a href="/decide/'+element+'" '
                       'class="list-group-item">'+element+'</a>')
    liststring += '</div>'
    return liststring

def javascript_array_string():
    """Returns a string with javascript arrays of all three lists."""
    whitelist = list_as_array('white')
    blacklist = list_as_array('black')
    graylist = list_as_array('gray')
    jsstring = ''
    jsstring = 'var whitelist = new Array('
    for item in whitelist:
        jsstring += '"' + item + '",'
    if jsstring[-1:] == ',':      # no trailing comma
        jsstring = jsstring[:-1]
    jsstring = jsstring + ');\n    var graylist = new Array('
    for item in graylist:
        jsstring += '"' + item + '",'
    if jsstring[-1:] == ',':      # no trailing comma
        jsstring = jsstring[:-1]
    jsstring = jsstring + ');\n    var blacklist = new Array('
    for item in blacklist:
        jsstring += '"' + item + '",'
    if jsstring[-1:] == ',':      # no trailing comma
        jsstring = jsstring[:-1]
    jsstring = jsstring + ');\n'
    return jsstring

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

@app.route('/decide/')
@app.route('/decide/<name>', methods=['GET', 'POST'])
def decidepage(name=None):
    """Render and process the decision page.

    If a POST is received, the approriate list changes are called.
    Otherwise the page for deciding the list to put it on it rendered.
    If enabled, the eduGAIN isFederatedCheck will be performed.
    """
    if request.method == 'POST':
        domain_to_list(name, request.form['list'])
        return redirect(url_for('mainpage'))
    else:
        domain = name.strip('@')
        edugainresult = False
        if app.config['EDUGAIN_CHECK']:
            edugainresult = edugain_check(domain)
        return render_template('decide.html',
                               name=name,
                               url='http://'+domain,
                               edugainresult=edugainresult)

@app.route('/download/')
@app.route('/download/<name>', methods=['GET', 'POST'])
def downloadfile(name=None):
    """Download lists."""
    return send_from_directory(directory=os.path.dirname(__file__),
                               filename=name, as_attachment=True)



@app.route('/')
def mainpage():
    """Render the main page with all three lists."""
    whiteliststring = list_to_htmlstring(list_as_array('white'))
    blackliststring = list_to_htmlstring(list_as_array('black'))
    grayliststring = list_to_htmlstring(list_as_array('gray'))
    return render_template('main.html',
                           whiteliststring=whiteliststring,
                           blackliststring=blackliststring,
                           grayliststring=grayliststring,
                           javascriptarraystring=javascript_array_string(),
                           whitenumber=len(list_as_array('white')),
                           blacknumber=len(list_as_array('black')),
                           graynumber=len(list_as_array('gray')))

if __name__ == "__main__":
    app.run()

