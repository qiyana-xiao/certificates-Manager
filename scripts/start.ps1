# 证件管家 · 一键启动脚本
# 自动：检测环境 -> 建venv装依赖 -> 生成.env -> 建库导种子 -> 启动后端+前端 -> 打开浏览器
# 面向小白：缺什么就在启动前用中文提示清楚，不静默失败。
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$be = Join-Path $root "backend"
$fe = Join-Path $root "frontend"
$venvPy = Join-Path $be ".venv\Scripts\python.exe"

function Print-OK([string]$m) { Write-Host ("  [OK] " + $m) -ForegroundColor Green }
function Print-Warn([string]$m) { Write-Host ("  [!] " + $m) -ForegroundColor Yellow }
function Print-Bad([string]$m) { Write-Host ("  [!!] " + $m) -ForegroundColor Red }

# 推荐 Python 版本号（3.10+），Store 存根会输出空，借此过滤
function Find-Python {
    foreach ($c in @("python", "py -3", "py")) {
        $parts = $c.Split(" ")
        try {
            $out = (& $parts[0] $parts[1..($parts.Length-1)] @("--version") 2>$null) -join " "
        } catch { $out = "" }
        if ($LASTEXITCODE -eq 0 -and $out -match "Python 3\.(\d+)") {
            $ver = [int]$matches[1]
            if ($ver -ge 10) { return @{ cmd = $c; version = $out.Trim() } }
        }
    }
    # 尝试常见安装路径
    foreach ($p in @("$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "C:\Python3*\python.exe")) {
        $hit = Get-ChildItem $p -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hit) {
            $out = (& $hit.FullName --version 2>$null) -join " "
            if ($out -match "Python") { return @{ cmd = $hit.FullName; version = $out.Trim() } }
        }
    }
    return $null
}

function Test-PortOpen([int]$port) {
    return (Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet)
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  证件管家 · 一键启动" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# ===== 0) 环境预检：缺啥先讲清楚，不静默失败 =====
Write-Host "步骤 0/7  检查运行环境 ..."
$py = Find-Python
if (-not $py) {
    Print-Bad "未找到 Python 3.10+。"
    Print-Bad "请到 https://www.python.org/downloads/ 安装，安装时务必勾选 Add Python to PATH，装完重开窗口再试。"
    Write-Host "按住任意键可查看上方提示……（安装好后重新双击启动脚本即可）"
    exit 1
}
Print-OK "Python: $($py.version)"

$nodeOk = $true
try { $nv = (& node --version 2>$null) -join "" } catch { $nv = "" }
if ($LASTEXITCODE -ne 0 -or -not $nv -match "v\d+") {
    $nodeOk = $false; Print-Bad "未找到 Node.js。"
    Print-Bad "请到 https://nodejs.org/ 下载 LTS 版安装，装完重开窗口再试。"
} else { Print-OK "Node: $($nv.Trim())" }

$mysqlOk = Test-PortOpen 3306
if (-not $mysqlOk) {
    Print-Bad "未检测到 MySQL（端口 3306 无服务）。"
    Print-Bad "证件管家需要本机 MySQL 8.0。请安装并启动 MySQL 后，再运行本脚本。"
} else { Print-OK "MySQL: 端口 3306 已监听" }

$redisOk = Test-PortOpen 6379
if ($redisOk) { Print-OK "Redis: 端口 6379 已监听（可选增强）" }
else { Print-Warn "Redis 未监听（可选）。系统会自动降级运行，不影响提醒正确性与数据安全。" }

if (-not $mysqlOk) {
    Write-Host ""
    Write-Host "环境就绪检查未通过，已停止启动。请解决上面 [!!] 标注的问题后重试。" -ForegroundColor Red
    exit 1
}
if (-not $nodeOk) {
    Write-Host ""
    Write-Host "环境就绪检查未通过，已停止启动。请解决上面 [!!] 标注的问题后重试。" -ForegroundColor Red
    exit 1
}

# ===== 1) 后端虚拟环境 =====
if (-not (Test-Path $venvPy)) {
    Write-Host "步骤 1/7  创建后端虚拟环境 (.venv) ..."
    & $py.cmd -m venv (Join-Path $be ".venv") 2>$null
    if ($LASTEXITCODE -ne 0 -and -not (Test-Path $venvPy)) {
        & $py.cmd -m pip install --quiet virtualenv
        & $py.cmd -m virtualenv (Join-Path $be ".venv")
    }
}
& $venvPy --version | Out-Null
Write-Host ("   Python 环境: " + (& $venvPy --version))

# ===== 2) 安装后端依赖 =====
Write-Host "步骤 2/7  安装后端依赖 (fastapi, sqlalchemy, ...) ..."
& $venvPy -m pip install --quiet --upgrade pip
& $venvPy -m pip install --quiet -r (Join-Path $be "requirements.txt")
if ($LASTEXITCODE -ne 0) { Print-Bad "后端依赖安装失败。请检查网络后重试。"; exit 1 }
Print-OK "后端依赖已就绪"

# ===== 3) 生成 backend\.env（若不存在） =====
$envFile = Join-Path $be ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "步骤 3/7  首次运行，生成配置 backend\.env ..."
    Copy-Item (Join-Path $be ".env.example") $envFile
    $dbPass = Read-Host "   请输入 MySQL 的 root 密码"
    $jwt = -join ((48..122) | Where-Object { $_ -notin 58..64 -and $_ -notin 91..96 } | Get-Random -Count 40 | ForEach-Object { [char]$_ })
    $bytes = New-Object byte[] 32
    (New-Object Random).NextBytes($bytes)
    $enc = [Convert]::ToBase64String($bytes)
    (Get-Content $envFile -Raw) `
        -replace "DB_PASSWORD=.*", ("DB_PASSWORD=" + $dbPass) `
        -replace "JWT_SECRET=.*", ("JWT_SECRET=" + $jwt) `
        -replace "ENC_KEY=.*", ("ENC_KEY=" + $enc) `
        | Set-Content -Path $envFile -Encoding UTF8
    Print-OK "已生成随机 JWT 密钥与加密密钥。下次启动将直接复用。"
} else {
    Print-OK "使用已有 backend\.env"
}

