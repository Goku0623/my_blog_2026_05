# Makefile for Docker Compose Management
# 简化 Docker 操作的快捷命令

.PHONY: help dev prod down down-volumes restart logs status migrate migrate-create backup restore purge-test-data purge-test-data-with-uploads shell stats clean clean-all

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

## help: 显示帮助信息
help:
	@echo "Docker Compose 管理命令"
	@echo ""
	@echo "用法: make [command]"
	@echo ""
	@echo "命令:"
	@echo "  ${GREEN}make dev${NC}              启动开发环境（热重载）"
	@echo "  ${GREEN}make prod${NC}             启动生产环境（多进程）"
	@echo "  ${GREEN}make down${NC}             停止所有服务"
	@echo "  ${GREEN}make down-volumes${NC}     停止服务并删除数据卷"
	@echo "  ${GREEN}make restart${NC}          重启所有服务"
	@echo "  ${GREEN}make logs${NC}             查看所有日志"
	@echo "  ${GREEN}make logs-backend${NC}     查看后端日志"
	@echo "  ${GREEN}make logs-celery${NC}      查看 Celery 日志"
	@echo "  ${GREEN}make status${NC}           查看服务状态"
	@echo ""
	@echo "  ${GREEN}make migrate${NC}          执行数据库迁移"
	@echo "  ${GREEN}make backup${NC}           备份数据库"
	@echo "  ${GREEN}make shell${NC}            进入后端容器"
	@echo "  ${GREEN}make shell-db${NC}         进入数据库容器"
	@echo "  ${GREEN}make stats${NC}            查看资源使用情况"
	@echo "  ${GREEN}make clean${NC}            清理未使用的 Docker 资源"
	@echo ""

## dev: 启动开发环境
dev:
	@if [ ! -f .env ]; then \
		echo "${YELLOW}[WARN]${NC} 未找到 .env，从 .env.example 复制"; \
		cp .env.example .env; \
		echo "${YELLOW}[WARN]${NC} 请编辑 .env 填写 Docker 编排配置（数据库/端口/Flower 认证）"; \
	fi
	@if [ ! -f backend/.env.docker ]; then \
		echo "${YELLOW}[WARN]${NC} 未找到 backend/.env.docker，从 backend/.env.docker.example 复制"; \
		cp backend/.env.docker.example backend/.env.docker; \
		echo "${YELLOW}[WARN]${NC} 请编辑 backend/.env.docker 填写应用配置"; \
	fi
	@echo "${GREEN}[INFO]${NC} 启动开发环境..."
	docker-compose up -d --build
	@echo "${GREEN}[INFO]${NC} 开发环境已启动"
	@echo "${GREEN}[INFO]${NC} 前端（Nginx）: http://localhost"
	@echo "${GREEN}[INFO]${NC} 后端 API: http://localhost:8000"
	@echo "${GREEN}[INFO]${NC} API 文档: http://localhost:8000/api/docs"
	@echo "${GREEN}[INFO]${NC} Flower 监控: http://localhost:5555"

## prod: 启动生产环境
prod:
	@if [ ! -f .env ]; then \
		echo "${YELLOW}[ERROR]${NC} 未找到 .env，请先配置 Docker 编排环境变量"; \
		exit 1; \
	fi
	@if [ ! -f backend/.env.docker ]; then \
		echo "${YELLOW}[ERROR]${NC} 未找到 backend/.env.docker，请先配置应用环境变量"; \
		exit 1; \
	fi
	@echo "${GREEN}[INFO]${NC} 启动生产环境..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "${GREEN}[INFO]${NC} 生产环境已启动"
	@echo "${GREEN}[INFO]${NC} 应用: http://localhost"

## down: 停止所有服务
down:
	@echo "${GREEN}[INFO]${NC} 停止所有服务..."
	docker-compose down
	@echo "${GREEN}[INFO]${NC} 所有服务已停止"

## down-volumes: 停止服务并删除数据卷
down-volumes:
	@echo "${YELLOW}[WARN]${NC} 即将停止所有服务并删除数据卷（数据库数据将被清空）"
	@read -p "确定继续吗？(y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down -v; \
		echo "${GREEN}[INFO]${NC} 服务已停止，数据卷已删除"; \
	else \
		echo "${GREEN}[INFO]${NC} 操作已取消"; \
	fi

## restart: 重启所有服务
restart:
	@echo "${GREEN}[INFO]${NC} 重启所有服务..."
	docker-compose restart
	@echo "${GREEN}[INFO]${NC} 服务已重启"

