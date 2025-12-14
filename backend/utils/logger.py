import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class Logger:
    """统一的日志记录器"""
    
    _instances = {}
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（按大小轮转）
        file_path = os.path.join(self.log_dir, f"{self.name}.log")
        file_handler = RotatingFileHandler(
            file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # 错误处理器（单独文件）
        error_path = os.path.join(self.log_dir, f"{self.name}_error.log")
        error_handler = TimedRotatingFileHandler(
            error_path, when='midnight', interval=1, backupCount=7, encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        self.logger.addHandler(error_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> 'Logger':
        """获取或创建日志记录器实例"""
        if name not in cls._instances:
            cls._instances[name] = cls(name)
        return cls._instances[name]
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """格式化消息"""
        if kwargs:
            return f"{message} | {kwargs}"
        return message
    
    def log_command(self, command: str, success: bool, details: dict = None):
        """记录命令执行日志"""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.info(f"Command: {command} - {status}", **details or {})
    
    def log_test(self, test_id: str, test_name: str, platform: str, result: dict):
        """记录测试日志"""
        success = result.get('success', False)
        status = "PASSED" if success else "FAILED"
        
        self.info(f"Test Complete - ID: {test_id}, Name: {test_name}, Platform: {platform}, Status: {status}",
                 test_result=result)

# 创建全局日志记录器实例
main_logger = Logger.get_logger("main")
robot_logger = Logger.get_logger("robot")
gazebo_logger = Logger.get_logger("gazebo")
test_logger = Logger.get_logger("test")
data_logger = Logger.get_logger("data")