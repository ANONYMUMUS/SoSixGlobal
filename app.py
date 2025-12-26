from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

# [[ 1. THE SECRET V3 SCRIPT ]]
# FIXED: Line 200 now correctly references UIListLayout instead of the Frame
SECRET_V3_SCRIPT = r"""
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
local COOLDOWN_TIME = 3
local MAX_CHARS = 300

-- [[ 1. UI ROOT ]]
local ScreenGui = Instance.new("ScreenGui", PlayerGui); ScreenGui.Name = "Sonix_Precision_Final"; ScreenGui.ResetOnSpawn = false

-- [[ 2. ANIMATION POSITIONS ]]
local ChatVisiblePos = UDim2.new(0.5, -160, 0.1, 0)
local ChatHiddenPos = UDim2.new(0.5, -160, 0.05, 0) 

local MenuVisiblePos = UDim2.new(0.5, 170, 0.1, 0)
local MenuHiddenPos = UDim2.new(0.5, 140, 0.1, 0) 

-- [[ 3. MAIN CONTAINER ]]
local MainContainer = Instance.new("CanvasGroup", ScreenGui)
MainContainer.Size = UDim2.new(0, 320, 0, 180); MainContainer.Position = ChatHiddenPos
MainContainer.BackgroundColor3 = Color3.fromRGB(12, 12, 12); MainContainer.Visible = false; MainContainer.GroupTransparency = 1
Instance.new("UICorner", MainContainer).CornerRadius = UDim.new(0, 20)

-- [[ 4. MENU SYSTEM ]]
local MenuContainer = Instance.new("CanvasGroup", ScreenGui)
MenuContainer.Size = UDim2.new(0, 100, 0, 220); MenuContainer.Position = MenuHiddenPos
MenuContainer.BackgroundTransparency = 1; MenuContainer.GroupTransparency = 1; MenuContainer.Visible = false

local MenuBtn = Instance.new("TextButton", MenuContainer)
MenuBtn.Size = UDim2.new(0, 85, 0, 30); MenuBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MenuBtn.Text = ""; MenuBtn.ClipsDescendants = true; MenuBtn.ZIndex = 10
Instance.new("UICorner", MenuBtn).CornerRadius = UDim.new(0, 10)

local function CreateLine(y)
    local l = Instance.new("Frame", MenuBtn); l.Size = UDim2.new(0, 16, 0, 2); l.AnchorPoint = Vector2.new(0.5, 0.5)
    l.Position = UDim2.new(0, 20, 0, y); l.BackgroundColor3 = Color3.fromRGB(0, 255, 150); l.BorderSizePixel = 0; l.ZIndex = 11; return l
end
local l1, l2, l3 = CreateLine(11), CreateLine(15), CreateLine(19)

local MenuLabel = Instance.new("TextLabel", MenuBtn)
MenuLabel.Size = UDim2.new(0, 50, 1, 0); MenuLabel.Position = UDim2.new(0, 38, 0, 0); MenuLabel.BackgroundTransparency = 1; MenuLabel.Text = "MENU"
MenuLabel.TextColor3 = Color3.fromRGB(0, 255, 150); MenuLabel.TextSize = 10; MenuLabel.Font = Enum.Font.GothamBold; MenuLabel.TextXAlignment = "Left"

local subButtons = {}
local btnNames = {"CHAT", "FRIENDS", "PROFILE", "INFO"}
for i, name in ipairs(btnNames) do
    local b = Instance.new("TextButton", MenuContainer)
    b.Size = UDim2.new(0, 85, 0, 30); b.Position = UDim2.new(0, 0, 0, 0); b.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
    b.TextColor3 = Color3.new(1, 1, 1); b.Text = name; b.Font = Enum.Font.GothamBold; b.TextSize = 8; b.ZIndex = 5; b.Visible = false; b.BackgroundTransparency = 1; b.TextTransparency = 1; Instance.new("UICorner", b).CornerRadius = UDim.new(0, 10)
    subButtons[i] = b
end

local menuOpen = false
local function ToggleMenu(state)
    menuOpen = state
    if menuOpen then
        TweenService:Create(l1, TweenInfo.new(0.3), {Rotation = 45, Position = UDim2.new(0, 20, 0, 15)}):Play()
        TweenService:Create(l2, TweenInfo.new(0.2), {BackgroundTransparency = 1}):Play()
        TweenService:Create(l3, TweenInfo.new(0.3), {Rotation = -45, Position = UDim2.new(0, 20, 0, 15)}):Play()
        for i, b in ipairs(subButtons) do
            b.Visible = true
            task.delay(i * 0.08, function()
                TweenService:Create(b, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = UDim2.new(0, 0, 0, 35 + (i-1)*35), BackgroundTransparency = 0, TextTransparency = 0}):Play()
            end)
        end
    else
        TweenService:Create(l1, TweenInfo.new(0.3), {Rotation = 0, Position = UDim2.new(0, 20, 0, 11)}):Play()
        TweenService:Create(l2, TweenInfo.new(0.2), {BackgroundTransparency = 0}):Play()
        TweenService:Create(l3, TweenInfo.new(0.3), {Rotation = 0, Position = UDim2.new(0, 20, 0, 19)}):Play()
        for _, b in ipairs(subButtons) do
            TweenService:Create(b, TweenInfo.new(0.25), {Position = UDim2.new(0, 0, 0, 0), BackgroundTransparency = 1, TextTransparency = 1}):Play()
        end
    end
end
MenuBtn.MouseButton1Click:Connect(function() ToggleMenu(not menuOpen) end)

-- [[ 5. PROFILE SYSTEM ]]
local InfoLayer = Instance.new("Frame", ScreenGui); InfoLayer.Size = MainContainer.Size; InfoLayer.Position = ChatVisiblePos; InfoLayer.BackgroundTransparency = 1; InfoLayer.Visible = false; InfoLayer.ZIndex = 999 
local BluffOverlay = Instance.new("Frame", InfoLayer); BluffOverlay.Size = UDim2.new(1, 0, 1, 0); BluffOverlay.BackgroundColor3 = Color3.new(0, 0, 0); BluffOverlay.BackgroundTransparency = 1; BluffOverlay.ZIndex = 1; Instance.new("UICorner", BluffOverlay).CornerRadius = UDim.new(0, 20)

local ActiveBoxes = {}; local CurrentInspecting = nil; local IsAnimating = false

local function ClearInfo()
    CurrentInspecting = nil
    TweenService:Create(BluffOverlay, TweenInfo.new(0.2), {BackgroundTransparency = 1}):Play()
    for _, box in ipairs(ActiveBoxes) do box:Destroy() end
    ActiveBoxes = {}
    InfoLayer.Visible = false
    IsAnimating = false
end

local function CreateInfoBox(label, value, targetPos, delay)
    task.wait(delay)
    if not InfoLayer.Visible then return end
    local box = Instance.new("TextButton", InfoLayer); box.Size = UDim2.new(0, 85, 0, 28); box.Position = targetPos - UDim2.new(0, 0, 0, 20); box.BackgroundColor3 = Color3.fromRGB(45, 45, 45); box.BackgroundTransparency = 1; box.ZIndex = 10; box.Text = ""; Instance.new("UICorner", box).CornerRadius = UDim.new(1, 0)
    local txt = Instance.new("TextLabel", box); txt.Size = UDim2.new(1, 0, 1, 0); txt.BackgroundTransparency = 1; txt.RichText = true; txt.Text = "<b>"..label.."</b>\n"..tostring(value); txt.TextColor3 = Color3.new(1, 1, 1); txt.TextSize = 7; txt.ZIndex = 11
    box.MouseButton1Click:Connect(function() setclipboard(tostring(value)); txt.Text = "<b>COPIED!</b>"; task.wait(0.8); txt.Text = "<b>"..label.."</b>\n"..tostring(value) end)
    table.insert(ActiveBoxes, box)
    TweenService:Create(box, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = targetPos, BackgroundTransparency = 0.1}):Play()
end

local function Inspect(uid, name)
    if IsAnimating then return end
    if CurrentInspecting == uid then ClearInfo() return end
    ClearInfo() 
    
    InfoLayer.Visible = true; IsAnimating = true; CurrentInspecting = uid
    TweenService:Create(BluffOverlay, TweenInfo.new(0.3), {BackgroundTransparency = 0.6}):Play()
    local age = 0; pcall(function() age = (Players:GetPlayerByUserId(uid) or {AccountAge = 0}).AccountAge end)
    
    local midPfp = Instance.new("ImageLabel", InfoLayer); midPfp.Size = UDim2.new(0, 40, 0, 40); midPfp.Position = UDim2.new(0.5, -20, 0.5, -20); midPfp.Image = Players:GetUserThumbnailAsync(uid, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); midPfp.BackgroundTransparency = 1; midPfp.ZIndex = 10; Instance.new("UICorner", midPfp).CornerRadius = UDim.new(1, 0)
    table.insert(ActiveBoxes, midPfp)

    local AddBtn = Instance.new("TextButton", InfoLayer)
    AddBtn.Size = UDim2.new(0, 85, 0, 24); AddBtn.Position = UDim2.new(0.5, -42, 0.5, 45); AddBtn.BackgroundColor3 = Color3.fromRGB(0, 255, 150); AddBtn.Text = "ADD FRIEND"; AddBtn.TextColor3 = Color3.fromRGB(12, 12, 12); AddBtn.Font = Enum.Font.GothamBold; AddBtn.TextSize = 8; AddBtn.ZIndex = 15; AddBtn.BackgroundTransparency = 1; AddBtn.TextTransparency = 1
    Instance.new("UICorner", AddBtn).CornerRadius = UDim.new(1, 0); table.insert(ActiveBoxes, AddBtn)
    TweenService:Create(AddBtn, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {BackgroundTransparency = 0, TextTransparency = 0}):Play()

    AddBtn.MouseButton1Click:Connect(function()
        if uid == Player.UserId then AddBtn.Text = "ITS YOU!"; task.wait(1); AddBtn.Text = "ADD FRIEND" else
            local targetPlayer = Players:GetPlayerByUserId(uid)
            if targetPlayer then SocialService:PromptSendFriendRequest(Player, targetPlayer) else 
                pcall(function() Player:SetFriendRequest(uid) end); AddBtn.Text = "REQUEST SENT!"; AddBtn.BackgroundColor3 = Color3.fromRGB(100, 100, 100)
            end
        end
    end)

    task.spawn(function() CreateInfoBox("USERNAME", name:lower(), UDim2.new(0.5, -95, 0.5, -60), 0) end)
    task.spawn(function() CreateInfoBox("USERID", uid, UDim2.new(0.5, 10, 0.5, -60), 0.1) end)
    task.spawn(function() CreateInfoBox("STATUS", "ONLINE", UDim2.new(0.5, -105, 0.5, 10), 0.2) end)
    task.spawn(function() CreateInfoBox("AGE", age .. " DAYS", UDim2.new(0.5, 20, 0.5, 10), 0.3) end)
    task.wait(0.6); IsAnimating = false
end

-- [[ 6. S BUTTON & TOGGLE ANIMATION ]]
local MainBtn = Instance.new("TextButton", ScreenGui); MainBtn.Size = UDim2.new(0, 35, 0, 30); MainBtn.Position = UDim2.new(0.5, -205, 0.1, 0); MainBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MainBtn.Text = "S"; MainBtn.TextColor3 = Color3.fromRGB(0, 255, 150); MainBtn.Font = Enum.Font.GothamBold; MainBtn.TextSize = 14; Instance.new("UICorner", MainBtn).CornerRadius = UDim.new(0, 10)

MainBtn.MouseButton1Click:Connect(function()
    if MainContainer.Visible then
        ClearInfo()
        ToggleMenu(false)
        TweenService:Create(MenuContainer, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {Position = MenuHiddenPos, GroupTransparency = 1}):Play()
        task.wait(0.15)
        TweenService:Create(MainContainer, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {Position = ChatHiddenPos, GroupTransparency = 1}):Play()
        task.wait(0.3)
        MainContainer.Visible = false; MenuContainer.Visible = false
    else
        MainContainer.Visible = true; MainContainer.GroupTransparency = 1; MainContainer.Position = ChatHiddenPos
        TweenService:Create(MainContainer, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = ChatVisiblePos, GroupTransparency = 0}):Play()
        task.wait(0.2)
        MenuContainer.Visible = true; MenuContainer.GroupTransparency = 1; MenuContainer.Position = MenuHiddenPos
        TweenService:Create(MenuContainer, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {Position = MenuVisiblePos, GroupTransparency = 0}):Play()
    end
end)

-- [[ 7. COPY CONTEXT SYSTEM ]]
local ContextOverlay = Instance.new("Frame", ScreenGui); ContextOverlay.Size = UDim2.new(1,0,1,0); ContextOverlay.BackgroundTransparency = 1; ContextOverlay.ZIndex = 2000; ContextOverlay.Visible = false
local Backdrop = Instance.new("TextButton", ContextOverlay); Backdrop.Size = UDim2.new(1, 0, 1, 0); Backdrop.BackgroundTransparency = 0.6; Backdrop.BackgroundColor3 = Color3.new(0,0,0); Backdrop.Text = ""; Backdrop.AutoButtonColor = false
Backdrop.MouseButton1Click:Connect(function() ContextOverlay.Visible = false; for _,v in pairs(ContextOverlay:GetChildren()) do if v.Name == "CopyBtn" then v:Destroy() end end end)

-- [[ 8. CHAT & INPUT ]]
local ChatBox = Instance.new("ScrollingFrame", MainContainer); ChatBox.Size = UDim2.new(1, -20, 1, -60); ChatBox.Position = UDim2.new(0, 10, 0, 10); ChatBox.BackgroundTransparency = 1; ChatBox.ScrollBarThickness = 0; ChatBox.AutomaticCanvasSize = Enum.AutomaticSize.Y; 
local ChatLayout = Instance.new("UIListLayout", ChatBox); ChatLayout.Padding = UDim.new(0, 6)

local function AddMsg(uid, user, text)
    local msgFrame = Instance.new("Frame", ChatBox); msgFrame.Size = UDim2.new(1, 0, 0, 0); msgFrame.BackgroundTransparency = 1; msgFrame.AutomaticSize = "Y"
    local pfp = Instance.new("ImageButton", msgFrame); pfp.Size = UDim2.new(0, 26, 0, 26); pfp.Position = UDim2.new(0, 0, 0, 2); pfp.Image = Players:GetUserThumbnailAsync(uid, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size48x48); Instance.new("UICorner", pfp).CornerRadius = UDim.new(1, 0); pfp.MouseButton1Click:Connect(function() Inspect(uid, user) end)
    
    local content = Instance.new("TextLabel", msgFrame); content.Size = UDim2.new(1, -32, 0, 0); content.Position = UDim2.new(0, 32, 0, 11); content.BackgroundTransparency = 1; content.TextColor3 = Color3.new(1,1,1); content.Text = text; content.TextSize = 10; content.TextXAlignment = "Left"; content.TextWrapped = true; content.AutomaticSize = "Y"
    content.Active = true; content.Selectable = true

    local header = Instance.new("TextLabel", msgFrame); header.Size = UDim2.new(1, -32, 0, 10); header.Position = UDim2.new(0, 32, 0, 0); header.BackgroundTransparency = 1; header.TextColor3 = Color3.fromRGB(160, 160, 160); header.Text = "<b>" .. user:lower() .. "</b>"; header.TextSize = 7; header.RichText = true; header.TextXAlignment = "Left"

    local holdTime = 0
    content.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
            holdTime = tick()
            local currentHold = holdTime
            task.delay(0.6, function()
                if holdTime == currentHold and (UIS:IsMouseButtonPressed(Enum.UserInputType.MouseButton1) or UIS:GetMouseButtonsPressed()[1]) then
                    ContextOverlay.Visible = true
                    local btnArea = Instance.new("Frame", ContextOverlay); btnArea.Name = "CopyBtn"; btnArea.Size = UDim2.new(0, 60, 0, 25); btnArea.BackgroundTransparency = 1; 
                    btnArea.Position = UDim2.new(0, content.AbsolutePosition.X + 20, 0, content.AbsolutePosition.Y + 15)
                    local b = Instance.new("TextButton", btnArea); b.Size = UDim2.new(1, 0, 1, 0); b.BackgroundColor3 = Color3.fromRGB(45, 45, 45); b.Text = "COPY"; b.TextColor3 = Color3.new(1,1,1); b.TextSize = 10; Instance.new("UICorner", b)
                    b.MouseButton1Click:Connect(function() setclipboard(text); ContextOverlay.Visible = false; btnArea:Destroy() end)
                end
            end)
        end
    end)
    content.InputEnded:Connect(function(input) if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then holdTime = 0 end end)
    
    -- FIXED LINE 200: Using ChatLayout.AbsoluteContentSize instead of ChatBox.AbsoluteContentSize
    task.defer(function() 
        if ChatLayout then
            ChatBox.CanvasPosition = Vector2.new(0, ChatLayout.AbsoluteContentSize.Y) 
        end
    end)
end

-- [[ 9. INPUT ]]
local InputBar = Instance.new("Frame", MainContainer); InputBar.Size = UDim2.new(1, -20, 0, 30); InputBar.Position = UDim2.new(0, 10, 1, -40); InputBar.BackgroundTransparency = 1
local InputBox = Instance.new("TextBox", InputBar); InputBox.Size = UDim2.new(1, -40, 1, 0); InputBox.BackgroundColor3 = Color3.fromRGB(20,20,20); InputBox.TextColor3 = Color3.new(1,1,1); InputBox.PlaceholderText = "Message..."; InputBox.Text = ""; Instance.new("UICorner", InputBox); Instance.new("UIPadding", InputBox).PaddingLeft = UDim.new(0, 10)

local CharCount = Instance.new("TextLabel", InputBar)
CharCount.Size = UDim2.new(0, 35, 0, 12); CharCount.Position = UDim2.new(1, -35, 0, -12); CharCount.BackgroundTransparency = 1; CharCount.TextColor3 = Color3.fromRGB(0, 255, 150); CharCount.Text = "0/300"; CharCount.TextSize = 8; CharCount.Font = Enum.Font.GothamBold; CharCount.TextXAlignment = "Center"

local SendBtn = Instance.new("TextButton", InputBar); SendBtn.Size = UDim2.new(0, 35, 1, 0); SendBtn.Position = UDim2.new(1,-35,0,0); SendBtn.BackgroundColor3 = Color3.fromRGB(30,30,30); SendBtn.Text = "»"; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150); Instance.new("UICorner", SendBtn)

InputBox:GetPropertyChangedSignal("Text"):Connect(function()
    local length = #InputBox.Text
    if length > MAX_CHARS then InputBox.Text = string.sub(InputBox.Text, 1, MAX_CHARS); length = MAX_CHARS end
    CharCount.Text = length .. "/" .. MAX_CHARS; CharCount.TextColor3 = (length >= MAX_CHARS) and Color3.fromRGB(255, 0, 0) or Color3.fromRGB(0, 255, 150)
end)

local function Send(txt)
    if not canSend or txt == "" then return end
    canSend = false; SendBtn.TextColor3 = Color3.fromRGB(80, 80, 80)
    
    local payload = HttpService:JSONEncode({
        PlayerName = Player.Name,
        UserId = Player.UserId,
        Message = txt
    })

    task.spawn(function()
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = SERVER_URL .. "/send",
                Method = "POST",
                Headers = {["Content-Type"] = "application/json"},
                Body = payload
            })
        end)
        if not success then warn("Sonix Send Error: " .. tostring(response)) end
    end)
    
    task.delay(COOLDOWN_TIME, function() canSend = true; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150) end)
end

SendBtn.MouseButton1Click:Connect(function() 
    if canSend and InputBox.Text ~= "" then 
        local t = InputBox.Text; InputBox.Text = ""; InputBox:ReleaseFocus(); Send(t) 
    end 
end)

-- [[ 10. RECODED RENDER SYNC LOOP ]]
subButtons[3].MouseButton1Click:Connect(function() Inspect(Player.UserId, Player.Name) end)

task.spawn(function()
    print("Sonix Precision: Sync Loop Started")
    while true do
        local success, response = pcall(function()
            return HttpService:RequestAsync({
                Url = SERVER_URL .. "/get_messages?after=" .. tostring(lastTimestamp),
                Method = "GET"
            })
        end)

        if success and response.StatusCode == 200 then
            local messages = HttpService:JSONDecode(response.Body)
            table.sort(messages, function(a, b) return a.Timestamp < b.Timestamp end)

            for _, m in ipairs(messages) do
                if m.Timestamp > lastTimestamp then
                    AddMsg(m.UserId or 1, m.PlayerName or "Unknown", m.Message or "")
                    lastTimestamp = m.Timestamp
                end
            end
        elseif success and response.StatusCode == 503 then
            print("Sonix: Server waking up...")
        else
            warn("Sonix Precision: Connection Interrupted. Code: " .. (response and tostring(response.StatusCode) or "Timeout"))
        end
        task.wait(3)
    end
end)"""

# [[ 2. CHAT STORAGE ]]
messages = []

@app.route('/')
def home():
    return "Sonix Precision API: ONLINE", 200

@app.route('/load_sonix', methods=['GET'])
def load_sonix():
    return SECRET_V3_SCRIPT, 200

@app.post('/send')
def send_message():
    data = request.json
    if not data: return jsonify({"status": "error"}), 400
    
    msg = {
        "PlayerName": data.get("PlayerName"),
        "UserId": data.get("UserId"),
        "Message": data.get("Message"),
        "Timestamp": time.time()
    }
    messages.append(msg)
    
    # Keep list from growing too large (memory optimization)
    if len(messages) > 200:
        messages.pop(0)
        
    return jsonify({"status": "ok"}), 200

@app.get('/get_messages')
def get_messages():
    try:
        after = float(request.args.get('after', 0))
        filtered = [m for m in messages if m['Timestamp'] > after]
        return jsonify(filtered), 200
    except:
        return jsonify([]), 200

if __name__ == '__main__':
    # Render uses dynamic ports; this ensures it binds correctly
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
