package main
import (
  "encoding/json"; "fmt"; "go/parser"; "go/token"; "os"; "regexp"; "strings"
)
type Result struct { SchemaVersion string `json:"schema_version"`; Status string `json:"status"`; Plugin string `json:"plugin"`; File string `json:"file,omitempty"`; Error string `json:"error,omitempty"`; Nodes []map[string]any `json:"nodes"`; Edges []map[string]any `json:"edges"`; Capabilities []string `json:"capabilities,omitempty"` }
func add(nodes *[]map[string]any, seen map[string]bool, typ,id,file string, extra map[string]any) string { k:=typ+"|"+id; if !seen[k] { seen[k]=true; m:=map[string]any{"id":id,"type":typ,"file":file}; for a,b:=range extra{m[a]=b}; *nodes=append(*nodes,m)}; return id }
func main(){
  if len(os.Args)<2 { json.NewEncoder(os.Stdout).Encode(Result{SchemaVersion:"phase4-security-graph-v2",Status:"failed",Plugin:"go_parser",Error:"missing input file",Nodes:[]map[string]any{},Edges:[]map[string]any{}}); return }
  file:=os.Args[1]; srcBytes,err:=os.ReadFile(file); if err!=nil { json.NewEncoder(os.Stdout).Encode(Result{SchemaVersion:"phase4-security-graph-v2",Status:"failed",Plugin:"go_parser",File:file,Error:err.Error(),Nodes:[]map[string]any{},Edges:[]map[string]any{}}); return }
  fset:=token.NewFileSet(); _,parseErr:=parser.ParseFile(fset,file,srcBytes,parser.ParseComments)
  nodes:=[]map[string]any{}; edges:=[]map[string]any{}; seen:=map[string]bool{}; src:=string(srcBytes)
  rx:=regexp.MustCompile(`\.(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|HandleFunc|Handle)\s*\(\s*"([^"]+)"`)
  for _,m:=range rx.FindAllStringSubmatchIndex(src,-1){
    method:=src[m[2]:m[3]]; route:=src[m[4]:m[5]]; if strings.HasPrefix(method,"Handle"){method="ANY"}
    line:=strings.Count(src[:m[0]],"\n")+1; rid:=add(&nodes,seen,"route",fmt.Sprintf("%s:%s %s",file,method,route),file,map[string]any{"method":method,"route":route,"framework_hint":"go_gin_fiber_chi","line":line})
    hid:=add(&nodes,seen,"handler",fmt.Sprintf("%s:handler:%d",file,line),file,map[string]any{"name":"inline_or_registered_handler","line":line})
    edges=append(edges,map[string]any{"from":rid,"to":hid,"type":"ROUTE_TO_HANDLER"})
    prx:=regexp.MustCompile(`[:{<]([A-Za-z_][A-Za-z0-9_]*)`); for _,pm:=range prx.FindAllStringSubmatch(route,-1){ pid:=add(&nodes,seen,"parameter",rid+":param:"+pm[1],file,map[string]any{"name":pm[1]}); edges=append(edges,map[string]any{"from":rid,"to":pid,"type":"READS_PARAMETER"}) }
  }
  status:="ready"; errText:=""; if parseErr!=nil { errText=parseErr.Error() }
  json.NewEncoder(os.Stdout).Encode(Result{SchemaVersion:"phase4-security-graph-v2",Status:status,Plugin:"go_parser",File:file,Error:errText,Nodes:nodes,Edges:edges,Capabilities:[]string{"go_parser","gin_fiber_chi_route_regex"}})
}
