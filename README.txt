trace: a small web tracer
=========================

Given any URL passed as argument, `trace` follows all <A> HTML
elements (with a maximal level specified by an optional command line
switch '-l') and save the hierarchy structure into a text file.

For example, to follow all links on http://www.google.com::

  $ trace.py http://www.google.com -l 3

should produce a text file like::

  http://www.google.es/
    http://www.google.es/intl/es/ads/
    http://www.google.es/services/
    http://www.google.es/intl/es/about.html
      http://www.google.es/intl/es/help/features.html
      ...
    ...

Note that URLs will not be duplicated, and that dynamical pages are
not included.

When Ctrl-C is pressed, the state is saved (using pickle). The script can be
continued from the previously saved state by::

  $ trace.py -continue


