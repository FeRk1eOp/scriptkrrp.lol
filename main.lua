local Players = game:GetService("Players")
local Player = Players.LocalPlayer
local PlayerGui = Player:WaitForChild("PlayerGui")

local ScreenGui = Instance.new("ScreenGui")
ScreenGui.Name = "Fer4ixzGUI"
ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
ScreenGui.Parent = PlayerGui

local MainFrame = Instance.new("Frame")
MainFrame.Size = UDim2.new(0, 300, 0, 200)
MainFrame.Position = UDim2.new(0, 10, 0, 10)
MainFrame.BackgroundColor3 = Color3.new(0, 0, 0)
MainFrame.BorderSizePixel = 0
MainFrame.Parent = ScreenGui

local TitleContainer = Instance.new("Frame")
TitleContainer.Size = UDim2.new(1, 0, 0, 30)
TitleContainer.Position = UDim2.new(0, 0, 0, 0)
TitleContainer.BackgroundColor3 = Color3.new(0.1, 0.1, 0.1)
TitleContainer.BorderSizePixel = 0
TitleContainer.Parent = MainFrame

local IconImage = Instance.new("ImageLabel")
IconImage.Size = UDim2.new(0, 24, 0, 24)
IconImage.Position = UDim2.new(0, 5, 0, 3)
IconImage.BackgroundTransparency = 1
IconImage.Image = "rbxassetid://16594334442" -- Замените на ваш ID
IconImage.Parent = TitleContainer

local TitleLabel = Instance.new("TextLabel")
TitleLabel.Size = UDim2.new(1, -30, 1, 0)
TitleLabel.Position = UDim2.new(0, 30, 0, 0)
TitleLabel.BackgroundTransparency = 1
TitleLabel.Text = "fer4ixz`script"
TitleLabel.TextColor3 = Color3.new(1, 1, 1)
TitleLabel.TextSize = 14
TitleLabel.Font = Enum.Font.GothamBold
TitleLabel.TextXAlignment = Enum.TextXAlignment.Left
TitleLabel.Parent = TitleContainer

local isLoopRunning = false

local function startLoop()
    if isLoopRunning then return end
    
    isLoopRunning = true
    print("Цикл 'Водитель автобуса' запущен")
    
    spawn(function()
        while isLoopRunning do
            game:GetService("ReplicatedStorage"):WaitForChild("Events"):WaitForChild("Jobs"):WaitForChild("Водитель автобуса"):WaitForChild("ChangeParentOfPath"):FireServer()
            wait(0.5)
        end
    end)
end

local function stopLoop()
    isLoopRunning = false
    print("Цикл 'Водитель автобуса' остановлен")
end

local StartButton = Instance.new("TextButton")
StartButton.Size = UDim2.new(0.8, 0, 0, 40)
StartButton.Position = UDim2.new(0.1, 0, 0.3, 0)
StartButton.BackgroundColor3 = Color3.new(0.2, 0.6, 0.2)
StartButton.Text = "Запустить цикл"
StartButton.TextColor3 = Color3.new(1, 1, 1)
StartButton.TextSize = 14
StartButton.Font = Enum.Font.Gotham
StartButton.Parent = MainFrame

StartButton.MouseButton1Click:Connect(startLoop)

local StopButton = Instance.new("TextButton")
StopButton.Size = UDim2.new(0.8, 0, 0, 40)
StopButton.Position = UDim2.new(0.1, 0, 0.6, 0)
StopButton.BackgroundColor3 = Color3.new(0.8, 0.2, 0.2)
StopButton.Text = "Остановить цикл"
StopButton.TextColor3 = Color3.new(1, 1, 1)
StopButton.TextSize = 14
StopButton.Font = Enum.Font.Gotham
StopButton.Parent = MainFrame

StopButton.MouseButton1Click:Connect(stopLoop)

local dragToggle = nil
local dragInput = nil
local dragStart = nil
local startPos = nil

local function updateInput(input)
    local delta = input.Position - dragStart
    MainFrame.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + delta.X, startPos.Y.Scale, startPos.Y.Offset + delta.Y)
end

TitleContainer.InputBegan:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1 then
        dragToggle = true
        dragStart = input.Position
        startPos = MainFrame.Position
        input.Changed:Connect(function()
            if input.UserInputState == Enum.UserInputState.End then
                dragToggle = false
            end
        end)
    end
end)

TitleContainer.InputChanged:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseMovement then
        dragInput = input
    end
end)

game:GetService("UserInputService").InputChanged:Connect(function(input)
    if input == dragInput and dragToggle then
        updateInput(input)
    end
end)

print("✅ Fer4ixz Script GUI загружен!")
