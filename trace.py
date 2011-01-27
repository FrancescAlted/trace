#!/usr/bin/env python

########################################################################
#
#       Created: January 25, 2011
#       Author:  Francesc Alted - faltet@pytables.org
#
########################################################################

"""
trace: a small web tracer
=========================

Given any URL passed as argument, follow all <A> HTML elements (with a
maximal level specified by an optional command line switch '-l') and
save the hierarchy structure into a text file.

See README.txt for details.

"""

from __future__ import print_function

import sys
import os.path

# Check Python version
python_version = sys.version_info[0]
if ( (python_version == 2 and sys.version_info[1] < 6) or
     python_version < 2 ):
    print("You need Python 2.6 or greater!")
    sys.exit()

if python_version == 2:
    from HTMLParser import HTMLParser, HTMLParseError
    from urllib2 import urlopen, HTTPError
else:
    from html.parser import HTMLParser, HTMLParseError
    from urllib.request import urlopen, HTTPError
from httplib import InvalidURL

#
# Global variables
#

currentlevel = 1
"The current level in hierarchy."
root_url = ""
"The root URL."
visited_urls = []
"The URLs that are already visited."

class ReturnLinks(HTMLParser):
    """Helper class to retrieve reference links."""

    def __init__(self):
        self.links = []
        self.maxlevel = 0  # default is not maxlevel
        self.url_base = ""
        HTMLParser.__init__(self)

    def set_url_base(self, url_base):
        """Set the URL base."""
        self.url_base = os.path.dirname(url_base)

    def handle_starttag(self, tag, attrs):
        """Retrieve <a href=...> links and populate `links` attribute."""
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    # Many different exceptions here (a bit crazy, and
                    # probably incomplete)
                    if '?' in value: return
                    if '#' in value: return
                    init_value = value
                    # Avoid external references
                    if ( value.startswith("http://") and
                         not value.startswith(root_url) ):
                        return
                    # Check relative URLs
                    elif value.startswith("../"):
                        value = os.path.join(self.url_base, value)
                    # Check absolute URLs
                    elif value.startswith("/"):
                        skip = 1
                        if value.startswith("//"):
                            skip = 2
                        value = root_url + value[skip:]
                    # Check if the url is complete
                    if not ( value.startswith("http://") or
                             value.startswith("https://") ):
                        value = root_url + value
                    # Avoid appending duplicates
                    if value not in visited_urls:
                        self.links.append(value)
                        visited_urls.append(value)
                        print("init, final-->", init_value, value)


def discover_links(url_):
    """Discover links hanging from `url_`."""

    # Setup the URL discoverer
    rlinks = ReturnLinks()
    rlinks.set_url_base(url_)

    # Read the URL
    try:
        url = urlopen(url_)
    except (HTTPError, InvalidURL):
        # Problems accessing the URL.  Give up.
        return []
    data = url.read()
    # Get the set encoding for this page
    if python_version == 2:
        charset = url.info().getparam('charset')
    else:
        charset = url.info().get_content_charset()
    if charset is None:
        charset = "utf-8"

    # Feed the data in URL to ReturnLinks discoverer
    rlinks.feed(data.decode(charset))
    links = rlinks.links
    try:
        rlinks.close()
    except HTMLParseError:
        # Problems parsing the HTML data.  Give up.
        pass
    return links


def print_links(url_iter):
    """Recursively print all references hanging from `url`."""
    global currentlevel

    # Check if we reached the maximum level
    if currentlevel > maxlevel:
        return

    links = discover_links(url_iter)
    for link in links:
        print("  "*currentlevel + link)

    # No, increment the level in one and continue
    currentlevel += 1

    # Iterate over the child URLs
    for link in links:
        print_links(link)


if __name__ == "__main__":
    import optparse
    usage = "usage: %prog [options] url"
    p = optparse.OptionParser(usage=usage)

    p.add_option("-l", type="int", dest="maxlevel", default=1)
    opts, args = p.parse_args()
    maxlevel = opts.maxlevel

    # Arguments in command line?
    if len(args) == 0:
        print("pass one url at least!")
        sys.exit()

    root_url = sys.argv[1]
    if not root_url.endswith('/'):
        root_url += '/'
    print(root_url)
    print_links(root_url)

