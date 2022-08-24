from typing import Any, List, Literal, TypedDict
from typing_extensions import Self
import ast as py_ast

class Scope:
    def __init__(self, scope_id: str,
                 node: Any):
        self.scope_id = scope_id;
        self.children: List[Self] = [];
        self.parent = None;
        self.node = node;
        self.function = None;

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

class LuaScope(Scope):
    def __init__(self,  scope_id: str,
                        node: Any,
                        parent: Self | None = None):
        from .lua_ast.lua_ast_nodes import Variable as LuaVariable;
        super().__init__(scope_id, node);
        self.options = [];
        self.variables: List[LuaVariable] = [];
        self.parent = parent;

    def get_function(self) -> Self:
        from .lua_ast.lua_ast_nodes import FunctionNode as LuaFunction;
        if isinstance(self.node, LuaFunction): return self;

        if self.parent is None:
            return self;

        ancestor: Self = self.parent;

        while ancestor is not None and ancestor.scope_id != "0" and isinstance(ancestor.node, LuaFunction):
            if ancestor.parent is None: 
                break
            else:
                ancestor = ancestor.parent;

        return ancestor;

    from .lua_ast.lua_ast_nodes import Variable as LuaVariable;

    def add_variable(self, variable: LuaVariable) -> None | Literal[True]:
        function_scope = self.get_function();
        
        # Make list of variable.names
        variable_names: List[str] = [];

        for k in self.variables:
            variable_names.append(k.name);

        if variable.name in variable_names: return None;

        if function_scope == self:
            variable.direct = True;
        
        function_scope.variables.append(variable);

        return True;

    def add_child(self, node: Any) -> Self: # Preferred over __init__
        from .lua_ast.lua_ast_nodes import FunctionNode as LuaFunction;
        # New id is the self.scope_id + "." + the next available int
        children: List[Self] = self.children # type: ignore
        new_id = self.scope_id + "." + str(len(children));

        # Create a new scope
        new_scope = LuaScope(new_id, node);

        # If node is not None, set the node of the scope
        if node is not None: new_scope.node = node;

        # If node is LuaFunction, set the function of the scope
        if isinstance(node, LuaFunction): new_scope.function = node;

        # Add the new scope to the children of the current scope
        children.append(new_scope);
        self.children = children;

        return new_scope;

class PyVariableDict(TypedDict):
    direct: bool;
    name: str;

class PyScope(Scope):
    def __init__(self, scope_id: str,
                        node: py_ast.stmt | py_ast.mod,
                        parent: Self | None = None):
        super().__init__(scope_id, node);
        self.variables: List[PyVariableDict] = [];
        self.parent = parent;

    def get_function(self) -> Self:
        def check_function(node: py_ast.stmt | py_ast.mod) -> bool:
            return (isinstance(node, py_ast.FunctionDef)
            or isinstance(node, py_ast.AsyncFunctionDef)
            or isinstance(node, py_ast.Lambda))

        if check_function(self.node): return self;  # type: ignore

        if self.parent is None:
            return self;

        ancestor: Self = self.parent;

        while ancestor is not None and ancestor.scope_id != "0" and check_function(ancestor.node):  # type: ignore
            if ancestor.parent is None: 
                break
            else:
                ancestor = ancestor.parent;

        return ancestor;

    def add_variable(self, variable: PyVariableDict) -> None | Literal[True]:
        function_scope = self.get_function();
        
        # Make list of variable.names
        variable_names: List[str] = [];

        for k in self.variables:
            variable_names.append(k["name"]);

        if variable["name"] in variable_names: return None;

        if function_scope == self:
            variable["direct"] = True;
        
        function_scope.variables.append(variable);

        return True;