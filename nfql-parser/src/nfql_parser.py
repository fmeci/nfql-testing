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
class Grouper(object):
    def __init__(self, name, line, modules, aggr, branches=None):
        self.name = name
        self.aggr = aggr
        self.modules = modules
        self.line = line
        self.branches = branches if branches else set()

    def __repr__(self):
        str = "Grouper('%s', %s, %s, %s, %s)"%(self.name, self.line,
                                      self.modules, self.aggr, self.branches)
        return str

class Filter(object):
    def __init__(self, id, line, br_mask):
        self.id = id
        self.line = line
        self.br_mask = br_mask

    def __repr__(self):
        str = "Filter('%s', %s, %s)" % (self.id, self.line, self.br_mask)
        return str
class Field(object):
    def __init__(self, name):
        self.name = name
    #def __repr__(self):
        #return "Field('%s')"%self.name
class FilterRef(object):
    def __init__(self, name, line, NOT=False):
        self.name = name
        self.NOT = NOT
        self.line = line

    def __repr__(self):
        str = "FilterRef('%s', %s, %s)"%(self.name, self.line, self.NOT)
        return str
class Rule(object):
    def __init__(self, branch_mask, operation, args):
        self.operation = operation
        self.args = args
        self.branch_mask = branch_mask
class AggregationRule(object):
    def __init__(self, field, operation, datatype):
        self.op = operation
        self.offset= {'datatype':datatype,
                      'name':field
        }

class GrouperRule(object):
    #def __init__(self, op, line, args):
        #self.line = line
        #self.args = args
        #self.op = op

    #def __repr__(self):
        #str = "GrouperRule('%s', %s, %s)"%(self.op, self.line, self.args)
        #return str
    def __init__(self, name1, datatype1,name2,datatype2, deltatype,deltavalue, op,optype):
        self.offset = {
            'f1_name': name1,
            'f1_datatype': datatype1,
            'f2_name': name2,
            'f2_datatype':datatype2
        }

        self.delta = deltavalue
        self.op = {#TODO type
            'type':optype,
            'name':op
        }
class Module(Filter):
    def __repr__(self):
        str = "Module('%s', %s, %s)"%(self.id, self.line,
                                           self.br_mask)
        return str
datatype_mappings = {'unsigned64': 'RULE_S1_64', 'unsigned32': 'RULE_S1_32', 'unsigned16': 'RULE_S1_16',
                     'unsigned8': 'RULE_S1_8','EQ':'RULE_EQ','GT':'RULE_GT','LT':'RULE_LT','LTEQ':'RULE_LE',
                     'GTEQ':'RULE_GE','IN':'RULE_IN',
                     'ipv4Address': 'RULE_S1_32', 'ipv6Address': 'RULE_S1_128', 'macAddress': 'RULE_S1_48', }
