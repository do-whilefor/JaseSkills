require 'ripper'
require 'json'
path = ARGV[0]
source = File.read(path, encoding: 'UTF-8')
sexp = Ripper.sexp(source)
if sexp.nil?
  puts({status: 'parser_error', parser: 'ruby.Ripper', errors: ['Ripper returned nil'], functions: [], classes: [], calls: [], imports: []}.to_json)
  exit 0
end
items = {functions: [], classes: [], calls: [], imports: []}
lex = Ripper.lex(source)
def line_for_name(lex, name)
  tok = lex.find { |x| x[2].to_s == name.to_s }
  tok ? tok[0][0] : nil
end
def walk(node, items, lex)
  return unless node.is_a?(Array)
  case node[0]
  when :def
    name = node[1][1] rescue '<anonymous>'
    items[:functions] << {kind: 'def', name: name.to_s, line: line_for_name(lex, name) || 1}
  when :defs
    name = node[3][1] rescue '<singleton>'
    items[:functions] << {kind: 'defs', name: name.to_s, line: line_for_name(lex, name) || 1}
  when :class
    name = node[1].flatten.select{|x| x.is_a?(String)}.first rescue '<class>'
    items[:classes] << {kind: 'class', name: name.to_s, line: line_for_name(lex, name) || 1}
  when :command, :method_add_arg, :call, :fcall, :vcall
    name = node.flatten.select{|x| x.is_a?(String)}.first rescue '<call>'
    items[:calls] << {kind: node[0].to_s, name: name.to_s, line: line_for_name(lex, name) || 1} if name
  when :command_call
    name = node.flatten.select{|x| x.is_a?(String)}.last rescue '<call>'
    items[:calls] << {kind: 'command_call', name: name.to_s, line: line_for_name(lex, name) || 1} if name
  end
  node.each { |child| walk(child, items, lex) }
end
walk(sexp, items, lex)
puts({status: 'parsed', parser: 'ruby.Ripper', errors: [], functions: items[:functions], classes: items[:classes], calls: items[:calls], imports: items[:imports]}.to_json)
