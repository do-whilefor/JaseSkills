package main
import (
  "encoding/json"; "flag"; "fmt"; "go/ast"; "go/parser"; "go/token"; "os"
)
func main(){ probe:=flag.Bool("probe", false, "probe"); flag.Parse(); src:="package main\nfunc Handler(){ }\n"; if *probe { fset:=token.NewFileSet(); _,err:=parser.ParseFile(fset,"probe.go",src,parser.ParseComments); if err!=nil{fmt.Println(err); os.Exit(1)}; fmt.Println("go/parser ready"); return }
  fset:=token.NewFileSet(); files:=[]map[string]any{}; for _,p:=range flag.Args(){ f,err:=parser.ParseFile(fset,p,nil,parser.ParseComments); if err!=nil{continue}; funcs:=[]map[string]any{}; ast.Inspect(f,func(n ast.Node)bool{ if fn,ok:=n.(*ast.FuncDecl); ok { funcs=append(funcs,map[string]any{"name":fn.Name.Name,"line":fset.Position(fn.Pos()).Line}) }; return true }); files=append(files,map[string]any{"file":p,"functions":funcs}) }; json.NewEncoder(os.Stdout).Encode(map[string]any{"backend":"go_parser","parser_confidence":"full_ast","files":files}) }
