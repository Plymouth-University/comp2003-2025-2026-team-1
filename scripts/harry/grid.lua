local grid = {}

function grid.countDimensions(gridStr)
    if not gridStr then return 0, 0 end
    local rows = 0
    local maxCols = 0
    for line in gridStr:gmatch("[^\n]+") do
        if line:match("%S") then
            rows = rows + 1
            local colCount = 0
            for _ in line:gmatch("[^,%s]+") do
                colCount = colCount + 1
            end
            if colCount > maxCols then maxCols = colCount end
        end
    end
    return rows, maxCols
end

function grid.countNonEmptyCells(gridStr)
    if not gridStr then return 0 end
    local count = 0
    for cell in gridStr:gmatch("[^,%s]+") do
        if cell ~= "__" and cell:match("%S") then
            count = count + 1
        end
    end
    return count
end

return grid
