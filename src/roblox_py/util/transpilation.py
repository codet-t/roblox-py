import ast
from os import stat

# Refer to:
# https://docs.python.org/3/library/ast.html#abstract-grammar

def transpile_call(node: ast.Call):
    result: str = "";

    # Get name of node
    name = node.func.id;

    result = result + name + "(";

    # Loop through the arguments
    for i in range(0, len(node.args)):
        arg = node.args[i];
        result = result + transpile_line(arg);

        if i != len(node.args) - 1:
            result = result + ", ";
    
    result = result + ")";

    result = "\n" + " " * node.col_offset + result;
            
    return result;

def transpile_while(node: ast.While):
    result: str = "while " + transpile_expression(node.test) + " do\n";

    result = result + transpile_lines(node.body) + "\n";

    result = result + (node.col_offset-4) * " " + "end\n";

    return result;

def transpile_if(node: ast.If):
    result: str = (node.col_offset) * " " + "if " + transpile_expression(node.test) + " then\n";

    result = result + transpile_lines(node.body) + "\n";

    result = result + (node.col_offset) * " " + "else\n";

    result = result + (node.col_offset-4) * " " + transpile_lines(node.orelse) + "\n";

    result = result + (node.col_offset) * " " + "end\n";

    return result;

def transpile_boolop(node: ast.BoolOp):
    result: str = "";

    # Loop through the values
    for i in range(0, len(node.values)):
        value = node.values[i];
        result = result + transpile_expression(value);
        if i != len(node.values) - 1:
            result = result + " " + transpile_expression(node.op);

    return result;

def transpile_function(node: ast.FunctionDef):
    result: str;

    # Get the function name
    function_name = node.name;

    result = "function " + function_name + "(";

    # Loop through the arguments
    for i in range(0, len(node.args.args)):
        arg = node.args.args[i];
        result = result + arg.arg;
        if i != len(node.args.args) - 1:
            result = result + ", ";

    result = result + ")\n";

    result = result + transpile_lines(node.body);
    
    # Add end to the end of the function
    result = result + (node.col_offset-4) * " " + "\nend\n";

    return result;

def transpile_return(node: ast.Return):
    result: str = node.col_offset * " " + "return " + transpile_expression(node.value) + ";";

    return result;

def transpile_assign(node: ast.Assign):
    result: str = "";

    # Loop through the targets
    for i in range(0, len(node.targets)):
        target = node.targets[i];
        result = result + transpile_expression(target);
        if i != len(node.targets) - 1:
            result = result + ", ";

    return result

def transpile_for(node: ast.For):
    result: str = "";

    result = result + transpile_lines(node.body) + "\n";

    result = result + (node.col_offset-4) * " " + "end\n";

    return result;

def transpile_compare(node: ast.Compare):
    result: str = "";

    # Loop through the expressions
    for i in range(0, len(node.ops)):
        op = node.ops[i];

        result = result + transpile_expression(node.left);

        if isinstance(op, ast.Eq):
            result = result + " == ";
        elif isinstance(op, ast.NotEq):
            result = result + " ~= ";
        elif isinstance(op, ast.Lt):
            result = result + " < ";
        elif isinstance(op, ast.LtE):
            result = result + " <= ";
        elif isinstance(op, ast.Gt):
            result = result + " > ";
        elif isinstance(op, ast.GtE):
            result = result + " >= ";
        elif isinstance(op, ast.Is):
            result = result + " == ";
        elif isinstance(op, ast.IsNot):
            result = result + " ~= ";
        elif isinstance(op, ast.In):
            result = result + " in "; # Probably not valid Lua
        elif isinstance(op, ast.NotIn):
            result = result + " not in "; # Probably not valid Lua
        
        result = result + transpile_expression(node.comparators[i]);

    return result;

def transpile_unaryop(node: ast.UnaryOp):
    result: str = "";

    # Check the operator
    if isinstance(node.op, ast.UAdd):
        result = result + "+";
    elif isinstance(node.op, ast.USub):
        result = result + "-";
    elif isinstance(node.op, ast.Not):
        result = result + "not ";
    elif isinstance(node.op, ast.Invert):
        result = result + "not ";

    result = result + transpile_expression(node.operand);

    return result;

def transpile_list(node: ast.List):
    result: str = "";

    # Loop through the expressions
    for i in range(0, len(node.elts)):
        elt = node.elts[i];
        result = result + transpile_expression(elt);
        if i != len(node.elts) - 1:
            result = result + ", ";

    return result;

def transpile_lamba(node: ast.Lambda):
    result: str = "";

    # Header
    result = result + "function (";

    # Loop through the arguments
    for i in range(0, len(node.args.args)):
        arg = node.args.args[i];
        result = result + arg.arg;
        if i != len(node.args.args) - 1:
            result = result + ", ";

    result = result + ")";
    result = result + transpile_lines(node.body);

    return result;

