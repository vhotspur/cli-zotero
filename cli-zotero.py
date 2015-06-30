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
import sys
import argparse
import pickle

# http://stackoverflow.com/a/518232/1360886
def strip_accents(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def latex_escape(s):
    return s.replace(u'\u2013', '--')

def item_to_bibtex(item):
    def make_key(item):
        author = strip_accents(item['data']['creators'][0]['lastName']).lower()
        year = item['data']['date']
        title_start = strip_accents(item['data']['title']).partition(' ')[0].lower()
        return "%s_%s_%s" % (author, year, title_start)
    
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
        else:
            return 'misc'
    
    def make_author_list(creators):
        names = []
        for c in creators:
            if c['creatorType'] == 'author':
                names.append('%s, %s' % (c['lastName'], c['firstName']))
        return ' and '.join(names)
    
    def print_key(key, value):
        print('  %s = {%s},' % (key, value.encode('utf-8')))
        
    def try_field(bibtexkey, zoterokey, item, escape=True, protect=False, conversion=None):
        if zoterokey in item['data']:
            if item['data'][zoterokey] != '':
                value = item['data'][zoterokey]
                if not conversion is None:
                    value = conversion(value)
                if escape:
                    value = latex_escape(value)
                if protect:
                    value = "{%s}" % value
                print_key(bibtexkey, value)
    
    if shall_skip(item):
        return
    
    print('@%s{%s,' % (bib_type(item), make_key(item)))
    
    try_field('title', 'title', item, protect=True)
    print_key('author', make_author_list(item['data']['creators']))
    
    try_field('booktitle', 'proceedingsTitle', item)
    try_field('doi', 'DOI', item)
    try_field('isbn', 'ISBN', item)
    try_field('issn', 'ISSN', item)
    try_field('journaltitle', 'publicationTitle', item)
    try_field('location', 'place', item)
    try_field('number', 'issue', item)
    try_field('pages', 'pages', item, conversion=lambda x : x.replace('-', '--'))
    try_field('publisher', 'publisher', item)
    try_field('series', 'series', item)
    try_field('url', 'url', item)
    try_field('volume', 'volume', item)
    
    print('}\n')        
        

parser = argparse.ArgumentParser(description='Command-line client for Zotero')
parser.add_argument('--key',
        dest='key',
        metavar='API-KEY',
        required=True,
        help='Zotero API key (https://www.zotero.org/settings/keys)')
parser.add_argument('--group',
        dest='group',
        metavar='ID',
        required=True,
        type=int,
        help='Group ID (https://www.zotero.org/groups/)')
parser.add_argument('--limit',
        dest='limit',
        type=int,
        default=30,
        metavar='N',
        help='Set internal limit of the queries')
parser.add_argument('--list-collections',
        dest='collection_filter',
        nargs='?',
        const='',
        metavar='TITLE',
        help='List your collections (title partial match)')
parser.add_argument('--collection-to-bibtex',
        dest='collection_to_bibtex',
        metavar='COLLECTION-ID',
        help='Export given collection to BibTeX')

cfg = parser.parse_args()


zot = zotero.Zotero(cfg.group, 'group', cfg.key)


if not cfg.collection_filter is None:
    all_collections = zot.collections(q=cfg.collection_filter, limit=cfg.limit)
    for col in all_collections:
        print("%s - %s" % (col['key'], col['data']['name']))
    sys.exit()

if not cfg.collection_to_bibtex is None:
    items = zot.collection_items(cfg.collection_to_bibtex, limit=cfg.limit)
    # Sort maybe?
    for item in items:
        item_to_bibtex(item)
    sys.exit()

parser.print_help()