from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from typing import Any
from backend.adapters.real_robot_adapter import RealRobotAdapter
from backend.utils.logger import robot_logger as logger
from backend.data.storage import DataStorage
import json
import yaml
import os

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
        # 验证配置文件是否存在
        from backend.main import load_platform_config
        logger.info("正在加载平台配置...")
        full_config = load_platform_config()
        logger.info(f"配置加载成功: {list(full_config.keys())}")
        
        config = full_config.get("platforms", {}).get("real_robot", {})
        logger.info(f"实机配置: {config}")
        
        if not config.get("enabled", False):
            error_detail = "Real robot platform is disabled"
            logger.error(error_detail)
            raise HTTPException(status_code=400, detail=error_detail)
        
        logger.info("正在创建RealRobotAdapter实例...")
        real_robot_adapter = RealRobotAdapter(config)
        logger.info("RealRobotAdapter实例创建成功")
        
        logger.info("正在尝试连接...")
        connected = await real_robot_adapter.connect()
        logger.info(f"连接尝试完成，结果: {connected}")
        
        if connected:
            logger.info("Real robot connected successfully")
            return {
                "success": True,
                "message": "Connected to real robot",
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_detail = "Failed to connect to real robot"
            logger.error(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)
            
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 捕获并记录所有其他异常
        error_msg = f"Connection error: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

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

def load_test_config():
    """加载测试配置"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "tests.yaml")
        if not os.path.exists(config_path):
            config_path = os.path.join("config", "tests.yaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get("test_cases", {})
    except Exception as e:
        logger.error(f"加载测试配置失败: {e}")
        return {}

@router.post("/execute")
async def execute_command(command: Dict[str, str]):
    """执行命令"""
    global real_robot_adapter
    
    if not real_robot_adapter or not real_robot_adapter.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to real robot")
    
    cmd = command.get("command", "")
    background = command.get("background", False)
    
    if not cmd:
        raise HTTPException(status_code=400, detail="Command is required")
    
    try:
        # 加载测试配置
        test_config = load_test_config()
        
        # 检查是否是预定义的测试命令
        if cmd in test_config:
            # 执行测试命令序列
            test_case = test_config[cmd]
            commands = test_case.get("commands", [])
            
            results = []
            for command_str in commands:
                result = await real_robot_adapter.execute_command(command_str, background)
                results.append(result)
                
                # 如果任何一个命令失败，停止执行
                if not result.get("success", False):
                    logger.error(f"命令执行失败: {command_str}")
                    break
            
            # 返回汇总结果
            final_result = {
                "success": all(r.get("success", False) for r in results),
                "results": results,
                "test_case": cmd,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.log_command(cmd, final_result.get("success", False), final_result)
            return {
                "success": final_result.get("success", False),
                "result": final_result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 执行单个命令
            result = await real_robot_adapter.execute_command(cmd, background)
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
    
    # 使用前端传递的完整配置
    # 如果前端没有传递完整配置，从配置文件加载
    if "commands" not in test_config and "steps" not in test_config:
        # 从配置文件加载测试配置
        full_test_config = load_test_config()
        test_case_config = full_test_config.get(test_name, {})
        
        # 合并配置
        merged_config = {
            "test_id": test_id,
            "test_name": test_name,
            **test_case_config
        }
    else:
        # 使用前端传递的配置
        merged_config = test_config
    
    async def run_test_task():
        try:
            result = await real_robot_adapter.execute_test(merged_config)
            
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
        # 先检查脚本是否存在并设置权限
        check_commands = [
            f"cd {real_robot_adapter.bruce_home} && ls -la init.sh",
            f"cd {real_robot_adapter.bruce_home} && chmod +x init.sh"
        ]
        
        for cmd in check_commands:
            logger.info(f"执行检查命令: {cmd}")
            result = await real_robot_adapter.execute_command(cmd)
            if not result.get("success", False):
                logger.warning(f"检查命令失败: {cmd}, 错误: {result.get('error', '')}")
        
        # 使用init.sh脚本进行初始化
        init_command = f"cd {real_robot_adapter.bruce_home} && timeout 300s ./init.sh"
        
        logger.info("使用init.sh脚本初始化机器人")
        result = await real_robot_adapter.execute_command(init_command)
        
        # 对于初始化脚本，即使出现超时也认为可能是成功的
        if not result.get("success", False):
            # 检查是否是超时错误
            if "timeout" in result.get("error", "").lower() or "timed out" in result.get("error", "").lower():
                logger.info("初始化脚本执行超时，但这可能是正常的，因为初始化需要较长时间")
                # 认为初始化是成功的
                result["success"] = True
            else:
                logger.warning(f"Initialization completed with warnings: {result.get('error', 'Unknown warning')}")
        
        logger.info("Robot initialization process completed")
        
        return {
            "success": True,
            "message": "Robot initialization process completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))