def transpile_binop(node: ast.BinOp):
    # BinOp(expr left, operator op, expr right)
    result = "";
    
    result = result + transpile_expression(node.left);

    result = result + transpile_operator(node.op);

    result = result + transpile_expression(node.right);

    return result;

# Selector function
def transpile_expression(expression: ast.Expr | ast.expr) -> str:
    # BoolOp
    if isinstance(expression, ast.BoolOp):
        return transpile_boolop(expression);

    # NamedExpr
    if isinstance(expression, ast.NamedExpr):
        return expression.name + " = " + transpile_expression(expression.value);

    # BinOp
    if isinstance(expression, ast.BinOp):
        return transpile_binop(expression);

    # UnaryOp
    if isinstance(expression, ast.UnaryOp):
        return transpile_unaryop(expression.op);
    
    # Lambda
    if isinstance(expression, ast.Lambda):
        return transpile_lamba(expression);

    # IfExp (should be a separate function)
    if isinstance(expression, ast.IfExp):
        return transpile_expression(expression.test) + " ? " + transpile_expression(expression.body) + " : " + transpile_expression(expression.orelse);

    # Dict (should be a separate function)
    if isinstance(expression, ast.Dict):
        result = "{";
        for i in range(0, len(expression.keys)):
            key = expression.keys[i];
            value = expression.values[i];
            result = result + transpile_expression(key) + ": " + transpile_expression(value);
            if i != len(expression.keys) - 1:
                result = result + ", ";
        result = result + "}";
        return result

    # Set (should be a separate function)
    if isinstance(expression, ast.Set):
        result = "{";
        for i in range(0, len(expression.elts)):
            elt = expression.elts[i];
            result = result + transpile_expression(elt);
            if i != len(expression.elts) - 1:
                result = result + ", ";
        result = result + "}";
        return result

    # Await (wtf is the equivalent in lua?)
    if isinstance(expression, ast.Await):
        return transpile_expression(expression.value);

    # Compare
    if isinstance(expression, ast.Compare):
        return transpile_compare(expression);

    # List
    if isinstance(expression, ast.List):
        return transpile_list(expression)
    
    # Call
    if isinstance(expression, ast.Call):
        return transpile_call(expression);

    # Name
    if isinstance(expression, ast.Name):
        return expression.id;

    if isinstance(expression, ast.Num):
        return str(expression.n);

    if isinstance(expression, ast.Str):
        return str(expression.s);

    if isinstance(expression, ast.UnaryOp):
        return transpile_expression(expression.op) + " " + transpile_expression(expression.operand);

    if isinstance(expression, ast.Expr):
        return transpile_expression(expression.value);

    print("Warning: unknown expression " + expression.__class__.__name__);
    exit();

# Selector function
def transpile_statement(statement: ast.stmt | list[ast.stmt]) -> str:
    result: str = ""

    # If the statement is a FunctionDef
    if isinstance(statement, ast.FunctionDef):
        return transpile_function(statement);

    # If the statement is a If
    if isinstance(statement, ast.If):
        return transpile_if(statement);

    # If the statement is a Return
    if isinstance(statement, ast.Return):
        return transpile_return(statement);

    # If the statement is a While
    if isinstance(statement, ast.While):
        return transpile_while(statement);

    # If the statement is an Assign
    if isinstance(statement, ast.Assign):
        return transpile_assign(statement);

    # If the statement is a For
    if isinstance(statement, ast.For):
        return transpile_for(statement);

    print("Warning: unknown statement " + statement.__class__.__name__)
    exit();

# Selector function
def transpile_operator(operator: ast.operator) -> str:
    # Check the operator
    if isinstance(operator, ast.Add):
        return "+";

    if isinstance(operator, ast.Sub):
        return "-";

    if isinstance(operator, ast.Mult):
        return "*";

    if isinstance(operator, ast.Div):
        return "/";

    if isinstance(operator, ast.Mod):
        return "%";

    if isinstance(operator, ast.Pow):
        return "^";
    
    print("Warning: Unknown operator " + operator.__class__.__name__);
    exit();

def transpile_lines(node: list[ast.expr | ast.Expr | ast.stmt | ast.operator]) -> str:
    # If statement is a list of statements/expressions
    result: str = "";

    if node.__class__.__name__ != "list":
        return result;

    for i in range(0, len(node)):
        result = result + transpile_line(node[i]);

    return result;

# Selector function
def transpile_line(node: ast.Expr | ast.expr | ast.stmt) -> str:
    # Check if statement or expression
    if isinstance(node, ast.Expr) or isinstance(node, ast.expr):
        return transpile_expression(node);

    if isinstance(node, ast.stmt):
        return transpile_statement(node);

    if isinstance(node, ast.operator):
        return transpile_operator(node);

    print("Warning: unknown node " + node.__class__.__name__ + " which inherits from " + node.__class__.__bases__[0].__name__);
    exit();