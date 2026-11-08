-- Interpreter workload: allocation-heavy trees, tables, strings and numeric loops.
local function bottom_up(d)
  if d == 0 then return {} end
  d = d - 1
  return { bottom_up(d), bottom_up(d) }
end
local function check(t)
  if t[1] then return 1 + check(t[1]) + check(t[2]) end
  return 1
end
local function binary_trees(n)
  local total = 0
  local long = bottom_up(n)
  for d = 4, n, 2 do
    local iters = 1 << (n - d + 4)
    for _ = 1, iters do total = total + check(bottom_up(d)) end
  end
  return total + check(long)
end
local function fannkuch(n)
  local p, q, s, sign, maxflips, sum = {}, {}, {}, 1, 0, 0
  for i = 1, n do p[i] = i; q[i] = i; s[i] = i end
  while true do
    local q1 = p[1]
    if q1 ~= 1 then
      for i = 2, n do q[i] = p[i] end
      local flips = 1
      while true do
        local qq = q[q1]
        if qq == 1 then sum = sum + sign * flips; if flips > maxflips then maxflips = flips end; break end
        q[q1] = q1
        if q1 >= 4 then local i, j = 2, q1 - 1; repeat q[i], q[j] = q[j], q[i]; i = i + 1; j = j - 1 until i >= j end
        q1 = qq; flips = flips + 1
      end
    end
    if sign == 1 then p[2], p[1] = p[1], p[2]; sign = -1
    else p[2], p[3] = p[3], p[2]; sign = 1
      for i = 3, n do
        local sx = s[i]
        if sx ~= 1 then s[i] = sx - 1; break end
        if i == n then return sum, maxflips end
        s[i] = i
        local t = p[1]; for j = 1, i do p[j] = p[j + 1] end; p[i + 1] = t
      end
    end
  end
end
local function strings(n)
  local parts, h = {}, 0
  for i = 1, n do
    local s = string.format("key%07d:%s", i, string.rep(string.char(97 + i % 26), i % 17))
    parts[#parts + 1] = s:upper():gsub("K", "k")
    if #parts > 1000 then h = h + #table.concat(parts, ","); parts = {} end
  end
  local t = {}
  for i = 1, n // 4 do t["k" .. (i * 7919 % n)] = i end
  local c = 0; for _ in pairs(t) do c = c + 1 end
  return h + c
end
local function spectral(n)
  local function A(i, j) local ij = i + j - 1; return 1.0 / (ij * (ij - 1) * 0.5 + i) end
  local function Av(x, y, N) for i = 1, N do local a = 0 for j = 1, N do a = a + x[j] * A(i, j) end y[i] = a end end
  local function Atv(x, y, N) for i = 1, N do local a = 0 for j = 1, N do a = a + x[j] * A(j, i) end y[i] = a end end
  local u, v, t = {}, {}, {}
  for i = 1, n do u[i] = 1 end
  for _ = 1, 10 do Av(u, t, n); Atv(t, v, n); Av(v, t, n); Atv(t, u, n) end
  local vBv, vv = 0, 0
  for i = 1, n do vBv = vBv + u[i] * v[i]; vv = vv + v[i] * v[i] end
  return math.sqrt(vBv / vv)
end
print("binary_trees", binary_trees(16))
print("fannkuch", fannkuch(9))
print("strings", strings(400000))
print(string.format("spectral %.9f", spectral(350)))
