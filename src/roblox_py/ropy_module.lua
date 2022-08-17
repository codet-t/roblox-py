-- roblox-py 
-- https://github.com/codetariat/roblox-py
local ropy = {}

-- VALUE in DICT -> ropy.operator_in(VALUE, DICT)
ropy.operator_in = function(needle, haystack)
	if type(haystack) == "string" and type(needle) == "string" then
		return string.find(haystack, needle, 1, true) ~= nil
	end
	
	if type(haystack) == "table" then
		for v in haystack do
			if v == needle then
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
	
	return pytable[key]
end

ropy.append = function(pytable, value)
	table.insert(pytable, value)
end

-- We have to loop through the table, because in python len() works for both dict and lists
-- in Lua only lists have a length
ropy.len = function(pytable)
	local result = 0;

	for _ in pairs(pytable) do
		result = result + 1
	end

	return result
end

return ropy;