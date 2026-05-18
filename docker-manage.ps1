# Docker 管理脚本 (PowerShell)
# 用法: .\docker-manage.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$Arg1
)

# 颜色输出函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

# 检查 Docker 是否安装
function Test-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Docker 未安装，请先安装 Docker Desktop"
        exit 1
    }
    
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Docker Compose 未安装"
        exit 1
    }
}

# 开发环境启动
function Start-Dev {
    Write-Info "启动开发环境..."
    
    if (-not (Test-Path ".env")) {
        Write-Warn "未找到 .env，从 .env.example 复制"
        Copy-Item ".env.example" ".env"
        Write-Warn "请编辑 .env 填写 Docker 编排配置（数据库/端口/Flower 认证）"
    }

    if (-not (Test-Path "backend\.env.docker")) {
        Write-Warn "未找到 backend\.env.docker，从 backend\.env.docker.example 复制"
        Copy-Item "backend\.env.docker.example" "backend\.env.docker"
        Write-Warn "请编辑 backend\.env.docker 填写应用配置"
    }
    
    docker-compose up -d --build
    Write-Info "开发环境已启动"
    Write-Info "前端（Nginx）: http://localhost"
    Write-Info "后端 API: http://localhost:8000"
    Write-Info "API 文档: http://localhost:8000/api/docs"
    Write-Info "Flower 监控: http://localhost:5555"
}

# 生产环境启动
function Start-Prod {
    Write-Info "启动生产环境..."
    
    if (-not (Test-Path ".env")) {
        Write-Error-Custom "未找到 .env，请先配置 Docker 编排环境变量"
        exit 1
    }

    if (-not (Test-Path "backend\.env.docker")) {
        Write-Error-Custom "未找到 backend\.env.docker，请先配置应用环境变量"
        exit 1
    }
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    Write-Info "生产环境已启动"
    Write-Info "应用: http://localhost"
}

# 停止所有服务
function Stop-Services {
    Write-Info "停止所有服务..."
    docker-compose down
    Write-Info "所有服务已停止"
}

# 停止并删除数据卷
function Stop-ServicesWithVolumes {
    Write-Warn "即将停止所有服务并删除数据卷（数据库数据将被清空）"
    $confirm = Read-Host "确定继续吗？(y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        docker-compose down -v
        Write-Info "服务已停止，数据卷已删除"
    } else {
        Write-Info "操作已取消"
    }
}

# 重启服务
function Restart-Services {
    Write-Info "重启所有服务..."
    docker-compose restart
    Write-Info "服务已重启"
}

# 查看日志
function Show-Logs {
    param([string]$Service)
    if ([string]::IsNullOrEmpty($Service)) {
        docker-compose logs -f
    } else {
        docker-compose logs -f $Service
    }
}

# 查看服务状态
function Show-Status {
    docker-compose ps
}

# 数据库迁移
function Invoke-Migrate {
    Write-Info "执行数据库迁移..."
    docker-compose exec backend aerich upgrade
    Write-Info "数据库迁移完成"
}

# 创建新的数据库迁移
function New-Migration {
    param([string]$Name)
    if ([string]::IsNullOrEmpty($Name)) {
        Write-Error-Custom "请提供迁移名称: .\docker-manage.ps1 migrate:create <name>"
        exit 1
    }
    
    Write-Info "创建新的数据库迁移: $Name"
    docker-compose exec backend aerich migrate --name $Name
    Write-Info "迁移文件已创建"
}

# 数据库备份
function Backup-Database {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_$timestamp.sql"
    Write-Info "备份数据库到 $backupFile..."
    
    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" | Out-Null
    }
    
    docker-compose exec -T postgres pg_dump -U blog_user blog_db | Out-File -FilePath "backups\$backupFile" -Encoding UTF8
    Write-Info "数据库备份完成: backups\$backupFile"
}

