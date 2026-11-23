-- Mirrors the apworld's rules (worlds/warriors_orochi/__init__.py).
SLOT = {
    story_character_requirement = 4,
    stage_locks = false,
    gaiden_unlock_checks = false,
    shuffled = nil,  -- set of character codes the server shuffled; nil = not connected yet
}

local function active(c)
    local obj = Tracker:FindObjectForCode(c)
    return obj ~= nil and obj.Active
end

local function count(c)
    local obj = Tracker:FindObjectForCode(c)
    if obj == nil then return 0 end
    return obj.AcquiredCount or 0
end

local function is_shuffled(c)
    if SLOT.shuffled == nil then return true end
    return SLOT.shuffled[c] == true
end

function story_pool(story)
    local n = 0
    for c, s in pairs(CHAR_STORY) do
        if s == story and is_shuffled(c) then n = n + 1 end
    end
    return n
end

function story_chars(story)
    local n = 0
    for c, s in pairs(CHAR_STORY) do
        if s == story and active(c) then n = n + 1 end
    end
    return n
end

function stage(story, n)
    n = tonumber(n)
    local req = math.min(SLOT.story_character_requirement, story_pool(story))
    local need = (req * (n - 1)) // (STAGES_PER_STORY - 1)
    if story_chars(story) < need then return false end
    if SLOT.stage_locks and count(STAGE_KEY[story]) < n - 1 then return false end
    return true
end

function hard()
    for _, story in ipairs({"Shu", "Wei", "Wu", "Samurai"}) do
        if stage(story, 5) then return true end
    end
    return false
end

function weapon(c)
    local w = WEAPON_CHAR[c]
    if w == nil then return false end
    if w.code ~= nil then
        if is_shuffled(w.code) then
            if not active(w.code) then return false end
        elseif not stage(w.story, w.stage) then
            return false
        end
    end
    return hard()
end
