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

ropy.evaluate = function(anything)
	if type(anything) == "table" then
		if ropy.len(anything) == 0 then
			return false
		else
			return anything;
		end
	end

	if type(anything) == "string" then
		if #anything == 0 then
			return false
		else
			return anything;
		end
	end

	if type(anything) == "number" then
		if anything == 0 then
			return false
		else
			return anything
		end
	end

	return anything;
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
	while i < stop do
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

ropy.slice = {
	list = function(pytable, start, stop, step)
		-- Replicate python's slice(start, stop, step) behaviour
		
		if step == nil then step = 1 end
		if stop == nil then stop = #pytable end
		if start == nil then start = 1 end

		if start < 0 then start = #pytable + start end
		if stop < 0 then stop = #pytable + stop end
		
		if start > stop then return {} end
		if step == 0 then return {} end

		if step > 1 then
			local result = {}
			for i = start, stop, step do
				table.insert(result, pytable[i])
			end
			return result
		elseif step < 1 then
			local result = {}
			for i = stop, start, step do
				table.insert(result, pytable[i])
			end
			return result
		else
			return ropy.range(start, stop)
		end
	end,

	error = function()
		error("slice is only a list or tuple method")
	end
}

ropy.slice.dict = ropy.slice.error
ropy.slice.set = ropy.slice.error
ropy.slice.tuple = ropy.slice.list

ropy.concat = {
	list = function(pytable, other)
		local result = {}
		for _, v in pairs(pytable) do
			table.insert(result, v)
		end
		for _, v in pairs(other) do
			table.insert(result, v)
		end
		return result
	end,

	error = function()
		error("concat is only a list, set or tuple method")
	end
}

ropy.concat.dict = ropy.concat.error
ropy.concat.set = ropy.concat.list
ropy.concat.tuple = ropy.concat.list

return ropy;