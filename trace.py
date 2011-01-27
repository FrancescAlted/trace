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

# Check Python version
python_version = sys.version_info[0]
if ( (python_version == 2 and sys.version_info[1] < 6) or
     python_version < 2 ):
    print("You need Python 2.6 or greater!")
    sys.exit()

if python_version == 2:
    from HTMLParser import HTMLParser
    from urllib2 import urlopen
else:
    from html.parser import HTMLParser
    from urllib.request import urlopen



class ReturnLinks(HTMLParser):
    """Helper class to retrieve reference links."""

    def __init__(self):
        self.links = []
        HTMLParser.__init__(self)

    def set_root(self, root):
        """The root for incomplete URLs."""
        self.root = root

    def handle_starttag(self, tag, attrs):
        """Retrieve <a href=...> links and populate `links` attribute."""
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    # Check is the url is complete
                    if not value.startswith("http:"):
                        value = self.root + value
                    self.links.append(value)


if __name__ == "__main__":
    # Arguments in command line?
    if len(sys.argv) <= 1:
        print("pass the url at least!")
        sys.exit()

    url_root = sys.argv[1]
    rlinks = ReturnLinks()
    rlinks.set_root(url_root)
    url = urlopen(url_root)
    data = url.read()
    # Get the set encoding for this page
    if python_version == 2:
        charset = url.info().getparam('charset')
    else:
        charset = url.info().get_content_charset()
    rlinks.feed(data.decode(charset))
    links = rlinks.links
    rlinks.close()
    print("links-->", links)

