from typing import Dict, List

import ast as py_ast

from ..analysis.build_lua_ast import map_module, script_options
from ..lua_ast import lua_ast_nodes as lua_ast

options: Dict[str, bool] = {
    "toggle_ast": False,
    "toggle_scope_ids": False,
    "toggle_lines": False
}

builtin_attribute_functions = {
    "list": {
        "append": "ropy.append.list"
    },

    "dict": {
        "setdefault": "ropy.setdefault.dict",
    },

    "set": {
        "add": "ropy.add.set",
    }
}

builtin_functions: Dict[str, str | Dict[str, str]] = {
    "len": "ropy.len",
    "help": "",
    "range": "ropy.range",
    "table_dependent": {
        "set": "ropy.set",
        "all": "ropy.all",
        "slice": "ropy.slice"
    }
}

def initialise_string(node: lua_ast.Node) -> str:
    result: str = "";

    if options["toggle_ast"]:
        result = result + "--[[" + node.__class__.__name__ + "]]"

    if options["toggle_scope_ids"]:
        result = result + "--[[ ScopeId: " + node.scope.scope_id + ", ScopeNodeClass: " + node.scope.node.__class__.__name__ + " ]]";
    
    return result;

def compile_if(node: lua_ast.IfNode):
    result = initialise_string(node);

    result = result + "if " + compile_expression(node.condition) + " then\n";
    result = result + compile_lines(node.body);

    if len(node.elseifbody) > 0:
        for elseif in node.elseifbody:
            result = result + node.scope.get_offset() + "elseif " + compile_expression(elseif.condition) + " then\n";
            result = result + compile_lines(elseif.body);

            if len(elseif.elsebody) > 0:
                result = result + node.scope.get_offset() + "else\n";
                result = result + compile_lines(elseif.elsebody);

    if len(node.elsebody) > 0:
        result = result + node.scope.get_offset() + "else\n";
        result = result + compile_lines(node.elsebody);

    result = result + node.scope.get_offset() + "end";

    return result;

def compile_function(node: lua_ast.FunctionNode) -> str:
    result: str = initialise_string(node);

    result = result + "function"
    if node.name is None:
        result = result + "(";
    else:
        result = result + " " + node.name + "(";

    for arg in node.args:
        result = result + arg.identifier
        if arg != node.args[-1]:
            result = result + ", ";

    result = result + ")\n";

    if len(node.yields) > 0:
        # we have to do offset=1 because yield is technically part of the node itself
        result = result + node.scope.get_offset(1) + "local yield = {};\n";

    result = result + compile_lines(node.body);

    if len(node.yields) > 0:
        # TODO: Check if we aren't encroaching on an existing return,
        # if so, we just need to convert it to "table.insert(yield, return.value); return yield;"
        result = result + node.scope.get_offset(1) + "return yield;\n";
    
    result = result + node.scope.get_offset() + "end";
    
    if node.scope.scope_id == "0":
        result = result + "\n";

    return result;

def compile_name(name_node: lua_ast.NameNode) -> str:
    result = initialise_string(name_node);

    result = result + name_node.name;

    return result;

def compile_constant(constant_node: lua_ast.ConstantNode) -> str:
    result = initialise_string(constant_node);

    if constant_node.type == "string":
        if constant_node.value in script_options:
            result = result + "-- " + constant_node.value
        else:
            result = result + "\"" + constant_node.value + "\"";
    else:
        result = result + constant_node.value;

    return result;

def compile_compoperator(operator_node: lua_ast.CompareOperatorNode, left: lua_ast.ExpressionNode, right: lua_ast.ExpressionNode) -> str:
    result = initialise_string(operator_node);

    if operator_node.parenthesis:
        result = result + operator_node.operator
        result = result + "(";
        result = result + compile_expression(left);
        result = result + ", "
        result = result + compile_expression(right);
        result = result + ")";
    else:
        result = result + compile_expression(left);
        result = result + " " + operator_node.operator + " ";
        result = result + compile_expression(right);
    
    return result;

