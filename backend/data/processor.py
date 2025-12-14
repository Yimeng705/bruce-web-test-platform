import json
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

class DataProcessor:
    """数据处理 - 分析和处理测试数据"""
    
    @staticmethod
    def calculate_statistics(data_points: List[Dict]) -> Dict[str, Any]:
        """计算数据统计信息"""
        if not data_points:
            return {}
        
        # 提取数值数据
        numeric_data = {}
        for point in data_points:
            for key, value in point['data'].items():
                if isinstance(value, (int, float)):
                    if key not in numeric_data:
                        numeric_data[key] = []
                    numeric_data[key].append(value)
        
        # 计算统计量
        statistics = {}
        for key, values in numeric_data.items():
            if values:
                stats = {
                    'count': len(values),
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'median': float(np.median(values)),
                    'q1': float(np.percentile(values, 25)),
                    'q3': float(np.percentile(values, 75))
                }
                statistics[key] = stats
        
        return statistics
    
    @staticmethod
    def compare_results(results_a: Dict, results_b: Dict) -> Dict[str, Any]:
        """比较两个测试结果"""
        comparison = {
            'platform_a': results_a.get('platform', 'Unknown'),
            'platform_b': results_b.get('platform', 'Unknown'),
            'test_name': results_a.get('test_name', 'Unknown Test'),
            'comparison_time': datetime.now().isoformat(),
            'metrics': {}
        }
        
        # 比较成功率
        success_a = results_a.get('result', {}).get('success', False)
        success_b = results_b.get('result', {}).get('success', False)
        
        comparison['success_comparison'] = {
            'platform_a': success_a,
            'platform_b': success_b,
            'equal': success_a == success_b
        }
        
        # 比较步骤数量
        steps_a = results_a.get('result', {}).get('steps', 0)
        steps_b = results_b.get('result', {}).get('steps', 0)
        
        comparison['steps_comparison'] = {
            'platform_a': steps_a,
            'platform_b': steps_b,
            'difference': steps_a - steps_b
        }
        
        return comparison
    
    @staticmethod
    def analyze_performance(data_points: List[Dict]) -> Dict[str, Any]:
        """分析性能数据"""
        if not data_points:
            return {}
        
        # 计算时间间隔
        timestamps = []
        for point in data_points:
            try:
                timestamp = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                timestamps.append(timestamp.timestamp())
            except:
                continue
        
        if len(timestamps) < 2:
            return {}
        
        intervals = np.diff(timestamps)
        
        return {
            'total_duration': timestamps[-1] - timestamps[0],
            'data_points': len(data_points),
            'avg_interval': float(np.mean(intervals)),
            'std_interval': float(np.std(intervals)),
            'min_interval': float(np.min(intervals)),
            'max_interval': float(np.max(intervals))
        }
    
    @staticmethod
    def filter_outliers(data_points: List[Dict], threshold: float = 3.0) -> List[Dict]:
        """过滤异常值"""
        if not data_points:
            return []
        
        # 提取数值数据
        numeric_keys = set()
        all_values = {}
        
        for point in data_points:
            for key, value in point['data'].items():
                if isinstance(value, (int, float)):
                    numeric_keys.add(key)
                    if key not in all_values:
                        all_values[key] = []
                    all_values[key].append(value)
        
        # 计算离群值边界
        outliers_indices = set()
        
        for key in numeric_keys:
            values = np.array(all_values[key])
            if len(values) < 3:
                continue
            
            mean = np.mean(values)
            std = np.std(values)
            
            if std == 0:
                continue
            
            # 标记离群值
            for i, value in enumerate(values):
                z_score = abs(value - mean) / std
                if z_score > threshold:
                    outliers_indices.add(i)
        
        # 过滤离群值
        filtered_points = []
        for i, point in enumerate(data_points):
            if i not in outliers_indices:
                filtered_points.append(point)
        
        return filtered_points