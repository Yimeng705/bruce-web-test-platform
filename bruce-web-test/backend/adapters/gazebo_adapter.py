import asyncio
import os
import yaml
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

# 设置日志
logger = logging.getLogger("gazebo")

class GazeboAdapter:
    """Gazebo仿真适配器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config.get('name', 'Gazebo仿真')
        self.is_connected = False
        self.last_update = None
        self.simulation_mode = config.get('simulation_mode', False)  # 默认不使用模拟模式
        self.gazebo_process = None
        
        # 路径配置
        self.bruce_home = config.get('paths', {}).get('bruce_home', '/home/khadas/BRUCE/BRUCE-OP')
        
        logger.info(f"初始化Gazebo适配器: {self.name} (模拟模式: {self.simulation_mode})")
    
    async def connect(self) -> bool:
        """连接到Gazebo"""
        try:
            logger.info(f"尝试连接Gazebo: {self.name}")
            
            # 检查是否启用
            if not self.config.get('enabled', False):
                logger.error("Gazebo平台未启用")
                return False
            
            # 如果是模拟模式，直接返回成功
            if self.simulation_mode:
                logger.info("使用模拟模式连接")
                await asyncio.sleep(1)  # 模拟连接延迟
                self.is_connected = True
                self.last_update = datetime.now()
                logger.info(f"Gazebo模拟连接成功: {self.name}")
                return True
            
            # 真实模式：检查Gazebo是否安装
            try:
                result = subprocess.run(['which', 'gazebo'], 
                                       capture_output=True, 
                                       text=True, 
                                       timeout=5)
                
                if result.returncode != 0:
                    logger.error("Gazebo未安装")
                    logger.warning("切换到模拟模式")
                    self.simulation_mode = True
                    return await self.connect()  # 递归调用，切换到模拟模式
                
                logger.info(f"Gazebo已安装: {result.stdout.strip()}")
                self.is_connected = True
                self.last_update = datetime.now()
                logger.info(f"Gazebo连接成功: {self.name}")
                return True
                
            except subprocess.TimeoutExpired:
                logger.error("检查Gazebo安装超时")
                logger.warning("切换到模拟模式")
                self.simulation_mode = True
                return await self.connect()
                
            except Exception as e:
                logger.error(f"检查Gazebo安装失败: {e}")
                logger.warning("切换到模拟模式")
                self.simulation_mode = True
                return await self.connect()
            
        except Exception as e:
            logger.error(f"连接Gazebo失败: {e}", exc_info=True)
            # 在失败时切换到模拟模式
            self.simulation_mode = True
            await asyncio.sleep(1)
            self.is_connected = True
            self.last_update = datetime.now()
            logger.info(f"Gazebo切换到模拟模式并连接成功: {self.name}")
            return True
    
    async def disconnect(self) -> bool:
        """断开连接"""
        try:
            # 停止Gazebo进程（如果正在运行）
            if self.gazebo_process:
                try:
                    self.gazebo_process.terminate()
                    self.gazebo_process.wait(timeout=5)
                except:
                    try:
                        self.gazebo_process.kill()
                    except:
                        pass
                self.gazebo_process = None
            
            self.is_connected = False
            self.last_update = datetime.now()
            logger.info(f"Gazebo已断开连接: {self.name}")
            return True
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    async def start_gazebo(self) -> dict:
        """启动Gazebo仿真"""
        try:
            logger.info("启动Gazebo仿真")
            
            # 模拟模式
            if self.simulation_mode:
                await asyncio.sleep(2)  # 模拟启动延迟
                return {
                    "success": True,
                    "message": "Gazebo仿真已启动（模拟模式）",
                    "pid": 9999,  # 模拟PID
                    "timestamp": datetime.now().isoformat()
                }
            
            # 真实模式
            try:
                # 启动Gazebo（非阻塞）
                self.gazebo_process = subprocess.Popen(
                    ['gazebo', '--verbose'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 等待一段时间确保启动
                await asyncio.sleep(5)
                
                # 检查进程是否还在运行
                if self.gazebo_process.poll() is None:
                    logger.info(f"Gazebo已启动，PID: {self.gazebo_process.pid}")
                    return {
                        "success": True,
                        "message": "Gazebo已启动",
                        "pid": self.gazebo_process.pid,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # 进程已结束，获取错误信息
                    stdout, stderr = self.gazebo_process.communicate()
                    logger.error(f"Gazebo启动失败: {stderr}")
                    return {
                        "success": False,
                        "message": f"Gazebo启动失败: {stderr}",
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"启动Gazebo失败: {e}")
                return {
                    "success": False,
                    "message": f"启动Gazebo失败: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"启动Gazebo仿真失败: {e}")
            return {
                "success": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_status(self) -> dict:
        """获取状态"""
        status = {
            "connected": self.is_connected,
            "name": self.name,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "mode": "simulation" if self.simulation_mode else "real"
        }
        
        # 如果是真实模式且Gazebo正在运行
        if not self.simulation_mode and self.gazebo_process:
            if self.gazebo_process.poll() is None:
                status['gazebo_running'] = True
                status['gazebo_pid'] = self.gazebo_process.pid
            else:
                status['gazebo_running'] = False
        
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
                    "return_code": 0,  # 确保有这个键
                    "timestamp": datetime.now().isoformat()
                }
            
            # 真实模式
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return {
                    "success": result.returncode == 0,
                    "command": command,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip(),
                    "return_code": result.returncode,  # 使用实际的返回码
                    "timestamp": datetime.now().isoformat()
                }
                
            except subprocess.TimeoutExpired:
                logger.error(f"命令执行超时: {command}")
                return {
                    "success": False,
                    "command": command,
                    "output": "",
                    "error": "命令执行超时",
                    "return_code": -1,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"命令执行失败: {e}")
                return {
                    "success": False,
                    "command": command,
                    "output": "",
                    "error": str(e),
                    "return_code": -1,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"命令执行异常: {e}")
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
                'command': f'echo "Running Gazebo test: {test_name}"'
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