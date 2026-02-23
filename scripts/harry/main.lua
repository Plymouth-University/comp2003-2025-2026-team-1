local yaml = require "lyaml"
local grid = require "harry.grid"
local objects = require "harry.objects"
local patients = require "harry.patients"

local filePath = arg[1] or "../levels/OscarLevels/First Level Recreated/Level_1_players_2.yaml"

local file = io.open(filePath, "r")
if not file then
    print("Error: Could not open file: " .. filePath)
    os.exit(1)
end

local content = file:read("*a")
file:close()

local data = yaml.load(content)

if not data then
    print("Error: Could not parse YAML file")
    os.exit(1)
end

print("=== Level Analysis ===")
print("File: " .. filePath:match("([^/]+)$"))
print("")

if data.fileProperties and data.fileProperties.creatorName then
    print("Creator: " .. data.fileProperties.creatorName)
end

if data.sceneName then
    print("Scene: " .. data.sceneName)
end

if data.include then
    local includes = type(data.include) == "table" and table.concat(data.include, ", ") or tostring(data.include)
    print("Includes: " .. includes)
end

print("")

local rows, cols = grid.countDimensions(data.grid)
local activeTiles = grid.countNonEmptyCells(data.grid)
print(string.format("Grid: %d rows x %d columns", rows, cols))
print(string.format("Active tiles: %d", activeTiles))

print("")
print("Objects:")

local playerCount = objects.countReferences(data.gridObjects, "^p[1-4]$") + objects.countReferences(data.gridObjects, "^player")
print(string.format("  Players: %d", playerCount))

local bedCount = objects.countByDefinition(data.gridObjects, data.objectDefinitions, {"bed"}) 
    + objects.countReferences(data.gridObjects, "^b_[nsew]$") 
    + objects.countReferences(data.gridObjects, "bed")
print(string.format("  Beds: %d", bedCount))

local wallCount = objects.countByDefinition(data.gridObjects, data.objectDefinitions, {"wall"})
print(string.format("  Walls: %d", wallCount))

local patientCount = objects.countByDefinition(data.gridObjects, data.objectDefinitions, {"patient"})
print(string.format("  Patients (placed): %d", patientCount))

local cabinetCount = objects.countReferences(data.gridObjects, "cab") + objects.countReferences(data.gridObjects, "cabinet")
print(string.format("  Cabinets: %d", cabinetCount))

print("")

local gdPatientCount, patientInfo = patients.fromGlobalData(data.globalData)
if gdPatientCount > 0 then
    print(string.format("Patients (from globalData): %d", gdPatientCount))
    for _, p in ipairs(patientInfo) do
        local spawn = p.appearOnTurn and string.format(" (spawns turn %d)", p.appearOnTurn) or " (starting)"
        print(string.format("  %s: health=%d, need=%s%s", p.id, p.health, p.need, spawn))
    end
end

print("")
print("======================")
