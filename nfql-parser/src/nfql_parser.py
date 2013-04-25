__author__ = 'd'
from nfql_tokenizer import *
import ply.yacc as yacc
import re
import json
import types
import itertools
from sys import argv
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
                     'unsigned8': 'RULE_S1_8','EQ':'RULE_EQ','GT':'RULE_GT','LT':'RULE_LT','LTEQ':'RULE_LE',
                     'GTEQ':'RULE_GE','IN':'RULE_IN',
                     'ipv4Address': 'RULE_S1_32', 'ipv6Address': 'RULE_S1_128', 'macAddress': 'RULE_S1_48', }
class Parser :
    tokens=[]
    tokens = Tokenizer.tokens
    filters = []
    filterRules=[]
    xml=[]
    entities={}
    def p_pipeline_stage_1n(self,p):
        'pipeline_stage_1n : pipeline_stage pipeline_stage_1n'
        # add a name mapping:
        p[0]=p[1]

    def p_pipeline_stage_end(self,p):
        'pipeline_stage_1n :'

    def p_pipeline_stage(self,p):
        '''
        pipeline_stage : filter
        '''

        p[0] = p[1]
    def p_filter(self,p):
        '''
        filter : filterKeyword id '{' filter_rule_1n '}'
        '''
        p[0] = Filter(p[2], p.lineno(2), p[4])
        #print(p[4][0].op)
        self.filters.append(p[0])#TODO p4 is empty

    #def p_filter_rule_1(self, p):
    #    'filter_rule_1n : filter_rule'
    #    p[0] = p[1]

    def p_filter_rule_1n(self, p):
        'filter_rule_1n : filter_rule newline filter_rule_1n'
        p[3].extend([p[1]])
        p[0] = p[3]

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
    def p_delta_rule(self,p):
        'infix_rule : arg_names op arg deltaKeyword EQ int'
        dt = p[1][0]
        opt = p[2][0]
        if (self.entities[dt] == 'unsigned8'):
            if (len('{0:08b}'.format(int(p[3][0]))) <= 8):
                pass
            else:
                print('Value out of range at line %s: 8bit' % p.lineno(1))
                exit(-1)
        elif (self.entities[dt] == 'unsigned16'):
            if (len('{0:08b}'.format(int(p[3][0]))) <= 16):
                pass
            else:
                print('Value out of range at line %s: 16bit' % p.lineno(1))
                exit(-1)
        elif (self.entities[dt] == 'unsigned32'):
            if (len('{0:08b}'.format(int(p[3][0]))) <= 32):
                pass
            else:
                print('Value out of range at line %s: 32bit' % p.lineno(1))
                exit(-1)
        elif (self.entities[dt] == 'unsigned64'):
            if (len('{0:08b}'.format(int(p[3][0]))) <= 64):
                pass
            else:
                print('Value out of range at line %s: 64bit' % p.lineno(1))
                exit(-1)

                #print('Value out of range at line %s')
        rdt = datatype_mappings[self.entities[dt]]

        operator = datatype_mappings[opt]
        fl = FilterRule(dt, p[3][0], rdt, int(p[6]), operator)
        self.filterRules.append(fl)
        p[1].extend(p[3])
        p[0] = fl
    def p_infix_rule(self,p):
        'infix_rule : arg_names op arg'
        dt=p[1][0]
        opt=p[2][0]
        if (self.entities[dt] == 'unsigned8'):
            if (len('{0:08b}'.format(int(p[3][0]))) <= 8):
                pass
            else:
                print('Value out of range at line %s: 8bit' % p.lineno(1))
                exit(-1)
        elif(self.entities[dt] == 'unsigned16'):
            if(len('{0:08b}'.format(int(p[3][0])))<=16):
                pass
            else:
                print('Value out of range at line %s: 16bit'%p.lineno(1))
                exit(-1)
        elif (self.entities[dt] == 'unsigned32'):
            if (len('{0:08b}'.format(int(p[3][0]))) <= 32):
                pass
            else:
                print('Value out of range at line %s: 32bit' % p.lineno(1))
                exit(-1)
        elif(self.entities[dt] == 'unsigned64'):
            if(len('{0:08b}'.format(int(p[3][0])))<=64):
                pass
            else:
                print('Value out of range at line %s: 64bit'%p.lineno(1))
                exit(-1)

                #print('Value out of range at line %s')
        rdt=datatype_mappings[self.entities[dt]]

        operator=datatype_mappings[opt]
        fl=FilterRule(dt,p[3][0],rdt,0,operator)
        self.filterRules.append(fl)
        p[1].extend(p[3])
        p[0]=fl

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
        p[0] = [p[1]] #lineno

    def p_rule_prefix(self,p):
        '''
        prefix_rule : id '(' args ')'
                    | bitANDKeyword '(' args ')'
                    | bitORKeyword '(' args ')'
        '''
        p[0] = Rule(p[1], p.lineno(1), p[3])

    def p_args(self,p):#TODO
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

        '''
        p[0] = [p[1]]

    def p_arg_names(self,p):
        '''
        arg_names : id
                    | prefix_rule
        '''
        p[0]=[p[1]]
    def p_cidr(self,p):
        '''
        CIDR : IPv4 '/' int
             | IPv6 '/' int
        '''
        p[0] = Rule('cidr_mask', p[1], p[3])


    def p_error(self,p):
        print("Syntax error at input line %s"%p.lineno)

    def Parse(self, data):
        #self.Error = False  tracking=True, debug=1, parse
        # yacc debug = True
        parser = yacc.yacc(module=self)

        lexer = Tokenizer().build()
        self.xml = Tokenizer.names
        self.entities=Tokenizer.entities
        return yacc.parse(data,tracking=True,lexer=lexer)


