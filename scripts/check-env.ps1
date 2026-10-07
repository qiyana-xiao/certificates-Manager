# 证件管家 · 环境检测脚本
# 检测 Python / Node / npm / MySQL(3306) / Redis(6379) 是否就绪
param()
$ErrorActionPreference = "Continue"

function Test-Cmd([string]$name, [string]$argsList) {
    try {
        $v = & $name $argsList 2>$null
        if ($LASTEXITCODE -eq 0) { return ($v -join ' ').Trim() }
    } catch {}
    return ""
}

Write-Host "== 证件管家环境检测 ==" -ForegroundColor Cyan

$py = ""
foreach ($c in @(@("python","--version"), @("py","-3 -m  --version"), @("py","--version"))) {
    # 简化：优先 python，其次 py
    $v = ""
    if ($c[0] -eq "python") { $v = Test-Cmd "python" "--version" }
    else {
        $vOut = & $c[0] $c[1].Split(" ") 2>$null
        $v = ($vOut -join ' ').Trim()
    }
    if ($py -eq "" -and $v) { $py = "$($c[0]) -> $v"; break }
}
if ($py) { Write-Host "  [OK] Python  $py" -ForegroundColor Green }
else {
    Write-Host "  [!!] Python 未找到。请安装 Python 3.10+ 并加入 PATH。" -ForegroundColor Red
}

$node = Test-Cmd "node" "--version"
if ($node) { Write-Host "  [OK] Node    $node" -ForegroundColor Green }
else { Write-Host "  [!!] Node.js 未找到。请安装 Node 18+。" -ForegroundColor Red }

$ports = @(3306, 6379)
foreach ($p in $ports) {
    $ok = (Test-NetConnection -ComputerName localhost -Port $p -WarningAction SilentlyContinue -InformationLevel Quiet)
    $name = if ($p -eq 3306) { "MySQL" } else { "Redis" }
    if ($ok) { Write-Host "  [OK] $name   端口 $p 已监听" -ForegroundColor Green }
    else { Write-Host "  [!!] $name   端口 $p 未监听（如需提醒可用 Redis 可暂缓）" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "检测完成。缺少项：请按上面的提示安装；MySQL 必须可用，Redis 可选。" -ForegroundColor Cyan