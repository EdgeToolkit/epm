from ply import lex, yacc


class Lex(object):
    reserved = {
        'in': 'IN',
    }
    tokens = ['STRING', 'QSTRING', 'SQSTRING', 'RE',
              'EQ', 'NEQ', 'LT', 'LE', 'GT', 'GE', 
              'MATCH', 'NMATCH',
              'AND', 'OR', 'LBEGIN', 'LEND'
    ] + list(reserved.values())

    # Regular expression rules for simple tokens
#    t_STRING = r'\w[.\S]*'
    t_QSTRING = r'\"[^\"]+\"'
    t_SQSTRING = r"'[^\']+'"
    t_RE = r"`[^`]+`"
    t_AND = r'&&'
    t_OR = r'\|\|'

    t_EQ = r'=='
    t_NEQ = r'!='
    t_LT = r'<'
    t_LE = r'<='
    t_GT = r'>'
    t_GE = r'>='
    t_MATCH = r'~='
    t_NMATCH = r'!~'
    t_LBEGIN = r'\['
    t_LEND = r'\]'
    
    def t_STRING(self, t):
        r'\w[\w\.\-]*'
        t.type = self.reserved.get(t.value, 'STRING')
        return t

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


class Yacc(Lex):

    @staticmethod
    def p_logical_operation(p):
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

    def p_string(self, p):
        '''string : STRING
                  | QSTRING
                  | SQSTRING
        '''
        if p[1][0] in ["'", '"']:
            p[0] = p[1][1:-1].strip()
        else:
            p[0] = p[1]
    def p_items(self, p):
        '''items : string
                | items string
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 3:
            p[0] = p[1] + [p[2]]
        

    def p_expression(self, p):
        '''expression : string EQ string
                      | string NEQ string
                      | string LT string
                      | string LE string
                      | string GT string
                      | string GE string
                      | string MATCH RE
                      | string NMATCH RE
                      | string IN LBEGIN items LEND
                      | string
        '''
        op = None
        value = self._vars.get(p[1], None)
        if len(p) > 2:
            op = p[2]
            value = str(self._vars.get(p[1], self._None))

        if op == '==':
            p[0] = value == p[3]
        elif op == '!=':
            p[0] = value != p[3]
        elif op == '>':
            p[0] = value > p[3]
        elif op == '>=':
            p[0] = value >= p[3]
        elif op == '<':
            p[0] = value < p[3]
        elif op == '<=':
            p[0] = value <= p[3]
        elif op == '~=':
            pattern = p[3]
            import re
            pattern = re.compile(p[3][1:-1])
            p[0] = bool(pattern.match(value))
        elif op == '!~':    
            pattern = p[3]
            import re
            pattern = re.compile(p[3][1:-1])
            p[0] = not bool(pattern.match(value))

        elif op == 'in':
            p[0] = bool( value in p[4])    
        elif op is None:
            p[0] = bool(value)

    # Error rule for syntax errors
    def p_error(self, p):
        raise SyntaxError('expr error: %s' % self._expr)

    def __init__(self, vars, none='None', debug=False):
        # Build the parser
        self._expr = None
        self._vars = vars or dict()
        self._None = none
        self._lexer = lex.lex(module=self)
        self._parser = yacc.yacc(module=self, write_tables=debug, debug=debug)

    def parse(self, expr):
        self._expr = expr
        return self._parser.parse(expr)
