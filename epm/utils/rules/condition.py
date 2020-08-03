from ply import lex, yacc

class Lex(object):
    # List of token names.   This is always required
    tokens = (
       'ID', 'VALUE',
       'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE',
       'AND', 'OR',
       'LPAREN', 'RPAREN',
    )

    # Regular expression rules for simple tokens
    t_ID = r'[\w\.\-]+'
    t_AND = r'&&'
    t_OR = r'\|\|'

    t_EQ = r'=='
    t_NEQ = r'!='
    t_LT = r'<'
    t_LE = r'<='
    t_GT = r'>'
    t_GE = r'>='

    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)


class Compiler(Lex):

    def p_logical_and(self, p):
        '''operation : expression
                     | expression AND expression
                     | expression OR expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        elif p[2] == '&&':
            p[0] = p[1] and p[3]
        elif p[2] == '||':
            p[0] = p[1] or p[3]

    def p_expression(self, p):
        '''expression : ID EQ ID
                      | ID NEQ ID
                      | ID LT ID
                      | ID GT ID
        '''
        op = p[2]
        if op == '==':
            p[0] = p[1] == p[3]
        elif op == '!=':
            p[0] = p[1] != p[3]
        elif op == '>':
            p[0] = p[1] > p[3]
        elif op == '>=':
            p[0] = p[1] >= p[3]
        elif op == '<':
            p[0] = p[1] < p[3]
        elif op == '<=':
            p[0] = p[1] <= p[3]

    # Error rule for syntax errors
    def p_error(self, p):
        print("Syntax error in input!")

    def __init__(self, vars):
        # Build the parser
        self._vars = vars
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self)

    def run(self, expr):
        return self._parser.parse(expr)


compiler = Compiler(None)
result = compiler.run(r'1 != 1-1 && A!=A ')
print(result)
#https://www.jianshu.com/p/0cac979377bd