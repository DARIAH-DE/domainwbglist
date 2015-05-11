import os
from flask import Flask

from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import send_from_directory
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_pyfile('settings_local.py', silent=True)
app.config.update(
    BOOTSTRAP_SERVE_LOCAL='True'
)
Bootstrap(app)

whitelistfile = os.path.join(os.path.dirname(__file__), 'white.txt')
blacklistfile = os.path.join(os.path.dirname(__file__), 'black.txt')
graylistfile = os.path.join(os.path.dirname(__file__), 'gray.txt')

whitelist = []
blacklist = []
graylist = []

whiteliststring = ''
blackliststring = ''
grayliststring = ''

javascriptarraystring = ''

def readfiles():
    global whitelist
    global blacklist
    global graylist
    whitefile = open(whitelistfile, "r")
    for aline in whitefile.readlines():
        whitelist.append(aline.strip())
    whitelist = list(set(whitelist))
    whitelist.sort();
    whitefile.close()
    blackfile = open(blacklistfile, "r")
    for aline in blackfile.readlines():
        blacklist.append(aline.strip())
    blacklist = list(set(blacklist))
    blacklist.sort();
    blackfile.close()
    grayfile = open(graylistfile, "r")
    for aline in grayfile.readlines():
        graylist.append(aline.strip())
    graylist = list(set(graylist))
    graylist.sort();
    grayfile.close()

def writefiles():
    global whitelist
    whitelist = list(set(whitelist))
    global blacklist
    blacklist = list(set(blacklist))
    global graylist
    graylist = list(set(graylist))
    whitefile = open(whitelistfile, "w")
    for item in whitelist:
        whitefile.write("%s\n" % item)
    whitefile.close()
    blackfile = open(blacklistfile, "w")
    for item in blacklist:
        blackfile.write("%s\n" % item)
    blackfile.close()
    grayfile = open(graylistfile, "w")
    for item in graylist:
        grayfile.write("%s\n" % item)
    grayfile.close()

def makestrings():
    global whiteliststring
    global blackliststring
    global grayliststring
    global javascriptarraystring
    javascriptarraystring = 'var whitelist = new Array('
    whiteliststring='<div class="list-group">'
    for w in whitelist:
        whiteliststring+='<a href="/decide/'+w+'" class="list-group-item">'+w+'</a>'
        javascriptarraystring += '"'+w+'",'
    whiteliststring+='</div>'
    javascriptarraystring = javascriptarraystring[:-1] + ');\n    var graylist = new Array('
    grayliststring='<div class="list-group">'
    for g in graylist:
        grayliststring+='<a href="/decide/'+g+'" class="list-group-item">'+g+'</a>'
        javascriptarraystring += '"'+g+'",'
    grayliststring+='</div>'
    javascriptarraystring = javascriptarraystring[:-1] + ');\n    var blacklist = new Array('
    blackliststring='<div class="list-group">'
    for b in blacklist:
        blackliststring+='<a href="/decide/'+b+'" class="list-group-item">'+b+'</a>'
        javascriptarraystring += '"'+b+'",'
    blackliststring+='</div>'
    javascriptarraystring = javascriptarraystring[:-1] + ');\n'


@app.route('/decide/')
@app.route('/decide/<name>', methods=['GET', 'POST'])
def decidepage(name=None):
    global whitelist
    global blacklist
    global graylist
    if request.method == 'POST':
        if request.form['list'] == 'white':
            whitelist.append(name)
            try:
                blacklist.remove(name)
            except:
                pass
            try:
                graylist.remove(name)
            except:
                pass
        elif request.form['list'] == 'black':
            blacklist.append(name)
            try:
                whitelist.remove(name)
            except:
                pass
            try:
                graylist.remove(name)
            except:
                pass
        elif request.form['list'] == 'gray':
            graylist.append(name)
            try:
                whitelist.remove(name)
            except:
                pass
            try:
                blacklist.remove(name)
            except:
                pass
        writefiles()
        return redirect(url_for('mainpage'))
    else:
        return render_template('decide.html', name=name, url='http://'+name.strip('@'))

@app.route('/download/')
@app.route('/download/<name>', methods=['GET', 'POST'])
def downloadfile(name=None):
    return send_from_directory(directory=os.path.dirname(__file__), filename=name, as_attachment=True)



@app.route('/')
def mainpage():
    readfiles()
    makestrings()
    writefiles()
    return render_template('main.html', whiteliststring=whiteliststring, blackliststring=blackliststring, grayliststring=grayliststring, javascriptarraystring=javascriptarraystring,
            whitenumber=len(whitelist), blacknumber=len(blacklist), graynumber=len(graylist))

if __name__ == "__main__":
    app.run()

