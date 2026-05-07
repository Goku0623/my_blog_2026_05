#!/bin/bash

# Docker Compose 管理脚本
# 用法: ./docker-manage.sh [command]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 函数：打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
}

# 开发环境启动
dev_up() {
    info "启动开发环境..."
    
    if [ ! -f "backend/.env" ]; then
        warn "未找到 backend/.env，从 backend/.env.example 复制"
        cp backend/.env.example backend/.env
        warn "请编辑 backend/.env 填写必要的配置"
    fi
    
    docker-compose up -d --build
    info "开发环境已启动"
    info "前端（Nginx）: http://localhost"
    info "后端 API: http://localhost:8000"
    info "API 文档: http://localhost:8000/docs"
    info "Flower 监控: http://localhost:5555"
}

# 生产环境启动
prod_up() {
    info "启动生产环境..."
    
    if [ ! -f "backend/.env" ]; then
        error "未找到 backend/.env，请先配置环境变量"
        exit 1
    fi
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    info "生产环境已启动"
    info "应用: http://localhost"
}

# 停止所有服务
down() {
    info "停止所有服务..."
    docker-compose down
    info "所有服务已停止"
}

# 停止并删除数据卷
down_volumes() {
    warn "即将停止所有服务并删除数据卷（数据库数据将被清空）"
    read -p "确定继续吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        info "服务已停止，数据卷已删除"
    else
        info "操作已取消"
    fi
}

# 重启服务
restart() {
    info "重启所有服务..."
    docker-compose restart
    info "服务已重启"
}

# 查看日志
logs() {
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

# 查看服务状态
status() {
    docker-compose ps
}

# 数据库迁移
migrate() {
    info "执行数据库迁移..."
    docker-compose exec backend aerich upgrade
    info "数据库迁移完成"
}

# 创建新的数据库迁移
migrate_create() {
    if [ -z "$1" ]; then
        error "请提供迁移名称: ./docker-manage.sh migrate:create <name>"
        exit 1
    fi
    
    info "创建新的数据库迁移: $1"
    docker-compose exec backend aerich migrate --name "$1"
    info "迁移文件已创建"
}

# 数据库备份
backup() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    info "备份数据库到 $BACKUP_FILE..."
    
    mkdir -p backups
    docker-compose exec -T postgres pg_dump -U blog_user blog_db > "backups/$BACKUP_FILE"
    
    info "数据库备份完成: backups/$BACKUP_FILE"
}

# 数据库恢复
restore() {
    if [ -z "$1" ]; then
        error "请提供备份文件: ./docker-manage.sh restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        error "备份文件不存在: $1"
        exit 1
    fi
    
    warn "即将从备份恢复数据库，当前数据将被覆盖"
    read -p "确定继续吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "恢复数据库从 $1..."
        docker-compose exec -T postgres psql -U blog_user blog_db < "$1"
        info "数据库恢复完成"
    else
        info "操作已取消"
    fi
}

# 清理 Docker 资源
clean() {
    warn "清理未使用的 Docker 资源..."
    docker image prune -f
    docker volume prune -f
    info "清理完成"
}

# 深度清理
clean_all() {
    warn "即将清理所有未使用的 Docker 资源（包括镜像、容器、卷）"
    read -p "确定继续吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -a --volumes -f
        info "深度清理完成"
    else
        info "操作已取消"
    fi
}

# 进入容器 shell
shell() {
    SERVICE="${1:-backend}"
    info "进入 $SERVICE 容器..."
    docker-compose exec "$SERVICE" /bin/sh
}

# 查看资源使用情况
stats() {
    docker stats
}

# 帮助信息
show_help() {
    cat << EOF
Docker Compose 管理脚本

用法: $0 [command]

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
  
  shell [service]   进入容器 shell（默认 backend）
  stats             查看资源使用情况
  clean             清理未使用的 Docker 资源
  clean:all         深度清理所有未使用资源
  
  help              显示此帮助信息

示例:
  $0 dev                          # 启动开发环境
  $0 logs backend                 # 查看后端日志
  $0 migrate:create add_user_table # 创建数据库迁移
  $0 backup                       # 备份数据库
  $0 shell backend                # 进入后端容器

EOF
}

# 主函数
main() {
    check_docker
    
    case "$1" in
        dev)
            dev_up
            ;;
        prod)
            prod_up
            ;;
        down)
            down
            ;;
        down:volumes)
            down_volumes
            ;;
        restart)
            restart
            ;;
        logs)
            logs "$2"
            ;;
        status)
            status
            ;;
        migrate)
            migrate
            ;;
        migrate:create)
            migrate_create "$2"
            ;;
        backup)
            backup
            ;;
        restore)
            restore "$2"
            ;;
        shell)
            shell "$2"
            ;;
        stats)
            stats
            ;;
        clean)
            clean
            ;;
        clean:all)
            clean_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

main "$@"
