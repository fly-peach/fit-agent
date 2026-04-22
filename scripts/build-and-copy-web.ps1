Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$webpageDir = Join-Path $root "webpage"
$target = Join-Path $root "Rogers/webpage"
$lockFile = Join-Path $webpageDir "package-lock.json"
$nodeModulesDir = Join-Path $webpageDir "node_modules"

if (-not (Test-Path $webpageDir)) {
  throw "webpage directory not found: $webpageDir"
}

Push-Location $webpageDir
# 1) Install deps (smart mode)
# FORCE_CI=1  -> always npm ci
# FORCE_INSTALL=1 -> always npm install
# SKIP_INSTALL=1 -> skip installation
$forceCi = $env:FORCE_CI -eq "1"
$forceInstall = $env:FORCE_INSTALL -eq "1"
$skipInstall = $env:SKIP_INSTALL -eq "1"

if (-not $skipInstall) {
  if ($forceCi) {
    npm ci
  } elseif ($forceInstall) {
    npm install
  } else {
    if (-not (Test-Path $nodeModulesDir)) {
      npm install
    } else {
      Write-Host "Skip npm install (node_modules is up to date)"
    }
  }
} else {
  Write-Host "Skip dependency install because SKIP_INSTALL=1"
}
if ($LASTEXITCODE -ne 0 -and -not $skipInstall) {
  Write-Host "Install failed, try to clean npm lock dirs and retry..."
  if (Test-Path $nodeModulesDir) {
    Get-ChildItem -Path $nodeModulesDir -Filter ".caniuse-lite*" -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $caniuseDir = Join-Path $nodeModulesDir "caniuse-lite"
    if (Test-Path $caniuseDir) {
      Remove-Item -Path $caniuseDir -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
  npm cache verify | Out-Null
  if ($forceCi -and (Test-Path $lockFile)) {
    npm ci
  } elseif ($forceInstall) {
    npm install
  } elseif (Test-Path $lockFile) {
    npm ci
  } else {
    npm install
  }
}
if ($LASTEXITCODE -ne 0) { throw "npm install failed, exit code: $LASTEXITCODE" }

npm run build
if ($LASTEXITCODE -ne 0) {
  if (-not $skipInstall -and -not $forceCi) {
    Write-Host "Build failed, retry after npm install..."
    npm install
    if ($LASTEXITCODE -ne 0) {
      Write-Host "npm install retry failed, clean node_modules and reinstall..."
      if (Test-Path $nodeModulesDir) {
        Remove-Item -Path $nodeModulesDir -Recurse -Force -ErrorAction SilentlyContinue
      }
      if (Test-Path $lockFile) {
        npm ci
      } else {
        npm install
      }
    }
    if ($LASTEXITCODE -ne 0) { throw "dependency install failed in retry, exit code: $LASTEXITCODE" }
    npm run build
  }
  if ($LASTEXITCODE -ne 0) { throw "npm build failed, exit code: $LASTEXITCODE" }
}
Pop-Location

# 2) 复制构建产物到包目录
New-Item -ItemType Directory -Path $target -Force | Out-Null
$distDir = Join-Path $webpageDir "dist"
if (-not (Test-Path $distDir)) {
  throw "dist directory not found: $distDir"
}
Copy-Item -Path (Join-Path $distDir "*") -Destination $target -Recurse -Force

Write-Host "Frontend build copied to Rogers/webpage"
