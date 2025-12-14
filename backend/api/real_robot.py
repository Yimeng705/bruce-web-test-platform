from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from typing import Any
from backend.adapters.real_robot_adapter import RealRobotAdapter
from backend.utils.logger import robot_logger as logger
from backend.data.storage import DataStorage

router = APIRouter()

# 全局适配器实例
real_robot_adapter: Optional[RealRobotAdapter] = None
data_storage = DataStorage()

@router.post("/connect")
async def connect():
    """连接实机"""
    global real_robot_adapter
    
    if real_robot_adapter and real_robot_adapter.is_connected:
        return {
            "success": True,
            "message": "Already connected",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        from backend.main import load_platform_config
        config = load_platform_config().get("real_robot", {})
        
        if not config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Real robot platform is disabled")
        
        real_robot_adapter = RealRobotAdapter(config)
        connected = await real_robot_adapter.connect()
        
        if connected:
            logger.info("Real robot connected successfully")
            return {
                "success": True,
                "message": "Connected to real robot",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("Failed to connect to real robot")
            raise HTTPException(status_code=500, detail="Failed to connect to real robot")
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
async def disconnect():
    """断开连接"""
    global real_robot_adapter
    
    try:
        if real_robot_adapter:
            await real_robot_adapter.disconnect()
            real_robot_adapter = None
            logger.info("Real robot disconnected")
        
        return {
            "success": True,
            "message": "Disconnected from real robot",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Disconnection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """获取实机状态"""
    if not real_robot_adapter or not real_robot_adapter.is_connected:
        return {
            "success": False,
            "connected": False,
            "message": "Not connected",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        status = await real_robot_adapter.get_status()
        return {
            "success": True,
            "connected": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_command(command: Dict[str, str]):
    """执行命令"""
    if not real_robot_adapter or not real_robot_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to real robot")
    
    cmd = command.get("command", "")
    background = command.get("background", False)
    
    if not cmd:
        raise HTTPException(status_code=400, detail="Command is required")
    
    try:
        result = await real_robot_adapter.execute_command(cmd, background)
        
        # 记录命令执行
        logger.log_command(cmd, result.get("success", False), result)
        
        return {
            "success": result.get("success", False),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-test")


async def run_test(test_config: Dict[str, Any], background_tasks: BackgroundTasks):
    """运行测试"""
    if not real_robot_adapter or not real_robot_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to real robot")
    
    test_id = test_config.get("test_id", f"test_{int(datetime.now().timestamp())}")
    test_name = test_config.get("test_name", "unknown_test")
    
    async def run_test_task():
        try:
            result = await real_robot_adapter.execute_test(test_config)
            
            # 保存测试结果
            data_storage.save_test_result(result)
            
            # 记录测试完成
            logger.log_test(test_id, test_name, "real_robot", result)
            
        except Exception as e:
            logger.error(f"Test execution error: {e}")
    
    # 在后台运行测试
    background_tasks.add_task(run_test_task)
    
    return {
        "success": True,
        "test_id": test_id,
        "message": f"Test '{test_name}' started",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/test-results/{test_id}")
async def get_test_results(test_id: str):
    """获取测试结果"""
    result = data_storage.get_test_result(test_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Test result not found: {test_id}")
    
    return {
        "success": True,
        "test_id": test_id,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/recent-tests")
async def get_recent_tests(limit: int = 10):
    """获取最近的测试"""
    tests = data_storage.get_all_tests(platform="real_robot", limit=limit)
    
    return {
        "success": True,
        "tests": tests,
        "count": len(tests),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/initialize")
async def initialize_robot():
    """初始化机器人"""
    if not real_robot_adapter or not real_robot_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to real robot")
    
    try:
        # 执行初始化命令序列
        init_commands = [
            "python3 -m Startups.memory_manager",
            "python3 -m Startups.run_dxl",
            "python3 -m Startups.run_bear",
            "python3 -m Play.initialize"
        ]
        
        results = []
        for cmd in init_commands:
            result = await real_robot_adapter.execute_command(cmd)
            results.append(result)
            
            if not result.get("success", False):
                logger.error(f"Initialization failed at command: {cmd}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Initialization failed: {result.get('error', 'Unknown error')}"
                )
        
        logger.info("Robot initialized successfully")
        
        return {
            "success": True,
            "message": "Robot initialized",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))