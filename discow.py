#!/usr/bin/env python3

import os
import re
import sys
import time
import requests
import json
import webbrowser
import getopt
import browser_cookie3
from random import randint
from time import sleep
from pprint import pprint
from config import conf

###############################################################################
###############################################################################
### API Doc:
### https://www.discogs.com/developers/
###############################################################################
###############################################################################

# User Agents
ua = 'WantListAdder/0.1 +http://frankmeffert.de'
oua = 'Mozilla Firefox Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0'

# list of sellers offering something for me
sellersf = "sellers.txt"
bestoffers = "bestoffers.txt"

# Header stuff
hdr_accept = 'application/vnd.discogs.v2.plaintext+json'
hdr_auth = 'Discogs token=' + conf['ptok']

# Endpoints
baseurl = 'https://discogs.com'
apiurl = 'https://api.discogs.com'
tokurl = apiurl + '/oauth/request_token'
idurl = apiurl + '/oauth/identity'
uauthurl = baseurl + '/oauth/authorize?oauth_token='
accessurl = apiurl + '/oauth/access_token'


def epoch():
    return str(int(time.time()))

def http_err(res):
    print("Error (%s): %s" % (res.status_code, res.text))

def jdump(_json):
    print(json.dumps(_json, indent=2, sort_keys=True))

def prompt_yn(msg):
    resp = input(msg+' (y/n):')
    return 'y' in resp.lower()

def auth_get_token():
    # get a request token
    h = {'Content-Type': 'application/x-www-form-urlencoded',
         'Authorization':
            'OAuth oauth_consumer_key="'+conf['appkey']+'",'
            'oauth_nonce="thisisarandomstring",'
            'oauth_signature="'+conf['appsecret']+'&",'
            'oauth_signature_method="PLAINTEXT",'
            'oauth_timestamp="'+epoch()+'",'
            'oauth_callback="http://frankmeffert.de"',
         'User-Agent': ua}

    r = requests.get(tokurl, headers=h)
    if r.status_code != 200:
        print("Moep (%s). %s" % (r.status_code,r.text))
        return None
    else:
        return dict(x.split("=") for x in r.text.split("&"))

def auth_get_verif(token):
    webbrowser.open("%s%s" % (uauthurl, token['oauth_token']), new=2)
    verif = input('Verifier:')
    return verif

def auth_get_access(token, verif):
    # get access token
    h = {'Content-Type': 'application/x-www-form-urlencoded',
         'Authorization':
            'OAuth oauth_consumer_key="'+conf['appkey']+'",'
            'oauth_nonce="'+epoch()+'",'
            'oauth_token="'+token['oauth_token']+'",'
            'oauth_signature="'+conf['appsecret']+'&'+token['oauth_token_secret']+'",'
            'oauth_signature_method="PLAINTEXT",'
            'oauth_timestamp="'+epoch()+'",'
            'oauth_verifier="'+verif+'"',
         'User-Agent': ua}
    r = requests.post(accessurl, data={}, headers=h)
    if r.status_code != 200:
        print("Moep (%s). %s" % (r.status_code,r.text))
        return None
    else:
        return dict(x.split("=") for x in r.text.split("&"))

def getNotFinished(url, atok):
    h = {'Content-Type': 'application/x-www-form-urlencoded',
         'Authorization':
            'OAuth oauth_token="'+atok['oauth_token']+'",'
            'oauth_token_secret="'+atok['oauth_token_secret']+'",',
         'User-Agent': ua}
    r = requests.get(url, headers=h)
    if r.status_code != 200:
        print("Moep (%s). %s" % (r.status_code,r.text))
        return None
    else:
        return r

def get(url):
    h = {
            'Authorization': hdr_auth,
            'Accept': hdr_accept
        }
    r = requests.get(url, headers=h)
    if r.status_code != 200:
        http_err(r)
        return None
    if "application/json" in r.headers['Content-Type']:
        return r.json()
    else:
        print("Received " + r.headers['Content-Type'])
        return None

def pget(url, appendkey, per_page=100):
    """ paginated get.
    """
    cur = 0
    end = 1
    jbunch = None
    while cur < end:
        print("Getting page " + str(cur+1) + " ...")
        uargs = "?per_page="+str(per_page)+"&page="+str(cur+1)
        j = get(url + uargs)

        if jbunch == None:
            jbunch = j
        else:
            jbunch[appendkey].extend(j[appendkey])

        # handle pagination updates
        end = int(j["pagination"]["pages"])
        cur += 1
    return jbunch


def post(url, payload):
    h = {
            'Authorization': hdr_auth,
            'Accept': hdr_accept
        }
    r = requests.post(url, data=payload, headers=h)
    if r.status_code != 200:
        http_err(r)
        return None

def put(url, payload):
    h = {
            'Authorization': hdr_auth,
            'Accept': hdr_accept
        }
    r = requests.put(url, data=payload, headers=h)
    if r.status_code != 201:
        http_err(r)
        return None
    else:
        return r.json()


def auth():
    rtok  = auth_get_token()
    verif = auth_get_verif(rtok)
    atok  = auth_get_access(rtok, verif)
    print(atok)


def get_versions_by_format(master_id, fmt):
    fmt_ids = []
    j = get(apiurl+'/masters/'+master_id+'/versions?format='+fmt)
    for v in j['versions']:
        fmt_ids.append(v['id'])
    return fmt_ids

