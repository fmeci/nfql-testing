__author__ = 'd'
from NFQL_Tokenizer import *
import ply.yacc as yacc
import re
import json

class FilterRule:
    def __init__(self, name, value, datatype, delta, op):
        self.offset = {
            'name': name,
            'value': value,
            'datatype': datatype
        }

        self.delta = delta
        self.op = op


class Filter(object):
    def __init__(self, id, records, br_mask):
        self.id = id
        self.records = records
        self.br_mask = br_mask


class Rule(object):
    def __init__(self, branch_mask, operation, args):
        self.operation = operation
        self.args = args
        self.branch_mask = branch_mask


datatype_mappings = {'unsigned64': 'RULE_S1_64', 'unsigned32': 'RULE_S1_32', 'unsigned16': 'RULE_S1_16',
                     'unsigned8': 'RULE_S1_8',
                     'ipv4Address': 'RULE_S1_32', 'ipv6Address': 'RULE_S1_128', 'macAddress': 'RULE_S1_48', }
class Parser :
    tokens = Tokenizer.tokens
    filters = []
    filterRules=[]
    xml=[]
    entities={}
    def p_filter(self,p):
        '''
        filter : filterKeyword id '{' filter_rule_1n '}'
        '''
        p[0] = Filter(p[2], p.lineno(2), p[4])
        self.filters.append(p[0])#TODO p4 is empty


    def p_filter_rule_1n(self,p):
        'filter_rule_1n : filter_rule filter_rule_1n'
        p[2].extend([p[1]])
        p[0] = p[2]

    def p_filter_rule_0(self,t):
        'filter_rule_1n :'
        t[0] = []

    def p_filter_rule(self,t):
        '''
        filter_rule : or_rule
        '''
        t[0] = t[1]

    def p_or_rule(self,p):
        '''
        or_rule : rule_or_not opt_rule
        '''
        if len(p[2]) > 0:
            ors = [p[1]]
            ors.extend(p[2])
            p[0] = ors
        else:
            p[0] = [p[1]]


    def p_term_opt_rule(self,t):
        'opt_rule :'
        t[0] = []

    def p_opt_rule(self,t):
        '''opt_rule : ORKeyword rule_or_not opt_rule'''
        r = [t[2]]
        r.extend(t[3])
        t[0] = r

    def p_rule_or_not(self,p):
        '''
        rule_or_not : rule
                    | NOTKeyword rule
        '''
        try:
            p[2].NOT = True
            p[0] = p[2]
        except IndexError:
            p[0] = p[1]

    def p_rule(self,t):
        '''
        rule : infix_rule
             | prefix_rule
        '''
        t[0] = t[1]

    def p_infix_rule(self,p):
        'infix_rule : arg_names op arg'
        #print(self.entities.keys())
        dt=''
        opt=''
        for ps in p[1]:
            dt=ps
        for op in p[2]:
            opt = op
        print(p[0])
        rdt=datatype_mappings[self.entities[dt]]
        fl=FilterRule(dt,p[3],rdt,0,opt)
        self.filterRules.append(fl)
        p[1].extend(p[3])

    def p_op(self,p):
        '''
        op : EQ
           | LT
           | GT
           | LTEQ
           | GTEQ
           | ML
           | MG
           | inKeyword
           | notinKeyword
        '''
        p[0] = p[1] #lineno

    def p_rule_prefix(self,p):
        '''
        prefix_rule : id '(' args ')'
                    | bitANDKeyword '(' args ')'
                    | bitORKeyword '(' args ')'
        '''
        p[0] = Rule(p[1], p.lineno(1), p[3])

    def p_args(self,p):
        '''
        args : arg ',' args
        '''
        p[0] = p[1]
        p[0].extend(p[3])


    def p_no_args(self,t):
        'args :'
        t[0] = []

    def p_arg(self,p): #TODO
        '''
        arg : IPv6
            | IPv4
            | CIDR
            | MAC
            | int
            | prefix_rule
        '''
        p[0] = [p[1]]

    def p_arg_names(self,p):
        '''
        arg_names : id
        '''
        p[0]=[p[1]]
    def p_cidr(self,p):
        '''
        CIDR : IPv4 '/' int
             | IPv6 '/' int
        '''
        p[0] = Rule('cidr_mask', p[1], p[3])


    def p_error(self,p):
        print("Syntax error at input!")

    def Parse(self, data):
        #self.Error = False  tracking=True, debug=1, parse
        # yacc debug = True
        parser = yacc.yacc(module=self)
        lexer = Tokenizer().build()
        self.xml = Tokenizer.names
        self.entities=Tokenizer.entities
        return yacc.parse(data,tracking=True,lexer=lexer)


if __name__ == "__main__":
    parsr = Parser()
    tests=['filter v4 { sourceIPv4Address = 18.0.0.1}','filter v6 {sourceIPv6Address=::1}','filter off{fragmentOffset=8}']
    #try:
        #s = input('debug > ') # Use raw_input on Python 2
    #except EOFError:
    #    pass
    for test in tests:
        parsr.Parse(test)
    lst=[]
    for pr in parsr.filterRules:
        print(vars(pr))
        lst.append({'term':vars(pr)})
    clause={'clause':lst}
    filter={'dnf-expr':[clause]}
    branchset=[]
    branchset.append({'filter':filter})
    query={'branchset':branchset,'grouper':{},'ungrouper':{}}
    fjson = json.dumps(query, indent=2)
    file = open('query-session.json', 'w')
    file.write(fjson)
    file.close


