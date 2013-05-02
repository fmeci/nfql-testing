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
                parsr.Parse(inp.read()+'\n')
                branchset = []
                query={}
                filter=[]


                grouper=[]
                for branch in parsr.branches:
                    grules=[]
                    gclause = []
                    gf_clause = []
                    clause = []
                    aggregation=[]
                    lst=[]
                    for gr in branch.groupers:
                        for grule in gr.modules:
                            grules.append(grule)
                        for aggr in gr.aggr:
                            for a_rule in aggr:
                                lst.append({'term': vars(a_rule)})
                            aggregation.append({'clause': lst})
                        lst=[]
                        for rule in list(itertools.product(*grules)):
                            for r in rule:
                                lst.append({'term': vars(r)})
                            gclause.append({'clause': lst})
                            lst = []
                    grouper = []
                    grouper = {'dnf-expr': gclause,'aggregation':aggregation}
                    for fl in branch.filters:
                        #print(fl.br_mask)
                        rules = []
                        lst = []

                        for frule in fl.br_mask:
                            #print(frule)
                            rules.append(frule)
                        for rule in list(itertools.product(*rules)):
                            for r in rule:
                                lst.append({'term': vars(r)})
                            clause.append({'clause': lst})
                            lst = []
                    filter = {'dnf-expr': clause}
                    for gf in branch.groupfilters:
                        gfrules = []
                        gflst = []

                        for gfrule in gf.br_mask:
                            gfrules.append(gfrule)
                        #print(gfrules)
                        for rule in list(itertools.product(*gfrules)):
                            for r in rule:
                                gflst.append({'term': vars(r)})
                            gf_clause.append({'clause': gflst})
                            gflst = []
                    groupfilter = []
                    groupfilter = {'dnf-expr': gf_clause}
                    branchset.append({'filter': filter,'grouper':grouper,'groupfilter':groupfilter})
                query['branchset']= branchset

				
                query['ungrouper']= {}
                #query['ungrouper']=branchset
                fjson = json.dumps(query, indent=2)
                file = open('%s.json'%inp.name[:-4], 'w')
                assert file.write(fjson)
				
                file.close


