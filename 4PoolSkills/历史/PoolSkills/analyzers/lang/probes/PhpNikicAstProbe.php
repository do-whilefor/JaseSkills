<?php
if ($argc < 2) { fwrite(STDERR, "usage: PhpNikicAstProbe.php <file> [projectRoot]\n"); exit(2); }
$file = $argv[1];
$root = $argv[2] ?? dirname($file);
$autoloads = [];
$dir = realpath($root) ?: $root;
while ($dir && $dir !== dirname($dir)) {
  $autoloads[] = $dir . DIRECTORY_SEPARATOR . 'vendor' . DIRECTORY_SEPARATOR . 'autoload.php';
  $dir = dirname($dir);
}
$autoloads[] = __DIR__ . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR . 'vendor' . DIRECTORY_SEPARATOR . 'autoload.php';
$loaded = false;
foreach ($autoloads as $a) { if (is_file($a)) { require_once $a; $loaded = true; break; } }
if (!class_exists('PhpParser\\ParserFactory')) {
  fwrite(STDERR, "nikic/php-parser not installed; run composer require nikic/php-parser\n"); exit(3);
}
use PhpParser\ParserFactory;
use PhpParser\Node;
$code = file_get_contents($file);
try {
  $factory = new ParserFactory();
  if (method_exists($factory, 'createForNewestSupportedVersion')) $parser = $factory->createForNewestSupportedVersion();
  else $parser = $factory->create(ParserFactory::PREFER_PHP7);
  $ast = $parser->parse($code);
} catch (Throwable $e) {
  echo json_encode(['status'=>'parser_error','parser'=>'nikic/php-parser','functions'=>[],'classes'=>[],'calls'=>[],'imports'=>[],'errors'=>[$e->getMessage()]], JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE); exit(0);
}
$out = ['status'=>'parsed','parser'=>'nikic/php-parser','functions'=>[],'classes'=>[],'calls'=>[],'imports'=>[],'errors'=>[]];
$walk = function($node) use (&$walk, &$out) {
  if ($node instanceof Node\Stmt\Function_) $out['functions'][] = ['name'=>(string)$node->name,'line'=>$node->getStartLine(),'end_line'=>$node->getEndLine(),'kind'=>'Function_'];
  if ($node instanceof Node\Stmt\ClassMethod) $out['functions'][] = ['name'=>(string)$node->name,'line'=>$node->getStartLine(),'end_line'=>$node->getEndLine(),'kind'=>'ClassMethod'];
  if ($node instanceof Node\Stmt\Class_) $out['classes'][] = ['name'=>$node->name ? (string)$node->name : '<anonymous>','line'=>$node->getStartLine(),'end_line'=>$node->getEndLine(),'kind'=>'Class_'];
  if ($node instanceof Node\Expr\FuncCall) $out['calls'][] = ['name'=>$node->name instanceof Node\Name ? $node->name->toString() : '<call>','line'=>$node->getStartLine(),'kind'=>'FuncCall'];
  if ($node instanceof Node\Expr\MethodCall) $out['calls'][] = ['name'=>$node->name instanceof Node\Identifier ? (string)$node->name : '<method>','line'=>$node->getStartLine(),'kind'=>'MethodCall'];
  if ($node instanceof Node\Expr\StaticCall) $out['calls'][] = ['name'=>$node->name instanceof Node\Identifier ? (string)$node->name : '<static>','line'=>$node->getStartLine(),'kind'=>'StaticCall'];
  if ($node instanceof Node\Stmt\Use_) foreach ($node->uses as $u) $out['imports'][] = ['name'=>$u->name->toString(),'line'=>$node->getStartLine(),'kind'=>'Use_'];
  foreach ($node->getSubNodeNames() as $name) {
    $child = $node->$name;
    if (is_array($child)) foreach ($child as $c) if ($c instanceof Node) $walk($c);
    elseif ($child instanceof Node) $walk($child);
  }
};
foreach ($ast as $n) if ($n instanceof Node) $walk($n);
echo json_encode($out, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE);
