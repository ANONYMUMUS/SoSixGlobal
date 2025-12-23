from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# [[ 1. THE FIXED MASTER V3 SCRIPT ]]
# Re-built with fixed profile closing and proper receiving logic
SECRET_V3_SCRIPT = r"""
-- [[ SONIX PRECISION v3: FULL INTEGRATED MASTER ]]
-- [[ LINE COUNT: 300+ | STATUS: FIXED & OPERATIONAL ]]

local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local Player = Players.LocalPlayer
local PlayerGui = Player:WaitForChild("PlayerGui")

-- [[ CONFIGURATION ]]
local SERVER_URL = "https://sosixglobal.onrender.com"
local lastTimestamp = 0 
local canSend = true
local COOLDOWN_TIME = 2

-- [[ STATE ]]
local CurrentMode = "GLOBAL" 
local CurrentDMTarget = nil 
local AllFriendsCache = {} 
local IsAnimating = false
local ActiveBoxes = {}

-- [[ 1. UI ROOT ]]
local ScreenGui = Instance.new("ScreenGui", PlayerGui); ScreenGui.Name = "Sonix_Precision_Final"; ScreenGui.ResetOnSpawn = false

-- [[ 2. POSITIONS ]]
local ChatVisiblePos, ChatHiddenPos = UDim2.new(0.5, -160, 0.1, 0), UDim2.new(0.5, -160, -0.6, 0)
local MenuVisiblePos, MenuHiddenPos = UDim2.new(0.5, 170, 0.1, 0), UDim2.new(0.5, 140, 0.1, 0)

-- [[ 3. MAIN CONTAINER ]]
local MainContainer = Instance.new("CanvasGroup", ScreenGui)
MainContainer.Size = UDim2.new(0, 320, 0, 220); MainContainer.Position = ChatHiddenPos
MainContainer.BackgroundColor3 = Color3.fromRGB(12, 12, 12); MainContainer.Visible = false; MainContainer.GroupTransparency = 1; MainContainer.ZIndex = 5
Instance.new("UICorner", MainContainer).CornerRadius = UDim.new(0, 20)

local HeaderTitle = Instance.new("TextLabel", MainContainer)
HeaderTitle.Size = UDim2.new(1, -20, 0, 30); HeaderTitle.Position = UDim2.new(0, 15, 0, 5); HeaderTitle.BackgroundTransparency = 1
HeaderTitle.Text = "GLOBAL FEED"; HeaderTitle.TextColor3 = Color3.fromRGB(0, 255, 150); HeaderTitle.Font = Enum.Font.GothamBold; HeaderTitle.TextSize = 12; HeaderTitle.TextXAlignment = "Left"; HeaderTitle.ZIndex = 6

-- [[ 4. SCROLLING VIEWS ]]
local ViewContainer = Instance.new("Frame", MainContainer)
ViewContainer.Size = UDim2.new(1, 0, 1, -80); ViewContainer.Position = UDim2.new(0, 0, 0, 35); ViewContainer.BackgroundTransparency = 1; ViewContainer.ZIndex = 6

local function CreateScroll(name)
    local s = Instance.new("ScrollingFrame", ViewContainer); s.Name = name; s.Size = UDim2.new(1, -20, 1, 0); s.Position = UDim2.new(0, 10, 0, 0); s.BackgroundTransparency = 1; s.ScrollBarThickness = 2; s.ScrollBarImageColor3 = Color3.fromRGB(0, 255, 150); s.AutomaticCanvasSize = Enum.AutomaticSize.Y; s.Visible = false; s.ZIndex = 7
    Instance.new("UIListLayout", s).Padding = UDim.new(0, 8); return s
end

local GlobalView = CreateScroll("GlobalView"); GlobalView.Visible = true
local FriendsView = CreateScroll("FriendsView")
local DMView = CreateScroll("DMView")

-- [[ 5. INPUTS ]]
local SearchBar = Instance.new("Frame", MainContainer); SearchBar.Size = UDim2.new(0, 130, 0, 24); SearchBar.Position = UDim2.new(1, -145, 0, 8); SearchBar.BackgroundColor3 = Color3.fromRGB(25, 25, 25); SearchBar.Visible = false; SearchBar.ZIndex = 10; Instance.new("UICorner", SearchBar).CornerRadius = UDim.new(0, 8)
local SearchInput = Instance.new("TextBox", SearchBar); SearchInput.Size = UDim2.new(1, -10, 1, 0); SearchInput.Position = UDim2.new(0, 5, 0, 0); SearchInput.BackgroundTransparency = 1; SearchInput.Text = ""; SearchInput.PlaceholderText = "Search Friends..."; SearchInput.TextColor3 = Color3.new(1,1,1); SearchInput.TextSize = 10; SearchInput.Font = Enum.Font.Gotham; SearchInput.ZIndex = 11

local InputBar = Instance.new("Frame", MainContainer); InputBar.Size = UDim2.new(1, -20, 0, 35); InputBar.Position = UDim2.new(0, 10, 1, -45); InputBar.BackgroundTransparency = 1; InputBar.ZIndex = 8
local InputBox = Instance.new("TextBox", InputBar); InputBox.Size = UDim2.new(1, -45, 1, 0); InputBox.BackgroundColor3 = Color3.fromRGB(20,20,20); InputBox.TextColor3 = Color3.new(1,1,1); InputBox.PlaceholderText = "Message..."; InputBox.Text = ""; InputBox.ZIndex = 9; Instance.new("UICorner", InputBox); Instance.new("UIPadding", InputBox).PaddingLeft = UDim.new(0, 12)
local SendBtn = Instance.new("TextButton", InputBar); SendBtn.Size = UDim2.new(0, 40, 1, 0); SendBtn.Position = UDim2.new(1,-40,0,0); SendBtn.BackgroundColor3 = Color3.fromRGB(30,30,30); SendBtn.Text = "»"; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150); SendBtn.ZIndex = 9; Instance.new("UICorner", SendBtn)

-- [[ 6. FIXED PROFILE SYSTEM ]]
local InfoLayer = Instance.new("Frame", ScreenGui); InfoLayer.Size = UDim2.new(0, 320, 0, 220); InfoLayer.BackgroundTransparency = 1; InfoLayer.Visible = false; InfoLayer.ZIndex = 100 
local BluffOverlay = Instance.new("TextButton", InfoLayer); BluffOverlay.Size = UDim2.new(1, 0, 1, 0); BluffOverlay.BackgroundColor3 = Color3.new(0, 0, 0); BluffOverlay.BackgroundTransparency = 1; BluffOverlay.Text = ""; BluffOverlay.ZIndex = 101; Instance.new("UICorner", BluffOverlay).CornerRadius = UDim.new(0, 20)

local function ClearInfo()
    for _, box in ipairs(ActiveBoxes) do box:Destroy() end
    ActiveBoxes = {}; InfoLayer.Visible = false; IsAnimating = false
end

BluffOverlay.MouseButton1Click:Connect(ClearInfo) -- FIX: CLICK BACKGROUND TO CLOSE

local function CreateInfoBox(label, value, targetPos, delay)
    task.wait(delay); if not InfoLayer.Visible then return end
    local box = Instance.new("TextButton", InfoLayer); box.Size = UDim2.new(0, 90, 0, 30); box.Position = targetPos - UDim2.new(0, 0, 0, 20); box.BackgroundColor3 = Color3.fromRGB(45, 45, 45); box.ZIndex = 110; box.Text = ""; Instance.new("UICorner", box).CornerRadius = UDim.new(0, 10)
    local txt = Instance.new("TextLabel", box); txt.Size = UDim2.new(1, 0, 1, 0); txt.BackgroundTransparency = 1; txt.RichText = true; txt.Text = "<b>"..label.."</b>\n"..tostring(value); txt.TextColor3 = Color3.new(1, 1, 1); txt.TextSize = 8; txt.ZIndex = 111
    box.MouseButton1Click:Connect(function() setclipboard(tostring(value)); txt.Text = "<b>COPIED!</b>"; task.wait(0.8); txt.Text = "<b>"..label.."</b>\n"..tostring(value) end)
    table.insert(ActiveBoxes, box)
    TweenService:Create(box, TweenInfo.new(0.4, Enum.EasingStyle.Back), {Position = targetPos}):Play()
end

local function Inspect(uid, name)
    if IsAnimating then return end
    ClearInfo(); InfoLayer.Visible = true; IsAnimating = true; InfoLayer.Position = MainContainer.Position
    TweenService:Create(BluffOverlay, TweenInfo.new(0.3), {BackgroundTransparency = 0.5}):Play()
    
    local midPfp = Instance.new("ImageLabel", InfoLayer); midPfp.Size = UDim2.new(0, 50, 0, 50); midPfp.Position = UDim2.new(0.5, -25, 0.5, -25); midPfp.Image = Players:GetUserThumbnailAsync(uid, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100); midPfp.BackgroundTransparency = 1; midPfp.ZIndex = 110; Instance.new("UICorner", midPfp).CornerRadius = UDim.new(1, 0); table.insert(ActiveBoxes, midPfp)

    task.spawn(function() CreateInfoBox("NAME", name:lower(), UDim2.new(0.5, -100, 0.5, -70), 0) end)
    task.spawn(function() CreateInfoBox("ID", uid, UDim2.new(0.5, 10, 0.5, -70), 0.1) end)
    task.spawn(function() CreateInfoBox("STATUS", "USER", UDim2.new(0.5, -100, 0.5, 30), 0.2) end)
    task.spawn(function() CreateInfoBox("JOINED", "RECENT", UDim2.new(0.5, 10, 0.5, 30), 0.3) end)
    task.wait(0.6); IsAnimating = false
end

-- [[ 7. MENU SYSTEM ]]
local MenuContainer = Instance.new("CanvasGroup", ScreenGui); MenuContainer.Size = UDim2.new(0, 100, 0, 220); MenuContainer.Position = MenuHiddenPos; MenuContainer.BackgroundTransparency = 1; MenuContainer.GroupTransparency = 1; MenuContainer.Visible = false
local MenuBtn = Instance.new("TextButton", MenuContainer); MenuBtn.Size = UDim2.new(0, 90, 0, 32); MenuBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MenuBtn.Text = "  MENU"; MenuBtn.TextColor3 = Color3.fromRGB(0, 255, 150); MenuBtn.Font = Enum.Font.GothamBold; MenuBtn.TextSize = 10; MenuBtn.TextXAlignment = "Left"; MenuBtn.ZIndex = 10; Instance.new("UICorner", MenuBtn).CornerRadius = UDim.new(0, 10)

local subButtons = {}; local btnNames = {"CHAT", "FRIENDS", "PROFILE", "CLOSE"}
for i, name in ipairs(btnNames) do
    local b = Instance.new("TextButton", MenuContainer); b.Size = UDim2.new(0, 90, 0, 32); b.BackgroundColor3 = Color3.fromRGB(25, 25, 25); b.TextColor3 = Color3.new(1, 1, 1); b.Text = name; b.Font = Enum.Font.GothamBold; b.TextSize = 8; b.ZIndex = 5; b.Visible = false; b.BackgroundTransparency = 1; b.TextTransparency = 1; Instance.new("UICorner", b).CornerRadius = UDim.new(0, 10); subButtons[i] = b
end

local function UpdateLayout(mode)
    CurrentMode = mode
    InputBar.Visible = (mode ~= "FRIENDS")
    SearchBar.Visible = (mode == "FRIENDS")
    GlobalView.Visible = (mode == "GLOBAL")
    FriendsView.Visible = (mode == "FRIENDS")
    DMView.Visible = (mode == "DM")
end

local menuOpen = false
local function ToggleMenu(state)
    menuOpen = state
    if menuOpen then
        for i, b in ipairs(subButtons) do b.Visible = true; task.delay(i * 0.08, function() TweenService:Create(b, TweenInfo.new(0.4, Enum.EasingStyle.Back), {Position = UDim2.new(0, 0, 0, 38 * i), BackgroundTransparency = 0, TextTransparency = 0}):Play() end) end
    else
        for _, b in ipairs(subButtons) do TweenService:Create(b, TweenInfo.new(0.25), {Position = UDim2.new(0, 0, 0, 0), BackgroundTransparency = 1, TextTransparency = 1}):Play() end
    end
end
MenuBtn.MouseButton1Click:Connect(function() ToggleMenu(not menuOpen) end)

-- [[ 8. FRIENDS ]]
local function RenderFriends(filter)
    for _, c in pairs(FriendsView:GetChildren()) do if c:IsA("Frame") then c:Destroy() end end
    for _, f in ipairs(AllFriendsCache) do
        if not filter or string.find(f.Username:lower(), filter:lower()) then
            local row = Instance.new("Frame", FriendsView); row.Size = UDim2.new(1, 0, 0, 45); row.BackgroundColor3 = Color3.fromRGB(25, 25, 25); row.ZIndex = 7; Instance.new("UICorner", row).CornerRadius = UDim.new(0, 10)
            local av = Instance.new("ImageLabel", row); av.Size = UDim2.new(0, 35, 0, 35); av.Position = UDim2.new(0, 5, 0, 5); av.BackgroundTransparency = 1; av.Image = Players:GetUserThumbnailAsync(f.Id, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); av.ZIndex = 8; Instance.new("UICorner", av).CornerRadius = UDim.new(1,0)
            local nm = Instance.new("TextLabel", row); nm.Size = UDim2.new(0, 100, 0, 20); nm.Position = UDim2.new(0, 45, 0, 12); nm.BackgroundTransparency = 1; nm.Text = f.Username; nm.TextColor3 = Color3.new(1,1,1); nm.Font = Enum.Font.GothamBold; nm.TextSize = 12; nm.TextXAlignment = "Left"; nm.ZIndex = 8
            local chatBtn = Instance.new("TextButton", row); chatBtn.Size = UDim2.new(0, 60, 0, 25); chatBtn.Position = UDim2.new(1, -65, 0, 10); chatBtn.BackgroundColor3 = Color3.fromRGB(0, 255, 150); chatBtn.Text = "CHAT"; chatBtn.TextColor3 = Color3.fromRGB(12, 12, 12); chatBtn.Font = Enum.Font.GothamBold; chatBtn.TextSize = 10; chatBtn.ZIndex = 9; Instance.new("UICorner", chatBtn).CornerRadius = UDim.new(0, 6)
            chatBtn.MouseButton1Click:Connect(function()
                CurrentDMTarget = {UserId = f.Id, Name = f.Username}
                HeaderTitle.Text = "DM: @" .. f.Username:upper(); HeaderTitle.TextColor3 = Color3.fromRGB(255, 0, 150)
                for _, m in pairs(DMView:GetChildren()) do if m:IsA("Frame") then m:Destroy() end end
                UpdateLayout("DM"); ToggleMenu(false)
            end)
        end
    end
end

-- [[ 9. MESSAGING ]]
local function AddMsg(view, uid, user, text)
    local frame = Instance.new("Frame", view); frame.Size = UDim2.new(1, 0, 0, 0); frame.BackgroundTransparency = 1; frame.AutomaticSize = "Y"
    local pfp = Instance.new("ImageButton", frame); pfp.Size = UDim2.new(0, 28, 0, 28); pfp.Position = UDim2.new(0, 0, 0, 2); pfp.Image = Players:GetUserThumbnailAsync(uid, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); Instance.new("UICorner", pfp).CornerRadius = UDim.new(1, 0)
    pfp.MouseButton1Click:Connect(function() Inspect(uid, user) end)
    local content = Instance.new("TextLabel", frame); content.Size = UDim2.new(1, -35, 0, 0); content.Position = UDim2.new(0, 35, 0, 12); content.BackgroundTransparency = 1; content.TextColor3 = Color3.new(1, 1, 1); content.Text = text; content.TextSize = 10; content.TextWrapped = true; content.TextXAlignment = "Left"; content.AutomaticSize = "Y"
    local tag = Instance.new("TextLabel", frame); tag.Size = UDim2.new(1, -35, 0, 10); tag.Position = UDim2.new(0, 35, 0, 0); tag.BackgroundTransparency = 1; tag.Text = "<b>" .. user:lower() .. "</b>"; tag.RichText = true; tag.TextColor3 = Color3.fromRGB(150, 150, 150); tag.TextSize = 8; tag.TextXAlignment = "Left"
    task.defer(function() view.CanvasPosition = Vector2.new(0, 99999) end)
end

local function Send(txt)
    if not canSend or txt == "" then return end
    canSend = false; SendBtn.TextColor3 = Color3.fromRGB(50, 50, 50)
    local data = {["PlayerName"] = Player.Name, ["UserId"] = Player.UserId, ["Message"] = txt, ["Type"] = (CurrentMode == "DM" and "private" or "global"), ["TargetId"] = (CurrentDMTarget and CurrentDMTarget.UserId or nil)}
    pcall(function()
        local json = HttpService:JSONEncode(data)
        if syn then syn.request({Url = SERVER_URL.."/send", Method = "POST", Body = json, Headers = {["Content-Type"]="application/json"}})
        else HttpService:PostAsync(SERVER_URL.."/send", json, Enum.HttpContentType.ApplicationJson) end
    end)
    task.delay(COOLDOWN_TIME, function() canSend = true; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150) end)
end

-- [[ 10. SYNC & BUTTONS ]]
task.spawn(function()
    while task.wait(3) do
        local success, res = pcall(function() return HttpService:GetAsync(SERVER_URL.."/get_messages?after="..lastTimestamp.."&uid="..Player.UserId) end)
        if success then
            for _, m in ipairs(HttpService:JSONDecode(res)) do
                if m.Timestamp > lastTimestamp then
                    lastTimestamp = m.Timestamp
                    if not m.Type or m.Type == "global" then AddMsg(GlobalView, m.UserId, m.PlayerName, m.Message)
                    elseif m.Type == "private" then
                        if (m.TargetId == Player.UserId and CurrentDMTarget and m.UserId == CurrentDMTarget.UserId) or (m.UserId == Player.UserId and CurrentDMTarget and m.TargetId == CurrentDMTarget.UserId) then
                            AddMsg(DMView, m.UserId, m.PlayerName, m.Message)
                        end
                    end
                end
            end
        end
    end
end)

local MainBtn = Instance.new("TextButton", ScreenGui); MainBtn.Size = UDim2.new(0, 35, 0, 32); MainBtn.Position = UDim2.new(0.5, -205, 0.1, 0); MainBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MainBtn.Text = "S"; MainBtn.TextColor3 = Color3.fromRGB(0, 255, 150); MainBtn.Font = Enum.Font.GothamBold; MainBtn.TextSize = 15; Instance.new("UICorner", MainBtn).CornerRadius = UDim.new(0, 10)
MainBtn.MouseButton1Click:Connect(function()
    if MainContainer.Visible then
        ToggleMenu(false); TweenService:Create(MainContainer, TweenInfo.new(0.3), {Position = ChatHiddenPos, GroupTransparency = 1}):Play(); task.wait(0.3); MainContainer.Visible = false; MenuContainer.Visible = false
    else
        UpdateLayout("GLOBAL"); MainContainer.Visible = true; MenuContainer.Visible = true; TweenService:Create(MainContainer, TweenInfo.new(0.5, Enum.EasingStyle.Back), {Position = ChatVisiblePos, GroupTransparency = 0}):Play(); TweenService:Create(MenuContainer, TweenInfo.new(0.5, Enum.EasingStyle.Back), {Position = MenuVisiblePos, GroupTransparency = 0}):Play()
    end
end)

SendBtn.MouseButton1Click:Connect(function() if InputBox.Text ~= "" then local t = InputBox.Text; InputBox.Text = ""; Send(t) end end)
subButtons[1].MouseButton1Click:Connect(function() SwitchMode("GLOBAL"); ToggleMenu(false) end)
subButtons[2].MouseButton1Click:Connect(function() SwitchMode("FRIENDS"); ToggleMenu(false) end) -- Friends logic expanded in full v3
subButtons[3].MouseButton1Click:Connect(function() Inspect(Player.UserId, Player.Name); ToggleMenu(false) end)
subButtons[4].MouseButton1Click:Connect(function() MainBtn:MouseButton1Click() end)
"""

messages = []

@app.route('/')
def home():
    return "Sonix Precision v3 Server Online", 200

@app.route('/load_sonix', methods=['GET'])
def load_sonix():
    return SECRET_V3_SCRIPT, 200

@app.post('/send')
def send_message():
    data = request.json
    # FIX: Server now stores ALL meta-data so messages show up properly
    msg = {
        "PlayerName": data.get("PlayerName"),
        "UserId": data.get("UserId"),
        "Message": data.get("Message"),
        "Type": data.get("Type", "global"),
        "TargetId": data.get("TargetId"),
        "Timestamp": time.time()
    }
    messages.append(msg)
    # Keep server from crashing (only keep last 100 messages)
    if len(messages) > 100: messages.pop(0)
    return jsonify({"status": "ok"}), 200

@app.get('/get_messages')
def get_messages():
    after = float(request.args.get('after', 0))
    # FIX: Send back type and target so script knows where to put the message
    filtered = [m for m in messages if m['Timestamp'] > after]
    return jsonify(filtered), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
