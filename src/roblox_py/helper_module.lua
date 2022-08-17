-- roblox-py 
-- https://github.com/codetariat/roblox-py
local ropy = {}

-- VALUE in DICT -> ropy.operator_in(VALUE, DICT)
ropy.operator_in = function(input, pytable)	
	if type(pytable) == "string" and type(input) == "string" then
		return string.find(pytable, input, 1, true) ~= nil
	end
	
	if type(pytable) == "table" then
		for v in pytable do
			if v == input then
				return true
			end
		end
	end

	return false
end

ropy.setdefault = function(pytable, key, value)
	if pytable[key] == nil then
		pytable[key] = value
	end
	
	return pytable
end

ropy.append = function(pytable, value)
	table.insert(pytable, value)
	
	return pytable
end

return ropy;