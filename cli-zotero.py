#!/usr/bin/env python
"""
Backwards compatibility.

The actual package was re-named cli_zotero (note the underscore versus the
hyphen).  This file is provide only such that the script cli-zotero can be run
directly from a cloned repo. This file is not installed via `python setup.py
install`. Instead, the cli-zotero entrypoint in setup.py is what is actually
installed.
"""
from cli_zotero import main

if __name__ == '__main__':
    main()
