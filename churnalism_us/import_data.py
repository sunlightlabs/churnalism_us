import logging
import urllib
import urllib2
import pickle
import base64
from optparse import OptionParser

SERVER = '127.0.0.1:8080'

try:
    (ID_MAP, URL_LIST) = pickle.load(open('id_map.py'))
except Exception as e:
    print e
    ID_MAP = None
    URL_LIST = []

def update_id_map(doctype, docid):
    ID_MAP[doctype] = docid

def get_id(doctype):
    global ID_MAP 
    if ID_MAP:
        if ID_MAP.has_key(doctype):
            return ID_MAP[doctype] + 1
        else:
            ID_MAP[doctype] = 1
            return 1
    else:
        ID_MAP = {}
        ID_MAP[doctype] = 1
        return 1

def save(doctype, data):
    
    if data['url'] in URL_LIST:
        print "URL was already present in list. Wasn't added"
        return

    docid = get_id(doctype)
    post_url = "http://%s/document/%s/%s" % (SERVER, doctype, docid)
    print post_url
    try:
        print "posting %s" %  post_url
        req = urllib2.Request(post_url)
        req.add_data(urllib.urlencode(data))
        req.get_method = lambda: 'PUT'

        resp = urllib2.urlopen(req)

        update_id_map(doctype, docid)
        URL_LIST.append(data['url'])

    except urllib2.HTTPError as e:
        raise StoreFailure('Failed to POST to {url}: {exception}'.format(url=api_url, exception=e))


def read_file(filename):
    """ This file is designed to read, parse and insert arbitrary content into superfastmatch. 
        The file format is an arbitrary flat format. Each document should be separated by 10 equal signs
        and each data element should be separated by a *|. Data elements should be in the order:
        date, document title, source title, source id, url, and text. """
    
    f = open(filename)
    docs = f.read().split("==========")
    docs = docs[1:]  #file should start with ====

    for d in docs:
        data = d.split("*|")
        data = data[1:]   #first element will be whitespace before first  **|

        pubdate = data[0].strip("\n")
        title = data[1].strip("\n")
        source_title = data[2].strip("\n")
        source_id = data[3].strip("\n")
        url = data[4].strip("\n")
        text = data[5].strip("\n")

        save(source_id, {'data': pubdate, 
                         'title': title, 
                         'source_title': source_title, 
                         'url': url, 
                         'text': text} )        


if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename", help="The file name to load into superfastmatch")

    (options, args) = parser.parse_args()
    if options.filename: 
        read_file(options.filename)
        
        pickle.dump((ID_MAP, URL_LIST), open('id_map.py', 'w'))

    else:
        pass
