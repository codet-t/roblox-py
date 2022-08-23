from typing import List
from typing_extensions import Self
from . import lua_ast_nodes as lua_ast;

class Scope:
    def __init__(self, scope_id: str, type: str, variables: List[str], children: List[Self], parent: Self | None = None):
        self.scope_id = scope_id;
        self.type = type;
        self.variables = variables;
        self.children = [];
        self.parent = parent;
        self.line = "";
        self.options = [];
        self.node = None;
        self.function = None;

    def get_function(self) -> Self:
        if self.type == "function": return self;

        if self.parent is None:
            return self;

        ancestor: Self = self.parent;

        while ancestor is not None and ancestor.scope_id != "0" and ancestor.type != "function":
            if ancestor.parent is None: 
                break
            else:
                ancestor = ancestor.parent;

        return ancestor;

    def add_variable(self, variable: str) -> None | str: # "surface" | "deep"
        function_scope = self.get_function();
        
        if variable in function_scope.variables: return None;

        if function_scope == self:
            function_scope.variables.append(variable);
            return "surface"

    def add_child(self, type: str, node: lua_ast.FunctionNode | lua_ast.IfNode) -> Self: # Preferred over __init__
        # New id is the self.scope_id + "." + the next available int
        children: List[Self] = self.children # type: ignore
        new_id = self.scope_id + "." + str(len(children));

        # Create a new scope
        new_scope = Scope(new_id, type, [], [], self);

        # If node is not None, set the node of the scope
        if node is not None: new_scope.node = node;

        # If node is FunctionNode, set the function of the scope
        if isinstance(node, lua_ast.FunctionNode): new_scope.function = node;

        # Add the new scope to the children of the current scope
        children.append(new_scope);
        self.children = children;

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
        if self.scope_id == "0": return self;

        if self.parent is None:
            return self;

        ancestor: Self = self.parent;

        while ancestor is not None and ancestor.scope_id != "0":
            if ancestor.parent is None: 
                break
            else:
                ancestor = ancestor.parent;

        return ancestor;