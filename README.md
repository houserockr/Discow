# Discow
Helper script for Discogs

## Introduction
It's 2020 and we're in this crazy Covid pandemic where we're stuck at home most
most of the time. Naturally, as an angineer, I always try out new things. So I
started collecting vinyl and mixing EDM. It didn't take me too long to land on
that extensive website discogs.com. The website is absolutely great and I'm
glad it exists. However, I also found room for improvements. Especially when it
comes to handling the wantlist. I found ou that discogs has a REST API, so it
didn't take long for the first couple of python lines.

This script is mainly aimed at developers and it's not perfect. If it only serves
as an example to get a quicker entry point into the discogs API, I'm happy.

Here's a short list of what it can do so far:
- Print all master releases of the wantlist (not just all versions/releases)
- Add all versions of a specific format (e.g. Vinyl) to the wantlist
- Get a list of sellers offering something from my wantlist (not via API)

## Dependencies
These are the python modules used:
- requests
- json
- webbrowser
- getopt
- browser_cookie3
- pprint

## API access
Discogs offers private/simple use of the API. To get a key navigate to
https://www.discogs.com/settings/developers
create a personal access token and add it to the config.py.

If you want to build an actual app for multi user access, I also added some
example functions in the script for the three step authentication used.

## Querying the market marketplace
... is not part of the API, unfortunately. However, I was able to scrape interesting
information from the website. If you go this road, you'll quickly run into
the problem of cookies. I tried multiple solutions I found online, including
wget and curl both using exported cookies from firefox/chrome. Those didn't work at
all for me and for this case.
I ended up using the browser_cookie3 module like so:

    browser_cookie3.chrome(domain_name='.discogs.com')

to create a requests session using the cookies from chrome. Don't know if this also
works with different browsers. But you'll get the idea.

## Usage
The script has a usage function.
Simply call

    $ ./discow -h

for the help.

## Examples
- Add all vinyl versions of "Insomnia" by Faithless to the wantlist:

    $ ./discow -a 55716 -f Vinyl

- Display all masters of the wantlist:

    $ ./discow -w

- Check if API access is working

    $ ./diwcow -c