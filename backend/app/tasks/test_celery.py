"""
Celery 任务测试脚本

运行此脚本验证 Celery 配置是否正确

用法：
    python -m app.tasks.test_celery
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.tasks.celery_app import celery_app
    
    print("✓ Celery app 加载成功")
    print(f"  Broker: {celery_app.conf.broker_url}")
    print(f"  Backend: {celery_app.conf.result_backend}")
    print(f"  Timezone: {celery_app.conf.timezone}")
    
    print("\n✓ 已注册的任务模块:")
    for module in celery_app.conf.include:
        print(f"  - {module}")
    
    print("\n✓ Beat 定时任务:")
    for name, config in celery_app.conf.beat_schedule.items():
        print(f"  - {name}: {config['task']} ({config['schedule']})")
    
    print("\n✓ 所有已注册的任务:")
    for task_name in sorted(celery_app.tasks.keys()):
        if not task_name.startswith('celery.'):
            print(f"  - {task_name}")
    
    print("\n✓ Celery 配置验证通过！")
    
except Exception as e:
    print(f"✗ Celery 配置验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
