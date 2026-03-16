package.path = package.path .. ";../shared/?.lua"

local function getColumnLetter(index)
    if index <= 9 then
        return string.char(96 + index) -- a-i
    else
        return string.char(64 + index - 9) -- A-R...
    end
end

local function getRowLetter(index)
    if index <= 9 then
        return tostring(index)
    else
        return string.char(64 + index - 9) -- A, B, C...
    end
end

local function parseArgs(args)
    local width = 9
    local height = 10
    
    for i, v in ipairs(args) do
        if v == "--width" or v == "-w" then
            width = tonumber(args[i + 1])
        elseif v == "--height" or v == "-h" then
            height = tonumber(args[i + 1])
        end
    end
    
    return width, height
end

local function generateGrid(width, height)
    local cols = {}
    for i = 1, width do
        table.insert(cols, getColumnLetter(i))
    end
    
    local rows = {}
    for i = 1, height do
        table.insert(rows, getRowLetter(i))
    end
    
    local gridStr = ""
    
    -- First header row: starts with gm
    gridStr = gridStr .. "gm,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,\n"
    
    -- Remaining header rows: 7 more rows (9 + 9 + 10 = 28 cells)
    for i = 2, 8 do
        gridStr = gridStr .. "__,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,\n"
    end
    
    -- Blank line between header and middle
    gridStr = gridStr .. "\n"
    
    -- Middle section: height rows with play area (8 + width + 4 = 12 + width cells)
    for _, row in ipairs(rows) do
        local playCells = {}
        for _, col in ipairs(cols) do
            table.insert(playCells, col .. row)
        end
        
        gridStr = gridStr .. "__,__,__,__,__,__,__,__, " .. table.concat(playCells, ",") .. ", __,__,__,__,__,\n"
    end
    
    -- Blank line between middle and footer
    gridStr = gridStr .. "\n"
    
    -- Footer: 6 rows of empty tiles (9 + 9 + 10 = 28 cells)
    for i = 1, 6 do
        gridStr = gridStr .. "__,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,\n"
    end
    
    return gridStr, cols, rows
end

local function generateGridObjects(width, height)
    local objects = {}
    
    local rows = {}
    for i = 1, height do
        table.insert(rows, getRowLetter(i))
    end
    
    -- Calculate p1 and p2 positions (center of the grid)
    local p1Row = math.floor(height / 2)
    local p2Row = p1Row + 1
    local p1Col = math.floor(width / 2) + 1
    local p2Col = p1Col
    
    local p1Key = getColumnLetter(p1Col) .. rows[p1Row]
    local p2Key = getColumnLetter(p2Col) .. rows[p2Row]
    
    for _, row in ipairs(rows) do
        for i = 1, width do
            local key = getColumnLetter(i) .. row
            if key == p1Key then
                objects[key] = {"p1"}
            elseif key == p2Key then
                objects[key] = {"p2"}
            else
                objects[key] = {}
            end
        end
    end
    
    return objects, p1Key, p2Key
end

local function generateYAML(width, height)
    local gridStr, cols, rows = generateGrid(width, height)
    local gridObjects, p1Key, p2Key = generateGridObjects(width, height)
    
    local yaml = {}
    
    table.insert(yaml, "include: [LevelsShared.yaml]")
    table.insert(yaml, "")
    table.insert(yaml, "fileProperties:")
    table.insert(yaml, "  creatorName: LuaGenerator")
    table.insert(yaml, "")
    table.insert(yaml, "sceneName: OriginalWorld")
    table.insert(yaml, "")
    table.insert(yaml, "cameraSettings:")
    table.insert(yaml, "  type: static")
    table.insert(yaml, "  postProcessing:")
    table.insert(yaml, "    depthOfField: { enabled: false }")
    table.insert(yaml, "")
    table.insert(yaml, "grid: |")
    
    local prevLineNum = 0
    for line in gridStr:gmatch("[^\n]+") do
        local lineNum = 0
        if line:gmatch("%S") then
            lineNum = lineNum + 1
        end
        
        -- Add blank line after row 8 (before middle section) and after row 8+height (before footer)
        if prevLineNum == 8 or prevLineNum == 8 + height then
            table.insert(yaml, "")
        end
        
        if line:gmatch("%S") then
            table.insert(yaml, "  " .. line)
        end
        prevLineNum = prevLineNum + 1
    end
    
    table.insert(yaml, "")
    table.insert(yaml, "gridObjects:")
    
    local sortedKeys = {}
    for key, _ in pairs(gridObjects) do
        table.insert(sortedKeys, key)
    end
    table.sort(sortedKeys, function(a, b)
        local aRow = a:sub(-1)
        local bRow = b:sub(-1)
        local aCol = a:sub(1, -2)
        local bCol = b:sub(1, -2)
        
        local function getColNum(col)
            if #col == 1 then
                local c = col:byte()
                if c >= 97 then -- a-i
                    return c - 96
                else -- A-R
                    return c - 64 + 26
                end
            else
                local c1, c2 = col:byte(1, 2)
                local num1 = (c1 >= 97 and c1 - 96 or c1 - 64 + 26)
                local num2 = (c2 >= 97 and c2 - 96 or c2 - 64 + 26)
                return num1 * 26 + num2
            end
        end
        
        local function getRowNum(row)
            local r = row:byte()
            if r >= 49 and r <= 57 then -- 1-9
                return tonumber(row)
            else -- A, B, etc.
                return r - 54 + 9
            end
        end
        
        local aRowNum = getRowNum(aRow)
        local bRowNum = getRowNum(bRow)
        
        if aRowNum ~= bRowNum then
            return aRowNum < bRowNum
        end
        
        local aColNum = getColNum(aCol)
        local bColNum = getColNum(bCol)
        return aColNum < bColNum
    end)
    
    local prevRow = nil
    for _, key in ipairs(sortedKeys) do
        local objs = gridObjects[key]
        
        -- Get the row letter from the key
        local currentRow = key:sub(-1)
        
        -- Add blank line when row changes
        if prevRow ~= nil and currentRow ~= prevRow then
            table.insert(yaml, "")
        end
        
        if #objs == 0 then
            table.insert(yaml, "  " .. key .. ": []")
        else
            table.insert(yaml, "  " .. key .. ": [" .. table.concat(objs, ", ") .. "]")
        end
        
        prevRow = currentRow
    end
    
    table.insert(yaml, "")
    table.insert(yaml, "objectDefinitions:")
    table.insert(yaml, "")
    table.insert(yaml, "sounds:")
    table.insert(yaml, "")
    table.insert(yaml, "globalData:")
    
    return table.concat(yaml, "\n")
end

-- Main
local width, height = parseArgs(arg)

if width < 1 or height < 1 then
    print("Error: Width and height must be positive integers")
    os.exit(1)
end

if width > 34 or height > 34 then
    print("Error: Maximum width and height is 34")
    os.exit(1)
end

local yamlOutput = generateYAML(width, height)
print(yamlOutput)
