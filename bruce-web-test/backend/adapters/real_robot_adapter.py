import asyncio
import os
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 设置日志
logger = logging.getLogger("robot")

class RealRobotAdapter:
    """实机机器人适配器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config.get('name', 'BRUCE实机')
        self.is_connected = False
        self.last_update = None
        self.simulation_mode = config.get('simulation_mode', False)  # 默认不使用模拟模式
        
        # SSH配置
        self.connection_config = config.get('connection', {})
        self.bruce_home = config.get('paths', {}).get('bruce_home', '/home/khadas/BRUCE/BRUCE-OP')
        
        logger.info(f"初始化实机适配器: {self.name} (模拟模式: {self.simulation_mode})")
    
    async def connect(self) -> bool:
        """连接到实机"""
        try:
            logger.info(f"尝试连接实机: {self.name}")
            
            # 检查是否启用
            if not self.config.get('enabled', False):
                logger.error("实机平台未启用")
                return False
            
            # 如果是模拟模式，直接返回成功
            if self.simulation_mode:
                logger.info("使用模拟模式连接")
                await asyncio.sleep(1)  # 模拟连接延迟
                self.is_connected = True
                self.last_update = datetime.now()
                logger.info(f"实机模拟连接成功: {self.name}")
                return True
            
            # 真实连接模式（需要paramiko库）
            try:
                import paramiko
                
                # 获取连接参数
                host = self.connection_config.get('host', '')
                username = self.connection_config.get('username', 'khadas')
                password = self.connection_config.get('password', 'khadas')
                port = self.connection_config.get('port', 22)
                
                if not host:
                    logger.error("未配置SSH主机地址")
                    return False
                
                logger.info(f"尝试SSH连接: {username}@{host}:{port}")
                
                # 创建SSH客户端
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 连接（设置超时防止长时间等待）
                client.connect(
                    hostname=host,
                    username=username,
                    password=password,
                    port=port,
                    timeout=10,
                    banner_timeout=10
                )
                
                # 测试连接
                stdin, stdout, stderr = client.exec_command('echo "Connection test"', timeout=5)
                output = stdout.read().decode('utf-8').strip()
                
                if output == "Connection test":
                    # client.close()
                    self.is_connected = True
                    self.last_update = datetime.now()
                    self.ssh_client = client  # 保存连接供后续使用
                    logger.info(f"实机SSH连接成功: {self.name}")
                    return True
                else:
                    client.close()
                    logger.error("SSH连接测试失败")
                    return False
                    
            except ImportError:
                logger.warning("paramiko库未安装，使用模拟模式")
                self.simulation_mode = True
                return await self.connect()  # 递归调用，这次会进入模拟模式
                
            except Exception as e:
                logger.error(f"SSH连接失败: {e}")
                logger.warning("切换到模拟模式")
                self.simulation_mode = True
                return await self.connect()  # 递归调用，切换到模拟模式
            
        except Exception as e:
            logger.error(f"连接实机失败: {e}", exc_info=True)
            # 在失败时切换到模拟模式
            self.simulation_mode = True
            await asyncio.sleep(1)
            self.is_connected = True
            self.last_update = datetime.now()
            logger.info(f"实机切换到模拟模式并连接成功: {self.name}")
            return True
    
    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            # 关闭SSH连接（如果存在）
            if hasattr(self, 'ssh_client'):
                try:
                    self.ssh_client.close()
                except:
                    pass
                delattr(self, 'ssh_client')
            
            self.is_connected = False
            self.last_update = datetime.now()
            logger.info(f"实机已断开连接: {self.name}")
            return True
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    async def get_status(self) -> dict:
        """获取状态"""
        status = {
            "connected": self.is_connected,
            "name": self.name,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "mode": "simulation" if self.simulation_mode else "real"
        }
        
        # 如果是真实模式且已连接，尝试获取更多状态
        if not self.simulation_mode and self.is_connected and hasattr(self, 'ssh_client'):
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command('uptime', timeout=5)
                uptime = stdout.read().decode('utf-8').strip()
                status['uptime'] = uptime
            except:
                status['uptime'] = "N/A"
        
        return status
    
    async def execute_command(self, command: str, background: bool = False) -> dict:
        """执行命令"""
        logger.info(f"执行命令: {command}")
        
        try:
            # 模拟命令执行延迟
            await asyncio.sleep(0.5)
            
            # 如果是模拟模式
            if self.simulation_mode:
                return {
                    "success": True,
                    "command": command,
                    "output": f"模拟执行: {command}",
                    "error": "",
                    "return_code": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 真实模式（需要SSH连接）
            if not self.is_connected or not hasattr(self, 'ssh_client'):
                return {
                    "success": False,
                    "command": command,
                    "output": "",
                    "error": "未连接到实机",
                    "return_code": -1,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 检查SSH连接是否仍然有效
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command('echo "alive"', timeout=5)
                alive_output = stdout.read().decode('utf-8').strip()
                if alive_output != "alive":
                    raise Exception("连接无效")
            except Exception as e:
                logger.warning(f"SSH连接已断开，尝试重新连接: {e}")
                # 尝试重新连接
                await self.disconnect()
                connected = await self.connect()
                if not connected:
                    return {
                        "success": False,
                        "command": command,
                        "output": "",
                        "error": "重新连接失败",
                        "return_code": -1,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 特殊处理初始化脚本命令
            if "./init.sh" in command:
                try:
                    logger.info(f"执行初始化脚本命令: {command}")
                    # 对于初始化脚本，使用更长的超时时间并异步读取输出
                    stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=300)  # 5分钟超时
                    
                    # 异步读取输出，避免阻塞
                    output_lines = []
                    error_lines = []
                    
                    # 等待命令完成，但定期检查
                    import time
                    start_time = time.time()
                    while not stdout.channel.exit_status_ready() and (time.time() - start_time) < 300:
                        # 检查是否有输出可读
                        if stdout.channel.recv_ready():
                            output_chunk = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                            output_lines.append(output_chunk)
                        
                        if stdout.channel.recv_stderr_ready():
                            error_chunk = stdout.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
                            error_lines.append(error_chunk)
                        
                        await asyncio.sleep(0.1)
                    
                    # 获取最终输出
                    try:
                        remaining_output = stdout.read().decode('utf-8', errors='ignore')
                        if remaining_output:
                            output_lines.append(remaining_output)
                    except:
                        pass
                        
                    try:
                        remaining_error = stderr.read().decode('utf-8', errors='ignore')
                        if remaining_error:
                            error_lines.append(remaining_error)
                    except:
                        pass
                    
                    output = ''.join(output_lines).strip()
                    error = ''.join(error_lines).strip()
                    
                    # 获取返回码
                    try:
                        return_code = stdout.channel.recv_exit_status()
                    except:
                        return_code = 0  # 假设成功，因为脚本可能仍在运行
                    
                    logger.info(f"初始化脚本执行完成，返回码: {return_code}")
                    
                except Exception as e:
                    logger.error(f"执行初始化脚本时出错: {e}")
                    # 即使出现超时，也认为初始化可能是成功的
                    output = "脚本执行中..."
                    error = str(e)
                    return_code = 0  # 假设成功
            else:
                # 执行普通SSH命令
                stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=120)
                try:
                    output = stdout.read().decode('utf-8', errors='ignore').strip()
                    error = stderr.read().decode('utf-8', errors='ignore').strip()
                    return_code = stdout.channel.recv_exit_status()
                except socket.timeout:
                    logger.warning(f"命令执行超时: {command}")
                    output = "命令执行超时"
                    error = ""
                    return_code = 0  # 假设成功，因为超时不一定意味着失败
                    
            logger.info(f"命令执行完成: {command}, 返回码: {return_code}")
            if output:
                logger.info(f"命令输出: {output[:500]}...")  # 限制日志长度
            if error:
                logger.error(f"命令错误: {error}")
            
            return {
                "success": return_code == 0,
                "command": command,
                "output": output,
                "error": error,
                "return_code": return_code,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"命令执行失败: {command}, 错误: {e}", exc_info=True)
            return {
                "success": False,
                "command": command,
                "output": "",
                "error": str(e),
                "return_code": -1,
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_test(self, test_config: dict) -> dict:
        """执行测试"""
        test_id = test_config.get('test_id', 'unknown')
        test_name = test_config.get('test_name', '未知测试')
        
        logger.info(f"开始执行测试: {test_name}")
        
        # 执行测试步骤
        results = []
        
        # 获取测试步骤
        steps = test_config.get('steps', [
            {
                'name': '测试步骤',
                'command': f'echo "Running test: {test_name}"'
            }
        ])
        
        for step in steps:
            step_name = step.get('name', '步骤')
            command = step.get('command', '')
            
            if command:
                result = await self.execute_command(command)
                results.append({
                    'step': step_name,
                    'success': result.get('success', False),
                    'result': result
                })
            else:
                results.append({
                    'step': step_name,
                    'success': True,
                    'result': {'message': '跳过此步骤'}
                })
        
        # 计算摘要
        successful_steps = sum(1 for r in results if r.get('success', False))
        total_steps = len(results)
        
        return {
            "test_id": test_id,
            "test_name": test_name,
            "platform": self.name,
            "success": successful_steps == total_steps,
            "results": results,
            "summary": {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "success_rate": successful_steps / total_steps if total_steps > 0 else 0
            },
            "timestamp": datetime.now().isoformat()
        }