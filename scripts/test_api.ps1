$ErrorActionPreference = "Stop"
$BaseUrl = "http://127.0.0.1:8000"

function Invoke-ArlawChatTest {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Question,
        [Parameter(Mandatory=$true)][string]$Jurisdiction
    )
    Write-Host "`n========== $Name ==========" -ForegroundColor Cyan
    $body = @{
        messages = @(@{ role = "user"; content = $Question })
        jurisdiction = $Jurisdiction
        use_knowledge = $true
    } | ConvertTo-Json -Depth 8
    $result = Invoke-RestMethod -Uri "$BaseUrl/api/chat" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
    Write-Host ($result | ConvertTo-Json -Depth 12)
    return $result
}

Write-Host "Checking ARLAW AI health..." -ForegroundColor Cyan
$health = Invoke-RestMethod "$BaseUrl/api/health"
$health | Format-List
if ($health.status -ne "ok") { throw "ARLAW health check failed." }

$jurisdictions = Invoke-RestMethod "$BaseUrl/api/jurisdictions"
$codes = @($jurisdictions.groups | ForEach-Object { $_.items } | ForEach-Object { $_.code })
foreach ($required in @("IN", "US")) {
    if ($codes -notcontains $required) { throw "Required jurisdiction code $required is not registered." }
}

$india = Invoke-ArlawChatTest -Name "India - Article 21" -Jurisdiction "IN" -Question "Explain Article 21 of the Constitution of India. Distinguish the constitutional text from later judicial interpretation, and cite retrieved sources. State clearly if no authoritative source was retrieved."
$us = Invoke-ArlawChatTest -Name "United States - First Amendment" -Jurisdiction "US" -Question "Explain the First Amendment of the United States Constitution. Distinguish the constitutional text from judicial interpretation, and cite retrieved sources. State clearly if no authoritative source was retrieved."
$ambiguous = Invoke-ArlawChatTest -Name "Ambiguity - Agenda 51" -Jurisdiction "GLOBAL" -Question "Explain Agenda 51."
if (-not $ambiguous.needs_clarification) { Write-Warning "Agenda 51 did not trigger the expected clarification flag. Review the answer carefully." }
else { Write-Host "Ambiguity gate passed: clarification requested." -ForegroundColor Green }
Write-Host "`nSmoke tests completed. Review provider connectivity, citations and legal correctness manually." -ForegroundColor Green