def compile_compare(compare_node: lua_ast.CompareNode) -> str:
    result = initialise_string(compare_node);

    # LEFT [OPERATOR] [COMPARATOR] [OPERATOR] [COMPARATOR]
    # 5    <          6            <          7
    # In Lua:
    # 5 < 6 and 6 < 7
    # i.e
    # Left < Comparator1 and Comparator1 < Comparator2
    # "<" is the operator in this case

    for i in range(0, len(compare_node.comparators)):
        op = compare_node.operators[i];
        comp = compare_node.comparators[i];
        last_comp = compare_node.left
        if i > 0:
            last_comp = compare_node.comparators[i - 1];

        result = result + compile_compoperator(op, last_comp, comp);

    return result;

def compile_return(return_node: lua_ast.ReturnNode) -> str:
    result = initialise_string(return_node);

    result = result + "return ";

    if return_node.value is not None:
        result = result + compile_expression(return_node.value);
    else:
        result = result + "nil";

    return result;

def compile_builtin_call(node: lua_ast.CallNode) -> str:
    if isinstance(node.value, lua_ast.NameNode):
        name = node.value.name;
    else:
        name = compile_expression(node.value);

    result = name;

    new_name = builtin_functions[name];

    if not isinstance(new_name, str):
        return "";

    result = new_name + "("

    for arg in node.args:
        result = result + compile_expression(arg)
        if arg != node.args[-1]:
            result = result + ", ";
        
    result = result + ")";

    return result;

def compile_table_dependent_builtin_call(node: lua_ast.CallNode) -> str:
    if isinstance(node.value, lua_ast.NameNode):
        name = node.value.name;
    else:
        name = compile_expression(node.value);

    new_name = builtin_functions[name];

    if not isinstance(new_name, str):
        return "";

    if len(node.args) > 0 and isinstance(node.args[0], lua_ast.TableNode):
        result = new_name + "." + node.args[0].type + "(";
    else:
        result = new_name + ".list(";

    for arg in node.args:
        result = result + compile_expression(arg);
        if arg != node.args[-1]:
            result = result + ", ";
    
    result = result + ")";

    return result;

def compile_regular_call(node: lua_ast.CallNode) -> str:
    if isinstance(node.value, lua_ast.NameNode):
        name = node.value.name;
    else:
        name = compile_expression(node.value);

    result = name;
    result = result + "(";

    for arg in node.args:
        result = result + compile_expression(arg);
        if arg != node.args[-1]:
            result = result + ", ";
    
    result = result + ")";

    return result;

def compile_help_call(node: lua_ast.CallNode) -> str:
    # Reformulate help(function) to function([nil, nil, nil... (depending on #args) ],"help")

    # Get actual function from func (so we can get args length)
    func: lua_ast.FunctionNode = node.scope.get_function().node;
    
    # Get amount of possible parameters
    num_args = len(func.args);

    # Check if func.name is possible
    if func.name is None:
        raise Exception("Tried to call help on an anonymous function");

    result = func.name + "(" + ", ".join(["nil"]) * num_args + ",\"help\"";

    # Replace only first instance of "help" with func.name
    result = result.replace("help", func.name, 1);

    result = result + ")";

    return result;

def compile_attributed_builtin_call(node: lua_ast.CallNode) -> str:
    if not isinstance(node.value, lua_ast.AttributeNode):
        raise Exception("Tried to call attributed builtin on non-attribute node");

    result = "";

    # See if node.value.value is a table
    if isinstance(node.value.attributed_to, lua_ast.TableNode):
        method_type = node.value.attributed_to.type
        methods = builtin_attribute_functions[method_type];

        if node.value.attribute not in methods:
            raise Exception("Tried to call attributed builtin (" + node.value.attribute + ") on unknown method");

        result = methods[node.value.attribute] + "(";
    elif isinstance(node.value.attributed_to, lua_ast.NameNode) or isinstance(node.value.attributed_to, lua_ast.CallNode):
        # Loop through all attributes in built_in_attributes
        for type in builtin_attribute_functions:
            # Loop through these
            for method in builtin_attribute_functions[type]:
                # Check if method == node.value.name
                if method == node.value.attribute:
                    result = builtin_attribute_functions[type][method] + "(";
    else: 
        raise Exception("Tried to call attributed builtin on unsupported node (" + node.value.attributed_to.__class__.__name__ + ")");

    result = result + compile_expression(node.value.attributed_to);

    if len(node.args) > 0:
        result = result + ", ";
        for arg in node.args:
            result = result + compile_expression(arg);
            if arg != node.args[-1]:
                result = result + ", ";

    result = result + ")";

    return result;

