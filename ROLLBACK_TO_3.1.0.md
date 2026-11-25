# Rollback plan

If 3.1.1 fails your local tests or behaves worse in production, restore the supplied `ARLAW_AI_Global_3.1.0_Final_Rollback.zip` archive. It is built from the previous 3.1.0 project source and its automated suite passes (115 tests in the prepared environment).

Windows PowerShell 5.1 (run from the directory containing the downloaded rollback ZIP):

```powershell
$Project = "$env:USERPROFILE\OneDrive\Desktop\ARLAW_AI_Global"
$Zip = "$env:USERPROFILE\Downloads\ARLAW_AI_Global_3.1.0_Final_Rollback.zip"
$Temp = "$env:TEMP\ARLAW_3.1.0_Rollback"

if (!(Test-Path $Project)) { throw "Project folder not found: $Project" }
Copy-Item $Project "$Project-backup-before-rollback" -Recurse
Remove-Item $Temp -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -LiteralPath $Zip -DestinationPath $Temp -Force

# The archive contains ARLAW_AI_Global as its top-level folder.
Get-ChildItem (Join-Path $Temp "ARLAW_AI_Global") -Force | ForEach-Object {
    Copy-Item $_.FullName $Project -Recurse -Force
}

Set-Location $Project
python -m pytest -q
```

Do not push or redeploy until the rollback test suite passes. Preserve the backup folder until the rollback is confirmed. This rollback restores the 3.1.0 code baseline; it does not reverse external database migrations or hosted environment-variable changes.
