# 证件管家 · 停止脚本
# 停止后端与前端（连同其子进程整棵树，避免端口残留）
$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot
$be = Join-Path $root "backend"
$fe = Join-Path $root "frontend"

foreach ($pidFile in @(@("$be\backend.pid", "后端"), @("$fe\frontend.pid", "前端"))) {
    $path = $pidFile[0]; $label = $pidFile[1]
    if (Test-Path $path) {
        $id = Get-Content $path
        if ($id -match "^\d+$") {
            # 整进程树强制终止，保证 8000/5173 一定被释放
            & taskkill.exe /PID $id /T /F 2>&1 | Out-Null
            Write-Host "  已停止 $label  (PID $id)"
        }
        Remove-Item $path -Force
    }
}

# 兜底：PID 文件丢失但端口仍被占用时，按端口清理（防止二次启动报端口占用）。
foreach ($port in 8000, 5173) {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($c) {
        & taskkill.exe /PID $c.OwningProcess /T /F 2>&1 | Out-Null
        Write-Host "  已清理端口 $port 上的残留进程"
    }
}

Write-Host "证件管家已停止。" -ForegroundColor Green