def compile_call(node: lua_ast.CallNode) -> str:
    result = initialise_string(node);

    if isinstance(node.value, lua_ast.NameNode):
        name = node.value.name;
    else:
        name = compile_expression(node.value);

    builtin: bool = (name in builtin_functions) or (name in builtin_functions["table_dependent"]);
    attribute: bool = isinstance(node.value, lua_ast.AttributeNode);
    
    if name == "help":
        return result + compile_help_call(node);
    elif attribute:
        return result + compile_attributed_builtin_call(node);
    elif builtin:
        if name in builtin_functions:
            return result + compile_builtin_call(node);
        else:
            return result + compile_table_dependent_builtin_call(node);
    else:
        return result + compile_regular_call(node);

def compile_subscript(subscript_node: lua_ast.SubscriptNode) -> str:
    result = initialise_string(subscript_node);

    if not hasattr(subscript_node.slice, "lower"):
        # Follow lua syntax: value + "[" + slice + "]"
        result = result + compile_expression(subscript_node.value);
        result = result + "[";
        result = result + compile_expression(subscript_node.slice);
        if not "@ropy:ignore_table_offset" in subscript_node.scope.options:
            result = result + " + 1";
        result = result + "]";
        return result;

    # ropy.slice.tuple(value, slice.lower or "nil", slice.upper or "nil", slice.step or "nil")
    if isinstance(subscript_node.value, lua_ast.TableNode):
        function_name = "ropy.slice." + subscript_node.value.type;
    else:
        function_name = "ropy.slice.list";

    result = result + function_name + "(";
    result = result + compile_expression(subscript_node.value);

    result = result + ", ";

    if hasattr(subscript_node.slice, "lower") and subscript_node.slice.lower is not None:
        result = result + compile_expression(subscript_node.slice.lower);
    else:
        result = result + "nil";

    result = result + ", ";

    if hasattr(subscript_node.slice, "upper") and subscript_node.slice.upper is not None:
        result = result + compile_expression(subscript_node.slice.upper);
    else:
        result = result + "nil";

    result = result + ", ";

    if hasattr(subscript_node.slice, "step") and subscript_node.slice.step is not None:
        result = result + compile_expression(subscript_node.slice.step);
    else:
        result = result + "nil";

    result = result + ")";

    return result;

def compile_binop(binop_node: lua_ast.BinOpNode) -> str:
    result = initialise_string(binop_node);

    parenthesis = binop_node.operator.parenthesis;

    if parenthesis:
        result = result + binop_node.operator.value + "(";
        result = result + compile_expression(binop_node.left);
        result = result + ", ";
        result = result + compile_expression(binop_node.right);
        result = result + ")";
    else:
        result = result + compile_expression(binop_node.left);
        result = result + " " + binop_node.operator.value + " ";
        result = result + compile_expression(binop_node.right);
    
    return result;

def compile_assignment(assignment_node: lua_ast.AssignmentNode) -> str:
    result = initialise_string(assignment_node);

    # Only one value is allowed in an assignment
    # But multiple targets...

    # Target1 = Value1; Target2 = Value1; Target3 = Value1; etc...
    value = compile_expression(assignment_node.value);

    function_scope = assignment_node.scope.get_function();

    for i in range(0, len(assignment_node.targets)):
        target = assignment_node.targets[i];
        if isinstance(target, lua_ast.NameNode):
            for v in function_scope.variables:
                if v.name == target.name and not v.administred:
                    result = result + "local ";
                    v.administred = True;
                    break;

        result = result + compile_expression(target);
        result = result + " = ";
        result = result + value

        if i < len(assignment_node.targets) - 1:
            result = result + "; ";
    
    return result;

def compile_table(table_node: lua_ast.TableNode) -> str:
    result = initialise_string(table_node);

    result = result + "{";
    for i in range(0, len(table_node.keys)):
        key = table_node.keys[i];
        value = table_node.values[i];
        # key = value
        result = result + "[" + compile_expression(key) + "] = ";
        result = result + compile_expression(value);
        if i < len(table_node.keys) - 1:
            result = result + ", ";
    result = result + "}";

    return result;

def compile_while(node: lua_ast.WhileNode) -> str:
    result = initialise_string(node);

    result = result + "while ";
    result = result + compile_expression(node.condition);
    result = result + " do\n";
    result = result + compile_lines(node.body);
    result = result + node.scope.get_offset() + "end";

    return result;

