import re
from typing import Dict, List, Any
import yaml
import json

class CommandParser:
    """命令解析器 - 用于解析和处理测试命令"""
    
    def __init__(self):
        self.variables = {}
        
    def parse_command(self, command: str, context: Dict[str, Any] = None) -> str:
        """解析命令中的变量和占位符"""
        if not command:
            return command
        
        # 合并上下文变量
        variables = {**self.variables, **(context or {})}
        
        # 替换变量 ${var}
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        
        parsed_command = re.sub(r'\$\{(\w+)\}', replace_var, command)
        
        return parsed_command
    
    def parse_test_config(self, config: Dict) -> List[Dict]:
        """解析测试配置，生成可执行的命令序列"""
        commands = []
        
        if 'steps' in config:
            for step in config['steps']:
                step_commands = []
                
                for cmd in step.get('commands', []):
                    parsed_cmd = self.parse_command(cmd)
                    step_commands.append({
                        'type': 'command',
                        'content': parsed_cmd,
                        'original': cmd
                    })
                
                commands.append({
                    'name': step.get('name', 'Unnamed Step'),
                    'commands': step_commands,
                    'description': step.get('description', '')
                })
                
        elif 'commands' in config:
            for cmd in config['commands']:
                parsed_cmd = self.parse_command(cmd)
                commands.append({
                    'type': 'command',
                    'content': parsed_cmd,
                    'original': cmd
                })
        
        return commands
    
    def load_test_from_yaml(self, yaml_path: str) -> Dict:
        """从YAML文件加载测试配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def save_results(self, results: Dict, output_path: str, format: str = 'json'):
        """保存测试结果"""
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif format == 'yaml':
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(results, f, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")