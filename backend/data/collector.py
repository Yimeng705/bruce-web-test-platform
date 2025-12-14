import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import aiofiles

class DataCollector:
    """数据收集器 - 收集和管理测试数据"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.current_data = {}
        self.data_streams = {}
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "processed"), exist_ok=True)
    
    async def start_collection(self, test_id: str, metrics: List[str]):
        """开始收集数据"""
        self.current_data[test_id] = {
            'test_id': test_id,
            'start_time': datetime.now().isoformat(),
            'metrics': metrics,
            'data_points': [],
            'metadata': {}
        }
        
        # 创建数据流
        self.data_streams[test_id] = asyncio.Queue()
        
        # 启动数据处理任务
        asyncio.create_task(self._process_data_stream(test_id))
    
    async def add_data_point(self, test_id: str, data: Dict):
        """添加数据点"""
        if test_id not in self.current_data:
            await self.start_collection(test_id, list(data.keys()))
        
        data_point = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        self.current_data[test_id]['data_points'].append(data_point)
        
        # 放入数据流
        if test_id in self.data_streams:
            await self.data_streams[test_id].put(data_point)
    
    async def stop_collection(self, test_id: str):
        """停止数据收集"""
        if test_id in self.current_data:
            self.current_data[test_id]['end_time'] = datetime.now().isoformat()
            
            # 保存数据到文件
            await self._save_data(test_id)
            
            # 清理数据流
            if test_id in self.data_streams:
                self.data_streams[test_id] = None
                del self.data_streams[test_id]
    
    async def _process_data_stream(self, test_id: str):
        """处理数据流"""
        while test_id in self.data_streams and self.data_streams[test_id] is not None:
            try:
                data_point = await asyncio.wait_for(
                    self.data_streams[test_id].get(),
                    timeout=1.0
                )
                
                # 这里可以添加实时数据处理逻辑
                # 例如：过滤、转换、分析等
                
                self.data_streams[test_id].task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing data stream for {test_id}: {e}")
    
    async def _save_data(self, test_id: str):
        """保存数据到文件"""
        if test_id not in self.current_data:
            return
        
        data = self.current_data[test_id]
        filename = f"{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.data_dir, "raw", filename)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        
        print(f"Data saved to: {filepath}")
    
    async def get_test_data(self, test_id: str) -> Optional[Dict]:
        """获取测试数据"""
        return self.current_data.get(test_id)
    
    async def get_all_tests(self) -> List[str]:
        """获取所有测试ID"""
        return list(self.current_data.keys())