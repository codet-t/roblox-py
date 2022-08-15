import ast
from os import stat

# Refer to:
# https://docs.python.org/3/library/ast.html#abstract-grammar

true = True
false = False

toggle_ast = true;
toggle_line_of_code = false;

def initialise_string(node: any) -> str:
    return "--[[" + node.__class__.__name__ + "]]" if toggle_ast else "";

def transpile_call(node: ast.Call):
    result = initialise_string(node)

    result = result + transpile_expression(node.func);

    result = result + "(";

    # Loop through the arguments
    for i in range(0, len(node.args)):
        arg = node.args[i];
        result = result + transpile_expression(arg);

        if i != len(node.args) - 1:
            result = result + ", ";
    
    result = result + ")";
            
    return result;

def transpile_while(node: ast.While):
    result = initialise_string(node)

    result = result + "while " + transpile_expression(node.test) + " do\n";

    result = result + transpile_lines(node.body);

    result = result + (node.col_offset) * " " + "end";

    return result;

def transpile_if(node: ast.If):
    result = initialise_string(node)

    result = result + "if " + transpile_expression(node.test) + " then\n";

    result = result + transpile_lines(node.body);

    result = result + (node.col_offset) * " " + "else\n";

    result = result + transpile_lines(node.orelse);

    return result;

def transpile_boolop(node: ast.BoolOp):
    result = initialise_string(node)

    # Loop through the values
    for i in range(0, len(node.values)):
        value = node.values[i];
        result = result + transpile_expression(value);
        if i != len(node.values) - 1:
            result = result + " " + transpile_expression(node.op);

    return result;

def transpile_function(node: ast.FunctionDef):
    result = initialise_string(node)

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
    result = result + (node.col_offset-4) * " " + "end\n";

    return result;

def transpile_return(node: ast.Return):
    result = initialise_string(node)

    result = result + "return " + transpile_expression(node.value);

    return result;

def transpile_assign(node: ast.Assign):
    result = initialise_string(node)

    # Assigns a variable to a value

    # Loop through the targets
    for i in range(0, len(node.targets)):
        target = node.targets[i];
        result = result + transpile_expression(target);
        if i != len(node.targets) - 1:
            result = result + ", ";

    result = result + " = ";

    result = result + transpile_expression(node.value);

    return result

def transpile_listcomp(node: ast.ListComp):
    result = initialise_string(node)

    print()

    result = result + "(function()\n";

    result = result + (node.col_offset-4) * " " + "local result = {};\n";

    # Loop through the generators
    for i in range(0, len(node.generators)):
        generator = node.generators[i];
        target = transpile_expression(generator.target);
        iter = transpile_expression(generator.iter);
        print(target, iter)
        ifs = generator.ifs;

        result = result + (node.col_offset-4) * " " + "for k, " + target
        result = result + " in pairs(" + iter + ") do\n";

        if len(ifs) == 0:
            result = result + (node.col_offset) * " " + "result[k] = " + transpile_expression(node.elt) + ";\n";
        else:
            for j in range(0, len(ifs)):
                if_ = ifs[j];
                result = result + (node.col_offset) * " " + "if " + transpile_expression(if_.test) + " then\n";
                result = result + (node.col_offset+4) * " " + "result[k] = " + target + ";\n";
                result = result + (node.col_offset) * " " + "end\n";
            
        result = result + (node.col_offset-4) * " " + "end\n";

    result = result + (node.col_offset-4) * " " + "return result;\n";

    result = result + (node.col_offset-8) * " " + "end)\n";

    return result;

def transpile_for(node: ast.For):
    result = initialise_string(node)

    result = result + transpile_lines(node.body);

    result = result + (node.col_offset-4) * " " + "end\n";

    return result;

def transpile_compare(node: ast.Compare):
    result = initialise_string(node)

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
    result = initialise_string(node)

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
    result = initialise_string(node)

    # Loop through the expressions
    for i in range(0, len(node.elts)):
        elt = node.elts[i];
        result = result + transpile_expression(elt);
        if i != len(node.elts) - 1:
            result = result + ", ";

    return result;

def transpile_lamba(node: ast.Lambda):
    result = initialise_string(node)

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
    result = initialise_string(node)
    
    result = result + transpile_expression(node.left);

    result = result + transpile_operator(node.op);

    result = result + transpile_expression(node.right);

    return result;

def transpile_yield(node: ast.Yield):
    result = initialise_string(node)

    result = result + "yield[#yield] = " + transpile_expression(node.value);

    return result;

def transpile_subscript(node: ast.Subscript):
    result = initialise_string(node)

    # Build the subscript in lua {} notation
    result = result + "{";
    result = result + transpile_expression(node.value);
    result = result + "}[";
    result = result + transpile_expression(node.slice);
    result = result + "]";

    return result;

def transpile_delete(node: ast.Delete):
    result = initialise_string(node)

    # Loop through the targets and add " = nil" after it
    for i in range(0, len(node.targets)):
        target = node.targets[i];

        result = result + transpile_expression(target);

        if i != len(node.targets) - 1:
            result = result + ", ";

        result = result + " = nil";

    return result;

