from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from typing import Any 

from backend.adapters.gazebo_adapter import GazeboAdapter
from backend.utils.logger import gazebo_logger as logger
from backend.data.storage import DataStorage

router = APIRouter()

# 全局适配器实例
gazebo_adapter: Optional[GazeboAdapter] = None
data_storage = DataStorage()

@router.post("/connect")
async def connect():
    """连接Gazebo"""
    global gazebo_adapter
    
    if gazebo_adapter and gazebo_adapter.is_connected:
        return {
            "success": True,
            "message": "Already connected",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        from backend.main import load_platform_config
        config = load_platform_config().get("gazebo", {})
        
        if not config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Gazebo platform is disabled")
        
        gazebo_adapter = GazeboAdapter(config)
        connected = await gazebo_adapter.connect()
        
        if connected:
            logger.info("Gazebo connected successfully")
            return {
                "success": True,
                "message": "Connected to Gazebo",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("Failed to connect to Gazebo")
            raise HTTPException(status_code=500, detail="Failed to connect to Gazebo")
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect")
async def disconnect():
    """断开连接"""
    global gazebo_adapter
    
    try:
        if gazebo_adapter:
            await gazebo_adapter.disconnect()
            gazebo_adapter = None
            logger.info("Gazebo disconnected")
        
        return {
            "success": True,
            "message": "Disconnected from Gazebo",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Disconnection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """获取Gazebo状态"""
    if not gazebo_adapter or not gazebo_adapter.is_connected:
        return {
            "success": False,
            "connected": False,
            "message": "Not connected",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        status = await gazebo_adapter.get_status()
        return {
            "success": True,
            "connected": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_gazebo():
    """启动Gazebo仿真"""
    if not gazebo_adapter:
        raise HTTPException(status_code=400, detail="Gazebo adapter not initialized")
    
    try:
        result = await gazebo_adapter.start_gazebo()
        
        return {
            "success": result.get("success", False),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start Gazebo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_command(command: Dict[str, str]):
    """执行命令"""
    if not gazebo_adapter or not gazebo_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Gazebo")
    
    cmd = command.get("command", "")
    background = command.get("background", False)
    
    if not cmd:
        raise HTTPException(status_code=400, detail="Command is required")
    
    try:
        result = await gazebo_adapter.execute_command(cmd, background)
        
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
    if not gazebo_adapter or not gazebo_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Gazebo")
    
    test_id = test_config.get("test_id", f"test_{int(datetime.now().timestamp())}")
    test_name = test_config.get("test_name", "unknown_test")
    
    async def run_test_task():
        try:
            result = await gazebo_adapter.execute_test(test_config)
            
            # 保存测试结果
            data_storage.save_test_result(result)
            
            # 记录测试完成
            logger.log_test(test_id, test_name, "gazebo", result)
            
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
    tests = data_storage.get_all_tests(platform="gazebo", limit=limit)
    
    return {
        "success": True,
        "tests": tests,
        "count": len(tests),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/initialize")
async def initialize_simulation():
    """初始化仿真"""
    if not gazebo_adapter or not gazebo_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Gazebo")
    
    try:
        # 启动Gazebo
        start_result = await gazebo_adapter.start_gazebo()
        
        if not start_result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start Gazebo: {start_result.get('error', 'Unknown error')}"
            )
        
        # 等待Gazebo启动
        await asyncio.sleep(5)
        
        # 执行初始化命令序列
        init_commands = [
            "python3 -m Startups.memory_manager",
            "python3 -m Startups.run_simulation",
            "python3 -m Startups.run_estimation"
        ]
        
        results = [start_result]
        for cmd in init_commands:
            result = await gazebo_adapter.execute_command(cmd)
            results.append(result)
            
            if not result.get("success", False):
                logger.error(f"Initialization failed at command: {cmd}")
                # 继续执行，但不抛出异常
        
        logger.info("Gazebo simulation initialized")
        
        return {
            "success": True,
            "message": "Gazebo simulation initialized",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))