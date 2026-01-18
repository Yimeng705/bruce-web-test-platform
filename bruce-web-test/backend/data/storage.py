import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class DataStorage:
    """数据存储 - 使用SQLite存储测试数据"""
    
    def __init__(self, db_path: str = "data/test_results.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建测试结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE,
                    test_name TEXT,
                    platform TEXT,
                    success BOOLEAN,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration REAL,
                    results_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建数据点表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    timestamp TIMESTAMP,
                    metric_name TEXT,
                    metric_value REAL,
                    FOREIGN KEY (test_id) REFERENCES test_results (test_id)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_id ON test_results(test_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_platform ON test_results(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON test_results(start_time)')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_test_result(self, test_result: Dict[str, Any]) -> bool:
        """保存测试结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 计算持续时间
                start_time = datetime.fromisoformat(test_result.get('timestamp', datetime.now().isoformat()))
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO test_results 
                    (test_id, test_name, platform, success, start_time, end_time, duration, results_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_result.get('test_id'),
                    test_result.get('test_name'),
                    test_result.get('platform'),
                    test_result.get('success', False),
                    start_time,
                    end_time,
                    duration,
                    json.dumps(test_result, ensure_ascii=False)
                ))
                
                # 保存数据点
                if 'result' in test_result and 'results' in test_result['result']:
                    for result in test_result['result']['results']:
                        if isinstance(result, dict) and 'data' in result:
                            for metric_name, metric_value in result['data'].items():
                                if isinstance(metric_value, (int, float)):
                                    cursor.execute('''
                                        INSERT INTO data_points 
                                        (test_id, timestamp, metric_name, metric_value)
                                        VALUES (?, ?, ?, ?)
                                    ''', (
                                        test_result.get('test_id'),
                                        datetime.now(),
                                        metric_name,
                                        metric_value
                                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error saving test result: {e}")
            return False
    
    def get_test_result(self, test_id: str) -> Optional[Dict]:
        """获取测试结果"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM test_results WHERE test_id = ?', (test_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            print(f"Error getting test result: {e}")
            return None
    
    def get_all_tests(self, platform: str = None, limit: int = 100) -> List[Dict]:
        """获取所有测试"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if platform:
                    cursor.execute(
                        'SELECT * FROM test_results WHERE platform = ? ORDER BY start_time DESC LIMIT ?',
                        (platform, limit)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM test_results ORDER BY start_time DESC LIMIT ?',
                        (limit,)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error getting all tests: {e}")
            return []
    
    def get_test_data_points(self, test_id: str) -> List[Dict]:
        """获取测试数据点"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM data_points WHERE test_id = ? ORDER BY timestamp',
                    (test_id,)
                )
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error getting data points: {e}")
            return []
    
    def get_statistics(self, platform: str = None) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if platform:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_tests,
                            AVG(duration) as avg_duration,
                            MIN(duration) as min_duration,
                            MAX(duration) as max_duration,
                            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_tests
                        FROM test_results 
                        WHERE platform = ?
                    ''', (platform,))
                else:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_tests,
                            AVG(duration) as avg_duration,
                            MIN(duration) as min_duration,
                            MAX(duration) as max_duration,
                            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_tests
                        FROM test_results
                    ''')
                
                row = cursor.fetchone()
                if row:
                    stats = dict(row)
                    if stats['total_tests'] > 0:
                        stats['success_rate'] = stats['successful_tests'] / stats['total_tests']
                    else:
                        stats['success_rate'] = 0
                    return stats
                
                return {}
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}