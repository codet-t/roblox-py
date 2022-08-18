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

ropy.range = function(start, stop, step)
	if stop == nil then stop = start; start = 1 end
	if step == nil then step = 1 end

	if type(start) ~= "number" or type(stop) ~= "number" or type(step) ~= "number" then
		warn("range() expects ints only")
	end

	if start % 1 ~= 0 or stop % 1 ~= 0 or step % 1 ~= 0 then
		warn("range() expects ints only")
	end

	local result = {}
	local i = start
	while i <= stop do
		table.insert(result, i)
		i = i + step
	end
	return result
end

-- == Table-specific methods begin here == --

-- We have to loop through the table, because in python len() works for both dict and lists
-- in Lua only lists have a length
-- We could probably optimise this by returning #pytable by adding ropy.len.list as a list-specific method
ropy.len = function(pytable)
	local result = 0;

	for _ in pairs(pytable) do
		result = result + 1
	end

	return result
end

ropy.setdefault = {
	dict = function(pytable, key, value)
		if pytable[key] == nil then
			pytable[key] = value
		end

		return pytable[key]
	end,

	error = function()
		error("setdefault is only a dict method")
	end
}

ropy.setdefault.list = ropy.setdefault.error
ropy.setdefault.tuple = ropy.setdefault.error
ropy.setdefault.set = ropy.setdefault.error

ropy.add = {
	set = function(pytable, value)
		table.insert(pytable, value)
	end,

	error = function()
		error("add is only a set method")
	end
}

ropy.append = {
	list = function(pytable, value)
		table.insert(pytable, value)
	end,

	error = function()
		error("append is only a list method")
	end
}

ropy.append.tuple = ropy.append.error
ropy.append.dict = ropy.append.error
ropy.append.set = ropy.append.error

ropy.set = {
	dict = function(pytable)
		local result = {}
		for k, v in pairs(pytable) do
			result[k] = v
		end
		return result
	end,

	list = function(pytable)
		return pytable or {}
	end
}

ropy.set.set = ropy.set.list
ropy.set.tuple = ropy.set.list

ropy.all = {
	dict = function(pytable)
		if #pytable == 0 then return true end
		
		for k, _ in pairs(pytable) do
			if not k or k == 0 or (type(k)=="string" and #k==0) then
				return false
			end
		end
		return true
	end,

	list = function(pytable)
		if #pytable == 0 then return true end

		for _, v in pairs(pytable) do
			if not v or v == 0 or (type(v)=="string" and #v==0) then
				return false
			end
		end
		return true
	end
}

ropy.all.tuple = ropy.all.list
ropy.all.set = ropy.all.list

return ropy;