def add_version_want(version_id):
    put(apiurl + '/users/'+conf['user']+'/wants/'+version_id, payload={})

def add_all_versions_by_fmt(master_id, fmt):
    # get all vinyl versions of one master
    versions = get_versions_by_format(master_id, fmt)
    if prompt_yn('Add %d versions?' % len(versions)):
        for v in versions:
            add_version_want(str(v))

def get_want_masters(username):
    """ Gets all masters instead of releases from the given user's wantlist
    """
    masters = {}
    wantdict = pget(apiurl + "/users/"+username+"/wants", "wants")
    for r in wantdict["wants"]:
        master_id = r["basic_information"]["master_id"]

        artists = ""
        for a in r["basic_information"]["artists"]:
            artists += a["name"] + ", "
        artists = artists[:-2]

        song = artists + " - " + r["basic_information"]["title"]
        if master_id not in masters:
            masters[master_id] = song

    print("### You've got %d wanted records:" % len(masters))
    for i,m in masters.items():
        print(m)

def xtract_sellers(html):
    restr = 'data-username="([^ ]+)"'
    matches = re.findall(restr, html, re.DOTALL)
    return set(matches)

def get_cookie_session():
    session = requests.session()
    session.headers.update({'User-Agent': oua})
    cookies = browser_cookie3.chrome(domain_name='.discogs.com')
    session.cookies.update(cookies)
    return session

def get_sellers(fname=""):
    session = get_cookie_session()
    html = paginate_sellers(session)
    sellers = xtract_sellers(html)

    if fname != "":
        with open(fname, "w") as fh:
            for s in sellers:
                fh.write("%s\n" % (s))


def paginate_sellers(session, fname=""):
    ep = baseurl+"/sell/mywants?sort=listed%2Cdesc&limit={pl}&page={pn}"
    out = ""
    i = 1
    while True:
        _ep = ep.format(pl="250", pn=str(i))
        print("Getting %s" % _ep)
        r = session.get(_ep)
        if r.status_code != 200:
            print("Code %s" % str(r.status_code))
            break
        if "No items for sale found" in r.text:
            break

        out += r.text
        i += 1

    if fname != "":
        with open(fname, "w") as fh:
            fh.write(out)
    return out

def get_num_wants(seller):
    session = get_cookie_session()
    ep = baseurl+"/seller/"+seller+"/mywants"
    r = session.get(ep)
    if r.status_code != 200:
        return None
    restr = '.*>(\d+) From My Wantlist</span>.*'
    m = re.match(restr, r.text, re.DOTALL)
    if m == None:
        return None
    if len(m.groups()) < 1:
        return None
    #print(m.groups())
    return int(m.groups()[0])

def get_most_offers():
    if not os.path.isfile(sellersf):
        print("List of sellers in %s not found." % sellersf)
        return

    sellers = []
    with open(sellersf, "r") as fh:
        sellers = fh.read().splitlines()

    i = 1
    max = ("", 0)
    offerdict = {}
    for s in sellers:
        print("Checking seller %04d/%04d ... " % (i,len(sellers)), end='')
        n = get_num_wants(s)
        print(n)
        if (n != None):
            offerdict[s] = n
            if n > max[1]:
                max = (s, n)
                print("New top: %s has %d items." % (s,n))
        i += 1
        t = randint(500,1000)/1000
        sleep(t)

    sortedoffers = dict(sorted(offerdict.items(), key=lambda item: item[1]))
    with open(bestoffers, "w") as fh:
        fh.truncate()
        for k,v in sortedoffers.items():
            fh.write("%s:%s\n" % (k,v))

def check_api():
    print("Check 1-2")
    j = get(idurl)
    print(j)

def userinventory(username):
    j = get(apiurl + "/users/"+username+"/inventory?status=for sale")
    jdump(j)

def market():
    # well shite. The API doesn't support searching the market place.
    # Even the undocumented endpoint search was removed 3 years ago.
    j = get('http://api.discogs.com/marketplace/search?release_id=5643677')
    jdump(j)

def want():
    j = get(apiurl + "/users/"+conf['user']+"/wants")
    jdump(j)

def usage():
    msg = """
    {progname} [options]
        -h --help           show this help
        -a --addwant <id>   adds all releases of the given master to the wantlist
        -c --check          check if the API is working
        -w --want           displays the want list
        -s --sellers        determines a list of sellers offering stuff I want
        -f --format <fmt>   format to filter for (defaults to Vinyl)
        -t --test           test whatever it is you wanna test :)
    """
    print(msg.format(progname=sys.argv[0]))

def test():
    #userinventory("Aratuna")
    #seller = "vinyl.eu"
    #n = get_num_wants(seller)
    #print("Seller %s has %s items I want." % (seller,str(n)))
    get_most_offers()

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:chwf:st",
            ["addwant=", "check", "help", "want", "format=", "sellers", "test"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    want = False
    addwant = ""
    format = "Vinyl"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-a", "--addwant"):
            addwant = a
        elif o in ("-w", "--want"):
            want = True
        elif o in ("-c", "--check"):
            check_api()
            sys.exit()
        elif o in ("-s", "--sellers"):
            get_sellers(sellersf)
            sys.exit()
        elif o in ("-t", "--test"):
            test()
            sys.exit()
        else:
            assert False, "unhandled option"

    # do the actual dispatch
    if addwant != "":
        add_all_versions_by_fmt(addwant, format)

    if want == True:
        get_want_masters(conf['user'])

if __name__ == "__main__":
    main()
