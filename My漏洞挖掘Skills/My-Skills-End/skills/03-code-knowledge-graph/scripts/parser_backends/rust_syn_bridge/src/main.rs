use std::{env, fs};
fn main() {
    if env::args().any(|a| a == "--probe") {
        syn::parse_file("fn probe() {} ").expect("syn probe failed");
        println!("rust syn ready");
        return;
    }
    let mut files = Vec::new();
    for p in env::args().skip(1) {
        if let Ok(src) = fs::read_to_string(&p) {
            let ok = syn::parse_file(&src).is_ok();
            files.push(serde_json::json!({"file": p, "parse_ok": ok}));
        }
    }
    println!("{}", serde_json::json!({"backend":"rust_syn","parser_confidence":"full_ast","files":files}));
}
