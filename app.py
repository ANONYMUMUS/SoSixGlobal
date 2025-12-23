from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# We use a tiny script first to make sure the server boots!
SECRET_V3_SCRIPT = """
-- [[ SONIX PRECISION: FULL INTEGRATED CLIENT v3 ]]
local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local HttpService = game:GetService("HttpService")
local SocialService = game:GetService("SocialService")
local Players = game:GetService("Players")
local Player = Players.LocalPlayer
local PlayerGui = Player:WaitForChild("PlayerGui")

-- [[ CONFIGURATION ]]
local SERVER_URL = "https://sosixglobal.onrender.com"
local lastTimestamp = 0 
local canSend = true
local COOLDOWN_TIME = 2
local MAX_CHARS = 300

-- [[ STATE ]]
local CurrentMode = "GLOBAL" -- "GLOBAL", "FRIENDS", "DM"
local CurrentDMTarget = nil 
local AllFriendsCache = {} -- Store friends for search

-- [[ 1. UI ROOT ]]
local ScreenGui = Instance.new("ScreenGui", PlayerGui); ScreenGui.Name = "Sonix_Precision_Final"; ScreenGui.ResetOnSpawn = false

-- [[ 2. POSITIONS ]]
local ChatVisiblePos, ChatHiddenPos = UDim2.new(0.5, -160, 0.1, 0), UDim2.new(0.5, -160, 0.05, 0)
local MenuVisiblePos, MenuHiddenPos = UDim2.new(0.5, 170, 0.1, 0), UDim2.new(0.5, 140, 0.1, 0)

-- [[ 3. MAIN CONTAINER ]]
local MainContainer = Instance.new("CanvasGroup", ScreenGui)
MainContainer.Size = UDim2.new(0, 320, 0, 200); MainContainer.Position = ChatHiddenPos
MainContainer.BackgroundColor3 = Color3.fromRGB(12, 12, 12); MainContainer.Visible = false; MainContainer.GroupTransparency = 1; MainContainer.ZIndex = 5
Instance.new("UICorner", MainContainer).CornerRadius = UDim.new(0, 20)

local HeaderTitle = Instance.new("TextLabel", MainContainer)
HeaderTitle.Size = UDim2.new(1, -20, 0, 20); HeaderTitle.Position = UDim2.new(0, 10, 0, 5); HeaderTitle.BackgroundTransparency = 1
HeaderTitle.Text = "GLOBAL FEED"; HeaderTitle.TextColor3 = Color3.fromRGB(0, 255, 150); HeaderTitle.Font = Enum.Font.GothamBold; HeaderTitle.TextSize = 10; HeaderTitle.TextXAlignment = "Left"; HeaderTitle.ZIndex = 6

-- [[ 4. SCROLLING VIEWS ]]
local ViewContainer = Instance.new("Frame", MainContainer)
ViewContainer.Size = UDim2.new(1, 0, 1, -60); ViewContainer.Position = UDim2.new(0, 0, 0, 25); ViewContainer.BackgroundTransparency = 1; ViewContainer.ZIndex = 6

local function CreateScroll(name)
    local s = Instance.new("ScrollingFrame", ViewContainer); s.Name = name; s.Size = UDim2.new(1, -20, 1, 0); s.Position = UDim2.new(0, 10, 0, 0); s.BackgroundTransparency = 1; s.ScrollBarThickness = 2; s.ScrollBarImageColor3 = Color3.fromRGB(0, 255, 150); s.AutomaticCanvasSize = Enum.AutomaticSize.Y; s.Visible = false; s.ZIndex = 7
    Instance.new("UIListLayout", s).Padding = UDim.new(0, 6); return s
end

local GlobalView = CreateScroll("GlobalView"); GlobalView.Visible = true
local FriendsView = CreateScroll("FriendsView")
local DMView = CreateScroll("DMView")

-- [[ 5. SEARCH BAR (FRIENDS) ]]
local SearchBar = Instance.new("Frame", MainContainer); SearchBar.Size = UDim2.new(0, 120, 0, 20); SearchBar.Position = UDim2.new(1, -130, 0, 5); SearchBar.BackgroundColor3 = Color3.fromRGB(25, 25, 25); SearchBar.Visible = false; SearchBar.ZIndex = 8; Instance.new("UICorner", SearchBar).CornerRadius = UDim.new(0, 6)
local SearchInput = Instance.new("TextBox", SearchBar); SearchInput.Size = UDim2.new(1, -10, 1, 0); SearchInput.Position = UDim2.new(0, 5, 0, 0); SearchInput.BackgroundTransparency = 1; SearchInput.Text = ""; SearchInput.PlaceholderText = "Search Friends..."; SearchInput.TextColor3 = Color3.new(1,1,1); SearchInput.TextSize = 10; SearchInput.Font = Enum.Font.Gotham; SearchInput.ZIndex = 9

-- [[ 6. INPUT BAR (CHAT) ]]
local InputBar = Instance.new("Frame", MainContainer); InputBar.Size = UDim2.new(1, -20, 0, 30); InputBar.Position = UDim2.new(0, 10, 1, -40); InputBar.BackgroundTransparency = 1; InputBar.ZIndex = 8
local InputBox = Instance.new("TextBox", InputBar); InputBox.Size = UDim2.new(1, -40, 1, 0); InputBox.BackgroundColor3 = Color3.fromRGB(20,20,20); InputBox.TextColor3 = Color3.new(1,1,1); InputBox.PlaceholderText = "Message..."; InputBox.Text = ""; InputBox.ZIndex = 9; Instance.new("UICorner", InputBox); Instance.new("UIPadding", InputBox).PaddingLeft = UDim.new(0, 10)
local SendBtn = Instance.new("TextButton", InputBar); SendBtn.Size = UDim2.new(0, 35, 1, 0); SendBtn.Position = UDim2.new(1,-35,0,0); SendBtn.BackgroundColor3 = Color3.fromRGB(30,30,30); SendBtn.Text = "»"; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150); SendBtn.ZIndex = 9; Instance.new("UICorner", SendBtn)

local function UpdateLayout(mode)
    CurrentMode = mode
    -- Toggle Input Bar Visibility
    InputBar.Visible = (mode ~= "FRIENDS")
    -- Toggle Search Bar Visibility
    SearchBar.Visible = (mode == "FRIENDS")
    
    -- View Visibility
    GlobalView.Visible = (mode == "GLOBAL")
    FriendsView.Visible = (mode == "FRIENDS")
    DMView.Visible = (mode == "DM")
end

-- [[ 7. PROFILE SYSTEM (FIXED) ]]
local InfoLayer = Instance.new("Frame", ScreenGui); InfoLayer.Size = MainContainer.Size; InfoLayer.Position = ChatVisiblePos; InfoLayer.BackgroundTransparency = 1; InfoLayer.Visible = false; InfoLayer.ZIndex = 20 -- HIGH ZINDEX
local BluffOverlay = Instance.new("Frame", InfoLayer); BluffOverlay.Size = UDim2.new(1, 0, 1, 0); BluffOverlay.BackgroundColor3 = Color3.new(0, 0, 0); BluffOverlay.BackgroundTransparency = 1; BluffOverlay.ZIndex = 21; Instance.new("UICorner", BluffOverlay).CornerRadius = UDim.new(0, 20)
local ActiveBoxes = {}; local IsAnimating = false

local function ClearInfo()
    TweenService:Create(BluffOverlay, TweenInfo.new(0.2), {BackgroundTransparency = 1}):Play()
    for _, box in ipairs(ActiveBoxes) do box:Destroy() end
    ActiveBoxes = {}; InfoLayer.Visible = false; IsAnimating = false
end

local function CreateInfoBox(label, value, targetPos, delay)
    task.wait(delay); if not InfoLayer.Visible then return end
    local box = Instance.new("TextButton", InfoLayer); box.Size = UDim2.new(0, 85, 0, 28); box.Position = targetPos - UDim2.new(0, 0, 0, 20); box.BackgroundColor3 = Color3.fromRGB(45, 45, 45); box.BackgroundTransparency = 1; box.ZIndex = 30; box.Text = ""; Instance.new("UICorner", box).CornerRadius = UDim.new(1, 0)
    local txt = Instance.new("TextLabel", box); txt.Size = UDim2.new(1, 0, 1, 0); txt.BackgroundTransparency = 1; txt.RichText = true; txt.Text = "<b>"..label.."</b>\n"..tostring(value); txt.TextColor3 = Color3.new(1, 1, 1); txt.TextSize = 7; txt.ZIndex = 31
    box.MouseButton1Click:Connect(function() setclipboard(tostring(value)); txt.Text = "<b>COPIED!</b>"; task.wait(0.8); txt.Text = "<b>"..label.."</b>\n"..tostring(value) end)
    table.insert(ActiveBoxes, box)
    TweenService:Create(box, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = targetPos, BackgroundTransparency = 0.1}):Play()
end

local function Inspect(uid, name)
    if IsAnimating then return end
    ClearInfo(); InfoLayer.Visible = true; IsAnimating = true
    TweenService:Create(BluffOverlay, TweenInfo.new(0.3), {BackgroundTransparency = 0.4}):Play() -- Dim background more
    
    local age = 0; pcall(function() age = (Players:GetPlayerByUserId(uid) or {AccountAge = 0}).AccountAge end)
    local midPfp = Instance.new("ImageLabel", InfoLayer); midPfp.Size = UDim2.new(0, 40, 0, 40); midPfp.Position = UDim2.new(0.5, -20, 0.5, -20); midPfp.Image = Players:GetUserThumbnailAsync(uid, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); midPfp.BackgroundTransparency = 1; midPfp.ZIndex = 30; Instance.new("UICorner", midPfp).CornerRadius = UDim.new(1, 0); table.insert(ActiveBoxes, midPfp)

    task.spawn(function() CreateInfoBox("USERNAME", name:lower(), UDim2.new(0.5, -95, 0.5, -60), 0) end)
    task.spawn(function() CreateInfoBox("USERID", uid, UDim2.new(0.5, 10, 0.5, -60), 0.1) end)
    task.spawn(function() CreateInfoBox("STATUS", "ONLINE", UDim2.new(0.5, -105, 0.5, 10), 0.2) end)
    task.spawn(function() CreateInfoBox("AGE", age .. " DAYS", UDim2.new(0.5, 20, 0.5, 10), 0.3) end)
    task.wait(0.6); IsAnimating = false
end

-- [[ 8. MENU SYSTEM ]]
local MenuContainer = Instance.new("CanvasGroup", ScreenGui); MenuContainer.Size = UDim2.new(0, 100, 0, 220); MenuContainer.Position = MenuHiddenPos; MenuContainer.BackgroundTransparency = 1; MenuContainer.GroupTransparency = 1; MenuContainer.Visible = false
local MenuBtn = Instance.new("TextButton", MenuContainer); MenuBtn.Size = UDim2.new(0, 85, 0, 30); MenuBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MenuBtn.Text = ""; MenuBtn.ClipsDescendants = true; MenuBtn.ZIndex = 10; Instance.new("UICorner", MenuBtn).CornerRadius = UDim.new(0, 10)

local l1, l2, l3 = Instance.new("Frame", MenuBtn), Instance.new("Frame", MenuBtn), Instance.new("Frame", MenuBtn)
for i, l in ipairs({l1, l2, l3}) do l.Size = UDim2.new(0, 16, 0, 2); l.BackgroundColor3 = Color3.fromRGB(0, 255, 150); l.BorderSizePixel = 0; l.ZIndex = 11; l.AnchorPoint = Vector2.new(0.5, 0.5); l.Position = UDim2.new(0, 20, 0, 11 + (i-1)*4) end
local MenuLabel = Instance.new("TextLabel", MenuBtn); MenuLabel.Size = UDim2.new(0, 50, 1, 0); MenuLabel.Position = UDim2.new(0, 38, 0, 0); MenuLabel.BackgroundTransparency = 1; MenuLabel.Text = "MENU"; MenuLabel.TextColor3 = Color3.fromRGB(0, 255, 150); MenuLabel.TextSize = 10; MenuLabel.Font = Enum.Font.GothamBold; MenuLabel.TextXAlignment = "Left"

local subButtons = {}; local btnNames = {"CHAT", "FRIENDS", "PROFILE", "INFO"}
for i, name in ipairs(btnNames) do
    local b = Instance.new("TextButton", MenuContainer); b.Size = UDim2.new(0, 85, 0, 30); b.BackgroundColor3 = Color3.fromRGB(20, 20, 20); b.TextColor3 = Color3.new(1, 1, 1); b.Text = name; b.Font = Enum.Font.GothamBold; b.TextSize = 8; b.ZIndex = 5; b.Visible = false; b.BackgroundTransparency = 1; b.TextTransparency = 1; Instance.new("UICorner", b).CornerRadius = UDim.new(0, 10); subButtons[i] = b
end

local menuOpen = false
local function ToggleMenu(state)
    menuOpen = state
    if menuOpen then
        TweenService:Create(l1, TweenInfo.new(0.3), {Rotation = 45, Position = UDim2.new(0, 20, 0, 15)}):Play(); TweenService:Create(l2, TweenInfo.new(0.2), {BackgroundTransparency = 1}):Play(); TweenService:Create(l3, TweenInfo.new(0.3), {Rotation = -45, Position = UDim2.new(0, 20, 0, 15)}):Play()
        for i, b in ipairs(subButtons) do b.Visible = true; task.delay(i * 0.08, function() TweenService:Create(b, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = UDim2.new(0, 0, 0, 35 + (i-1)*35), BackgroundTransparency = 0, TextTransparency = 0}):Play() end) end
    else
        TweenService:Create(l1, TweenInfo.new(0.3), {Rotation = 0, Position = UDim2.new(0, 20, 0, 11)}):Play(); TweenService:Create(l2, TweenInfo.new(0.2), {BackgroundTransparency = 0}):Play(); TweenService:Create(l3, TweenInfo.new(0.3), {Rotation = 0, Position = UDim2.new(0, 20, 0, 19)}):Play()
        for _, b in ipairs(subButtons) do TweenService:Create(b, TweenInfo.new(0.25), {Position = UDim2.new(0, 0, 0, 0), BackgroundTransparency = 1, TextTransparency = 1}):Play() end
    end
end
MenuBtn.MouseButton1Click:Connect(function() ToggleMenu(not menuOpen) end)

-- [[ 9. FRIENDS & SEARCH LOGIC ]]
local function RenderFriendList(filter)
    for _, c in pairs(FriendsView:GetChildren()) do if c:IsA("Frame") then c:Destroy() end end
    for _, f in ipairs(AllFriendsCache) do
        if not filter or string.find(f.Username:lower(), filter:lower()) then
            local row = Instance.new("Frame", FriendsView); row.Size = UDim2.new(1, 0, 0, 40); row.BackgroundColor3 = Color3.fromRGB(25, 25, 25); row.ZIndex = 7; Instance.new("UICorner", row).CornerRadius = UDim.new(0, 8)
            local av = Instance.new("ImageLabel", row); av.Size = UDim2.new(0, 30, 0, 30); av.Position = UDim2.new(0, 5, 0, 5); av.BackgroundTransparency = 1; av.Image = Players:GetUserThumbnailAsync(f.Id, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); av.ZIndex = 8; Instance.new("UICorner", av).CornerRadius = UDim.new(1,0)
            local nm = Instance.new("TextLabel", row); nm.Size = UDim2.new(0, 100, 0, 20); nm.Position = UDim2.new(0, 40, 0, 10); nm.BackgroundTransparency = 1; nm.Text = f.Username; nm.TextColor3 = Color3.new(1,1,1); nm.Font = Enum.Font.GothamBold; nm.TextSize = 12; nm.TextXAlignment = "Left"; nm.ZIndex = 8
            local chatBtn = Instance.new("TextButton", row); chatBtn.Size = UDim2.new(0, 60, 0, 24); chatBtn.Position = UDim2.new(1, -65, 0, 8); chatBtn.BackgroundColor3 = Color3.fromRGB(0, 255, 150); chatBtn.Text = "CHAT"; chatBtn.TextColor3 = Color3.fromRGB(12, 12, 12); chatBtn.Font = Enum.Font.GothamBold; chatBtn.TextSize = 10; chatBtn.ZIndex = 9; Instance.new("UICorner", chatBtn).CornerRadius = UDim.new(0, 6)
            chatBtn.MouseButton1Click:Connect(function()
                CurrentDMTarget = {UserId = f.Id, Name = f.Username}
                HeaderTitle.Text = "PRIVATE: @" .. f.Username:upper(); HeaderTitle.TextColor3 = Color3.fromRGB(255, 0, 150)
                -- CLEAR DM VIEW ON SWITCH
                for _, m in pairs(DMView:GetChildren()) do if m:IsA("Frame") then m:Destroy() end end
                UpdateLayout("DM")
                ToggleMenu(false)
            end)
        end
    end
end

local function LoadFriends()
    HeaderTitle.Text = "FRIENDS"; HeaderTitle.TextColor3 = Color3.fromRGB(0, 255, 150)
    UpdateLayout("FRIENDS")
    AllFriendsCache = {} -- Reset
    task.spawn(function()
        local success, pages = pcall(function() return Players:GetFriendsAsync(Player.UserId) end)
        if success then
            while true do
                for _, item in ipairs(pages:GetCurrentPage()) do table.insert(AllFriendsCache, item) end
                if pages.IsFinished then break end
                pages:AdvanceToNextPageAsync()
            end
            RenderFriendList(nil)
        end
    end)
end

SearchInput:GetPropertyChangedSignal("Text"):Connect(function() RenderFriendList(SearchInput.Text) end)

-- [[ 10. MENU CONNECTIONS ]]
subButtons[1].MouseButton1Click:Connect(function() 
    HeaderTitle.Text = "GLOBAL FEED"; HeaderTitle.TextColor3 = Color3.fromRGB(0, 255, 150)
    UpdateLayout("GLOBAL")
    ToggleMenu(false) -- Smooth close
end)
subButtons[2].MouseButton1Click:Connect(function() LoadFriends(); ToggleMenu(false) end) -- Friends
subButtons[3].MouseButton1Click:Connect(function() Inspect(Player.UserId, Player.Name) end) -- Profile

-- [[ 11. MESSAGING & SERVER ]]
local function AddMsg(scroll, uid, user, text, isSystem)
    if not scroll.Visible and not isSystem then return end -- Optimization
    local msgFrame = Instance.new("Frame", scroll); msgFrame.Size = UDim2.new(1, 0, 0, 0); msgFrame.BackgroundTransparency = 1; msgFrame.AutomaticSize = "Y"; msgFrame.ZIndex = 7
    local pfp = Instance.new("ImageButton", msgFrame); pfp.Size = UDim2.new(0, 26, 0, 26); pfp.Position = UDim2.new(0, 0, 0, 2); pfp.Image = Players:GetUserThumbnailAsync(uid, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); pfp.ZIndex = 8; Instance.new("UICorner", pfp).CornerRadius = UDim.new(1, 0)
    pfp.MouseButton1Click:Connect(function() Inspect(uid, user) end)
    
    local content = Instance.new("TextLabel", msgFrame); content.Size = UDim2.new(1, -32, 0, 0); content.Position = UDim2.new(0, 32, 0, 11); content.BackgroundTransparency = 1; content.TextColor3 = Color3.new(1,1,1); content.Text = text; content.TextSize = 10; content.TextXAlignment = "Left"; content.TextWrapped = true; content.AutomaticSize = "Y"; content.ZIndex = 8
    local header = Instance.new("TextLabel", msgFrame); header.Size = UDim2.new(1, -32, 0, 10); header.Position = UDim2.new(0, 32, 0, 0); header.BackgroundTransparency = 1; header.TextColor3 = Color3.fromRGB(160, 160, 160); header.Text = "<b>" .. user:lower() .. "</b>"; header.TextSize = 7; header.RichText = true; header.TextXAlignment = "Left"; header.ZIndex = 8
    task.defer(function() scroll.CanvasPosition = Vector2.new(0, scroll.AbsoluteContentSize.Y) end)
end

local function Send(txt)
    if not canSend or txt == "" then return end
    canSend = false; SendBtn.TextColor3 = Color3.fromRGB(80, 80, 80)
    local payload = {
        ["PlayerName"] = Player.Name, ["UserId"] = Player.UserId, ["Message"] = txt,
        ["Type"] = (CurrentMode == "DM" and "private" or "global"),
        ["TargetId"] = (CurrentMode == "DM" and CurrentDMTarget.UserId or nil)
    }
    task.spawn(function() pcall(function() request({Url = SERVER_URL .. "/send", Method = "POST", Headers = {["Content-Type"] = "application/json"}, Body = HttpService:JSONEncode(payload)}) end) end)
    task.delay(COOLDOWN_TIME, function() canSend = true; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150) end)
end
SendBtn.MouseButton1Click:Connect(function() if canSend and InputBox.Text ~= "" then local t = InputBox.Text; InputBox.Text = ""; InputBox:ReleaseFocus(); Send(t) end end)

task.spawn(function()
    while task.wait(3) do
        local success, response = pcall(function() return request({Url = SERVER_URL .. "/get_messages?after=" .. lastTimestamp .. "&uid=" .. Player.UserId, Method = "GET"}) end)
        if success and response.StatusCode == 200 then
            local messages = HttpService:JSONDecode(response.Body)
            for _, m in ipairs(messages) do 
                if m.Timestamp > lastTimestamp then 
                    lastTimestamp = m.Timestamp
                    if (m.Type == "global" or not m.Type) then AddMsg(GlobalView, m.UserId, m.PlayerName, m.Message, false) 
                    elseif m.Type == "private" then
                        -- IF message is FOR me OR sent BY me to current target
                        if (m.TargetId == Player.UserId and CurrentMode == "DM" and CurrentDMTarget and CurrentDMTarget.UserId == m.UserId) or
                           (m.UserId == Player.UserId and CurrentMode == "DM" and CurrentDMTarget and CurrentDMTarget.UserId == m.TargetId) then
                            AddMsg(DMView, m.UserId, m.PlayerName, m.Message, false)
                        end
                    end
                end 
            end
        end
    end
end)

-- [[ 12. S BUTTON ]]
local MainBtn = Instance.new("TextButton", ScreenGui); MainBtn.Size = UDim2.new(0, 35, 0, 30); MainBtn.Position = UDim2.new(0.5, -205, 0.1, 0); MainBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MainBtn.Text = "S"; MainBtn.TextColor3 = Color3.fromRGB(0, 255, 150); MainBtn.Font = Enum.Font.GothamBold; MainBtn.TextSize = 14; Instance.new("UICorner", MainBtn).CornerRadius = UDim.new(0, 10)
MainBtn.MouseButton1Click:Connect(function()
    if MainContainer.Visible then
        ToggleMenu(false); TweenService:Create(MenuContainer, TweenInfo.new(0.3), {Position = MenuHiddenPos, GroupTransparency = 1}):Play(); task.wait(0.15); TweenService:Create(MainContainer, TweenInfo.new(0.3), {Position = ChatHiddenPos, GroupTransparency = 1}):Play(); task.wait(0.3); MainContainer.Visible = false; MenuContainer.Visible = false
    else
        HeaderTitle.Text = "GLOBAL FEED"; UpdateLayout("GLOBAL") -- Default to global on open
        MainContainer.Visible = true; MainContainer.GroupTransparency = 1; MainContainer.Position = ChatHiddenPos; TweenService:Create(MainContainer, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = ChatVisiblePos, GroupTransparency = 0}):Play(); task.wait(0.2); MenuContainer.Visible = true; MenuContainer.GroupTransparency = 1; MenuContainer.Position = MenuHiddenPos; TweenService:Create(MenuContainer, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = MenuVisiblePos, GroupTransparency = 0}):Play()
    end
end)"""

@app.route('/')
def home():
    return "Sonix Server is Online", 200

@app.route('/load_sonix', methods=['GET'])
def load_sonix():
    return SECRET_V3_SCRIPT, 200

if __name__ == '__main__':
    # Render needs port 10000
    app.run(host='0.0.0.0', port=10000)
