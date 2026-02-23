local objects = {}

function objects.countReferences(gridObjects, pattern)
    if not gridObjects then return 0 end
    local count = 0
    for _, objs in pairs(gridObjects) do
        if type(objs) == "table" then
            for _, obj in ipairs(objs) do
                if type(obj) == "string" and obj:match(pattern) then
                    count = count + 1
                elseif type(obj) == "table" and obj.id then
                    if obj.id:match(pattern) then
                        count = count + 1
                    end
                end
            end
        end
    end
    return count
end

local function isObjectOfType(objDef, keywords)
    if not objDef then return false end
    if objDef.tags then
        for _, tag in ipairs(objDef.tags) do
            for _, keyword in ipairs(keywords) do
                if tag:lower():find(keyword:lower()) then
                    return true
                end
            end
        end
    end
    if objDef.mapObject then
        for _, keyword in ipairs(keywords) do
            if objDef.mapObject:lower():find(keyword:lower()) then
                return true
            end
        end
    end
    return false
end

function objects.countByDefinition(gridObjects, objectDefinitions, keywords)
    if not gridObjects or not objectDefinitions then return 0 end
    local count = 0
    local countedCells = {}
    
    for cellCode, objs in pairs(gridObjects) do
        if type(objs) == "table" and not countedCells[cellCode] then
            for _, objRef in ipairs(objs) do
                local defName = type(objRef) == "string" and objRef or (type(objRef) == "table" and objRef.id)
                if defName and objectDefinitions[defName] then
                    if isObjectOfType(objectDefinitions[defName], keywords) then
                        count = count + 1
                        countedCells[cellCode] = true
                        break
                    end
                elseif defName then
                    for _, keyword in ipairs(keywords) do
                        if defName:lower():find(keyword:lower()) then
                            count = count + 1
                            countedCells[cellCode] = true
                            break
                        end
                    end
                end
            end
        end
    end
    return count
end

return objects
