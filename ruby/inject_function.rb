def inject_function(number, operation)
  operation = method(operation) if operation.is_a?(Symbol)
  for i in 1..number - 1
      number = operation.call(number, i)
  end
  number
end

# User-defined lambda function
mul = lambda { |a, b| a * b }

# User-defined method
def triple_mul(a, b)
  a * b * 3
end

puts inject_function(5, mul) # 120
puts inject_function(5, :triple_mul) # 9720
puts inject_function(5, :*.to_proc) # 120