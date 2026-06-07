#!/usr/bin/env ruby
require 'json'
require 'ripper'
if ARGV.include?('--probe')
  sexp = Ripper.sexp('class A; def b; end; end')
  abort('ripper failed') unless sexp
  puts 'ruby Ripper ready'
  exit 0
end
out = {backend: 'ruby_ripper', parser_confidence: 'full_ast', files: []}
ARGV.each do |path|
  next unless File.file?(path)
  out[:files] << {file: path, sexp_present: !!Ripper.sexp(File.read(path))}
end
puts JSON.pretty_generate(out)
