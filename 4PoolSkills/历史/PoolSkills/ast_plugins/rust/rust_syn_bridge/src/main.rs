use std::{env, fs};
use regex::Regex;
use serde_json::json;
fn main() {
  let file = match env::args().nth(1) { Some(f)=>f, None=>{println!("{}", json!({"schema_version":"phase4-security-graph-v2","status":"failed","plugin":"rust_syn","error":"missing input file","nodes":[],"edges":[]})); return;} };
  let src = match fs::read_to_string(&file) { Ok(s)=>s, Err(e)=>{println!("{}", json!({"schema_version":"phase4-security-graph-v2","status":"failed","plugin":"rust_syn","file":file,"error":e.to_string(),"nodes":[],"edges":[]})); return;} };
  let _parsed = syn::parse_file(&src).ok();
  let mut nodes=Vec::new(); let mut edges=Vec::new();
  let rx=Regex::new(r#"\.route\s*\(\s*\"([^\"]+)\"\s*,\s*(get|post|put|patch|delete|any)\s*\("#).unwrap();
  for cap in rx.captures_iter(&src) {
    let route=cap.get(1).unwrap().as_str(); let method=cap.get(2).unwrap().as_str().to_uppercase();
    let rid=format!("{}:{} {}", file, method, route); let hid=format!("{}:handler:{}", file, route);
    nodes.push(json!({"id":rid,"type":"route","file":file,"method":method,"route":route,"framework_hint":"rust_axum_actix"}));
    nodes.push(json!({"id":hid,"type":"handler","file":file,"name":"axum_handler"}));
    edges.push(json!({"from":rid,"to":hid,"type":"ROUTE_TO_HANDLER"}));
  }
  println!("{}", json!({"schema_version":"phase4-security-graph-v2","status":"ready","plugin":"rust_syn","file":file,"nodes":nodes,"edges":edges,"capabilities":["syn_parse","axum_route_regex"]}));
}