def compile_yield(yield_node: lua_ast.YieldNode) -> str:
    result = initialise_string(yield_node);

    value = "nil"

    if yield_node.value is not None:
        value = compile_expression(yield_node.value);

    result = result + "table.insert(yield, "
    result = result + value
    result = result + ")";

    return result;

def compile_for(node: lua_ast.ForNode) -> str:
    result = initialise_string(node);

    result = result + "for ";
    result = result + compile_expression(node.target);
    result = result + " in ";
    result = result + compile_expression(node.iterable);
    result = result + " do\n";
    result = result + compile_lines(node.body);
    result = result + node.scope.get_offset() + "end";

    return result;

def compile_attribute(attribute_node: lua_ast.AttributeNode) -> str:
    result = initialise_string(attribute_node);

    result = result + compile_expression(attribute_node.attributed_to);
    result = result + "." + attribute_node.attribute;
    
    return result;

def compile_delete(delete_node: lua_ast.DeleteNode) -> str:
    result = initialise_string(delete_node);

    # target1 = nil; target2 = nil; target3 = nil; etc...
    # or:
    # target1, target2, target3 = nil, nil, nil; etc...

    for i in range(0, len(delete_node.targets)):
        target = delete_node.targets[i];

        result = result + compile_expression(target);
        result = result + " = nil";
        if i < len(delete_node.targets) - 1:
            result = result + "; ";

    return result;

def compile_augmentedassignment(node: lua_ast.AugmentedAssignmentNode) -> str:
    result = initialise_string(node);

    parenthesis = node.operator.parenthesis;

    if parenthesis:
        result = result + node.operator.value + "(";
        result = result + compile_expression(node.target);
        result = result + ", ";
        result = result + compile_expression(node.value);
        result = result + ")";
    else:
        result = result + compile_expression(node.target);
        result = result + " = "
        result = result + compile_expression(node.target);
        result = result + " " + node.operator.value + " ";
        result = result + compile_expression(node.value);
    
    return result;

def compile_comprehensions(comprehensions_nodes: List[lua_ast.ComprehensionNode]) -> str:
    result = "";
    layers: int = 1;

    for i in range(0, len(comprehensions_nodes)):
        comprehension_node = comprehensions_nodes[i];

        result = result + initialise_string(comprehension_node);

        result = result + comprehension_node.scope.get_offset() + "(function()\n"
        result = result + comprehension_node.scope.get_offset(layers) + "local result = {}\n"
        result = result + comprehension_node.scope.get_offset(1) + "for k,"
        result = result + compile_expression(comprehension_node.target);
        result = result + " in pairs(";
        result = result + compile_expression(comprehension_node.iterable);
        result = result + ") do\n";

        layers += 1;

        length = len(comprehension_node.conditions);

        if length > 0:
            result = result + comprehension_node.scope.get_offset(layers) + "if ";

            if length == 1:
                result = result + compile_expression(comprehension_node.conditions[0]);
            else:
                result = result + "(";
                for j in range(0, length):
                    condition = comprehension_node.conditions[j];

                    result = result + "("
                    result = result + compile_expression(condition);
                    result = result + ")"
                    
                    # if not last, then "and";
                    if j < length - 1:
                        result = result + " and ";
                
                result = result + ")";

            result = result + " then\n";

            layers += 1;

        result = result + comprehension_node.scope.get_offset(layers) + "table.insert(result, ";
        result = result + compile_expression(comprehension_node.target);
        result = result + ")\n"
        result = result + comprehension_node.scope.get_offset(layers-1) + "end\n"
        result = result + comprehension_node.scope.get_offset(layers-1) + "return result\n"
        result = result + comprehension_node.scope.get_offset(layers-2) + "end)()\n"


        layers -= 1

    return result;

