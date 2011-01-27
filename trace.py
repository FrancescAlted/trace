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
    from cPickle import dump, load
else:
    from html.parser import HTMLParser, HTMLParseError
    from urllib.request import urlopen, HTTPError
    from pickle import dump, load

from httplib import InvalidURL

#
# Global variables
#
visited_urls = []
"The URLs that are already visited."
printed_urls = []
"The already printed URLs."


class ReturnLinks(HTMLParser):
    """Helper class to retrieve reference links."""

    def __init__(self):
        self.links = []
        self.maxlevel = 0  # default is not maxlevel
        self.base_url = ""
        HTMLParser.__init__(self)

    def set_base_url(self, base_url):
        """Set the URL base."""
        self.base_url = os.path.dirname(base_url)

    def handle_starttag(self, tag, attrs):
        """Retrieve <a href=...> links and populate `links` attribute."""
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    # Many different exceptions here (a bit crazy, and
                    # probably incomplete)
                    if (not dynamic_urls) and ('?' in value):
                        return
                    # Internal references are not listed by default
                    if '#' in value:
                        return
                    if debug:
                        init_value = value
                    # Avoid external references
                    if value.startswith("//"):
                        return
                    elif ( value.startswith("http://") and
                           not value.startswith(root_url) ):
                        return
                    # Check relative URLs
                    elif value.startswith("../"):
                        value = os.path.join(self.base_url, value)
                    # Check absolute URLs
                    elif value.startswith("/"):
                        value = root_url + value[1:]
                    # Check if the url is complete
                    if not ( value.startswith("http://") or
                             value.startswith("https://") ):
                        value = root_url + value
                    # Avoid appending duplicates
                    if value not in visited_urls:
                        self.links.append(value)
                        visited_urls.append(value)
                        if debug:
                            print("init, final-->", init_value, value)


def discover_links(url_):
    """Discover links hanging from `url_`."""

    # Setup the URL discoverer
    rlinks = ReturnLinks()
    rlinks.set_base_url(url_)

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
    links = []
    try:
        rlinks.feed(data.decode(charset))
        links.extend(rlinks.links)
        rlinks.close()
    except HTMLParseError:
        # Problems parsing the HTML data.  Give up.
        pass

    return links


def print_links(url_iter):
    """Recursively print all references hanging from `url`."""
    global currentlevel
    global printed_urls

    if debug:
        print("currentlevel, maxlevel-->", currentlevel, maxlevel)

    # Increment the level in one
    currentlevel += 1
    # Check if we reached the maximum level
    if (maxlevel > 0) and (currentlevel > maxlevel-1):
        return

    if type(url_iter) is list:
        # We are continuing
        links = url_iter
    else:
        links = discover_links(url_iter)
        for link in links:
            print("  "*currentlevel + link, file=outfile)
        printed_urls = links

    # Iterate over the child URLs
    for link in links:
        print_links(link)


if __name__ == "__main__":
    import optparse

    # Deal with options
    usage = "usage: %prog [options] url"
    p = optparse.OptionParser(usage=usage)

    p.add_option("-l", type="int", dest="maxlevel", default=0)
    p.add_option("-o", type="string", dest="outfile", default=sys.stdout)
    p.add_option("-f", type="string", dest="dumpfile", default="trace.dump")
    p.add_option("-d", action="store_true", dest="dynamic_urls")
    p.add_option("-D", action="store_true", dest="debug")
    p.add_option("--continue", action="store_true", dest="continue_")

    opts, args = p.parse_args()
    continue_ = opts.continue_
    dumpfile = opts.dumpfile
    currentlevel = 0  # default current level

    if continue_:
        # Continuing.  Retrieve the previous state.
        f = open(dumpfile, "rb")
        state = load(f)
        f.close()
        maxlevel = state['maxlevel']
        currentlevel = state['currentlevel'] - 1
        root_url = state['root_url']
        outfile = state['outfile']
        dynamic_urls = state['dynamic_urls']
        visited_urls = state['visited_urls']
        printed_urls = state['printed_urls']
        print("printed_urls-->", printed_urls)

        print("Continuing trace for %s starting from level %d" %
              (root_url, currentlevel+1))

    # Override with possible new options
    maxlevel = opts.maxlevel
    outfile = opts.outfile
    dynamic_urls = opts.dynamic_urls
    debug = opts.debug

    if type(outfile) is str:
        outfile = open(outfile, 'w')

    if not continue_:
        # Arguments in command line?
        if len(args) == 0:
            print("pass one url at least!")
            sys.exit()

        # First deal with the root
        root_url = sys.argv[1]
        if not root_url.endswith('/'):
            root_url += '/'
        print(root_url, file=outfile)
        url_iter = root_url
        visited_urls.append(root_url)
    else:
        url_iter = printed_urls

    # Then all the rest
    try:
        print_links(url_iter)
    except KeyboardInterrupt:
        print(" ...tracing interrupted in level %d!", currentlevel)
        print("Saving state for later continuation (please wait...)")
        # Save the current state
        state = {'maxlevel': maxlevel,
                 'currentlevel': currentlevel,
                 'root_url': root_url,
                 'outfile': outfile,
                 'dynamic_urls': dynamic_urls,
                 'visited_urls': visited_urls,
                 'printed_urls': printed_urls,
                 }
        f = open(dumpfile, "wb")
        dump(state, f, protocol=-1)
        f.close()