# ===== 4) 初始化数据库（幂等） =====
Write-Host "步骤 4/7  初始化数据库（建库 doc_keeper + 种子指南）..."
& $venvPy (Join-Path $root "scripts\init_db.py")
if ($LASTEXITCODE -ne 0) {
    Print-Bad "初始化数据库失败，请检查上面的报错（通常是 MySQL 密码不对或 MySQL 未启动）。"
    exit 1
}
Print-OK "数据库就绪"

# ===== 5) 启动后端（后台） =====
Write-Host "步骤 5/7  启动后端 FastAPI (127.0.0.1:8000) ..."
$newProcess = Start-Process -FilePath $venvPy -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -WorkingDirectory $be -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $be "backend.log") -RedirectStandardError (Join-Path $be "backend.err.log")
Set-Content -Path (Join-Path $be "backend.pid") -Value $newProcess.Id
Print-OK "后端 PID: $($newProcess.Id)（日志 backend\backend.log）"

# ===== 6) 前端依赖与启动 =====
Write-Host "步骤 6/7  准备前端 (Vue + Vite) ..."
if (-not (Test-Path (Join-Path $fe "node_modules"))) {
    Write-Host "   首次运行，安装前端依赖 (npm install) ..."
    Push-Location $fe
    npm install --no-audit --no-fund 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { Pop-Location; Print-Bad "前端依赖安装失败。请检查网络后重试。"; exit 1 }
    Pop-Location
}
$feProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run","dev" -WorkingDirectory $fe `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $fe "frontend.log") -RedirectStandardError (Join-Path $fe "frontend.err.log")
Set-Content -Path (Join-Path $fe "frontend.pid") -Value $feProcess.Id
Print-OK "前端 PID: $($feProcess.Id)"

# ===== 7) 等待就绪并打开浏览器 =====
Write-Host "步骤 7/7  等待服务就绪 ..."
$probe = $null
foreach ($i in 1..15) {
    Start-Sleep -Seconds 2
    try { $probe = Invoke-WebRequest "http://127.0.0.1:8000/api/health/ready" -TimeoutSec 4 -UseBasicParsing; if ($probe.StatusCode -eq 200) { break } } catch { $probe = $null }
}
if ($probe) {
    Start-Process "http://localhost:5173"
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host "  证件管家已启动！" -ForegroundColor Green
    Write-Host "  使用入口     http://localhost:5173" -ForegroundColor Green
    Write-Host "  首次使用：注册账号 -> 添加第一张证件 -> 提醒即刻生效" -ForegroundColor Green
    Write-Host "  停止服务：双击「停止-证件管家.bat」，或运行 scripts\stop.ps1" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "服务就绪等待超时。" -ForegroundColor Red
    Write-Host "  后端日志: backend\backend.err.log" -ForegroundColor Yellow
    Write-Host "  前端日志: frontend\frontend.err.log" -ForegroundColor Yellow
    Write-Host "  请查看日志中的报错，或确认端口 8000/5173 未被占用。" -ForegroundColor Yellow
    exit 1
}