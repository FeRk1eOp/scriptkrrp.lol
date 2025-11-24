local whitelistecheck = loadstring(game:HttpGet("https://raw.githubusercontent.com/FeRk1eOp/scriptkrrp.lol/refs/heads/main/DataBase.lua", true))()

if whitelistecheck[game:service('Players').LocalPlayer.UserId] then
  loadstring(game:HttpGet("https://raw.githubusercontent.com/FeRk1eOp/scriptkrrp.lol/refs/heads/main/main.lua", true))()
else
  game:service('Players').LocalPlayer:Kick('Bruh')
end
