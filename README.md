# Command-line client for Zotero

Right now, only export to BibTeX is implemented.

This utility is using the [Pyzotero library](https://pypi.python.org/pypi/Pyzotero/).

```
usage: cli-zotero.py [-h] [--key API-KEY] (--group ID | --user ID | --id NAME)
                     (--list-collections [TITLE] | --collection-to-bibtex COLLECTION-ID)
                     [--dump FILENAME] [--limit N]

Command-line client for Zotero

optional arguments:
  -h, --help            show this help message and exit
  --key API-KEY         Zotero API key (https://www.zotero.org/settings/keys)
                        Or specify in [core] of configuration file.
  --group ID            Group ID (https://www.zotero.org/groups/)
  --user ID             User ID (https://www.zotero.org/settings/keys)
  --id NAME             Identity specified in [identities] in configuration
                        file.
  --list-collections [TITLE]
                        List your collections (title partial match)
  --collection-to-bibtex COLLECTION-ID
                        Export given collection to BibTeX
  --dump FILENAME       Dump retrieved data through pprint to FILENAME
  --limit N             Set internal limit of the queries
```

