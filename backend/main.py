from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yaml
import asyncio
from typing import Dict, List
import json

# 导入API路由
try:
    from backend.api import real_robot, gazebo, test, data
except ImportError:
    # 如果导入失败，尝试相对导入
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from api import real_robot, gazebo, test, data
from backend.adapters.real_robot_adapter import RealRobotAdapter
from backend.adapters.gazebo_adapter import GazeboAdapter

import sys
import os
# 获取当前文件所在目录的父目录
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将项目根目录添加到Python路径
sys.path.insert(0, parent_dir)

app = FastAPI(
    title="BRUCE机器人交互测试平台",
    description="通过Web界面控制BRUCE实机和Gazebo仿真",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 导入API路由
app.include_router(real_robot.router, prefix="/api/real-robot")
app.include_router(gazebo.router, prefix="/api/gazebo")
app.include_router(test.router, prefix="/api/test")
app.include_router(data.router, prefix="/api/data")

# 全局状态
platform_adapters = {}
active_tests = {}
test_results = {}

def load_platform_config() -> Dict:
    """加载平台配置"""
    try:
        config_path = os.path.join("config", "platforms.yaml")
        if not os.path.exists(config_path):
            # 尝试相对路径
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "platforms.yaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        # 返回默认配置
        return {
            "platforms": {
                "real_robot": {
                    "enabled": False,
                    "name": "BRUCE实机",
                    "connection": {
                        "type": "ssh",
                        "host": "khadas@khadas.local",
                        "port": 22,
                        "password": "khadas"
                    }
                },
                "gazebo": {
                    "enabled": False,
                    "name": "Gazebo仿真",
                    "connection": {
                        "type": "local"
                    }
                }
            }
        }

@app.on_event("startup")
async def startup_event():
    """启动时初始化平台适配器"""
    print("🚀 启动BRUCE机器人测试平台...")
    
    # 加载配置
    with open("config/platforms.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # 初始化实机适配器
    if config["platforms"]["real_robot"]["enabled"]:
        try:
            real_adapter = RealRobotAdapter(config["platforms"]["real_robot"])
            if await real_adapter.connect():
                platform_adapters["real_robot"] = real_adapter
                print("✅ 实机适配器已连接")
        except Exception as e:
            print(f"❌ 实机适配器连接失败: {e}")
    
    # 初始化Gazebo适配器
    if config["platforms"]["gazebo"]["enabled"]:
        try:
            gazebo_adapter = GazeboAdapter(config["platforms"]["gazebo"])
            if await gazebo_adapter.connect():
                platform_adapters["gazebo"] = gazebo_adapter
                print("✅ Gazebo适配器已连接")
        except Exception as e:
            print(f"❌ Gazebo适配器连接失败: {e}")
    
    print(f"📊 已连接平台: {list(platform_adapters.keys())}")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    print("🛑 关闭平台...")
    for name, adapter in platform_adapters.items():
        await adapter.disconnect()
        print(f"✅ 已断开连接: {name}")

@app.get("/")
async def root():
    return {"message": "BRUCE机器人交互测试平台 API"}

@app.get("/api/status")
async def get_status():
    """获取所有平台状态"""
    status = {}
    for name, adapter in platform_adapters.items():
        try:
            platform_status = await adapter.get_status()
            status[name] = {
                "name": adapter.name,
                "connected": adapter.is_connected,
                "status": platform_status,
                "last_update": adapter.last_update
            }
        except Exception as e:
            status[name] = {
                "name": adapter.name,
                "connected": False,
                "error": str(e)
            }
    return status

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时数据传输"""
    await websocket.accept()
    client_id = id(websocket)
    print(f"🔗 WebSocket客户端已连接: {client_id}")
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "subscribe_status":
                # 定期发送状态更新
                async def send_status_updates():
                    while True:
                        status = await get_status()
                        await websocket.send_json({
                            "type": "status_update",
                            "data": status,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        await asyncio.sleep(1)  # 每秒更新一次
                
                asyncio.create_task(send_status_updates())
                
            elif command == "start_test":
                test_config = data.get("config", {})
                test_id = data.get("test_id", f"test_{int(asyncio.get_event_loop().time())}")
                
                # 执行测试
                results = await execute_test_concurrently(test_id, test_config)
                
                # 发送结果
                await websocket.send_json({
                    "type": "test_complete",
                    "test_id": test_id,
                    "results": results
                })
                
            elif command == "stop_test":
                test_id = data.get("test_id")
                if test_id in active_tests:
                    await active_tests[test_id].stop()
                    await websocket.send_json({
                        "type": "test_stopped",
                        "test_id": test_id
                    })
                    
    except WebSocketDisconnect:
        print(f"🔌 WebSocket客户端断开: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket错误: {e}")

async def execute_test_concurrently(test_id: str, config: dict):
    """并行执行测试"""
    target_platforms = config.get("platforms", list(platform_adapters.keys()))
    
    tasks = []
    for platform_name in target_platforms:
        if platform_name in platform_adapters:
            adapter = platform_adapters[platform_name]
            task = adapter.execute_test(config)
            tasks.append((platform_name, task))
    
    # 并行执行所有测试
    results = {}
    for platform_name, task in tasks:
        try:
            result = await task
            results[platform_name] = result
        except Exception as e:
            results[platform_name] = {
                "error": str(e),
                "status": "failed"
            }
    
    # 保存结果
    test_results[test_id] = {
        "test_id": test_id,
        "timestamp": asyncio.get_event_loop().time(),
        "config": config,
        "results": results
    }
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)