## logs: 查看所有日志
logs:
	docker-compose logs -f

## logs-backend: 查看后端日志
logs-backend:
	docker-compose logs -f backend

## logs-celery: 查看 Celery Worker 日志
logs-celery:
	docker-compose logs -f celery_worker

## logs-nginx: 查看 Nginx 日志
logs-nginx:
	docker-compose logs -f nginx

## status: 查看服务状态
status:
	docker-compose ps

## migrate: 执行数据库迁移
migrate:
	@echo "${GREEN}[INFO]${NC} 执行数据库迁移..."
	docker-compose exec backend aerich upgrade
	@echo "${GREEN}[INFO]${NC} 数据库迁移完成"

## migrate-create: 创建新的数据库迁移
migrate-create:
	@read -p "迁移名称: " name; \
	echo "${GREEN}[INFO]${NC} 创建新的数据库迁移: $$name"; \
	docker-compose exec backend aerich migrate --name "$$name"; \
	echo "${GREEN}[INFO]${NC} 迁移文件已创建"

## backup: 备份数据库
backup:
	@mkdir -p backups
	@BACKUP_FILE="backup_$$(date +%Y%m%d_%H%M%S).sql"; \
	echo "${GREEN}[INFO]${NC} 备份数据库到 $$BACKUP_FILE..."; \
	docker-compose exec -T postgres pg_dump -U blog_user blog_db > "backups/$$BACKUP_FILE"; \
	echo "${GREEN}[INFO]${NC} 数据库备份完成: backups/$$BACKUP_FILE"

## restore: 从备份恢复数据库
restore:
	@read -p "备份文件路径: " file; \
	if [ ! -f "$$file" ]; then \
		echo "${YELLOW}[ERROR]${NC} 备份文件不存在: $$file"; \
		exit 1; \
	fi; \
	echo "${YELLOW}[WARN]${NC} 即将从备份恢复数据库，当前数据将被覆盖"; \
	read -p "确定继续吗？(y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "${GREEN}[INFO]${NC} 恢复数据库从 $$file..."; \
		docker-compose exec -T postgres psql -U blog_user blog_db < "$$file"; \
		echo "${GREEN}[INFO]${NC} 数据库恢复完成"; \
	else \
		echo "${GREEN}[INFO]${NC} 操作已取消"; \
	fi

## purge-test-data: 清理测试数据（保留管理员账户与系统配置）
purge-test-data:
	@echo "${YELLOW}[WARN]${NC} 即将清理测试数据（保留管理员账户与系统配置）"
	@read -p "确定继续吗？(y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose exec backend python -m scripts.purge_test_data --yes; \
	else \
		echo "${GREEN}[INFO]${NC} 操作已取消"; \
	fi

## purge-test-data-with-uploads: 清理测试数据并清空上传目录
purge-test-data-with-uploads:
	@echo "${YELLOW}[WARN]${NC} 即将清理测试数据并清空 uploads（保留管理员账户与系统配置）"
	@read -p "确定继续吗？(y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose exec backend python -m scripts.purge_test_data --yes --clear-uploads; \
	else \
		echo "${GREEN}[INFO]${NC} 操作已取消"; \
	fi

## shell: 进入后端容器
shell:
	@echo "${GREEN}[INFO]${NC} 进入后端容器..."
	docker-compose exec backend /bin/sh

## shell-db: 进入数据库容器
shell-db:
	@echo "${GREEN}[INFO]${NC} 进入数据库容器..."
	docker-compose exec postgres psql -U blog_user -d blog_db

## shell-redis: 进入 Redis 容器
shell-redis:
	@echo "${GREEN}[INFO]${NC} 进入 Redis 容器..."
	docker-compose exec redis redis-cli

## stats: 查看资源使用情况
stats:
	docker stats

## clean: 清理未使用的 Docker 资源
clean:
	@echo "${YELLOW}[WARN]${NC} 清理未使用的 Docker 资源..."
	docker image prune -f
	docker volume prune -f
	@echo "${GREEN}[INFO]${NC} 清理完成"

## clean-all: 深度清理所有未使用资源
clean-all:
	@echo "${YELLOW}[WARN]${NC} 即将清理所有未使用的 Docker 资源（包括镜像、容器、卷）"
	@read -p "确定继续吗？(y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker system prune -a --volumes -f; \
		echo "${GREEN}[INFO]${NC} 深度清理完成"; \
	else \
		echo "${GREEN}[INFO]${NC} 操作已取消"; \
	fi
