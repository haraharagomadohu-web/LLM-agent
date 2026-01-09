$profilePath = $PROFILE
$dir = Split-Path $profilePath
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force }

# 完全に新しく作り直す（既存の壊れた記述を消去）
$content = @'
# AI Agent Recording Alias
function Record-AIProject {
    param($ProjectArgs)
    & "C:\Users\natum\anaconda3\python.exe" "C:\Users\natum\Desktop\LLM-agent\record_agent.py" $ProjectArgs
}
if (Test-Path Alias:record) { Remove-Item Alias:record -Force }
Set-Alias record Record-AIProject
'@

Set-Content -Path $profilePath -Value $content -Encoding utf8
Write-Host "✅ PowerShell profile has been fixed and overwritten!"
