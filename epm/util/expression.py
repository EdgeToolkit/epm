from ply import lex, yacc

tokens = (
    'ID', 'VALUE',
    'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE',
    'AND', 'OR',
    'LPAREN', 'RPAREN',
)

t_ID = r'\w(\.\w+)*'
t_VALUE = r'[\w\-\.]+'

t_EQ = r'=='
t_NEQ = r'!='
t_GE = r'>='
t_GT = r'>'
t_LE = r'<='
t_LT = r'<'

t_AND = r'&&'
t_OR = r'\|\|'

t_LPAREN = r'\('
t_RPAREN = r'\)'

# Ignored characters
t_ignore = " \t"


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    print(f"Illegal character {t.value[0]!r}")
    t.lexer.skip(1)

lexer = lex.lex()

class Boolean(object):

    names = {}


    def __init__(self, vars):
        self._vars = vars
        self._result = ''

    def p_statement_operation(self, p):
        'statement : ID OR ID'
        print('->', p[0], p[1], p[2])


#    def p_expression_id(self, p):
#        'expression : ID'
#        try:
#            #p[0] = names[p[1]]
#            self._result = p
#        except LookupError:
#            print(f"Undefined name {p[1]!r}")
#            p[0] = 0
#
#    def p_expression_binop(p):
#        '''expression : expression EQ expression
#                      | expression NEQ expression
#                      | expression LG expression
#                      | expression LGEQ expression
#                      | expression LT expression
#                      | expression LTEQ expression'''
#        if p[2] == '+':
#            p[0] = p[1] + p[3]
#        elif p[2] == '-':
#            p[0] = p[1] - p[3]
#        elif p[2] == '*':
#            p[0] = p[1] * p[3]
#        elif p[2] == '/':
#            p[0] = p[1] / p[3]

    def build(self, **kwargs):

        self.parser = yacc.yacc(module=self)

    def test(self, expr):
        return self.parser.parse(expr, lexer=lexer)

m = Boolean(dict())
m.build()           # Build the lexer
result = m.test("a||b")
print(result)
