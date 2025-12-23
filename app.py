from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# [[ 1. THE SECRET V3 SCRIPT ]]
# Added 'r' before quotes to handle special characters and backslashes
SECRET_V3_SCRIPT = r"""
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
local CurrentMode = "GLOBAL"
local CurrentDMTarget = nil
local AllFriendsCache = {}

-- [[ UI ROOT ]]
local ScreenGui = Instance.new("ScreenGui", PlayerGui); ScreenGui.Name = "Sonix_Precision_Final"; ScreenGui.ResetOnSpawn = false

-- [[ POSITIONS ]]
local ChatVisiblePos, ChatHiddenPos = UDim2.new(0.5, -160, 0.1, 0), UDim2.new(0.5, -160, 0.05, 0)
local MenuVisiblePos, MenuHiddenPos = UDim2.new(0.5, 170, 0.1, 0), UDim2.new(0.5, 140, 0.1, 0)

-- [[ MAIN CONTAINER ]]
local MainContainer = Instance.new("CanvasGroup", ScreenGui)
MainContainer.Size = UDim2.new(0, 320, 0, 200); MainContainer.Position = ChatHiddenPos
MainContainer.BackgroundColor3 = Color3.fromRGB(12, 12, 12); MainContainer.Visible = false; MainContainer.GroupTransparency = 1; MainContainer.ZIndex = 5
Instance.new("UICorner", MainContainer).CornerRadius = UDim.new(0, 20)

local HeaderTitle = Instance.new("TextLabel", MainContainer)
HeaderTitle.Size = UDim2.new(1, -20, 0, 20); HeaderTitle.Position = UDim2.new(0, 10, 0, 5); HeaderTitle.BackgroundTransparency = 1
HeaderTitle.Text = "GLOBAL FEED"; HeaderTitle.TextColor3 = Color3.fromRGB(0, 255, 150); HeaderTitle.Font = Enum.Font.GothamBold; HeaderTitle.TextSize = 10; HeaderTitle.TextXAlignment = "Left"; HeaderTitle.ZIndex = 6

-- [[ SCROLLING VIEWS ]]
local ViewContainer = Instance.new("Frame", MainContainer)
ViewContainer.Size = UDim2.new(1, 0, 1, -60); ViewContainer.Position = UDim2.new(0, 0, 0, 25); ViewContainer.BackgroundTransparency = 1; ViewContainer.ZIndex = 6

local function CreateScroll(name)
    local s = Instance.new("ScrollingFrame", ViewContainer); s.Name = name; s.Size = UDim2.new(1, -20, 1, 0); s.Position = UDim2.new(0, 10, 0, 0); s.BackgroundTransparency = 1; s.ScrollBarThickness = 2; s.ScrollBarImageColor3 = Color3.fromRGB(0, 255, 150); s.AutomaticCanvasSize = Enum.AutomaticSize.Y; s.Visible = false; s.ZIndex = 7
    Instance.new("UIListLayout", s).Padding = UDim.new(0, 6); return s
end

local GlobalView = CreateScroll("GlobalView"); GlobalView.Visible = true
local FriendsView = CreateScroll("FriendsView")
local DMView = CreateScroll("DMView")

-- [[ INPUT BAR ]]
local InputBar = Instance.new("Frame", MainContainer); InputBar.Size = UDim2.new(1, -20, 0, 30); InputBar.Position = UDim2.new(0, 10, 1, -40); InputBar.BackgroundTransparency = 1; InputBar.ZIndex = 8
local InputBox = Instance.new("TextBox", InputBar); InputBox.Size = UDim2.new(1, -40, 1, 0); InputBox.BackgroundColor3 = Color3.fromRGB(20,20,20); InputBox.TextColor3 = Color3.new(1,1,1); InputBox.PlaceholderText = "Message..."; InputBox.Text = ""; InputBox.ZIndex = 9; Instance.new("UICorner", InputBox); Instance.new("UIPadding", InputBox).PaddingLeft = UDim.new(0, 10)
local SendBtn = Instance.new("TextButton", InputBar); SendBtn.Size = UDim2.new(0, 35, 1, 0); SendBtn.Position = UDim2.new(1,-35,0,0); SendBtn.BackgroundColor3 = Color3.fromRGB(30,30,30); SendBtn.Text = "»"; SendBtn.TextColor3 = Color3.fromRGB(0, 255, 150); SendBtn.ZIndex = 9; Instance.new("UICorner", SendBtn)

local function AddMsg(scroll, uid, user, text)
    local msgFrame = Instance.new("Frame", scroll); msgFrame.Size = UDim2.new(1, 0, 0, 0); msgFrame.BackgroundTransparency = 1; msgFrame.AutomaticSize = "Y"; msgFrame.ZIndex = 7
    local content = Instance.new("TextLabel", msgFrame); content.Size = UDim2.new(1, -32, 0, 0); content.Position = UDim2.new(0, 32, 0, 11); content.BackgroundTransparency = 1; content.TextColor3 = Color3.new(1,1,1); content.Text = text; content.TextSize = 10; content.TextXAlignment = "Left"; content.TextWrapped = true; content.AutomaticSize = "Y"; content.ZIndex = 8
    local header = Instance.new("TextLabel", msgFrame); header.Size = UDim2.new(1, -32, 0, 10); header.Position = UDim2.new(0, 32, 0, 0); header.BackgroundTransparency = 1; header.TextColor3 = Color3.fromRGB(160, 160, 160); header.Text = "<b>" .. user:lower() .. "</b>"; header.TextSize = 7; header.RichText = true; header.TextXAlignment = "Left"; header.ZIndex = 8
    scroll.CanvasPosition = Vector2.new(0, 99999)
end

local function Send(txt)
    if not canSend or txt == "" then return end
    canSend = false
    local payload = HttpService:JSONEncode({["PlayerName"] = Player.Name, ["UserId"] = Player.UserId, ["Message"] = txt})
    pcall(function()
        HttpService:PostAsync(SERVER_URL .. "/send", payload, Enum.HttpContentType.ApplicationJson)
    end)
    task.wait(COOLDOWN_TIME)
    canSend = true
end

SendBtn.MouseButton1Click:Connect(function() Send(InputBox.Text); InputBox.Text = "" end)

-- [[ S BUTTON ]]
local MainBtn = Instance.new("TextButton", ScreenGui); MainBtn.Size = UDim2.new(0, 35, 0, 30); MainBtn.Position = UDim2.new(0.5, -205, 0.1, 0); MainBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 20); MainBtn.Text = "S"; MainBtn.TextColor3 = Color3.fromRGB(0, 255, 150); MainBtn.Font = Enum.Font.GothamBold; MainBtn.TextSize = 14; Instance.new("UICorner", MainBtn).CornerRadius = UDim.new(0, 10)
MainBtn.MouseButton1Click:Connect(function() MainContainer.Visible = not MainContainer.Visible; MainContainer.GroupTransparency = MainContainer.Visible and 0 or 1 end)

task.spawn(function()
    while task.wait(3) do
        local success, res = pcall(function() return HttpService:GetAsync(SERVER_URL .. "/get_messages?after=" .. lastTimestamp) end)
        if success then
            local data = HttpService:JSONDecode(res)
            for _, m in ipairs(data) do
                if m.Timestamp > lastTimestamp then
                    lastTimestamp = m.Timestamp
                    AddMsg(GlobalView, m.UserId, m.PlayerName, m.Message)
                end
            end
        end
    end
end)
print("Sonix v3 Live!")
"""

# [[ 2. CHAT STORAGE ]]
messages = []

@app.route('/')
def home():
    return "Sonix Server is Online", 200

@app.route('/load_sonix', methods=['GET'])
def load_sonix():
    return SECRET_V3_SCRIPT, 200

@app.post('/send')
def send_message():
    data = request.json
    msg = {
        "PlayerName": data.get("PlayerName"),
        "UserId": data.get("UserId"),
        "Message": data.get("Message"),
        "Timestamp": time.time()
    }
    messages.append(msg)
    return jsonify({"status": "ok"}), 200

@app.get('/get_messages')
def get_messages():
    after = float(request.args.get('after', 0))
    filtered = [m for m in messages if m['Timestamp'] > after]
    return jsonify(filtered), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
