#!/usr/bin/env ruby
require 'json'; require 'ripper'
file = ARGV[0]
if !file || !File.exist?(file)
  puts JSON.pretty_generate({status:'failed', plugin:'ruby_ripper', error:'missing input file', nodes:[], edges:[]}); exit
end
src = File.read(file)
nodes=[]; edges=[]
if src =~ /(get|post|put|patch|delete)\s+['\"]([^'\"]+)/
  method=$1.upcase; route=$2; rid="#{file}:#{method} #{route}"; nodes << {id:rid,type:'route',file:file,method:method,route:route,framework:'rails/sinatra-candidate'}
end
puts JSON.pretty_generate({status:'ready', plugin:'ruby_ripper', file:file, nodes:nodes, edges:edges})
