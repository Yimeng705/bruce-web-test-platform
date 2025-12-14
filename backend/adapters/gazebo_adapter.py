import subprocess
import asyncio
from typing import Dict, List
import yaml
from datetime import datetime
from ..commands.local_executor import LocalExecutor
from .base import PlatformAdapter

class GazeboAdapter(PlatformAdapter):
    """Gazebo仿真适配器 - 本地运行"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Gazebo仿真"
        self.executor = None
        self.gazebo_process = None
        
    async def connect(self) -> bool:
        """连接到Gazebo仿真"""
        try:
            # 初始化本地命令执行器
            bruce_home = self.config['paths'].get('bruce_home', './BRUCE-OP')
            self.executor = LocalExecutor(bruce_home)
            
            # 检查Gazebo是否可用
            result = await self.executor.execute("which gazebo")
            if result["return_code"] != 0:
                print("❌ Gazebo未安装")
                return False
            
            self.is_connected = True
            self.last_update = datetime.now()
            return True
            
        except Exception as e:
            print(f"Gazebo适配器初始化失败: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.gazebo_process:
            self.gazebo_process.terminate()
            try:
                self.gazebo_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.gazebo_process.kill()
        
        self.is_connected = False
        self.last_update = datetime.now()
    
    async def start_gazebo(self) -> dict:
        """启动Gazebo仿真"""
        try:
            # 修改配置文件为仿真模式
            config_path = f"{self.config['paths']['bruce_home']}/Play/config.py"
            config_content = f"""
SIMULATION = True  # if in simulation or not
GAMEPAD = False    # if using gamepad or not
"""
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            # 启动Gazebo
            gazebo_script = self.config['paths'].get('gazebo_script', 'Simulation/launch_gazebo.sh')
            self.gazebo_process = subprocess.Popen(
                [gazebo_script],
                cwd=self.config['paths']['bruce_home'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待Gazebo启动
            await asyncio.sleep(5)
            
            # 检查是否启动成功
            if self.gazebo_process.poll() is None:
                return {
                    "success": True,
                    "pid": self.gazebo_process.pid,
                    "message": "Gazebo已启动"
                }
            else:
                return {
                    "success": False,
                    "error": "Gazebo启动失败"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_command(self, command: str, background: bool = False) -> dict:
        """执行命令"""
        if not self.executor:
            return {"error": "执行器未初始化", "success": False}
        
        try:
            if background:
                # 后台执行
                result = await self.executor.execute_background(command)
                return {
                    "success": True,
                    "process_id": result.get("process_id"),
                    "command": command,
                    "output": result.get("output", "")
                }
            else:
                # 同步执行
                result = await self.executor.execute(command)
                self.last_update = datetime.now()
                return result
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_status(self) -> dict:
        """获取Gazebo状态"""
        if not self.is_connected:
            return {"status": "disconnected"}
        
        try:
            # 检查Gazebo进程
            gazebo_running = False
            gazebo_pid = None
            
            if self.gazebo_process and self.gazebo_process.poll() is None:
                gazebo_running = True
                gazebo_pid = self.gazebo_process.pid
            
            # 检查仿真相关进程
            processes = {
                "gazebo": gazebo_running,
                "memory_manager": await self._check_process_running("memory_manager"),
                "run_simulation": await self._check_process_running("run_simulation"),
                "run_estimation": await self._check_process_running("run_estimation"),
            }
            
            return {
                "status": "connected",
                "processes": processes,
                "gazebo_pid": gazebo_pid,
                "connected_since": self.last_update.isoformat() if self.last_update else None
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _check_process_running(self, process_name: str) -> bool:
        """检查进程是否运行"""
        if not self.executor:
            return False
        
        try:
            # 使用pgrep检查进程
            result = await self.executor.execute(f"pgrep -f {process_name}")
            return result["return_code"] == 0 and result["stdout"].strip() != ""
        except:
            return False
    
    async def execute_test(self, test_config: dict) -> dict:
        """执行测试用例"""
        # 与RealRobotAdapter类似的实现，但针对Gazebo
        test_id = test_config.get("test_id", "unnamed_test")
        
        with open("config/tests.yaml") as f:
            all_tests = yaml.safe_load(f)["test_cases"]
        
        test_name = test_config.get("test_name")
        if test_name not in all_tests:
            return {"error": f"未找到测试用例: {test_name}", "success": False}
        
        test_spec = all_tests[test_name]
        
        # 确保Gazebo已启动
        if test_name not in ["compile_check"]:
            status = await self.get_status()
            if not status.get("processes", {}).get("gazebo", False):
                await self.start_gazebo()
                await asyncio.sleep(3)
        
        # 执行测试步骤
        results = []
        for step in test_spec.get("steps", []):
            step_result = await self._execute_test_step(step)
            results.append(step_result)
            
            if not step_result.get("success", False):
                break
        
        return {
            "test_id": test_id,
            "test_name": test_name,
            "platform": self.name,
            "results": results,
            "summary": self._analyze_results(results)
        }
    
    async def _execute_test_step(self, step: dict) -> dict:
        """执行单个测试步骤"""
        step_name = step.get("name", "unnamed_step")
        commands = step.get("commands", [])
        
        step_results = []
        for cmd in commands:
            result = await self.execute_command(cmd)
            step_results.append(result)
            
            if not result.get("success", False):
                return {
                    "step": step_name,
                    "success": False,
                    "error": result.get("error"),
                    "results": step_results
                }
        
        return {
            "step": step_name,
            "success": True,
            "results": step_results
        }
    
    def _analyze_results(self, results: List[dict]) -> dict:
        """分析测试结果"""
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r.get("success", False))
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0
        }