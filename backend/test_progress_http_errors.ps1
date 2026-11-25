
# AI-Pulse Progress Tracking: HTTP Error Tests

$ErrorActionPreference = "Stop"
$baseUrl = "http://127.0.0.1:8000/api/v1/progress"
$passed = 0

function Assert-HttpError {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [int]$ExpectedStatus,
        [object]$Body = $null
    )

    $params = @{
        Uri = $Url
        Method = $Method
        ErrorAction = "Stop"
    }

    if ($null -ne $Body) {
        $params.ContentType = "application/json"
        $params.Body = ConvertTo-Json -InputObject $Body -Depth 10
    }

    try {
        $null = Invoke-RestMethod @params
    }
    catch {
        if ($null -eq $_.Exception.Response) {
            throw
        }

        $actual = [int]$_.Exception.Response.StatusCode

        if ($actual -ne $ExpectedStatus) {
            throw "$($Name): expected $ExpectedStatus, received $actual"
        }

        $script:passed++
        Write-Host "PASS $($script:passed): $Name (HTTP $actual)"
        return
    }

    throw "$($Name): expected HTTP $ExpectedStatus, but the request succeeded."
}

Write-Host "`n=== PROGRESS API ERROR HANDLING TESTS ==="

$before = Invoke-RestMethod `
    -Uri "$baseUrl/stats" `
    -Method Get

# Test 1: Missing goal
Assert-HttpError `
    -Name "Missing learning goal" `
    -Method "Get" `
    -Url "$baseUrl/goals/999999999" `
    -ExpectedStatus 404

# Test 2: Missing implementation log
Assert-HttpError `
    -Name "Missing activity log" `
    -Method "Get" `
    -Url "$baseUrl/logs/999999999" `
    -ExpectedStatus 404

# Test 3: Invalid referenced project
Assert-HttpError `
    -Name "Invalid project reference" `
    -Method "Post" `
    -Url "$baseUrl/logs" `
    -ExpectedStatus 404 `
    -Body @{
        title = "Invalid Project Test"
        project_id = 999999999
    }

# Test 4: Invalid referenced skill
Assert-HttpError `
    -Name "Invalid skill reference" `
    -Method "Post" `
    -Url "$baseUrl/goals" `
    -ExpectedStatus 404 `
    -Body @{
        title = "Invalid Skill Test"
        skill_id = 999999999
    }

# Test 5: Invalid completion progress
Assert-HttpError `
    -Name "Completed goal below 100 percent" `
    -Method "Post" `
    -Url "$baseUrl/goals" `
    -ExpectedStatus 400 `
    -Body @{
        title = "Invalid Completed Goal"
        status = "Completed"
        progress = 40
    }

# Test 6: Invalid date range for log filtering
Assert-HttpError `
    -Name "Reversed activity date range" `
    -Method "Get" `
    -Url "$baseUrl/logs?start_date=2026-11-25&end_date=2026-11-20" `
    -ExpectedStatus 400

# Test 7: Missing required title
Assert-HttpError `
    -Name "Missing goal title" `
    -Method "Post" `
    -Url "$baseUrl/goals" `
    -ExpectedStatus 422 `
    -Body @{
        progress = 20
    }

# Test 8: Progress outside allowed range
Assert-HttpError `
    -Name "Goal progress greater than 100" `
    -Method "Post" `
    -Url "$baseUrl/goals" `
    -ExpectedStatus 422 `
    -Body @{
        title = "Invalid Progress Test"
        progress = 150
    }

# Test 9: Negative activity duration
Assert-HttpError `
    -Name "Negative activity duration" `
    -Method "Post" `
    -Url "$baseUrl/logs" `
    -ExpectedStatus 422 `
    -Body @{
        title = "Invalid Duration Test"
        duration_minutes = -30
    }

# Test 10: Invalid activity type
Assert-HttpError `
    -Name "Unsupported activity type" `
    -Method "Post" `
    -Url "$baseUrl/logs" `
    -ExpectedStatus 422 `
    -Body @{
        title = "Invalid Activity Type"
        activity_type = "Gaming"
    }

# Test 11: Invalid pagination
Assert-HttpError `
    -Name "Invalid page size" `
    -Method "Get" `
    -Url "$baseUrl/goals?page_size=0" `
    -ExpectedStatus 422

# Test 12: Invalid goal dates
Assert-HttpError `
    -Name "Target date before start date" `
    -Method "Post" `
    -Url "$baseUrl/goals" `
    -ExpectedStatus 422 `
    -Body @{
        title = "Invalid Dates Test"
        start_date = "2026-11-23"
        target_date = "2026-11-22"
    }

# Verify no goals or activity logs were created.
$after = Invoke-RestMethod `
    -Uri "$baseUrl/stats" `
    -Method Get

if (
    $before.total_goals -ne $after.total_goals -or
    $before.total_logs -ne $after.total_logs
) {
    throw "Database counts changed during error tests."
}

Write-Host "`nPASS: Database record counts unchanged"

if ($passed -ne 12) {
    throw "Expected 12 passing tests, received $passed"
}

Write-Host "`nALL 12 HTTP ERROR TESTS PASSED"
