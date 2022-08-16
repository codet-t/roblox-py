import ast
from typing_extensions import Self

# Refer to:
# https://docs.python.org/3/library/ast.html#abstract-grammar

toggle_ast = False;
toggle_line_of_code = False;
toggle_block_ids = False;

# Keep track of every block

class CodeBlock:
    def __init__(self, block_id: str, type: str, variables: list[str], children: list[Self], parent: Self | None = None):
        self.block_id: str = block_id;
        self.type: str = type;
        self.variables: str = variables;
        self.children: list[Self] = children;
        self.parent: Self | None = parent;

    def get_function(self) -> Self:
        if self.parent is None: return self;

        ancestor = self.parent;

        while ancestor.block_id != "0" and ancestor.type != "function":
            ancestor = ancestor.parent

        return ancestor;

    def add_variable(self, variable: str) -> Self:
        parent_function = self.get_function();

        if variable in parent_function.variables: return False;

        parent_function.variables.append(variable);
        return True;

    def add_child(self, type: str) -> Self: # Preferred over __init__
        # New id is the self.block_id + "." + the next available int
        new_id = self.block_id + "." + str(len(self.children));

        # Create a new block
        new_block = CodeBlock(new_id, type, [], [], self);

        # Add the new block to the children of the current block
        self.children.append(new_block);

        return new_block;

top_block = CodeBlock("0", "top", [], []);

def initialise_string(node: any, block: CodeBlock) -> str:
    result = "";

    if toggle_ast:
        result = result + "--[[" + node.__class__.__name__ + "]]"

    if toggle_block_ids:
        result = result + "--[[ BlockId: " + block["block_id"] + "]]";
    
    return result;

