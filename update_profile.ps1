$profilePath = $PROFILE
if (!(Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force
}

$content = @"

# AI Agent Recording Alias
function Record-AIProject {
    & "C:\Users\natum\anaconda3\python.exe" "C:\Users\natum\Desktop\LLM-agent\record_agent.py" $args
}
if (Test-Path Alias:record) { Remove-Item Alias:record }
Set-Alias record Record-AIProject
"@

Add-Content -Path $profilePath -Value $content
Write-Host "✅ PowerShell profile has been updated!"
