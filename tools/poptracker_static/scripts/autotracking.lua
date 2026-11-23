-- Archipelago autotracking: items, checked locations and options from slot_data.
local FLAG_CODES = {"opt_gaiden_stages", "opt_last_gaiden", "opt_gaiden_unlocks", "opt_weapons", "opt_abilities"}

local function set_flag(code, on)
    local obj = Tracker:FindObjectForCode(code)
    if obj then obj.Active = on and true or false end
end

function onClear(slot_data)
    for _, v in pairs(ITEM_MAPPING) do
        local obj = Tracker:FindObjectForCode(v[1])
        if obj then
            if v[2] == "toggle" then obj.Active = false else obj.AcquiredCount = 0 end
        end
    end
    for _, path in pairs(LOCATION_MAPPING) do
        local obj = Tracker:FindObjectForCode(path)
        if obj then obj.AvailableChestCount = obj.ChestCount end
    end
    slot_data = slot_data or {}
    SLOT.story_character_requirement = slot_data.story_character_requirement or 4
    SLOT.stage_locks = slot_data.stage_locks == true
    SLOT.gaiden_unlock_checks = slot_data.gaiden_unlock_checks == true
    if slot_data.shuffled_characters then
        SLOT.shuffled = {}
        for _, name in pairs(slot_data.shuffled_characters) do
            local c = CHAR_CODE_BY_NAME[name]
            if c then SLOT.shuffled[c] = true end
        end
    end
    set_flag("opt_gaiden_stages", slot_data.gaiden_stage_checks)
    set_flag("opt_last_gaiden", slot_data.last_gaiden_checks)
    set_flag("opt_gaiden_unlocks", slot_data.gaiden_unlock_checks)
    set_flag("opt_weapons", slot_data.fourth_weapon_checks)
    set_flag("opt_abilities", slot_data.ability_shuffle)
    local ko = slot_data.ko_milestone_max or 0
    for _, c in ipairs(KO_MILESTONES) do set_flag("opt_ko_" .. c, c <= ko) end
end

function onItem(index, item_id, item_name, player_number)
    local v = ITEM_MAPPING[item_id]
    if not v then return end
    local obj = Tracker:FindObjectForCode(v[1])
    if not obj then return end
    if v[2] == "toggle" then
        obj.Active = true
    else
        obj.AcquiredCount = obj.AcquiredCount + obj.Increment
    end
end

function onLocation(location_id, location_name)
    local path = LOCATION_MAPPING[location_id]
    if not path then return end
    local obj = Tracker:FindObjectForCode(path)
    if obj and obj.AvailableChestCount > 0 then
        obj.AvailableChestCount = obj.AvailableChestCount - 1
    end
end

Archipelago:AddClearHandler("warriors orochi clear", onClear)
Archipelago:AddItemHandler("warriors orochi item", onItem)
Archipelago:AddLocationHandler("warriors orochi location", onLocation)
