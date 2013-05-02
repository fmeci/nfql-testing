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
class GroupFilterRule:
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

class Filter(object):
    def __init__(self, id, line, br_mask):
        self.id = id
        self.line = line
        self.br_mask = br_mask
class Merger(object):
    def __init__(self, id, line, br_mask):
        self.id = id
        self.line = line
        self.br_mask = br_mask
class GroupFilter(object):
    def __init__(self, id, line, br_mask):
        self.id = id
        self.line = line
        self.br_mask = br_mask
class Branch(object):
    def __init__(self, id, line, filters,groupers,groupfilters):
        self.id = id
        self.line = line
        self.filters = filters
        self.groupers = groupers
        self.groupfilters = groupfilters
class Field(object):
    def __init__(self, name):
        self.name = name
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
        self.offset= {
            'datatype':datatype,
            'name':field
        }

class GrouperRule(object):
    def __init__(self, name1, datatype1,name2,datatype2,deltavalue, op,optype):
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
class MergerRule(object):
    def __init__(self, branch1_id,branch2_id,name1, datatype1,name2,datatype2,deltavalue, op,optype):
        self.branch1_id = branch1_id,
        self.branch2_id = branch2_id,
        self.offset = {
            'f1_name': name1,
            'f1_datatype': datatype1,
            'f2_name': name2,
            'f2_datatype':datatype2
        }

        self.delta = deltavalue
        self.op = {
            'type':optype,
            'name':op
        }
datatype_mappings = {'unsigned64': 'RULE_S1_64', 'unsigned32': 'RULE_S1_32', 'unsigned16': 'RULE_S1_16',
                     'unsigned8': 'RULE_S1_8','EQ':'RULE_EQ','GT':'RULE_GT','LT':'RULE_LT','LTEQ':'RULE_LE',
                     'GTEQ':'RULE_GE','IN':'RULE_IN','SUM':'RULE_SUM','COUNT':'RULE_COUNT','STATIC':'RULE_STATIC',
                     'ABS':'RULE_ABS','REL':'RULE_REL','PROD':'RULE_PROD','STDDEV':'RULE_STDDEV','BITOR':'RULE_OR',
                     'BITAND':'RULE_AND',
                     'MIN':'RULE_MIN','MAX':'RULE_MAX','UNION':'RULE_UNION','MEDIAN':'RULE_MEDIAN','MEAN':'RULE_MEAN',
                     'ipv4Address': 'RULE_S1_32', 'ipv6Address': 'RULE_S1_128', 'macAddress': 'RULE_S1_48', }
