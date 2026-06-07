from __future__ import annotations
import ast

def _call_name(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute): return _call_name(node.value) + '.' + node.attr if _call_name(node.value) else node.attr
    return type(node).__name__

def parse_functions(source: str, path: str | None = None):
    tree=ast.parse(source)
    funcs=[]; classes=[]; calls=[]; imports=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append({'name':node.name,'line':node.lineno,'end_line':getattr(node,'end_lineno',None),'kind':'async_function' if isinstance(node,ast.AsyncFunctionDef) else 'function','decorators':[getattr(d,'id',getattr(d,'attr','')) for d in node.decorator_list]})
        elif isinstance(node, ast.ClassDef):
            classes.append({'name':node.name,'line':node.lineno,'end_line':getattr(node,'end_lineno',None),'kind':'class'})
        elif isinstance(node, ast.Call):
            calls.append({'name':_call_name(node.func),'line':node.lineno,'kind':'call'})
        elif isinstance(node, ast.Import):
            for a in node.names: imports.append({'name':a.name,'line':node.lineno,'kind':'import'})
        elif isinstance(node, ast.ImportFrom):
            for a in node.names: imports.append({'name':f"{node.module}.{a.name}" if node.module else a.name,'line':node.lineno,'kind':'from_import'})
    return {'status':'parsed','parser':'python.ast','functions':funcs,'classes':classes,'calls':calls,'imports':imports,'errors':[]}
