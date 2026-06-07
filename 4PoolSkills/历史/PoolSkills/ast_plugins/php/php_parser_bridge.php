<?php
$file = $argv[1] ?? null;
if (!$file || !file_exists($file)) { echo json_encode(["schema_version"=>"phase4-security-graph-v2","status"=>"failed","plugin"=>"php_parser","error"=>"missing input file","nodes"=>[],"edges"=>[]], JSON_PRETTY_PRINT); exit; }
$src = file_get_contents($file); $nodes=[]; $edges=[]; $seen=[];
function add_node(&$nodes,&$seen,$type,$id,$file,$extra=[]) { $k=$type.'|'.$id; if(!isset($seen[$k])) { $seen[$k]=true; $nodes[]=array_merge(["id"=>$id,"type"=>$type,"file"=>$file],$extra); } return $id; }
if (preg_match_all('/Route::(?:middleware\s*\([^)]*\)\s*->\s*)?(get|post|put|patch|delete|any|match)\s*\(\s*[\'\"]([^\'\"]+)/i', $src, $m, PREG_OFFSET_CAPTURE)) {
  foreach($m[1] as $i=>$meth) { $method=strtoupper($meth[0]); $route=$m[2][$i][0]; $line=substr_count(substr($src,0,$meth[1]),"\n")+1; $rid=add_node($nodes,$seen,'route',"$file:$method $route",$file,["method"=>$method,"route"=>$route,"framework_hint"=>"laravel_symfony_candidate","line"=>$line]); $hid=add_node($nodes,$seen,'handler',"$file:handler:$line",$file,["name"=>"controller_or_closure","line"=>$line]); $edges[]=["from"=>$rid,"to"=>$hid,"type"=>"ROUTE_TO_HANDLER"]; if (strpos(strtolower(substr($src,max(0,$meth[1]-150),300)),'auth')!==false) { $mid=add_node($nodes,$seen,'middleware',"$file:auth_middleware:$line",$file,["name"=>"auth"]); $edges[]=["from"=>$rid,"to"=>$mid,"type"=>"USES_MIDDLEWARE"]; } }
}
echo json_encode(["schema_version"=>"phase4-security-graph-v2","status"=>"ready","plugin"=>"php_parser","file"=>$file,"nodes"=>$nodes,"edges"=>$edges,"capabilities"=>["laravel_route_regex","php_parser_optional"]], JSON_PRETTY_PRINT);
?>