def transpile_augassign(node: ast.AugAssign):
    result = initialise_string(node)

    # x += 1
    # x = x + 1
    # target = target op value

    target = transpile_expression(node.target)
    op = transpile_operator(node.op)
    value = transpile_expression(node.value)

    result = target + " = " + target + " " + op + " " + value;

    return result;

def transpile_comprehension(node: ast.comprehension):
    result = initialise_string(node)

    # [i for i in p]

    target = transpile_expression(node.target)
    iter = transpile_expression(node.iter)

    print(target, iter)

    result = result + "for "
    result = result + target
    result = result + " in "
    result = result + iter

    if len(node.ifs) > 0:
        result = result + " if "
        result = result + transpile_expressions(node.ifs)

    return result;

def transpile_attribute(node: ast.Attribute):
    result = initialise_string(node)

    result = result + transpile_expression(node.value);
    result = result + "." + node.attr;

    return result;

def transpile_dict(node: ast.Dict):
    result = initialise_string(node)

    result = result + "{";

    # Loop through the keys and values
    for i in range(0, len(node.keys)):
        key = node.keys[i];
        value = node.values[i];
        result = result + transpile_expression(key);
        result = result + " = ";
        result = result + transpile_expression(value);
        if i != len(node.keys) - 1:
            result = result + ", ";
    
    result = result + "}";

    return result;

def transpile_name(node: ast.Name):
    result = initialise_string(node)

    result = result + node.id;

    return result;

def transpile_string(node: ast.Str):
    result = initialise_string(node)

    result = result + "\"" + node.s + "\"";

    return result;

def transpile_set(node: ast.Set):
    result = initialise_string(node)

    result = result + "{";

    # Loop through the expressions
    for i in range(0, len(node.elts)):
        elt = node.elts[i];
        result = result + transpile_expression(elt);
        if i != len(node.elts) - 1:
            result = result + ", ";

    result = result + "}";

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
        return transpile_dict(expression);

    # Set (should be a separate function)
    if isinstance(expression, ast.Set):
        return transpile_set(expression);

    # Await (what is the equivalent in lua?)
    if isinstance(expression, ast.Await):
        return transpile_expression(expression.value);

    # Yield (what is the equivalent in lua?)
    if isinstance(expression, ast.Yield):
        return transpile_yield(expression);

    # Subscript
    if isinstance(expression, ast.Subscript):
        return transpile_subscript(expression);

    # Compare
    if isinstance(expression, ast.Compare):
        return transpile_compare(expression);

    # List
    if isinstance(expression, ast.List):
        return transpile_list(expression);

    # ListComp
    if isinstance(expression, ast.ListComp):
        return transpile_listcomp(expression);

    # comprehension
    if isinstance(expression, ast.comprehension):
        return transpile_comprehension(expression);

    # Attribute
    if isinstance(expression, ast.Attribute):
        return transpile_attribute(expression);
    
    # Call
    if isinstance(expression, ast.Call):
        return transpile_call(expression);

    # Name
    if isinstance(expression, ast.Name):
        return transpile_name(expression);

    # Num
    if isinstance(expression, ast.Num):
        return str(expression.n);

    # Str
    if isinstance(expression, ast.Str):
        return transpile_string(expression);

    if isinstance(expression, ast.UnaryOp):
        return transpile_expression(expression.op) + " " + transpile_expression(expression.operand);

    if isinstance(expression, ast.Expr):
        return transpile_expression(expression.value);

    print("Warning: unknown expression " + expression.__class__.__name__);
    exit();

# Selector function
def transpile_statement(statement: ast.stmt | list[ast.stmt]) -> str:
    # If the statement is a FunctionDef
    if isinstance(statement, ast.FunctionDef):
        return transpile_function(statement);

    # If the statement is a If
    if isinstance(statement, ast.If):
        return transpile_if(statement);

    # Return
    if isinstance(statement, ast.Return):
        return transpile_return(statement);

    # Delete
    if isinstance(statement, ast.Delete):
        return transpile_delete(statement);

    # While
    if isinstance(statement, ast.While):
        return transpile_while(statement);

    # Assign
    if isinstance(statement, ast.Assign):
        return transpile_assign(statement);

    # AugAssign
    if isinstance(statement, ast.AugAssign):
        return transpile_augassign(statement);

    # For
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

def transpile_statements(statements: list[ast.stmt]) -> str:
    result = "";

    for statement in statements:
        result = result + transpile_statement(statement);

    return result;

def transpile_expressions(expressions: list[ast.expr]) -> str:
    result = "";

    for expression in expressions:
        result = result + transpile_expression(expression);

    return result;

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
        return node.col_offset * " " + transpile_expression(node) + ( (" -- Line " + str(node.lineno) + "\n") if toggle_line_of_code else "\n");

    if isinstance(node, ast.stmt):
        return node.col_offset * " " + transpile_statement(node)  + ( (" -- Line " + str(node.lineno) + "\n") if toggle_line_of_code else "\n");

    if isinstance(node, ast.operator):
        return node.col_offset * " " + transpile_operator(node)   + ( (" -- Line " + str(node.lineno) + "\n") if toggle_line_of_code else "\n");

    print("Warning: unknown node " + node.__class__.__name__ + " which inherits from " + node.__class__.__bases__[0].__name__);
    exit();