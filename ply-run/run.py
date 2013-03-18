__author__ = 'd'
import ply.lex as lex
import netaddr
import os
import sys
import re
import string
from xml.dom import minidom
import json
datatype_mappings={'unsigned64':'RULE_S1_64','unsigned32':'RULE_S1_32','unsigned16':'RULE_S1_16','unsigned8':'RULE_S1_8',
names=[]
reserved = {
    'filter' : 'filterKeyword',
    'srcport' : 'srcportKeyword',
    'in' : 'inKeyword',
    'notin' : 'notinKeyword',
    'OR' : 'ORKeyword',
    'NOT' : 'NOTKeyword',
    'bitOR': 'bitORKeyword',
    'bitAND' : 'bitANDKeyword',
    }
entities={}
def xml_data():
    xmldoc = minidom.parse('ipfix.xml')
    node = xmldoc.documentElement
    records = xmldoc.getElementsByTagName('record')
    #print itemlist[0].attributes['name'].value
    for record in records :
        nameObj = record.getElementsByTagName('name')
        dataTypeObj = record.getElementsByTagName('dataType')
        dataType=""
        for data in dataTypeObj:
            dataType=data.childNodes[0].nodeValue
            break
        for name in nameObj:
            try:
                nameText=name.childNodes[0].nodeValue
                if nameText.find(' ') == -1 and str(dataType):
                #print nameText
                    reserved[nameText]=str(nameText).replace('\n','')
                    entities[nameText]=dataType.replace('\n','')
                    #reserved[nameText.]
                    names.append(nameText.replace('\n',''))
            except IndexError:
                pass
def t_LTEQ(t):
    r'<='
    t.value = 'LTEQ'
    return t

def t_GTEQ(t):
    r'>='
    t.value = 'GTEQ'
    return t

def t_ML(t):
    r'<<'
    t.value = 'ML'
    return t

def t_MG(t):
    r'>>'
    t.value = 'MG'
    return t

def t_LT(t):
    r'<'
    t.value = 'LT'
    return t

def t_EQ(t):
    r'='
    t.value = 'EQ'
    return t

def t_GT(t):
    r'>'
    t.value = 'GT'
    return t
xml_data()
tokens = ['GT','EQ','LT','LTEQ','GTEQ',
          'id', 'string','IPv4','IPv6','int','MAC',
          'ML','MG']+list(reserved.values())
#literals = "+-*/(),."



def t_IPv4(t):
    r'(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])(%[\p{N}\p{L}]+)?'
    return t

def t_IPv6(t):
    r"""((:|[0-9a-fA-F]{0,4}):)([0-9a-fA-F]{0,4}:){0,5}((([0-9a-fA-F]{0,4}:)?(:|[0-9a-fA-F]{0,4}))|(((25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.){3}
    (25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])))(%[\p{N}\p{L}]+)?"""
    return t
def t_int(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
        raise
    return t
def t_MAC(t):
    r'([a-fA-F0-9]{2}[:\-]){5}[a-fA-F0-9]{2}'

def t_id(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # matches also keywords, so be careful
    t.type = reserved.get(t.value,'id')    # Check for reserved words
    return t



# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_comment(t):
    r"[ ]*\043[^\n]*" # \043 is '#'
    pass
# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print ("Illegal character '%s'" % t.value[0])
    #t.lexer.skip(1)

# Build the lexer

lexer = lex.lex(debug=0)

data = '''
filter ff { sourceIPv6Address=2001::1}
'''


lexer.input(data)
# Tokenize
while True:
    tok = lexer.token()
    if not tok: break      # No more input
    print (tok)
##parser
filters=[]
def p_filter(p):
    '''
    filter : filterKeyword id '{' filter_rule_1n '}'
    '''
    p[0] = Filter(p[2], p.lineno(2), p[4])
    filters.append(p[0])


def p_filter_rule_1n(p):
    'filter_rule_1n : filter_rule filter_rule_1n'
    p[2].extend([p[1]])
    p[0] = p[2]

def p_filter_rule_0(t):
    'filter_rule_1n :'
    t[0]=[]
def p_filter_rule(t):
    '''
    filter_rule : or_rule
    '''
    t[0]=t[1]
def p_or_rule(p):
    '''
    or_rule : rule_or_not opt_rule
    '''
    if len(p[2]) > 0:
        ors = [p[1]]
        ors.extend(p[2])
        p[0] = ors
    else:
        p[0] = [p[1]]


def p_term_opt_rule(t):
    'opt_rule :'
    t[0]=[]
def p_opt_rule(t):
    '''opt_rule : ORKeyword rule_or_not opt_rule'''
    r=[t[2]]
    r.extend(t[3])
    t[0]=r

def p_rule_or_not(p):
    '''
    rule_or_not : rule 
                | NOTKeyword rule
    '''
    try:
        p[2].NOT = True
        p[0] = p[2]
    except IndexError:
        p[0] = p[1]

def p_rule(t):
    '''
    rule : infix_rule
         | prefix_rule
    '''
    t[0]=t[1]
def p_infix_rule(p):
    'infix_rule : arg op arg'
    p[1].extend(p[3])
def p_op(p):
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
    p[0] = (p[1], p.lineno(1))
def p_rule_prefix(p):
    '''
    prefix_rule : id '(' args ')'
                | bitANDKeyword '(' args ')'
                | bitORKeyword '(' args ')'
    '''
    p[0] = Rule(p[1], p.lineno(1), p[3])
def p_args(p):
    '''
    args : arg ',' args
    '''
    p[0] = p[1]
    p[0].extend(p[3])


def p_no_args(t):
    'args :'
    t[0]=[]
def p_arg(p): #TODO
    '''
    arg : id
        | IPv6
        | IPv4
        | CIDR
        | MAC
        | int
        | prefix_rule
    '''

    p[0] = [p[1]]


def p_cidr(p):
    '''
    CIDR : IPv4 '/' int
         | IPv6 '/' int
    '''
    p[0] = Rule('cidr_mask', p[1], p[3])


def p_error(p):
    msg = "Syntax error "
    #msg += "(%s)" % (p.type)
    msg += " at line %s" % lexer.lineno
    raise SyntaxError(msg)

import ply.yacc as yacc
parser=yacc.yacc()
s=input(data)
result=parser.parse(s,debug=0)
#print (result)
#with open('query.json', mode='w', encoding='utf-8') as f:  
#    json.dump(entities, f,indent=2)
for name in filters:
    print(name)

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
