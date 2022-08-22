from typing_extensions import Self
from . import lua_ast_nodes as lua_ast;

class Scope:
    def __init__(self, scope_id: str, type: str, variables: list[str], children: list[Self], parent: Self | None = None):
        self.scope_id = scope_id;
        self.type = type;
        self.variables = variables;
        self.children = [];
        self.parent = parent;
        self.line = "";
        self.deep_variables = [];
        self.options = [];

    def get_function(self) -> Self:
        if self.parent is None: return self;

        if self.type == "function": return self;

        ancestor = self.parent;

        while ancestor.scope_id != "0" and ancestor.type != "function":
            ancestor = ancestor.parent

        return ancestor;

    def add_variable(self, variable: str) -> None | str: # "surface" | "deep"
        function_scope = self.get_function();
        
        if variable in function_scope.variables or variable in function_scope.deep_variables: return None;

        if function_scope == self:
            function_scope.variables.append(variable);
            return "surface"
        else:
            function_scope.deep_variables.append(variable);
            return "deep"

    def add_child(self, type: str, function_node: lua_ast.FunctionNode | None = None) -> Self: # Preferred over __init__
        # New id is the self.scope_id + "." + the next available int
        new_id = self.scope_id + "." + str(len(self.children));

        # Create a new scope
        new_scope = Scope(new_id, type, [], [], self);

        # If node is not None, set the node of the scope
        if function_node is not None: new_scope.node = function_node;

        # Add the new scope to the children of the current scope
        self.children.append(new_scope);

        return new_scope;
    
    def get_offset(self, relative_offset: int = 0) -> str:
        # Get amount of periods in the scope_id
        # Multiply " " by this amount
        level = len(self.scope_id.split(".")) - 1 + relative_offset

        # kirby = ["(>'-')>","<('-'<)","^('-')^","v('-')v","(>'-')>","(^-^)"]; 
        # return "--[[" + " ".join(kirby[i % len(kirby)] for i in range(level)) + "]]"
        
        spaces = 1;
        char = "\t";

        offset = level * spaces * char;

        return offset

    def get_top_scope(self) -> Self:
        if self.parent is None: return self;

        ancestor = self.parent;

        while ancestor.scope_id != "0":
            ancestor = ancestor.parent

        return ancestor;