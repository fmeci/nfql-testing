import re
import json
import types
import itertools
import sys
from nfql_parser import *

import shutil
if __name__ == "__main__":

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
                    filter = {'dnf-expr': clause}
                    branchset.append({'filter': filter})
                    filter=[]

				
                query = {'branchset': branchset,'ungrouper': {}}
                fjson = json.dumps(query, indent=2)
                file = open('%s.json'%inp.name[:-4], 'w')
                assert file.write(fjson)
				
                file.close


