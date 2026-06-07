use std::{env, fs};
use syn::{visit::Visit, File, Item, Expr, UseTree};
use serde_json::json;

struct Collector { functions: Vec<serde_json::Value>, classes: Vec<serde_json::Value>, calls: Vec<serde_json::Value>, imports: Vec<serde_json::Value> }
fn span_line<T>(_t: &T) -> usize { 1 }
impl<'ast> Visit<'ast> for Collector {
    fn visit_item(&mut self, i: &'ast Item) {
        match i {
            Item::Fn(f) => self.functions.push(json!({"name": f.sig.ident.to_string(), "line": span_line(f), "end_line": null, "kind": "ItemFn"})),
            Item::Struct(s) => self.classes.push(json!({"name": s.ident.to_string(), "line": span_line(s), "end_line": null, "kind": "ItemStruct"})),
            Item::Enum(e) => self.classes.push(json!({"name": e.ident.to_string(), "line": span_line(e), "end_line": null, "kind": "ItemEnum"})),
            Item::Use(u) => self.imports.push(json!({"name": use_tree_name(&u.tree), "line": span_line(u), "kind": "Use"})),
            _ => {}
        }
        syn::visit::visit_item(self, i);
    }
    fn visit_expr(&mut self, e: &'ast Expr) {
        match e {
            Expr::Call(c) => self.calls.push(json!({"name": expr_name(&c.func), "line": span_line(c), "kind": "ExprCall"})),
            Expr::MethodCall(m) => self.calls.push(json!({"name": m.method.to_string(), "line": span_line(m), "kind": "ExprMethodCall"})),
            _ => {}
        }
        syn::visit::visit_expr(self, e);
    }
}
fn use_tree_name(t: &UseTree) -> String { match t { UseTree::Path(p) => p.ident.to_string(), UseTree::Name(n) => n.ident.to_string(), UseTree::Rename(r) => r.rename.to_string(), UseTree::Glob(_) => "*".into(), UseTree::Group(_) => "group".into() } }
fn expr_name(e: &Box<Expr>) -> String { match &**e { Expr::Path(p) => p.path.segments.last().map(|s| s.ident.to_string()).unwrap_or("<call>".into()), _ => "<call>".into() } }
fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 { eprintln!("usage: bridge <file>"); std::process::exit(2); }
    let src = fs::read_to_string(&args[1]).unwrap_or_default();
    match syn::parse_file(&src) {
        Ok(ast) => {
            let mut c = Collector { functions: vec![], classes: vec![], calls: vec![], imports: vec![] };
            c.visit_file(&ast);
            println!("{}", json!({"status":"parsed","parser":"syn_full","functions":c.functions,"classes":c.classes,"calls":c.calls,"imports":c.imports,"errors":[]}));
        }
        Err(e) => println!("{}", json!({"status":"parser_error","parser":"syn_full","functions":[],"classes":[],"calls":[],"imports":[],"errors":[e.to_string()]}))
    }
}
