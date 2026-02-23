local yaml = require "lyaml"

local filePath = arg[1] or "../levels/OscarLevels/First Level Recreated/Level_1_players_2.yaml"

local file = io.open(filePath, "r")
if not file then
    print("Error: Could not open file: " .. filePath)
    os.exit(1)
end

local content = file:read("*a")
file:close()

local data = yaml.load(content)

print(yaml.dump({data}))
