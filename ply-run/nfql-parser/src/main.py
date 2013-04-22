import re
import json
import types
import itertools
import sys
from nfql_parser import *

import shutil
if __name__ == "__main__":

    #tests=['filter v4 { sourceIPv4Address = 18.0.0.1}','filter v6 {sourceIPv6Address=::1}','filter off{fragmentOffset=8}']
    #tests=["""filter v3{sourceIPv4Address=18.0.0.255 OR  sourceIPv6Address>=::192.168.1.190
    # sourceIPv6Address>=::1 OR sourceIPv4Address=0.0.0.0
    # sourceTransportPort=143
    #           }"""]
    #try:
        #s = input('debug > ') # Use raw_input on Python 2
    #except EOFError:
    #    pass

    files = len(sys.argv)
    for i in range(files):
        exists=True
        if(i!=0):
            try:
                inp = open((sys.argv[i]))
            except IOError:
                print('Error opening file %s'%str(sys.argv[i]))
                exists=False
            if(exists):
                parsr = Parser()
                parsr.Parse(inp.read())
                branchset = []
                for fl in parsr.filters:
                    rules = []
                    lst = []
                    clause = []
                    for frule in fl.br_mask:
                        rules.append(frule)
                    for rule in list(itertools.product(*rules)):
                        for r in rule:
                            lst.append({'term': vars(r)})
                        clause.append({'clause': lst})
                        lst = []
                    filter = {'dnf-expr': [clause]}
                    branchset.append({'filter': filter})
				
                query = {'branchset': branchset, 'grouper': {}, 'ungrouper': {}}
                fjson = json.dumps(query, indent=2)
                file = open('%s.json'%inp.name[:-4], 'w')
                file.write(fjson)
				
                file.close
