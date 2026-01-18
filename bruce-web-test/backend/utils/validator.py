import re
import ipaddress
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """验证IP地址"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """验证端口号"""
        return 1 <= port <= 65535
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """验证主机名"""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, hostname))
    
    @staticmethod
    def validate_ssh_connection(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证SSH连接配置"""
        errors = []
        
        # 必需字段
        required_fields = ['host', 'username']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # 验证主机格式
        if 'host' in config:
            host = config['host']
            if not (ConfigValidator.validate_ip_address(host) or ConfigValidator.validate_hostname(host)):
                errors.append(f"Invalid host format: {host}")
        
        # 验证端口
        if 'port' in config:
            port = config['port']
            if not ConfigValidator.validate_port(port):
                errors.append(f"Invalid port: {port}")
        
        # 验证用户名
        if 'username' in config:
            username = config['username']
            if not re.match(r'^[a-z_][a-z0-9_-]*$', username):
                errors.append(f"Invalid username: {username}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_test_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证测试配置"""
        errors = []
        
        # 必需字段
        if 'name' not in config:
            errors.append("Test config must have a 'name'")
        
        if 'description' not in config:
            errors.append("Test config must have a 'description'")
        
        # 验证命令或步骤
        has_commands = 'commands' in config and config['commands']
        has_steps = 'steps' in config and config['steps']
        
        if not has_commands and not has_steps:
            errors.append("Test config must have either 'commands' or 'steps'")
        
        # 验证命令格式
        if has_commands:
            commands = config['commands']
            if not isinstance(commands, list):
                errors.append("'commands' must be a list")
            else:
                for i, cmd in enumerate(commands):
                    if not isinstance(cmd, str):
                        errors.append(f"Command {i} must be a string")
                    elif not cmd.strip():
                        errors.append(f"Command {i} cannot be empty")
        
        # 验证步骤格式
        if has_steps:
            steps = config['steps']
            if not isinstance(steps, list):
                errors.append("'steps' must be a list")
            else:
                for i, step in enumerate(steps):
                    if not isinstance(step, dict):
                        errors.append(f"Step {i} must be a dictionary")
                    else:
                        if 'name' not in step:
                            errors.append(f"Step {i} must have a 'name'")
                        if 'commands' not in step:
                            errors.append(f"Step {i} must have 'commands'")
                        elif not isinstance(step['commands'], list):
                            errors.append(f"Step {i} commands must be a list")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_data_point(data_point: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证数据点"""
        errors = []
        
        # 必需字段
        if 'timestamp' not in data_point:
            errors.append("Data point must have a 'timestamp'")
        else:
            try:
                datetime.fromisoformat(data_point['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"Invalid timestamp format: {data_point['timestamp']}")
        
        if 'data' not in data_point:
            errors.append("Data point must have 'data'")
        elif not isinstance(data_point['data'], dict):
            errors.append("'data' must be a dictionary")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """清理命令字符串"""
        # 移除危险字符
        dangerous_chars = [';', '&&', '||', '`', '$', '>', '<', '|']
        sanitized = command
        
        for char in dangerous_chars:
            if char in ['&&', '||']:
                # 这些字符在特定上下文中可能是合法的，所以只检查是否在开头
                if sanitized.strip().startswith(char):
                    sanitized = sanitized.replace(char, '', 1)
            else:
                sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> Tuple[bool, str]:
        """验证文件路径"""
        if not path or not isinstance(path, str):
            return False, "Path must be a non-empty string"
        
        # 检查路径是否包含危险字符
        dangerous_patterns = ['../', '~/', '..\\']
        for pattern in dangerous_patterns:
            if pattern in path:
                return False, f"Path contains dangerous pattern: {pattern}"
        
        # 检查路径是否存在
        if must_exist and not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        return True, ""