def compile_comprehension(comprehension_node: lua_ast.ComprehensionNode) -> str:
    result = initialise_string(comprehension_node);

    result = result + "for k,"
    result = result + compile_expression(comprehension_node.target);
    result = result + " in pairs(";
    result = result + compile_expression(comprehension_node.iterable);
    result = result + ") do\n";
    result = result + comprehension_node.scope.get_offset(1) + "local result = {}"

    if len(comprehension_node.conditions) == 0:
        result = result + comprehension_node.scope.get_offset(1) + "table.insert(result, " + compile_expression(comprehension_node.target) + ")";
    #else:
    for condition in comprehension_node.conditions:
        result = result + comprehension_node.scope.get_offset(1) + "if " + compile_expression(condition) + " then\n";
        
        result = result + comprehension_node.scope.get_offset(2) + "table.insert(result, " + compile_expression(comprehension_node.target) + ")";

        result = result + comprehension_node.scope.get_offset(1) + "end\n";

    result = result + comprehension_node.scope.get_offset() + "end\n";

    return result;

def compile_listcomp(listcomp_node: lua_ast.ListCompNode) -> str:
    result = initialise_string(listcomp_node);

    result = result + compile_comprehensions(listcomp_node.generators);

    return result;

def compile_statement(statement_node: lua_ast.StatementNode) -> str:
    if isinstance(statement_node, lua_ast.FunctionNode):
        return compile_function(statement_node);
    elif isinstance(statement_node, lua_ast.IfNode):
        return compile_if(statement_node)
    elif isinstance(statement_node, lua_ast.ReturnNode):
        return compile_return(statement_node)
    elif isinstance(statement_node, lua_ast.CallNode):
        return compile_call(statement_node)
    elif isinstance(statement_node, lua_ast.AssignmentNode):
        return compile_assignment(statement_node)
    elif isinstance(statement_node, lua_ast.WhileNode):
        return compile_while(statement_node)
    elif isinstance(statement_node, lua_ast.ForNode):
        return compile_for(statement_node)
    elif isinstance(statement_node, lua_ast.DeleteNode):
        return compile_delete(statement_node)
    elif isinstance(statement_node, lua_ast.AugmentedAssignmentNode):
        return compile_augmentedassignment(statement_node)

    raise Exception("Unknown statement node type during Lua AST -> Lua compilation " + str(type(statement_node)));

def compile_expression(expression_node: lua_ast.ExpressionNode) -> str:
    if isinstance(expression_node, lua_ast.NameNode):
        return compile_name(expression_node);
    elif isinstance(expression_node, lua_ast.CompareNode):
        return compile_compare(expression_node);
    elif isinstance(expression_node, lua_ast.ConstantNode):
        return compile_constant(expression_node);
    elif isinstance(expression_node, lua_ast.SubscriptNode):
        return compile_subscript(expression_node);
    elif isinstance(expression_node, lua_ast.BinOpNode):
        return compile_binop(expression_node);
    elif isinstance(expression_node, lua_ast.CallNode):
        return compile_call(expression_node);
    elif isinstance(expression_node, lua_ast.TableNode):
        return compile_table(expression_node);
    elif isinstance(expression_node, lua_ast.YieldNode):
        return compile_yield(expression_node);
    elif isinstance(expression_node, lua_ast.AttributeNode):
        return compile_attribute(expression_node);
    elif isinstance(expression_node, lua_ast.ListCompNode):
        return compile_listcomp(expression_node);
    
    raise Exception("Unknown expression node type during Lua AST -> Lua compilation " + str(type(expression_node)));

def compile_line(node: lua_ast.Node) -> str:
    result = "";

    if issubclass(type(node), lua_ast.StatementNode):
        result = result + compile_statement(node);  # type: ignore
    elif issubclass(type(node), lua_ast.ExpressionNode):
        result = result + compile_expression(node);  # type: ignore
    else:
        raise Exception("Unknown node type during Lua AST -> Lua compilation " + str(type(node)));

    result = node.scope.get_offset() + result;

    if options["toggle_lines"]:
        result = result + "--" + str(node.line_begin)
    
    result = result + "\n";

    return result;

def compile_lines(nodes: List[lua_ast.Node]) -> str:
    result = "";

    for node in nodes:
        result = result + compile_line(node);

    return result;

prefix = "-- Compiled with roblox-py:\n-- https://github.com/codetariat/roblox-py\n\nlocal ropy = require(game:FindFirstChild('ropy', true))\n\n"

def compile_module(module_node: py_ast.Module) -> str:
    compiled_module_node = map_module(module_node);

    result = prefix + compile_lines(compiled_module_node.body)

    # Check if last char is \n and remove it if it is
    if result[-1] == "\n":
        result = result[:-1]

    return result;