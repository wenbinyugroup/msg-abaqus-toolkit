# Sync Documentation Images Script
# This script copies images from the source code to the documentation _static directory

Write-Host "🔄 Syncing documentation images..." -ForegroundColor Cyan

# Define source and target directories
$sourceIconDir = "scripts\Icon"
$sourceImageDir = "scripts\Image"
$targetIconDir = "doc\source\_static\images\icons"
$targetImageDir = "doc\source\_static\images\source_images"

# Check if source directories exist
if (!(Test-Path $sourceIconDir)) {
    Write-Host "❌ Source icon directory not found: $sourceIconDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $sourceImageDir)) {
    Write-Host "❌ Source image directory not found: $sourceImageDir" -ForegroundColor Red
    exit 1
}

# Create target directories if they don't exist
if (!(Test-Path $targetIconDir)) {
    Write-Host "📁 Creating target icon directory: $targetIconDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetIconDir -Force | Out-Null
}

if (!(Test-Path $targetImageDir)) {
    Write-Host "📁 Creating target image directory: $targetImageDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $targetImageDir -Force | Out-Null
}

# Copy icons
Write-Host "📋 Copying icons from $sourceIconDir to $targetIconDir..." -ForegroundColor Green
try {
    Copy-Item "$sourceIconDir\*" $targetIconDir -Force
    $iconCount = (Get-ChildItem $targetIconDir | Measure-Object).Count
    Write-Host "✅ Copied $iconCount icon files" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to copy icons: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Copy images
Write-Host "📋 Copying images from $sourceImageDir to $targetImageDir..." -ForegroundColor Green
try {
    Copy-Item "$sourceImageDir\*" $targetImageDir -Force
    $imageCount = (Get-ChildItem $targetImageDir | Measure-Object).Count
    Write-Host "✅ Copied $imageCount image files" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to copy images: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host ""
Write-Host "🎉 Image sync completed successfully!" -ForegroundColor Cyan
Write-Host "   Icons: $iconCount files in $targetIconDir" -ForegroundColor White
Write-Host "   Images: $imageCount files in $targetImageDir" -ForegroundColor White
Write-Host ""
Write-Host "💡 You can now reference these images in your documentation:" -ForegroundColor Yellow
Write-Host "   Icons: /_static/images/icons/filename.png" -ForegroundColor Gray
Write-Host "   Images: /_static/images/source_images/filename.png" -ForegroundColor Gray
Write-Host ""
Write-Host "🔨 To build documentation, run: cd doc && make html" -ForegroundColor Cyan
