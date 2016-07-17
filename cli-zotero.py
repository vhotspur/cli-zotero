#!/usr/bin/python2

# Copyright 2015 Charles University in Prague
# Copyright 2015 Vojtech Horky
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from pyzotero import zotero
from pprint import pprint
from ConfigParser import SafeConfigParser
import sys
import os
import argparse
import pickle

# http://stackoverflow.com/a/518232/1360886
def strip_accents(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def latex_escape(s):
    return s.replace(u'\u2013', '--').replace(u'&', '\\&')

def parse_date_guessing(datestr):
    import datetime
    for fmt in [ "%B %d %Y", "%B %d, %Y", "%B %Y", "%Y", "%Y-%m-%d" ]:
        try:
            return datetime.datetime.strptime(datestr, fmt)
        except ValueError as e:
            pass
    return datetime.datetime.today()

def skip_useless_words(where):
    useless_words = 'a the on'.split()
    idx = 0
    while where[idx].lower() in useless_words:
        idx = idx + 1
    return where[idx]

def get_first_author(item):
    author = item['data']['creators'][0]
    if 'lastName' in author:
        return author['lastName']
    else:
        return author['name']

def make_bibtex_key(item):
    if 'extra' in item['data']:
        import re
        lines = item['data']['extra'].split('\n')
        pat = re.compile('bibtex:[ \t]*(.*)')
        for l in lines:
            m = pat.match(l)
            if m:
                return m.group(1)
    author = filter(unicode.isalpha, strip_accents(get_first_author(item)).lower())
    year = parse_date_guessing(item['data']['date']).year
    title_words = strip_accents(item['data']['title']).split()
    title_start = filter(unicode.isalnum, skip_useless_words(title_words).lower())
    return "%s_%s_%s" % (author, title_start, year)

def make_sort_key(item):
    if item['data']['itemType'] == 'attachment':
        return 'xxx'
    author = strip_accents(get_first_author(item)).lower()
    year = parse_date_guessing(item['data']['date']).year
    title_words = strip_accents(item['data']['title']).split()
    title_start = skip_useless_words(title_words).lower()
    return "%s %s %s" % (year, author, title_start)
    

def item_to_bibtex(item):
    def shall_skip(item):
        if item['data']['itemType'] == 'attachment':
            return True
        else:
            return False
        
    def bib_type(item):
        if item['data']['itemType'] == 'journalArticle':
            return 'article'
        elif item['data']['itemType'] == 'conferencePaper':
            return 'inproceedings'
        elif item['data']['itemType'] == 'bookSection':
            return 'incollection'
        else:
            return 'misc'
    
    def make_author_list(creators, creator_type = None):
        # By default, we try to collect only authors.
        # If there is no author explicitly specify, we take everybody
        # (probably not the best thing as different types has different
        # names for creators, e.g. presenter but it is better than to
        # mix authors with editors for book chapters).
        if creator_type is None:
            result = make_author_list(creators, 'author')
            if result != '':
                return result
        names = []
        for c in creators:
            if (not creator_type is None) and ('creatorType' in c) and (c['creatorType'] != creator_type):
                continue
            if 'lastName' in c:
                names.append('%s, %s' % (c['lastName'], c['firstName']))
            else:
                names.append('{%s}' % (c['name']))
        return ' and '.join(names)
    
    def print_key(key, value, print_empty = True):
        if (not print_empty) and (value == ''):
            return
        print('    %s = {%s},' % (key, value.encode('utf-8')))
    
    def has_field(zoterokey, item):
        return zoterokey in item['data'] and item['data'][zoterokey] != ''
    
    def try_field(bibtexkey, zoterokeys, item, escape=True, protect=False, conversion=None):
        if not type(zoterokeys) is list:
            zoterokeys = [ zoterokeys ]
        for key in zoterokeys:
            if (key in item['data']) and (item['data'][key] != ''):
                value = item['data'][key]
                if not conversion is None:
                    value = conversion(value)
                if escape:
                    value = latex_escape(value)
                if protect:
                    value = "{%s}" % value
                print_key(bibtexkey, value)
                # Exit after first match
                return
    
    def get_doi(item):
        if ('DOI' in item['data']) and (item['data']['DOI'] != ''):
            return item['data']['DOI']
        else:
            import re
            lines = item['data']['extra'].split('\n')
            pat = re.compile('[dD][oO][iI]:[ \t]*(.*)')
            for l in lines:
                m = pat.match(l)
                if m:
                    return m.group(1)
            return ''

    if shall_skip(item):
        return
    
    print('@%s{%s,' % (bib_type(item), make_bibtex_key(item)))
    
    try_field('title', 'title', item, protect=True)
    print_key('author', make_author_list(item['data']['creators']))
    
    print_key('year', '%d' % parse_date_guessing(item['data']['date']).year)
    
    # Not so traditional types are distinguished by howpublished field for now
    if item['data']['itemType'] in [ 'blogPost', 'webpage', 'computerProgram' ]:
        try_field('howpublished', 'url', item, conversion=lambda x : '\\url{%s}' % x)
    if item['data']['itemType'] == 'presentation':
        if has_field('meetingName', item):
            s = 'Presentation at {%s}' % item['data']['meetingName']
            if has_field('url', item):
                s = '%s, \\url{%s}' % (s, item['data']['url'])
            print_key('howpublished', s)
    
    try_field('booktitle', [ 'proceedingsTitle', 'bookTitle' ], item, protect=True)
    try_field('journal', 'publicationTitle', item, protect=True)
    print_key('editor', make_author_list(item['data']['creators'], 'editor'), False)
    try_field('publisher', 'publisher', item)
    try_field('series', 'series', item, protect=True)
    try_field('number', [ 'seriesNumber', 'issue' ], item)

    try_field('location', 'place', item)

    item_doi = get_doi(item)
    if item_doi != '':
        print_key('doi', item_doi)
    try_field('isbn', 'ISBN', item)
    try_field('issn', 'ISSN', item)

    try_field('pages', 'pages', item, conversion=lambda x : x.replace('-', '--'))

    try_field('url', 'url', item)
    try_field('volume', 'volume', item)
    try_field('shorttitle', 'shortTitle', item)
    try_field('abstract', 'abstractNote', item)
    
    print('}\n')


class MyConfigParser(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
    
    def get_with_default(self, section, option, default_value=None):
        if self.has_option(section, option):
            return self.get(section, option)
        else:
            return default_value

cfgfile = MyConfigParser()
cfgfile.read(os.path.expanduser('~/.config/cli-zotero.conf'))

parser = argparse.ArgumentParser(description='Command-line client for Zotero')

parser.add_argument('--key',
        dest='key',
        required=not cfgfile.has_option('core', 'key'),
        default=cfgfile.get_with_default('core', 'key'),
        metavar='API-KEY',
        help='Zotero API key (https://www.zotero.org/settings/keys)\nOr specify in [core] of configuration file.')

identity_opts = parser.add_mutually_exclusive_group(required=True)
identity_opts.add_argument('--group',
        dest='group',
        metavar='ID',
        type=int,
        help='Group ID (https://www.zotero.org/groups/)')
identity_opts.add_argument('--user',
        dest='user',
        metavar='ID',
        type=int,
        help='User ID (https://www.zotero.org/settings/keys)')
identity_opts.add_argument('--id',
        dest='identity',
        metavar='NAME',
        help='Identity specified in [identities] in configuration file.')

action_args = parser.add_mutually_exclusive_group(required=True)
action_args.add_argument('--list-collections',
        dest='collection_filter',
        nargs='?',
        const='',
        metavar='TITLE',
        help='List your collections (title partial match)')
action_args.add_argument('--collection-to-bibtex',
        dest='collection_to_bibtex',
        metavar='COLLECTION-ID',
        help='Export given collection to BibTeX')

parser.add_argument('--dump',
        dest='dump_file',
        metavar='FILENAME',
        help='Dump retrieved data through pprint to FILENAME')

parser.add_argument('--limit',
        dest='limit',
        type=int,
        default=30,
        metavar='N',
        help='Set internal limit of the queries')

cfg = parser.parse_args()

zot = None
if cfg.group:
    zot = zotero.Zotero(cfg.group, 'group', cfg.key)
elif cfg.user:
    zot = zotero.Zotero(cfg.user, 'user', cfg.key)
else:
    id_line = cfgfile.get_with_default('identities', cfg.identity)
    if id_line is None:
        sys.exit('Unknown identity "%s".' % cfg.identity)
    id_parts = id_line.split()
    if len(id_parts) != 2 or (id_parts[0] not in ['user', 'group' ]):
        sys.exit('Wrong identity configuration "%s".' % id_line)
    zot = zotero.Zotero(id_parts[1], id_parts[0], cfg.key)


if not cfg.collection_filter is None:
    all_collections = zot.collections(q=cfg.collection_filter, limit=cfg.limit)
    if cfg.dump_file:
        with open(cfg.dump_file, "w") as f:
            pprint(all_collections, f)
    for col in all_collections:
        print("%s - %s" % (col['key'], col['data']['name']))
    sys.exit()

if cfg.collection_to_bibtex:
    items = []
    start_index = 0
    while True:
        next_items = zot.collection_items(cfg.collection_to_bibtex, limit=cfg.limit, start=start_index)
        if len(next_items) == 0:
            break
        items.extend(next_items)
        start_index = start_index + len(next_items)
    if cfg.dump_file:
        with open(cfg.dump_file, "w") as f:
            pprint(items, f)
    items = sorted(items, key=make_sort_key)
    for item in items:
        item_to_bibtex(item)
    sys.exit()

parser.print_help()
