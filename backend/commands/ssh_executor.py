import paramiko
import asyncio
from typing import Dict, Optional
from datetime import datetime

class SSHExecutor:
    """SSH命令执行器"""
    
    def __init__(self, ssh_client: paramiko.SSHClient, working_dir: str):
        self.ssh_client = ssh_client
        self.working_dir = working_dir
        self.process_counter = 0
        self.active_processes = {}
        
    async def execute(self, command: str, timeout: int = 30) -> Dict:
        """执行命令并返回结果"""
        full_command = f"cd {self.working_dir} && {command}"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(full_command)
            
            # 等待命令完成
            start_time = datetime.now()
            while not stdout.channel.exit_status_ready():
                await asyncio.sleep(0.1)
                if (datetime.now() - start_time).seconds > timeout:
                    stdout.channel.close()
                    return {
                        "success": False,
                        "error": f"命令执行超时: {command}",
                        "return_code": -1,
                        "stdout": "",
                        "stderr": ""
                    }
            
            # 获取输出
            return_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8', errors='ignore')
            stderr_text = stderr.read().decode('utf-8', errors='ignore')
            
            return {
                "success": return_code == 0,
                "return_code": return_code,
                "stdout": stdout_text.strip(),
                "stderr": stderr_text.strip(),
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "return_code": -1,
                "stdout": "",
                "stderr": ""
            }
    
    async def execute_background(self, command: str) -> Dict:
        """在后台执行命令"""
        full_command = f"cd {self.working_dir} && nohup {command} > /dev/null 2>&1 & echo $!"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(full_command)
            pid = stdout.read().decode('utf-8').strip()
            
            if pid.isdigit():
                self.process_counter += 1
                process_id = f"ssh_{self.process_counter}"
                self.active_processes[process_id] = int(pid)
                
                return {
                    "success": True,
                    "process_id": process_id,
                    "pid": int(pid),
                    "command": command
                }
            else:
                return {
                    "success": False,
                    "error": "无法获取进程ID",
                    "command": command
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def stop_process(self, process_id: str) -> bool:
        """停止后台进程"""
        if process_id in self.active_processes:
            pid = self.active_processes[process_id]
            kill_command = f"kill -9 {pid}"
            result = await self.execute(kill_command)
            
            if result["success"]:
                del self.active_processes[process_id]
                return True
        return False