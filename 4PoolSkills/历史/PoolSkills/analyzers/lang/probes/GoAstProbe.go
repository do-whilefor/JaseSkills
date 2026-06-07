package main
import (
  "encoding/json"
  "fmt"
  "go/ast"
  "go/parser"
  "go/token"
  "os"
)
type Item struct { Kind string `json:"kind"`; Name string `json:"name"`; Line int `json:"line"`; EndLine int `json:"end_line,omitempty"` }
type Result struct { Status string `json:"status"`; Parser string `json:"parser"`; Functions []Item `json:"functions"`; Classes []Item `json:"classes"`; Calls []Item `json:"calls"`; Imports []Item `json:"imports"`; Errors []string `json:"errors"` }
func main(){
  r:=Result{Status:"parsed", Parser:"go/parser", Functions:[]Item{}, Classes:[]Item{}, Calls:[]Item{}, Imports:[]Item{}, Errors:[]string{}}
  if len(os.Args)<2 { r.Status="parser_error"; r.Errors=[]string{"missing source path"}; json.NewEncoder(os.Stdout).Encode(r); return }
  srcPath := os.Args[1]
  if srcPath == "--" && len(os.Args) > 2 { srcPath = os.Args[2] }
  fs:=token.NewFileSet()
  f, err:=parser.ParseFile(fs, srcPath, nil, parser.AllErrors|parser.ParseComments)
  if err!=nil { r.Status="parser_error"; r.Errors=[]string{err.Error()} }
  if f!=nil {
    for _, im:= range f.Imports { r.Imports=append(r.Imports, Item{Kind:"import", Name: im.Path.Value, Line: fs.Position(im.Pos()).Line}) }
    ast.Inspect(f, func(n ast.Node) bool {
      switch x := n.(type) {
      case *ast.FuncDecl:
        r.Functions=append(r.Functions, Item{Kind:"function", Name:x.Name.Name, Line:fs.Position(x.Pos()).Line, EndLine:fs.Position(x.End()).Line})
      case *ast.CallExpr:
        name := fmt.Sprintf("%T", x.Fun)
        switch fun := x.Fun.(type) { case *ast.Ident: name=fun.Name; case *ast.SelectorExpr: name=fun.Sel.Name }
        r.Calls=append(r.Calls, Item{Kind:"call", Name:name, Line:fs.Position(x.Pos()).Line})
      case *ast.TypeSpec:
        r.Classes=append(r.Classes, Item{Kind:"type", Name:x.Name.Name, Line:fs.Position(x.Pos()).Line})
      }
      return true
    })
  }
  json.NewEncoder(os.Stdout).Encode(r)
}