# 数据库恢复
function Restore-Database {
    param([string]$BackupFile)
    if ([string]::IsNullOrEmpty($BackupFile)) {
        Write-Error-Custom "请提供备份文件: .\docker-manage.ps1 restore <backup_file>"
        exit 1
    }
    
    if (-not (Test-Path $BackupFile)) {
        Write-Error-Custom "备份文件不存在: $BackupFile"
        exit 1
    }
    
    Write-Warn "即将从备份恢复数据库，当前数据将被覆盖"
    $confirm = Read-Host "确定继续吗？(y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        Write-Info "恢复数据库从 $BackupFile..."
        Get-Content $BackupFile | docker-compose exec -T postgres psql -U blog_user blog_db
        Write-Info "数据库恢复完成"
    } else {
        Write-Info "操作已取消"
    }
}

# 清理 Docker 资源
function Clear-DockerResources {
    Write-Warn "清理未使用的 Docker 资源..."
    docker image prune -f
    docker volume prune -f
    Write-Info "清理完成"
}

# 深度清理
function Clear-AllDockerResources {
    Write-Warn "即将清理所有未使用的 Docker 资源（包括镜像、容器、卷）"
    $confirm = Read-Host "确定继续吗？(y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        docker system prune -a --volumes -f
        Write-Info "深度清理完成"
    } else {
        Write-Info "操作已取消"
    }
}

# 进入容器 shell
function Enter-Shell {
    param([string]$Service = "backend")
    Write-Info "进入 $Service 容器..."
    docker-compose exec $Service /bin/sh
}

# 查看资源使用情况
function Show-Stats {
    docker stats
}

# 帮助信息
function Invoke-PurgeTestData {
    param([string]$Mode)

    Write-Warn "即将清理测试数据（保留管理员账户与系统配置）"
    $confirm = Read-Host "确定继续吗？(y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Info "操作已取消"
        return
    }

    if ($Mode -eq "with-uploads") {
        Write-Warn "将同时清空 backend/uploads 下文件，请确认系统配置中的媒体 URL 可重建"
        docker-compose exec backend python -m scripts.purge_test_data --yes --clear-uploads
    } else {
        docker-compose exec backend python -m scripts.purge_test_data --yes
    }
}

# 帮助信息
function Show-Help {
    Write-Host @"

Docker Compose 管理脚本 (PowerShell)

用法: .\docker-manage.ps1 [command]

命令:
  dev               启动开发环境（热重载）
  prod              启动生产环境（多进程）
  down              停止所有服务
  down:volumes      停止服务并删除数据卷
  restart           重启所有服务
  logs [service]    查看日志（可选指定服务）
  status            查看服务状态
  
  migrate           执行数据库迁移
  migrate:create    创建新的数据库迁移
  backup            备份数据库
  restore <file>    从备份恢复数据库
  purge:test-data [with-uploads]
                    清理测试数据（保留管理员账户与系统配置）
  
  shell [service]   进入容器 shell（默认 backend）
  stats             查看资源使用情况
  clean             清理未使用的 Docker 资源
  clean:all         深度清理所有未使用资源
  
  help              显示此帮助信息

示例:
  .\docker-manage.ps1 dev                          # 启动开发环境
  .\docker-manage.ps1 logs backend                 # 查看后端日志
  .\docker-manage.ps1 migrate:create add_user_table # 创建数据库迁移
  .\docker-manage.ps1 backup                       # 备份数据库
  .\docker-manage.ps1 shell backend                # 进入后端容器

"@
}

# 主函数
function Main {
    Test-Docker
    
    switch ($Command) {
        "dev" { Start-Dev }
        "prod" { Start-Prod }
        "down" { Stop-Services }
        "down:volumes" { Stop-ServicesWithVolumes }
        "restart" { Restart-Services }
        "logs" { Show-Logs -Service $Arg1 }
        "status" { Show-Status }
        "migrate" { Invoke-Migrate }
        "migrate:create" { New-Migration -Name $Arg1 }
        "backup" { Backup-Database }
        "restore" { Restore-Database -BackupFile $Arg1 }
        "purge:test-data" { Invoke-PurgeTestData -Mode $Arg1 }
        "shell" { Enter-Shell -Service $Arg1 }
        "stats" { Show-Stats }
        "clean" { Clear-DockerResources }
        "clean:all" { Clear-AllDockerResources }
        { $_ -in "help", "--help", "-h", "" } { Show-Help }
        default {
            Write-Error-Custom "未知命令: $Command"
            Write-Host ""
            Show-Help
            exit 1
        }
    }
}

# 执行主函数
Main