def transpile_call(node: ast.Call, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + transpile_expression(node.func, block) + "(";

    # Loop through the arguments
    for i in range(0, len(node.args)):
        arg = node.args[i];
        result = result + transpile_expression(arg, block);

        if i != len(node.args) - 1:
            result = result + ", ";
    
    result = result + ")";
            
    return result;

def transpile_while(node: ast.While, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "while " + transpile_expression(node.test, block) + " do\n";

    result = result + transpile_lines(node.body, block.add_child("while"));

    result = result + (node.col_offset) * " " + "end";

    return result;

def transpile_if(node: ast.If, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "if " + transpile_expression(node.test, block) + " then\n";

    result = result + transpile_lines(node.body, block.add_child("if"));

    result = result + (node.col_offset) * " " + "else\n";

    result = result + transpile_lines(node.orelse, block.add_child("else"));

    result = result + (node.col_offset) * " " + "end\n";

    return result;

def transpile_function(node: ast.FunctionDef, block: CodeBlock) -> str:
    result = initialise_string(node, block)

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

    result = result + transpile_lines(node.body, block.add_child("function"));
    
    # Add end to the end of the function
    result = result + (node.col_offset-4) * " " + "end\n";

    return result;

def transpile_boolop(node: ast.BoolOp, block: CodeBlock):
    result = initialise_string(node, block);

    # Loop through the values
    for i in range(0, len(node.values)):
        value = node.values[i];
        result = result + transpile_expression(value);
        if i != len(node.values) - 1:
            result = result + " " + transpile_expression(node.op);

    return result;

def transpile_return(node: ast.Return, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "return " + transpile_expression(node.value, block);

    return result;

def transpile_assign(node: ast.Assign, block: CodeBlock) -> str:

    result = initialise_string(node, block)

    # Check if assignment is new (i.e check if we have to append "local" in front of the variable)

    # Get targets as array
    targets = [];
    added = False;

    for i in range(0, len(node.targets)):
        node_target = node.targets[i]
        target = transpile_expression(node_target, block)
        targets.append(target);
        
        if not isinstance(node_target, ast.Name): continue;
        if block.add_variable(target):
            added = True;

    if added:
        result = result + "local ";

    # Assigns a variable to a value

    # Loop through the targets
    for i in range(0, len(targets)):
        target = targets[i];
        result = result + target
        if i != len(node.targets) - 1:
            result = result + ", ";

    result = result + " = ";

    result = result + transpile_expression(node.value, block);

    return result

def transpile_listcomp(node: ast.ListComp, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "(function()\n";

    result = result + (node.col_offset-4) * " " + "local result = {};\n";

    # Loop through the generators
    for i in range(0, len(node.generators)):
        generator = node.generators[i];
        target = transpile_expression(generator.target, block);
        iter = transpile_expression(generator.iter, block);
        ifs = generator.ifs;

        result = result + (node.col_offset-4) * " " + "for k, " + target
        result = result + " in pairs(" + iter + ") do\n";

        if len(ifs) == 0:
            result = result + (node.col_offset) * " " + "result[k] = " + transpile_expression(node.elt, block) + ";\n";
        else:
            for j in range(0, len(ifs)):
                if_ = ifs[j];
                result = result + (node.col_offset) * " " + "if " + transpile_expression(if_.test, block) + " then\n";
                result = result + (node.col_offset+4) * " " + "result[k] = " + target + ";\n";
                result = result + (node.col_offset) * " " + "end\n";
            
        result = result + (node.col_offset-4) * " " + "end\n";

    result = result + (node.col_offset-4) * " " + "return result;\n";

    result = result + (node.col_offset-8) * " " + "end)\n";

    return result;

def transpile_for(node: ast.For, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "for " + transpile_expression(node.target, block) + " in " + transpile_expression(node.iter, block) + " do\n";

    result = result + transpile_lines(node.body, block.add_child("for"));

    result = result + (node.col_offset) * " " + "end\n";

    return result;

def transpile_compare(node: ast.Compare, block: CodeBlock):
    result = initialise_string(node, block)

    # Loop through the expressions
    for i in range(0, len(node.ops)):
        op = node.ops[i];
        left = transpile_expression(node.left, block);
        comparator = transpile_expression(node.comparators[i], block);

        if isinstance(op, ast.Eq):
            result = result + left + " == " + comparator;
        elif isinstance(op, ast.NotEq):
            result = result + left + " ~= " + comparator;
        elif isinstance(op, ast.Lt):
            result = result + left + " < " + comparator;
        elif isinstance(op, ast.LtE):
            result = result + left + " <= " + comparator;
        elif isinstance(op, ast.Gt):
            result = result + left + " > " + comparator;
        elif isinstance(op, ast.GtE):
            result = result + left + " >= " + comparator;
        elif isinstance(op, ast.Is):
            result = result + left + " == " + comparator; # Probably wrong
        elif isinstance(op, ast.IsNot):
            result = result + left + " ~= " + comparator; # Probably wrong
        elif isinstance(op, ast.In):
            result = result + "table.find("+comparator+"," + left+")"
        elif isinstance(op, ast.NotIn):
            result = result + "not " + "table.find("+comparator+"," + left+")"

    return result;

def transpile_unaryop(node: ast.UnaryOp, block: CodeBlock) -> str:
    result = initialise_string(node, block)

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

def transpile_list(node: ast.List, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    # Loop through the expressions
    for i in range(0, len(node.elts)):
        elt = node.elts[i];
        result = result + transpile_expression(elt, block);
        if i != len(node.elts) - 1:
            result = result + ", ";

    return result;

def transpile_lamba(node: ast.Lambda, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    # Header
    result = result + "function (";

    # Loop through the arguments
    for i in range(0, len(node.args.args)):
        arg = node.args.args[i];
        result = result + arg.arg;
        if i != len(node.args.args) - 1:
            result = result + ", ";

    result = result + ")";
    result = result + transpile_lines(node.body, block.add_child("lambda"));

    return result;

def transpile_binop(node: ast.BinOp, block: CodeBlock) -> str:
    # BinOp(expr left, operator op, expr right)
    result = initialise_string(node, block)
    
    result = result + transpile_expression(node.left, block);

    result = result + transpile_operator(node.op, block);

    result = result + transpile_expression(node.right, block);

    return result;

def transpile_yield(node: ast.Yield, block: CodeBlock):
    result = initialise_string(node, block)

    result = result + "yield[#yield] = " + transpile_expression(node.value, block);

    return result;

def transpile_subscript(node: ast.Subscript, block: CodeBlock):
    result = initialise_string(node, block)

    # Build the subscript in lua {} notation
    result = result + transpile_expression(node.value, block);
    result = result + "[";
    result = result + transpile_expression(node.slice, block);
    result = result + "]";

    return result;

def transpile_delete(node: ast.Delete, block: CodeBlock):
    result = initialise_string(node, block)

    # Loop through the targets and add " = nil" after it
    for i in range(0, len(node.targets)):
        target = node.targets[i];

        result = result + transpile_expression(target, block);

        if i != len(node.targets) - 1:
            result = result + ", ";

        result = result + " = nil";

    return result;

def transpile_augassign(node: ast.AugAssign, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    # x += 1
    # x = x + 1
    # target = target op value

    target = transpile_expression(node.target, block)
    op = transpile_operator(node.op, block)
    value = transpile_expression(node.value, block)

    result = target + " = " + target + " " + op + " " + value;

    return result;

def transpile_comprehension(node: ast.comprehension, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    # [i for i in p]

    target = transpile_expression(node.target, block)
    iter = transpile_expression(node.iter, block)

    result = result + "for "
    result = result + target
    result = result + " in "
    result = result + iter

    if len(node.ifs) > 0:
        result = result + " if "
        result = result + transpile_expressions(node.ifs, block)

    return result;

def transpile_attribute(node: ast.Attribute, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + transpile_expression(node.value, block);
    result = result + "." + node.attr;

    return result;

def transpile_dict(node: ast.Dict, block: CodeBlock) -> str:
    result = initialise_string(node, block)

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

def transpile_name(node: ast.Name, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + node.id;

    return result;

def transpile_string(node: ast.Str, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "\"" + node.s + "\"";

    return result;

def transpile_set(node: ast.Set, block: CodeBlock) -> str:
    result = initialise_string(node, block)

    result = result + "{";

    # Loop through the expressions
    for i in range(0, len(node.elts)):
        elt = node.elts[i];
        result = result + transpile_expression(elt, block);
        if i != len(node.elts) - 1:
            result = result + ", ";

    result = result + "}";

    return result;

# Selector function
def transpile_expression(expression: ast.Expr | ast.expr, block: CodeBlock) -> str:
    # BoolOp
    if isinstance(expression, ast.BoolOp):
        return transpile_boolop(expression, block);

    # NamedExpr (probably needs to be a separate function)
    if isinstance(expression, ast.NamedExpr):
        return expression.name + " = " + transpile_expression(expression.value, block);

    # BinOp
    if isinstance(expression, ast.BinOp):
        return transpile_binop(expression, block);

    # UnaryOp
    if isinstance(expression, ast.UnaryOp):
        return transpile_unaryop(expression.op, block);
    
    # Lambda
    if isinstance(expression, ast.Lambda):
        return transpile_lamba(expression, block);

    # IfExp (should be a separate function)
    if isinstance(expression, ast.IfExp):
        return transpile_expression(expression.test, block) + " ? " + transpile_expression(expression.body, block) + " : " + transpile_expression(expression.orelse, block);

    # Dict (should be a separate function)
    if isinstance(expression, ast.Dict):
        return transpile_dict(expression, block);

    # Set (should be a separate function)
    if isinstance(expression, ast.Set):
        return transpile_set(expression, block);

    # Await (what is the equivalent in lua?)
    if isinstance(expression, ast.Await):
        return transpile_expression(expression.value, block);

    # Yield (what is the equivalent in lua?)
    if isinstance(expression, ast.Yield):
        return transpile_yield(expression, block);

    # Subscript
    if isinstance(expression, ast.Subscript):
        return transpile_subscript(expression, block);

    # Compare
    if isinstance(expression, ast.Compare):
        return transpile_compare(expression, block);

    # List
    if isinstance(expression, ast.List):
        return transpile_list(expression, block);

    # ListComp
    if isinstance(expression, ast.ListComp):
        return transpile_listcomp(expression, block);

    # comprehension
    if isinstance(expression, ast.comprehension):
        return transpile_comprehension(expression, block);

    # Attribute
    if isinstance(expression, ast.Attribute):
        return transpile_attribute(expression, block);
    
    # Call
    if isinstance(expression, ast.Call):
        return transpile_call(expression, block);

    # Name
    if isinstance(expression, ast.Name):
        return transpile_name(expression, block);

    # Num (should be a separate function)
    if isinstance(expression, ast.Num):
        return str(expression.n);

    # Str
    if isinstance(expression, ast.Str):
        return transpile_string(expression, block);

    # Expr
    if isinstance(expression, ast.Expr):
        return transpile_expression(expression.value, block);

    print("Warning: unknown expression " + expression.__class__.__name__);
    exit();

# Selector function
def transpile_statement(statement: ast.stmt | list[ast.stmt], block: CodeBlock) -> str:
    # If the statement is a FunctionDef
    if isinstance(statement, ast.FunctionDef):
        return transpile_function(statement, block);

    # If the statement is a If
    if isinstance(statement, ast.If):
        return transpile_if(statement, block);

    # Return
    if isinstance(statement, ast.Return):
        return transpile_return(statement, block);

    # Delete
    if isinstance(statement, ast.Delete):
        return transpile_delete(statement, block);

    # While
    if isinstance(statement, ast.While):
        return transpile_while(statement, block);

    # Assign
    if isinstance(statement, ast.Assign):
        return transpile_assign(statement, block);

    # AugAssign
    if isinstance(statement, ast.AugAssign):
        return transpile_augassign(statement, block);

    # For
    if isinstance(statement, ast.For):
        return transpile_for(statement, block);

    # Expr
    if isinstance(statement, ast.Expr):
        return transpile_expression(statement.value, block);

    print("Warning: unknown statement " + statement.__class__.__name__)
    exit();

# Selector function
def transpile_operator(operator: ast.operator, block: CodeBlock) -> str:
    result = initialise_string(operator, block)

    # Check the operator
    if isinstance(operator, ast.Add):
        return result + "+";

    if isinstance(operator, ast.Sub):
        return result + "-";

    if isinstance(operator, ast.Mult):
        return result + "*";

    if isinstance(operator, ast.Div):
        return result + "/";

    if isinstance(operator, ast.Mod):
        return result + "%";

    if isinstance(operator, ast.Pow):
        return result + "^";
    
    print("Warning: Unknown operator " + operator.__class__.__name__);
    exit();

def transpile_statements(statements: list[ast.stmt], block: CodeBlock) -> str:
    result = "";

    for statement in statements:
        result = result + transpile_statement(statement, block);

    return result;

def transpile_expressions(expressions: list[ast.expr], block: CodeBlock) -> str:
    result = "";

    for expression in expressions:
        result = result + transpile_expression(expression, block);

    return result;

# Selector function
def transpile_line(node: ast.Expr | ast.expr | ast.stmt, block: CodeBlock) -> str:
    # Check if statement or expression
    result = "";

    if isinstance(node, ast.Expr) or isinstance(node, ast.expr):
        result = transpile_expression(node, block);

    if isinstance(node, ast.stmt):
        result = transpile_statement(node, block);

    if isinstance(node, ast.operator):
        result = transpile_operator(node, block);

    if result == "":
        print("Warning: unknown node " + node.__class__.__name__ + " which inherits from " + node.__class__.__bases__[0].__name__);
        exit();

    return (
        node.col_offset * " " + result + 
        ( (" -- Line " + str(node.lineno) + "\n") if toggle_line_of_code else "\n" )
    );

def transpile_lines(node: list[ast.expr | ast.Expr | ast.stmt | ast.operator], block: CodeBlock) -> str:
    # If statement is a list of statements/expressions
    result: str = "";

    if node.__class__.__name__ != "list":
        return result;

    for i in range(0, len(node)):
        result = result + transpile_line(node[i], block);

    return result;

def transpile_module(module: ast.Module) -> str:
    global top_block
    result = transpile_lines(module.body, top_block);

    # Reset top block
    top_block = CodeBlock("0", "module", [], []);

    return result