class Parser :
    tokens=[]
    tokens = Tokenizer.tokens
    filters = []
    groupers=[]
    grouper= Grouper('',0,'','','')
    groupfilters=[]
    branches=[]
    branch_ids=[]
    merger=[]
    filterRules=[]
    xml=[]
    entities={}
    def p_stage(self,p):
        '''
            stage : branches merger ungrouper
        '''
        p[0]=[]
    def p_branches(self,p):
        '''
        branches : branch newline branches
        '''
        p[0]=p[1]
    def p_branches_empty(self,p):
        'branches :'
        p[0]=[]
    def p_branch(self,p):
        '''
        branch : branchKeyword id '{' pipeline_stage_1n '}'

                | branchKeyword id '{' newline pipeline_stage_1n '}'
                | branchKeyword id '{' pipeline_stage_1n newline '}'
                | branchKeyword id '{' newline pipeline_stage_1n newline '}'
                | branchKeyword id newline '{' pipeline_stage_1n '}' newline
                | branchKeyword id newline '{' pipeline_stage_1n newline '}'
                | branchKeyword id newline '{' newline pipeline_stage_1n newline '}'
                | branchKeyword id newline '{' newline pipeline_stage_1n '}'

        '''
        p[0]= Branch(p[2],p.lineno(2),self.filters,self.groupers,self.groupfilters)
        self.branches.append(p[0])
        self.branch_ids.append(p[2])
        self.groupfilters=[]
        self.filters=[]
        self.groupers=[]

    def p_branch_empty(self, p):
        'branch :'
        p[0]=[]
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
                        | groupfilter
        '''

        p[0] = p[1]
    def p_filter(self,p):
        '''
        filter : filterKeyword id '{' filter_rule_1n '}'
        '''
        p[0] = Filter(p[2], p.lineno(2), p[4])
        #print(p[4][0].op)
        self.filters.append(p[0])

    def p_filter_newline(self, p):
        '''
        filter : filterKeyword id newline '{' filter_rule_1n '}'
        '''
        p[0] = Filter(p[2], p.lineno(2), p[5])
        #print(p[0].br_mask)
        self.filters.append(p[0])
    def p_filter_rule_1n(self, p):
        'filter_rule_1n : filter_rule newline filter_rule_1n'
        p[3].extend([p[1]])
        p[0] = p[3]

    def p_filter_rule_1n_newline(self, p):
        'filter_rule_1n : newline filter_rule newline filter_rule_1n'
        p[4].extend([p[2]])
        p[0] = p[4]

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
        'infix_rule : arg_names op arg deltaKeyword delta_arg'
        dt = p[1][0]
        opt = p[2]
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
        opt=p[2]
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
        #self.filterRules.append(fl)
        #p[1].extend(p[3])
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
        p[0] = p[1] #lineno

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
        "grouper : grouperKeyword id '{' grouper_rule1_n aggregate '}'"
        p[0] = Grouper(p[2], p.lineno(2), p[4], p[5])
        #self.grouper = p[0]
        self.groupers.append(p[0])
        #print(p[0])

    def p_grouper_newline(self, p):
        """grouper : grouperKeyword id newline '{' grouper_rule1_n aggregate '}'
                    | grouperKeyword id newline '{' grouper_rule1_n aggregate newline '}'
        """
        p[0] = Grouper(p[2], p.lineno(2), p[5], p[6])
        self.grouper = p[0]
        #print(p[0].modules)
        self.groupers.append(p[0])

    def p_grouper_rule1_n(self, p):
        'grouper_rule1_n : grouper_rule_n newline grouper_rule1_n'
        p[3].extend([p[1]])
        p[0] = p[3]

    def p_grouper_rule1_n_newline(self, p):
        'grouper_rule1_n : newline grouper_rule_n newline grouper_rule1_n'
        p[4].extend([p[2]])
        p[0] = p[4]
    def p_grouper_rule0(self, p):
        'grouper_rule1_n :'
        p[0] = []
    def p_grouper_rule_n(self,p):
        'grouper_rule_n : grouper_or_rule'
        p[0]=p[1]

    def p_grouper_or_rule(self,p):
        'grouper_or_rule : grouper_rule g_opt_rule'
        if len(p[2]) > 0:
            ors = [p[1]]
            ors.extend(p[2])
            p[0] = ors
        else:
            p[0] = [p[1]]
    def p_grouper_opt_rule_empty(self,p):
        'g_opt_rule :'
        p[0]=[]
    def p_grouper_opt_rule(self,p):
        'g_opt_rule : ORKeyword grouper_rule g_opt_rule'
        r = [p[2]]
        r.extend(p[3])
        p[0] = r
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
        p[0] = GrouperRule(p[1],rdt1,p[3],rdt2,0,operator,'RULE_REL')


    ##absolute id=arg
    def p_grouper_rule_abs(self,p):#TODO fix the dt
        'grouper_rule : id grouper_op g_arg'
        dt = p[1]
        try:
            if (self.entities[dt] == 'unsigned8'):
                if (len('{0:08b}'.format(int(p[3]))) <= 8):
                    pass
                else:
                    print('Value out of range at line %s: 8bit' % p.lineno(1))
                    exit(-1)
            elif (self.entities[dt] == 'unsigned16'):
                if (len('{0:08b}'.format(int(p[3]))) <= 16):
                    pass
                else:
                    print('Value out of range at line %s: 16bit' % p.lineno(1))
                    exit(-1)
            elif (self.entities[dt] == 'unsigned32'):
                if (len('{0:08b}'.format(int(p[3]))) <= 32):
                    pass
                else:
                    print('Value out of range at line %s: 32bit' % p.lineno(1))
                    exit(-1)
            elif (self.entities[dt] == 'unsigned64'):
                if (len('{0:08b}'.format(int(p[3]))) <= 64):
                    pass
                else:
                    print('Value out of range at line %s: 64bit' % p.lineno(1))
                    exit(-1)
        except KeyError:
            pass

        operator = datatype_mappings[p[2]]
        p[0] = GrouperRule(p[1], p[1], p[3], p[1], 0, operator, 'RULE_ABS')

    def p_grouper_arg(self, p):
        '''
        g_arg : IPv6
            | IPv4
            | CIDR
            | MAC
            | int

        '''
        p[0] = p[1]
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
        p[0] = GrouperRule(p[1],rdt1,p[3],rdt2,p[5],operator,'RULE_REL')


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

    def p_aggregate_empty(self,p):
        'aggregate :'
        p[0]=[]
    def p_aggregate(self, p):
        "aggregate : aggregateKeyword '{' aggr1_n '}'"
        p[0] = p[3]

    def p_aggregate_newline(self, p):
        "aggregate : aggregateKeyword newline '{' aggr1_n '}'"
        p[0] = p[4]

    def p_aggr1_n(self, p):
        'aggr1_n : aggr_rule newline aggr1_n'
        p[3].extend([p[1]])
        p[0] = p[3]

    def p_aggr1_n_newline(self, p):
        'aggr1_n : newline aggr_rule newline aggr1_n'
        p[4].extend([p[2]])
        p[0] = p[4]

    def p_aggr1_n_empty(self, p):
        'aggr1_n : '
        p[0]=[]

    def p_aggr_rule(self,p):
        "aggr_rule : aggr_op '(' id ')'"
        rdt1 = datatype_mappings[self.entities[p[3]]]
        op = datatype_mappings[str(p[1]).upper()]
        p[0]=[AggregationRule(p[3],op,rdt1)]

    def p_aggr_op(self, p):
        '''
        aggr_op : minKeyword
                | maxKeyword
                | sumKeyword
                | avgKeyword
                | staticKeyword
                | unionKeyword
                | countKeyword
                | bitANDKeyword
                | bitORKeyword
        '''
        p[0] = p[1]
### GroupFilter
    def p_groupfilter(self, p):
        '''
        groupfilter : groupfilterKeyword id '{' groupfilter_rule_1n '}'
        '''
        p[0] = GroupFilter(p[2], p.lineno(2), p[4])
        #print(p[4][0].op)
        self.groupfilters.append(p[0])

    def p_groupfilter_newline(self, p):
        '''
        groupfilter : groupfilterKeyword id newline '{' groupfilter_rule_1n '}'
        '''
        p[0] = GroupFilter(p[2], p.lineno(2), p[5])
        #print(p[0].br_mask)
        self.groupfilters.append(p[0])

    def p_groupfilter_rule_1n(self, p):
        'groupfilter_rule_1n : groupfilter_rule newline groupfilter_rule_1n'
        p[3].extend([p[1]])
        p[0] = p[3]

    def p_groupfilter_rule_1n_newline(self, p):
        'groupfilter_rule_1n : newline groupfilter_rule newline groupfilter_rule_1n'
        p[4].extend([p[2]])
        p[0] = p[4]

    def p_grouperfilter_rule_0(self, t):
        'groupfilter_rule_1n :'
        t[0] = []

    def p_groupfilter_rule(self, t):
        '''
        groupfilter_rule : gf_or_rule
        '''
        t[0] = t[1]

    def p_gf_or_rule(self, p):
        '''
        gf_or_rule : gf_rule gf_opt_rule
        '''
        if len(p[2]) > 0:
            ors = [p[1]]
            ors.extend(p[2])
            p[0] = ors
        else:
            p[0] = [p[1]]


    def p_gf_term_opt_rule(self, t):
        'gf_opt_rule :'
        t[0] = []

    def p_gf_opt_rule(self, t):
        '''gf_opt_rule : ORKeyword gf_rule gf_opt_rule'''
        r = [t[2]]
        r.extend(t[3])
        t[0] = r
    def p_gf_rule(self,p):
        'gf_rule : arg_names op arg'
        dt = p[1][0]
        opt = p[2]
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
        fl = GroupFilterRule(dt, p[3][0], rdt, 0, operator)
        p[0] = fl

    def p_gf_rule_delta(self, p):
        'gf_rule : arg_names op arg deltaKeyword delta_arg'
        dt = p[1][0]
        opt = p[2]
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
        fl = GroupFilterRule(dt, p[3][0], rdt, int(p[5]), operator)
        p[0] = fl
### Merger
    def p_merger_empty(self, p):
        'merger :'
        p[0]=[]
    def p_merger(self,p):
        '''
        merger : mergerKeyword '{' merger_rule_1n '}'
                | mergerKeyword '{' merger_rule_1n '}' newline
        '''
        p[0]=Merger('merger',p.lineno(2),p[3])
        self.merger.append(p[0])
    def p_merger_empty_br(self,p):
        '''
        merger : mergerKeyword '{' '}'
                | mergerKeyword '{' '}' newline
                | mergerKeyword '{' newline '}' newline
                | mergerKeyword newline '{' '}'
                | mergerKeyword newline '{' '}' newline
        '''
        p[0]=[]

    def p_merger_newline(self, p):
        '''
        merger : mergerKeyword newline '{' merger_rule_1n '}'
                | mergerKeyword newline '{' merger_rule_1n '}' newline
        '''
        p[0] = Merger('merger', p.lineno(2), p[4])
        self.merger.append(p[0])

    def p_merger_rule_1n(self, p):
        'merger_rule_1n : merger_rule newline merger_rule_1n'
        p[3].extend([p[1]])
        p[0] = p[3]

    def p_merger_rule_1n_newline(self, p):
        'merger_rule_1n : newline merger_rule newline merger_rule_1n'
        p[4].extend([p[2]])
        p[0] = p[4]

    def p_merger_rule_0(self, t):
        'merger_rule_1n :'
        t[0] = []

    def p_merger_rule(self, t):
        '''
        merger_rule : merger_or_rule
        '''
        t[0] = t[1]

    def p_merger_or_rule(self, p):
        '''
        merger_or_rule : merger_m_rule merger_opt_rule
        '''
        if len(p[2]) > 0:
            ors = [p[1]]
            ors.extend(p[2])
            p[0] = ors
        else:
            p[0] = [p[1]]


    def p_merger_term_opt_rule(self, t):
        'merger_opt_rule :'
        t[0] = []

    def p_merger_opt_rule(self, t):
        'merger_opt_rule : ORKeyword merger_m_rule merger_opt_rule'
        r = [t[2]]
        r.extend(t[3])
        t[0] = r
    def p_m_rule(self,p):
        "merger_m_rule : id '.' id allen_op id '.' id"
        if p[1] in self.branch_ids:
            pass
        else:
            print("Undefined branch id '%s' used at line %s"%(p[1],p.lineno(2)))
            exit(-1)
        if p[5] in self.branch_ids:
            pass
        else:
            print("Undefined branch id '%s' used at line %s" % (p[5], p.lineno(2)))
            exit(-1)

        try:
            rdt1 = datatype_mappings[self.entities[p[3]]]
            rdt2 = datatype_mappings[self.entities[p[7]]]
        except KeyError:
            print('Invalid field name at line %s' % p.lineno(2))
            exit(-1)
        operator = datatype_mappings[p[4]]
        if (rdt1 != rdt2):
            print('Datatype mismatch at line %s' % p.lineno(2))
            exit(1)
        p[0]=MergerRule(0,1,p[3],rdt1,p[7],rdt2,0,operator,'RULE_REL')


    def p_allen_op(self, p):
        '''
        allen_op : LT
                | GT
                | EQ
                | mKeyword
                | miKeyword
                | oKeyword
                | oiKeyword
                | sKeyword
                | siKeyword
                | dKeyword
                | diKeyword
                | fKeyword
                | fiKeyword
                | eqKeyword
        '''
        p[0]=p[1]
### Ungrouper
    def p_ungrouper(self,p):
        'ungrouper :'
        p[0] = []

    def p_ungrouper_empty(self, p):
        '''
        ungrouper : ungrouperKeyword '{' '}'
                | ungrouperKeyword '{' '}' newline
                | ungrouperKeyword '{' newline '}' newline
                | ungrouperKeyword newline '{' '}'
                | ungrouperKeyword newline '{' '}' newline
        '''
        p[0] = []
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