class Parser :
    tokens=[]
    tokens = Tokenizer.tokens
    filters = []
    groupers=[]
    filterRules=[]
    xml=[]
    entities={}
    def p_pipeline_stage_1n(self,p):
        'pipeline_stage_1n : pipeline_stage newline pipeline_stage_1n'
        # add a name mapping:
        p[0]=p[1]

    def p_pipeline_stage_end(self,p):
        'pipeline_stage_1n :'

    def p_pipeline_stage(self,p):
        '''
        pipeline_stage : filter
                        | grouper
        '''

        p[0] = p[1]
    def p_filter(self,p):
        '''
        filter : filterKeyword id '{' filter_rule_1n '}'
        '''
        p[0] = Filter(p[2], p.lineno(2), p[4])
        #print(p[4][0].op)
        self.filters.append(p[0])#TODO p4 is empty


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

    ####Grouper####
    def p_grouper(self, p):
        "grouper : grouperKeyword id '{' module1_n aggregate '}'"
        p[0] = Grouper(p[2], p.lineno(2), p[4], p[5])
        #p[0].aggr.insert(0, (Rule('union', p.lineno(2), [Field('rec_id'),
        #                                                 'records'])))
        #p[0].aggr.insert(0, (Rule('min', p.lineno(2), [Field('stime'),
        #                                               'stime'])))
        #p[0].aggr.insert(0, (Rule('max', p.lineno(2), [Field('etime'),
        #                                               'etime'])))
        self.groupers.append(p[0])

    def p_module1_n(self, p):
        'module1_n : module module1_n newline'
        p[1].extend(p[2])
        p[0] = p[1]

    def p_module0(self, p):
        'module1_n :'
        p[0] = []

    def p_module(self, p):
        "module : moduleKeyword id '{' grouper_rule1_n '}'"
        p[0] = [Module(p[2], p.lineno(2), p[4])]

    def p_grouper_rule1_n(self, p):
        'grouper_rule1_n : grouper_rule grouper_rule1_n'
        p[1].extend(p[2])
        p[0] = p[1]

    def p_grouper_rule0(self, p):
        'grouper_rule1_n :'
        p[0] = []

    def p_grouper_rule(self, p):#TODO
        'grouper_rule : id grouper_op id'
        try:
            rdt1=datatype_mappings[self.entities[p[1]]]
            rdt2=datatype_mappings[self.entities[p[3]]]
        except KeyError:
            print('Invalid field name at line %s'%p.lineno)
        operator = datatype_mappings[p[2]]
        if(rdt1 != rdt2):
            print('Datatype mismatch at line %s'%p.lineno)
            exit(1)
        #print(operator)
        p[0] = [GrouperRule(p[1],rdt1,p[3],rdt2,'none',0,operator,'RULE_REL')]
    ##absolute id=arg

    def p_grouper_rule_delta(self, p):
        '''
        grouper_rule : id grouper_op id deltaKeyword delta_arg
        '''
        try:
            rdt1 = datatype_mappings[self.entities[p[1]]]
            rdt2 = datatype_mappings[self.entities[p[3]]]
        except KeyError:
            print('Invalid field name at line %s' % p.lineno)
        operator = datatype_mappings[p[2]]
        if (rdt1 != rdt2):
            print('Datatype mismatch at line %s' % p.lineno)
            exit(1)
        p[0] = [GrouperRule(p[1],rdt1,p[3],rdt2,'delta',p[5],operator,'RULE_REL')]

    def p_grouper_rule_rel_delta(self, p):
        '''
        grouper_rule : id grouper_op id rdeltaKeyword delta_arg
        '''
        try:
            rdt1 = datatype_mappings[self.entities[p[1]]]
            rdt2 = datatype_mappings[self.entities[p[3]]]
        except KeyError:
            print('Invalid field name at line %s' % p.lineno)
        operator = datatype_mappings[p[2]]
        if (rdt1 != rdt2):
            print('Datatype mismatch at line %s' % p.lineno)
            exit(1)
        p[0] = [GrouperRule(p[1], rdt1, p[3], rdt2, 'rdelta', p[5], operator,'RULE_REL')]

    def p_grouper_op(self, p):
        '''
        grouper_op : EQ
                    | LT
                    | GT
                    | GTEQ
                    | LTEQ
        '''
        p[0] = p[1]

    def p_delta_arg(self, p):
        '''
        delta_arg :     time
                    | int
        '''
        p[0] = p[1]

    def p_time(self, p):
        '''
        time :  int sKeyword
                | int msKeyword
                | int minKeyword
        '''
        # the number should be in ms:
        if p[2] == 's':
            p[1].value = p[1].value * 1000
        if p[2] == 'min':
            p[1].value = p[1].value * 60 * 1000
        p[0] = p[1]

    def p_aggregate(self, p):
        'aggregate : aggregateKeyword aggr1_n'
        #print(p[2])
        #for aggr in p[2]:
        #    if aggr.line == 0:
        #        aggr.line = p.lineno(1)
        p[0] = p[2]

    def p_aggr1_n(self, p):
        'aggr1_n : aggr opt_aggr'
        p[1].extend(p[2])
        p[0] = p[1]

    def p_opt_aggr(self, p):
        "opt_aggr : ',' aggr opt_aggr"
        p[2].extend(p[3])
        p[0] = p[2]

    def p_opt_aggr_end(self, p):
        'opt_aggr :'
        p[0] = []

    def p_aggr(self, p):
        "aggr : aggr_op '(' id_or_qid ')' asKeyword id"
        args = [Field(p[3]), p[6]] # [id_or_qid, id, aggr_op]
        p[0] = [Rule(p[1], p.lineno(4), args)]

    def p_simple_agg(self, p):
        'aggr : id_or_qid asKeyword id'
        args = [Field(p[1]), p[3]] # [qid, id]
        p[0] = [Rule('last', p.lineno(2), args)]

    def p_simple_agg_same_name(self, p):
        'aggr : id_or_qid'
        #args = [Field(p[1]), p[1]] # [qid, id]
        #print('hello')
        rdt1=datatype_mappings[self.entities[p[1]]]
        p[0] = [AggregationRule(p[1], 'RULE_STATIC',rdt1)]

    def p_qid(self, p):
        '''
        qid : id '.' id
        '''
        p[0] = p[1] + p[2] + p[3]

    def p_id_or_qid(self, p):
        '''
        id_or_qid : id
                    | qid
        '''
        p[0] = p[1]

    def p_aggr_op(self, p):
        '''
        aggr_op : minKeyword
                | maxKeyword
                | sumKeyword
                | avgKeyword
                | unionKeyword
                | countKeyword
                | bitANDKeyword
                | bitORKeyword
        '''
        p[0] = p[1]


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


