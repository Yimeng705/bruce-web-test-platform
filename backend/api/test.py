from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
import asyncio
import yaml
from datetime import datetime
from typing import Any

from backend.utils.logger import test_logger as logger
from backend.data.storage import DataStorage
from backend.data.processor import DataProcessor

router = APIRouter()
data_storage = DataStorage()

@router.get("/test-cases")
async def get_test_cases():
    """获取所有测试用例"""
    try:
        with open("config/tests.yaml", "r", encoding="utf-8") as f:
            tests = yaml.safe_load(f)
        
        test_cases = tests.get("test_cases", {})
        
        return {
            "success": True,
            "test_cases": test_cases,
            "count": len(test_cases),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to load test cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-cases/{test_name}")
async def get_test_case(test_name: str):
    """获取特定测试用例"""
    try:
        with open("config/tests.yaml", "r", encoding="utf-8") as f:
            tests = yaml.safe_load(f)
        
        test_cases = tests.get("test_cases", {})
        
        if test_name not in test_cases:
            raise HTTPException(status_code=404, detail=f"Test case not found: {test_name}")
        
        return {
            "success": True,
            "test_name": test_name,
            "test_case": test_cases[test_name],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to load test case: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_test(test_config: Dict[str, Any], background_tasks: BackgroundTasks):
    """执行测试"""
    test_name = test_config.get("test_name")
    platforms = test_config.get("platforms", [])
    
    if not test_name:
        raise HTTPException(status_code=400, detail="Test name is required")
    
    if not platforms:
        raise HTTPException(status_code=400, detail="At least one platform is required")
    
    try:
        # 加载测试配置
        with open("config/tests.yaml", "r", encoding="utf-8") as f:
            tests = yaml.safe_load(f)
        
        test_cases = tests.get("test_cases", {})
        
        if test_name not in test_cases:
            raise HTTPException(status_code=404, detail=f"Test case not found: {test_name}")
        
        test_spec = test_cases[test_name]
        test_id = test_config.get("test_id", f"{test_name}_{int(datetime.now().timestamp())}")
        
        # 创建测试配置
        full_test_config = {
            "test_id": test_id,
            "test_name": test_name,
            **test_spec,
            "platforms": platforms
        }
        
        async def run_test_on_platforms():
            """在多个平台上运行测试"""
            results = {}
            
            for platform in platforms:
                try:
                    if platform == "real_robot":
                        from backend.api.real_robot import real_robot_adapter
                        if real_robot_adapter and real_robot_adapter.is_connected:
                            platform_result = await real_robot_adapter.execute_test(full_test_config)
                            results["real_robot"] = platform_result
                        else:
                            results["real_robot"] = {
                                "error": "Real robot not connected",
                                "success": False
                            }
                    
                    elif platform == "gazebo":
                        from backend.api.gazebo import gazebo_adapter
                        if gazebo_adapter and gazebo_adapter.is_connected:
                            platform_result = await gazebo_adapter.execute_test(full_test_config)
                            results["gazebo"] = platform_result
                        else:
                            results["gazebo"] = {
                                "error": "Gazebo not connected",
                                "success": False
                            }
                    
                    else:
                        results[platform] = {
                            "error": f"Unknown platform: {platform}",
                            "success": False
                        }
                        
                except Exception as e:
                    logger.error(f"Test execution error on {platform}: {e}")
                    results[platform] = {
                        "error": str(e),
                        "success": False
                    }
            
            # 分析结果
            analysis = {}
            if "real_robot" in results and "gazebo" in results:
                real_result = results.get("real_robot", {})
                gazebo_result = results.get("gazebo", {})
                
                if not real_result.get("error") and not gazebo_result.get("error"):
                    comparison = DataProcessor.compare_results(real_result, gazebo_result)
                    analysis["comparison"] = comparison
            
            # 保存总体结果
            overall_result = {
                "test_id": test_id,
                "test_name": test_name,
                "platforms": platforms,
                "results": results,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            data_storage.save_test_result(overall_result)
            logger.log_test(test_id, test_name, "multiple", overall_result)
        
        # 在后台运行测试
        background_tasks.add_task(run_test_on_platforms)
        
        return {
            "success": True,
            "test_id": test_id,
            "test_name": test_name,
            "platforms": platforms,
            "message": f"Test '{test_name}' started on platforms: {platforms}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to execute test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{test_id}")
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

@router.get("/all-results")
async def get_all_results(limit: int = 50):
    """获取所有测试结果"""
    tests = data_storage.get_all_tests(limit=limit)
    
    return {
        "success": True,
        "tests": tests,
        "count": len(tests),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/comparison/{test_id}")
async def get_comparison(test_id: str):
    """获取测试对比结果"""
    result = data_storage.get_test_result(test_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Test result not found: {test_id}")
    
    results = result.get("results", {})
    real_result = results.get("real_robot", {})
    gazebo_result = results.get("gazebo", {})
    
    if not real_result or not gazebo_result:
        raise HTTPException(
            status_code=400,
            detail="Both real robot and Gazebo results are required for comparison"
        )
    
    comparison = DataProcessor.compare_results(real_result, gazebo_result)
    
    return {
        "success": True,
        "test_id": test_id,
        "comparison": comparison,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/compile")
async def compile_all(background_tasks: BackgroundTasks):
    """编译所有平台"""
    
    async def compile_platforms():
        """在多个平台上执行编译"""
        results = {}
        
        # 实机编译
        from backend.api.real_robot import real_robot_adapter
        if real_robot_adapter and real_robot_adapter.is_connected:
            try:
                compile_commands = [
                    "python3 -m Library.ROBOT_MODEL.BRUCE_DYNAMICS_AOT",
                    "python3 -m Library.ROBOT_MODEL.BRUCE_KINEMATICS_AOT",
                    "python3 -m Library.STATE_ESTIMATION.BRUCE_ESTIMATION_AOT"
                ]
                
                compile_results = []
                for cmd in compile_commands:
                    result = await real_robot_adapter.execute_command(cmd)
                    compile_results.append(result)
                
                results["real_robot"] = {
                    "success": all(r.get("success", False) for r in compile_results),
                    "results": compile_results
                }
            except Exception as e:
                results["real_robot"] = {
                    "error": str(e),
                    "success": False
                }
        
        # Gazebo编译
        from backend.api.gazebo import gazebo_adapter
        if gazebo_adapter and gazebo_adapter.is_connected:
            try:
                compile_commands = [
                    "python3 -m Library.ROBOT_MODEL.BRUCE_DYNAMICS_AOT",
                    "python3 -m Library.ROBOT_MODEL.BRUCE_KINEMATICS_AOT",
                    "python3 -m Library.STATE_ESTIMATION.BRUCE_ESTIMATION_AOT"
                ]
                
                compile_results = []
                for cmd in compile_commands:
                    result = await gazebo_adapter.execute_command(cmd)
                    compile_results.append(result)
                
                results["gazebo"] = {
                    "success": all(r.get("success", False) for r in compile_results),
                    "results": compile_results
                }
            except Exception as e:
                results["gazebo"] = {
                    "error": str(e),
                    "success": False
                }
        
        # 保存编译结果
        compile_result = {
            "test_id": f"compile_{int(datetime.now().timestamp())}",
            "test_name": "compile_all",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        data_storage.save_test_result(compile_result)
        logger.info("Compilation completed", results=results)
    
    # 在后台运行编译
    background_tasks.add_task(compile_platforms)
    
    return {
        "success": True,
        "message": "Compilation started on all platforms",
        "timestamp": datetime.now().isoformat()
    }