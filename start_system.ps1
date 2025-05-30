# PowerShell script to start YouTube Sentiment Analysis System
# Usage: .\start_system.ps1

Write-Host "🚀 Starting YouTube Sentiment Analysis System..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Yellow

# Function to start service in new window
function Start-ServiceInNewWindow {
    param(
        [string]$ServiceName,
        [string]$ScriptPath,
        [string]$WorkingDirectory
    )
    
    try {
        Start-Process -FilePath "python" -ArgumentList $ScriptPath -WorkingDirectory $WorkingDirectory -WindowStyle Normal
        Write-Host "   ✅ Started $ServiceName" -ForegroundColor Green
        Start-Sleep -Seconds 2
    }
    catch {
        Write-Host "   ❌ Failed to start $ServiceName : $_" -ForegroundColor Red
    }
}

# Get current directory
$RootDir = Get-Location

# Define services to start
$Services = @(
    @{Name = "YouTube API"; Path = "ingestion\youtube_api.py"},
    @{Name = "Sentiment Analyzer"; Path = "processing\sentiment_analyzer.py"},
    @{Name = "Comment Summarizer"; Path = "processing\comment_summarizer.py"}
)

# Start Python services
foreach ($Service in $Services) {
    Start-ServiceInNewWindow -ServiceName $Service.Name -ScriptPath $Service.Path -WorkingDirectory $RootDir
}

# Start Streamlit Dashboard
try {
    Start-Process -FilePath "streamlit" -ArgumentList "run", "dashboard\dashboard.py" -WorkingDirectory $RootDir -WindowStyle Normal
    Write-Host "   ✅ Started Streamlit Dashboard" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Failed to start Dashboard: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎯 All services started successfully!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Yellow
Write-Host "📊 Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host "⚡ Storm UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🔧 To stop services, close the command windows" -ForegroundColor Yellow
