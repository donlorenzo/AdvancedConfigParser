import ast
import re

__all__ = ["ast_to_src"]

def ast_to_src(ast_node):
    def quote_str(s):
        if not isinstance(s, str):
            s = str(s)
        tick_result = re.search(r"(?<!\\)'", s)
        dbl_tick_result = re.search(r'(?<!\\)"', s)
        if tick_result is not None and dbl_tick_result is not None:
            raise RuntimeError("could not determine suitable string quotes for >{s}<".format(s))
        if tick_result is None:
            quotation = "'"
        else:
            quotation = '"'
        if "\n" in s:
            quotation *= 3
        return quotation + s + quotation
        
    if isinstance(ast_node, ast.Num):
        return str(ast_node.n)
    elif isinstance(ast_node, ast.UnaryOp):
        ops = {ast.Invert: "~", ast.Not: "!", ast.UAdd: "+", ast.USub: "-"}
        return ops[ast_node.op.__class__] + ast_to_src(ast_node.operand)
    elif isinstance(ast_node, ast.BinOp):
        lhs = ast_to_src(ast_node.left)
        rhs = ast_to_src(ast_node.right)
        ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
               ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%",
               ast.Pow: "**", ast.LShift: "<<", ast.RShift: ">>",
               ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&",}
        op = ops[ast_node.op.__class__]
        return "(" + lhs + " " + op + " " + rhs + ")"
    elif isinstance(ast_node, ast.Name):
        return ast_node.id
    elif isinstance(ast_node, ast.Attribute):
        return ast_to_src(ast_node.value) + "." + ast_node.attr
    elif isinstance(ast_node, ast.Str):
        return quote_str(ast_node.s)
    elif isinstance(ast_node, ast.Call):
        args_list = list(map(lambda n : ast_to_src(n), ast_node.args))
        kwargs_list = []
        for keyword_node in ast_node.keywords:
            kwargs_list.append("=".join((keyword_node.arg, ast_to_src(keyword_node.value))))
        return ast_to_src(ast_node.func) + "(" + ", ".join(args_list + kwargs_list) + ")"
    elif isinstance(ast_node, ast.List):
        return "[" + ", ".join(map(lambda n : ast_to_src(n), ast_node.elts)) + "]"
    elif isinstance(ast_node, ast.Tuple):
        if len(ast_node.elts) == 1:
            return "(" + ast_to_src(ast_node.elts[0]) + ",)"
        return "(" + ", ".join(map(lambda n : ast_to_src(n), ast_node.elts)) + ")"
    elif isinstance(ast_node, ast.Dict):
        keys = list(map(lambda n : ast_to_src(n), ast_node.keys))
        values = list(map(lambda n : ast_to_src(n), ast_node.values))
        assert len(keys) == len(values)
        if len(keys) == 0:
            return "{}"
        s = "{ "
        for k, v in zip(keys, values):
            s += k + ": " + v + ", "
        s = s[:-2] + " }"
        return s
    elif isinstance(ast_node, ast.IfExp):
        return ast_to_src(ast_node.body) + " if " + ast_to_src(ast_node.test) + " else " + ast_to_src(ast_node.orelse)
    elif isinstance(ast_node, ast.BoolOp):
        if ast_node.op.__class__ == ast.And:
            return "(" + " and ".join(ast_to_src(v) for v in ast_node.values) + ")"
        elif ast_node.op.__class__ == ast.Or:
            return "(" + " or ".join(ast_to_src(v) for v in ast_node.values) + ")"
        raise RuntimeError("unreachable")
    elif isinstance(ast_node, ast.Compare):
        astOp2Str = {ast.Eq: "==", ast.NotEq: "!=",
                     ast.Lt: "<", ast.LtE: "<=",
                     ast.Gt: ">", ast.GtE: ">=",
                     ast.Is: "is", ast.IsNot: "is not",
                     ast.In: "in", ast.NotIn: "not in"}
        s = ast_to_src(ast_node.left)
        for ast_op, ast_right in zip(ast_node.ops, ast_node.comparators):
            s += " " + astOp2Str[ast_op.__class__] + " " + ast_to_src(ast_right)
        return "(" + s + ")"
    elif isinstance(ast_node, ast.NameConstant):
        return str(ast_node.value)
    raise RuntimeError('support for this ast node has not been implemented yet: "{ast}"'.format(ast=str(ast_node)))
