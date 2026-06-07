import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;

/**
 * JavaParser bridge for authorized local security graph extraction.
 * If com.github.javaparser is present on the runtime classpath the bridge marks javaparser_available=true.
 * The extraction path is intentionally conservative and still works without external jars by scanning Spring annotations.
 */
public class javaparser_bridge {
  static String esc(String s){ return s==null?"":s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r",""); }
  static class Node { String id,type,extra; Node(String t,String i,String e){type=t;id=i;extra=e;} }
  static class Edge { String from,to,type; Edge(String f,String t,String ty){from=f;to=t;type=ty;} }
  static List<Node> nodes = new ArrayList<>();
  static List<Edge> edges = new ArrayList<>();
  static Set<String> seen = new HashSet<>();
  static String file;
  static String addNode(String type, String id, String extra){ String k=type+"|"+id; if(!seen.contains(k)){seen.add(k);nodes.add(new Node(type,id,extra));} return id; }
  static void addEdge(String f,String t,String ty){ if(f!=null && t!=null) edges.add(new Edge(f,t,ty)); }
  static int lineOf(String src, int idx){ int line=1; for(int i=0;i<idx && i<src.length();i++) if(src.charAt(i)=='\n') line++; return line; }
  static String methodFor(String ann){
    ann=ann.toLowerCase(Locale.ROOT);
    if(ann.contains("post")) return "POST"; if(ann.contains("put")) return "PUT"; if(ann.contains("patch")) return "PATCH";
    if(ann.contains("delete")) return "DELETE"; if(ann.contains("request")) return "ANY"; return "GET";
  }
  static String routeFrom(String body){
    Matcher m=Pattern.compile("(?:value|path)\\s*=\\s*\\\"([^\\\"]+)\\\"|\\(\\s*\\\"([^\\\"]+)\\\"").matcher(body);
    if(m.find()) return m.group(1)!=null?m.group(1):m.group(2);
    return "/";
  }
  static void scan(String src){
    addNode("module", file+":module", "\"path\":\""+esc(file)+"\"");
    Matcher base=Pattern.compile("@(RequestMapping|Controller|RestController)\\s*(\\([^)]*\\))?", Pattern.MULTILINE).matcher(src);
    String basePath=""; if(base.find()) basePath = routeFrom(base.group(2)==null?"":base.group(2)); if("/".equals(basePath)) basePath="";
    Pattern p=Pattern.compile("@((?:Get|Post|Put|Patch|Delete|Request)Mapping)\\s*(\\([^)]*\\))?[\\s\\S]{0,600}?(?:public|private|protected)?\\s+[A-Za-z0-9_<>, ?\\[\\]]+\\s+([A-Za-z0-9_]+)\\s*\\(([^)]*)\\)", Pattern.MULTILINE);
    Matcher m=p.matcher(src);
    while(m.find()){
      String ann=m.group(1), args=m.group(2)==null?"":m.group(2), name=m.group(3), params=m.group(4);
      String method=methodFor(ann), route=basePath + routeFrom(args); if(route.length()==0) route="/";
      int line=lineOf(src,m.start());
      String rid=addNode("route", file+":"+method+" "+route, "\"method\":\""+method+"\",\"route\":\""+esc(route)+"\",\"framework_hint\":\"spring\",\"line\":"+line);
      String hid=addNode("handler", file+":"+name+":"+line, "\"name\":\""+esc(name)+"\",\"line\":"+line);
      addEdge(rid,hid,"ROUTE_TO_HANDLER");
      if(src.substring(Math.max(0,m.start()-500), Math.min(src.length(), m.end()+200)).matches("(?is).*(PreAuthorize|Secured|RolesAllowed|AuthenticationPrincipal|Principal|SecurityContext|hasRole|hasAuthority).*")){
        String az=addNode("authz", hid+":authz", "\"name\":\"spring_security_annotation\""); addEdge(hid,az,"ENFORCES_AUTHZ");
      }
      if(src.substring(Math.max(0,m.start()-500), Math.min(src.length(), m.end()+200)).matches("(?is).*(Authentication|Principal|JWT|Session|SecurityContext).*")){
        String an=addNode("authn", hid+":authn", "\"name\":\"spring_authentication_signal\""); addEdge(hid,an,"ENFORCES_AUTHN");
      }
      Matcher pm=Pattern.compile("@(PathVariable|RequestParam|RequestBody)\\s*(?:\\([^)]*\\))?\\s*[A-Za-z0-9_<>, ?\\[\\]]+\\s+([A-Za-z0-9_]+)").matcher(params);
      while(pm.find()){
        String pid=addNode("parameter", hid+":param:"+pm.group(2), "\"name\":\""+esc(pm.group(2))+"\",\"source\":\""+pm.group(1)+"\"");
        addEdge(hid,pid,"READS_PARAMETER");
      }
    }
  }
  public static void main(String[] args) throws Exception {
    if(args.length<1){ System.out.println("{\"schema_version\":\"phase4-security-graph-v2\",\"status\":\"missing\",\"plugin\":\"javaparser\",\"error\":\"missing input file\",\"nodes\":[],\"edges\":[]}"); return; }
    file=args[0]; String src=Files.readString(Path.of(file), StandardCharsets.UTF_8);
    boolean jp=false; try { Class.forName("com.github.javaparser.StaticJavaParser"); jp=true; } catch(Throwable t) { jp=false; }
    scan(src);
    StringBuilder sb=new StringBuilder();
    sb.append("{\n  \"schema_version\": \"phase4-security-graph-v2\",\n  \"status\": \"").append(jp?"ready":"degraded").append("\",\n  \"plugin\": \"javaparser\",\n  \"parser_mode\": \"").append(jp?"javaparser_classpath":"spring_annotation_fallback").append("\",\n  \"degraded_reason\": \"").append(jp?"":"JavaParser classpath not available; annotation fallback cannot confirm vulnerabilities").append("\",\n  \"javaparser_available\": ").append(jp).append(",\n  \"file\": \"").append(esc(file)).append("\",\n  \"nodes\": [");
    for(int i=0;i<nodes.size();i++){ Node n=nodes.get(i); if(i>0) sb.append(','); sb.append("{\"id\":\"").append(esc(n.id)).append("\",\"type\":\"").append(esc(n.type)).append("\",\"file\":\"").append(esc(file)).append("\""); if(n.extra!=null && n.extra.length()>0) sb.append(',').append(n.extra); sb.append('}'); }
    sb.append("],\n  \"edges\": [");
    for(int i=0;i<edges.size();i++){ Edge e=edges.get(i); if(i>0) sb.append(','); sb.append("{\"from\":\"").append(esc(e.from)).append("\",\"to\":\"").append(esc(e.to)).append("\",\"type\":\"").append(esc(e.type)).append("\"}"); }
    sb.append("],\n  \"capabilities\": [\"spring_mapping_annotations\",\"spring_security_annotations\",\"path_variable_request_param_body\",\"optional_javaparser_classpath_detection\"]\n}");
    System.out.println(sb.toString());
  }
}
