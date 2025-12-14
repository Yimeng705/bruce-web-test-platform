import asyncio
import subprocess
import os
from datetime import datetime
from typing import Dict, Optional

class LocalExecutor:
    """本地命令执行器"""
    
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()
        self.active_processes = {}
        
    async def execute(self, command: str, timeout: int = 30) -> Dict:
        """执行命令并返回结果"""
        try:
            # 构建完整命令
            if self.working_dir:
                full_command = f"cd {self.working_dir} && {command}"
            else:
                full_command = command
            
            # 执行命令
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            # 等待命令完成或超时
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    'success': process.returncode == 0,
                    'return_code': process.returncode,
                    'stdout': stdout.decode('utf-8', errors='ignore').strip(),
                    'stderr': stderr.decode('utf-8', errors='ignore').strip(),
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    'success': False,
                    'error': f'Command timed out after {timeout} seconds',
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'timestamp': datetime.now().isoformat()
            }
    
    async def execute_background(self, command: str) -> Dict:
        """在后台执行命令"""
        try:
            if self.working_dir:
                full_command = f"cd {self.working_dir} && nohup {command} > /dev/null 2>&1 & echo $!"
            else:
                full_command = f"nohup {command} > /dev/null 2>&1 & echo $!"
            
            # 执行命令获取进程ID
            result = await self.execute(full_command)
            
            if result['success'] and result['stdout'].isdigit():
                pid = int(result['stdout'])
                self.active_processes[pid] = command
                
                return {
                    'success': True,
                    'pid': pid,
                    'command': command,
                    'process_id': str(pid)
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get process ID',
                    'command': command
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command
            }
    
    async def stop_process(self, pid: int) -> bool:
        """停止后台进程"""
        if pid in self.active_processes:
            try:
                kill_command = f"kill -9 {pid}"
                await self.execute(kill_command)
                del self.active_processes[pid]
                return True
            except:
                return False
        return False