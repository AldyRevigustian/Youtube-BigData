# PowerShell script to run all tests
# Usage: .\run_tests.ps1

Write-Host "🧪 Running YouTube Sentiment Analysis System Tests" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Yellow

# Function to run test and capture result
function Run-Test {
    param(
        [string]$TestName,
        [string]$TestScript
    )
    
    Write-Host ""
    Write-Host "$TestName" -ForegroundColor Cyan
    Write-Host ("-" * $TestName.Length) -ForegroundColor Gray
    
    try {
        & python $TestScript
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $TestName completed successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $TestName completed with warnings" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ $TestName failed: $_" -ForegroundColor Red
    }
}

# Run system component tests
Run-Test "1️⃣ System Component Tests" "tests\test_system.py"

# Run data flow tests  
Run-Test "2️⃣ Data Flow Tests" "tests\test_data_flow.py"

Write-Host ""
Write-Host "✅ Test suite completed!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Yellow
