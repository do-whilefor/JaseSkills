import unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzers.lang.java_ast import parse_functions as parse_java
from analyzers.lang.go_ast import parse_functions as parse_go
from analyzers.lang.php_ast import parse_functions as parse_php
from analyzers.lang.ruby_ast import parse_functions as parse_ruby
from analyzers.lang.rust_ast import parse_functions as parse_rust

class RealAstParserAdaptersTest(unittest.TestCase):
    def test_java_uses_javac_or_explicit_unavailable_not_regex(self):
        r=parse_java('class A { void run(){ helper(); } void helper(){} }')
        self.assertNotIn('regex', str(r.get('parser')))
        self.assertIn(r['status'], {'parsed','parser_unavailable','parser_error'})
        if r['status']=='parsed': self.assertTrue(any(f['name']=='run' for f in r['functions']))

    def test_go_uses_go_parser_or_explicit_unavailable_not_regex(self):
        r=parse_go('package main\nfunc run(){ helper() }\nfunc helper(){}')
        self.assertNotIn('regex', str(r.get('parser')))
        self.assertIn(r['status'], {'parsed','parser_unavailable','parser_error'})
        if r['status']=='parsed': self.assertTrue(any(f['name']=='run' for f in r['functions']))

    def test_php_uses_tree_sitter_or_php_structural_parser_not_regex(self):
        r=parse_php('<?php function run(){ helper(); } function helper(){}')
        self.assertNotIn('regex', str(r.get('parser')))
        self.assertIn(r['status'], {'parsed','parsed_structural_ast','parser_unavailable','parser_error'})
        if r['status'].startswith('parsed'): self.assertTrue(any(f['name']=='run' for f in r['functions']))

    def test_ruby_uses_ripper_or_explicit_unavailable_not_regex(self):
        r=parse_ruby('def run\n helper\nend\ndef helper\nend')
        self.assertNotIn('regex', str(r.get('parser')))
        self.assertIn(r['status'], {'parsed','parser_unavailable','parser_error'})
        if r['status']=='parsed': self.assertTrue(any(f['name']=='run' for f in r['functions']))

    def test_rust_requires_real_parser_and_never_regex_fallback(self):
        r=parse_rust('fn run(){ helper(); } fn helper(){}')
        self.assertNotIn('regex', str(r.get('parser')))
        self.assertIn(r['status'], {'parsed','parser_unavailable','parser_error'})

if __name__=='__main__': unittest.main()
