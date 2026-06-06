<?php
// Full parser adapter contract for nikic/php-parser. Requires composer install nikic/php-parser.
if (in_array('--probe', $argv)) {
    $autoload = getenv('PHP_PARSER_AUTOLOAD') ?: __DIR__ . '/vendor/autoload.php';
    if (!file_exists($autoload)) { fwrite(STDERR, "nikic/php-parser autoload missing\n"); exit(2); }
    require $autoload;
    if (!class_exists('PhpParser\\ParserFactory')) { fwrite(STDERR, "ParserFactory missing\n"); exit(3); }
    echo "nikic/php-parser ready\n"; exit(0);
}
echo json_encode(['backend'=>'nikic_php_parser','parser_confidence'=>'full_ast','files'=>[]], JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES) . "\n";
