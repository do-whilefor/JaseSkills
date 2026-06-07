import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;
import com.sun.source.tree.*;
import com.sun.source.util.*;

public class JavaAstProbe {
  static class Item {
    String kind; String name; long line; long endLine;
    Item(String kind, String name, long line, long endLine) { this.kind=kind; this.name=name; this.line=line; this.endLine=endLine; }
  }
  static String esc(String s) { return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", ""); }
  static String arr(String name, List<Item> xs) {
    StringBuilder sb = new StringBuilder(); sb.append("\"").append(name).append("\":[");
    for (int i=0;i<xs.size();i++) { Item x=xs.get(i); if (i>0) sb.append(','); sb.append("{\"kind\":\"").append(esc(x.kind)).append("\",\"name\":\"").append(esc(x.name)).append("\",\"line\":").append(x.line).append(",\"end_line\":").append(x.endLine).append("}"); }
    sb.append(']'); return sb.toString();
  }
  public static void main(String[] args) throws Exception {
    if (args.length < 1) { System.out.println("{\"status\":\"parser_error\",\"parser\":\"javac.TreeScanner\",\"errors\":[\"missing source path\"],\"functions\":[],\"classes\":[],\"calls\":[],\"imports\":[]}"); return; }
    JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
    if (compiler == null) { System.out.println("{\"status\":\"parser_unavailable\",\"parser\":\"javac.TreeScanner\",\"errors\":[\"JDK compiler unavailable\"],\"functions\":[],\"classes\":[],\"calls\":[],\"imports\":[]}"); return; }
    StandardJavaFileManager fm = compiler.getStandardFileManager(null, null, StandardCharsets.UTF_8);
    Iterable<? extends JavaFileObject> files = fm.getJavaFileObjectsFromStrings(Arrays.asList(args[0]));
    JavacTask task = (JavacTask) compiler.getTask(null, fm, null, Arrays.asList("-proc:none"), null, files);
    Iterable<? extends CompilationUnitTree> units = task.parse();
    List<Item> funcs = new ArrayList<>(), classes = new ArrayList<>(), calls = new ArrayList<>(), imports = new ArrayList<>();
    for (CompilationUnitTree unit: units) {
      LineMap lm = unit.getLineMap();
      Trees trees = Trees.instance(task);
      for (ImportTree it: unit.getImports()) {
        long sp = trees.getSourcePositions().getStartPosition(unit, it);
        imports.add(new Item("import", it.getQualifiedIdentifier().toString(), lm.getLineNumber(sp), lm.getLineNumber(sp)));
      }
      new TreeScanner<Void, Void>() {
        public Void visitClass(ClassTree node, Void p) { long s=trees.getSourcePositions().getStartPosition(unit,node); long e=trees.getSourcePositions().getEndPosition(unit,node); classes.add(new Item("class", node.getSimpleName().toString(), lm.getLineNumber(s), lm.getLineNumber(e))); return super.visitClass(node,p); }
        public Void visitMethod(MethodTree node, Void p) { long s=trees.getSourcePositions().getStartPosition(unit,node); long e=trees.getSourcePositions().getEndPosition(unit,node); funcs.add(new Item("method", node.getName().toString(), lm.getLineNumber(s), lm.getLineNumber(e))); return super.visitMethod(node,p); }
        public Void visitMethodInvocation(MethodInvocationTree node, Void p) { long s=trees.getSourcePositions().getStartPosition(unit,node); calls.add(new Item("call", node.getMethodSelect().toString(), lm.getLineNumber(s), lm.getLineNumber(s))); return super.visitMethodInvocation(node,p); }
      }.scan(unit, null);
    }
    System.out.println("{\"status\":\"parsed\",\"parser\":\"javac.com.sun.source.TreeScanner\",\"errors\":[]," + arr("functions", funcs) + "," + arr("classes", classes) + "," + arr("calls", calls) + "," + arr("imports", imports) + "}");
  }
}
