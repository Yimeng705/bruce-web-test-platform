import paramiko
import asyncio
from typing import Dict, List, Optional
import json
import yaml
from datetime import datetime
from ..commands.ssh_executor import SSHExecutor
from .base import PlatformAdapter

class RealRobotAdapter(PlatformAdapter):
    """实机机器人适配器 - 通过SSH连接"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "BRUCE实机"
        self.ssh_client = None
        self.executor = None
        self.current_processes = {}
        
    async def connect(self) -> bool:
        """通过SSH连接到实机"""
        try:
            connection_config = self.config['connection']
            
            # 创建SSH客户端
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接
            self.ssh_client.connect(
                hostname=connection_config['host'],
                port=connection_config.get('port', 22),
                username=connection_config['host'].split('@')[0] if '@' in connection_config['host'] else 'khadas',
                password=connection_config.get('password', 'khadas'),
                timeout=10
            )
            
            # 初始化命令执行器
            self.executor = SSHExecutor(self.ssh_client, self.config['paths']['bruce_home'])
            
            # 测试连接
            stdin, stdout, stderr = self.ssh_client.exec_command('echo "Connection test"')
            if stdout.channel.recv_exit_status() == 0:
                self.is_connected = True
                self.last_update = datetime.now()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"SSH连接失败: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """断开SSH连接"""
        if self.ssh_client:
            self.ssh_client.close()
        self.is_connected = False
        self.last_update = datetime.now()
    
    async def execute_command(self, command: str, background: bool = False) -> dict:
        """执行命令"""
        if not self.is_connected or not self.executor:
            return {"error": "未连接到机器人", "success": False}
        
        try:
            if background:
                # 后台执行（返回进程ID）
                process_id = await self.executor.execute_background(command)
                self.current_processes[process_id] = command
                return {
                    "success": True,
                    "process_id": process_id,
                    "command": command
                }
            else:
                # 同步执行
                result = await self.executor.execute(command)
                self.last_update = datetime.now()
                return result
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_status(self) -> dict:
        """获取机器人状态"""
        if not self.is_connected:
            return {"status": "disconnected"}
        
        try:
            # 检查关键进程是否运行
            status_checks = {
                "memory_manager": self._check_process_running("memory_manager"),
                "dxl_motors": self._check_process_running("run_dxl"),
                "bear_actuators": self._check_process_running("run_bear"),
                "estimation": self._check_process_running("run_estimation"),
            }
            
            # 获取系统信息
            system_info = await self._get_system_info()
            
            return {
                "status": "connected",
                "processes": status_checks,
                "system": system_info,
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
    
    async def _get_system_info(self) -> dict:
        """获取系统信息"""
        if not self.executor:
            return {}
        
        try:
            commands = {
                "uptime": "uptime -p",
                "memory": "free -h | grep Mem",
                "cpu": "top -bn1 | grep 'Cpu(s)'",
                "disk": "df -h / | tail -1"
            }
            
            info = {}
            for key, cmd in commands.items():
                result = await self.executor.execute(cmd)
                if result["success"]:
                    info[key] = result["stdout"].strip()
            
            return info
        except:
            return {}
    
    async def execute_test(self, test_config: dict) -> dict:
        """执行测试用例"""
        test_id = test_config.get("test_id", "unnamed_test")
        
        # 加载测试配置
        with open("config/tests.yaml") as f:
            all_tests = yaml.safe_load(f)["test_cases"]
        
        test_name = test_config.get("test_name")
        if test_name not in all_tests:
            return {"error": f"未找到测试用例: {test_name}", "success": False}
        
        test_spec = all_tests[test_name]
        results = []
        
        # 执行测试步骤
        for step in test_spec.get("steps", []):
            step_result = await self._execute_test_step(step)
            results.append(step_result)
            
            if not step_result.get("success", False):
                # 如果步骤失败，停止测试
                break
        
        # 收集数据
        data_collection = test_spec.get("data_collection", {})
        if data_collection:
            collected_data = await self._collect_data(data_collection)
            results.append({
                "step": "data_collection",
                "data": collected_data
            })
        
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
    
    async def _collect_data(self, config: dict) -> dict:
        """收集数据"""
        # 这里实现数据收集逻辑
        # 可以从共享内存、日志文件等收集数据
        return {"status": "data_collection_not_implemented"}
    
    def _analyze_results(self, results: List[dict]) -> dict:
        """分析测试结果"""
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r.get("success", False))
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0
        }