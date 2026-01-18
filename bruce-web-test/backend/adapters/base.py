import asyncio
from abc import ABC, abstractmethod
from datetime import datetime

class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config.get('name', 'Unknown Platform')
        self.is_connected = False
        self.last_update = None
        self.test_results = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """连接到平台"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def get_status(self) -> dict:
        """获取平台状态"""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, background: bool = False) -> dict:
        """执行命令"""
        pass
    
    async def execute_test(self, test_config: dict) -> dict:
        """执行测试用例"""
        test_id = test_config.get('test_id', f'test_{datetime.now().timestamp()}')
        test_name = test_config.get('test_name', 'unknown_test')
        
        try:
            # 执行测试逻辑
            result = await self._run_test_steps(test_config)
            
            # 存储结果
            self.test_results[test_id] = {
                'test_id': test_id,
                'test_name': test_name,
                'platform': self.name,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.test_results[test_id]
            
        except Exception as e:
            return {
                'test_id': test_id,
                'test_name': test_name,
                'platform': self.name,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _run_test_steps(self, test_config: dict) -> dict:
        """运行测试步骤"""
        results = []
        
        if 'commands' in test_config:
            for command in test_config['commands']:
                result = await self.execute_command(command)
                results.append(result)
                
        elif 'steps' in test_config:
            for step in test_config['steps']:
                step_result = {'step': step.get('name', 'unknown'), 'results': []}
                
                for cmd in step.get('commands', []):
                    result = await self.execute_command(cmd)
                    step_result['results'].append(result)
                    
                results.append(step_result)
        
        return {
            'success': all(r.get('success', False) for r in results),
            'steps': len(results),
            'results': results
        }