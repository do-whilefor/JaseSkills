<?php
$path = $argv[1] ?? null;
if (!$path) { echo json_encode(['status'=>'parser_error','parser'=>'php.token_get_all+php_lint','errors'=>['missing source path'],'functions'=>[],'classes'=>[],'calls'=>[],'imports'=>[]]); exit; }
$source = file_get_contents($path);
$tokens = token_get_all($source, TOKEN_PARSE);
$result = ['status'=>'parsed_structural_ast','parser'=>'php.token_get_all+zend_syntax_parser_lint','errors'=>[],'functions'=>[],'classes'=>[],'calls'=>[],'imports'=>[]];
$expect = null;
$lastSig = null;
foreach ($tokens as $tok) {
  if (is_array($tok)) {
    [$id, $text, $line] = $tok;
    if ($id === T_FUNCTION) { $expect = 'function'; continue; }
    if ($id === T_CLASS || $id === T_INTERFACE || $id === T_TRAIT) { $expect = 'class'; continue; }
    if ($id === T_USE) { $expect = 'import'; continue; }
    if ($expect && $id === T_STRING) {
      if ($expect === 'function') $result['functions'][] = ['kind'=>'function', 'name'=>$text, 'line'=>$line];
      elseif ($expect === 'class') $result['classes'][] = ['kind'=>'class', 'name'=>$text, 'line'=>$line];
      elseif ($expect === 'import') $result['imports'][] = ['kind'=>'use', 'name'=>$text, 'line'=>$line];
      $expect = null; continue;
    }
    if ($id === T_STRING) { $lastSig = ['name'=>$text, 'line'=>$line]; }
  } else {
    if ($tok === '(' && $lastSig) { $result['calls'][] = ['kind'=>'call', 'name'=>$lastSig['name'], 'line'=>$lastSig['line']]; $lastSig = null; }
    if ($tok === ';' || $tok === '{') { if ($expect === 'import') $expect = null; }
  }
}
echo json_encode($result);
