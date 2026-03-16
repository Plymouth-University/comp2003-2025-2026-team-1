local patients = {}

function patients.fromGlobalData(globalData)
    if not globalData then return 0, {} end
    local count = 0
    local patientInfo = {}
    for id, props in pairs(globalData) do
        if type(props) == "table" and props.health then
            count = count + 1
            table.insert(patientInfo, {
                id = id,
                health = props.health,
                need = props.need or "unknown",
                appearOnTurn = props.appearOnTurn
            })
        end
    end
    table.sort(patientInfo, function(a, b) return (a.appearOnTurn or 0) < (b.appearOnTurn or 0) end)
    return count, patientInfo
end

return patients
