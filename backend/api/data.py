from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import json
from datetime import datetime
import os

from backend.data.storage import DataStorage
from backend.data.processor import DataProcessor
from backend.utils.logger import data_logger as logger

router = APIRouter()
data_storage = DataStorage()

@router.get("/statistics")
async def get_statistics(platform: Optional[str] = None):
    """获取统计信息"""
    try:
        stats = data_storage.get_statistics(platform)
        
        return {
            "success": True,
            "statistics": stats,
            "platform": platform,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-points/{test_id}")
async def get_data_points(test_id: str):
    """获取测试数据点"""
    try:
        data_points = data_storage.get_test_data_points(test_id)
        
        # 处理数据
        if data_points:
            # 转换为适合前端使用的格式
            formatted_points = []
            for point in data_points:
                formatted_points.append({
                    "timestamp": point["timestamp"],
                    "metric_name": point["metric_name"],
                    "metric_value": point["metric_value"]
                })
            
            # 计算统计信息
            statistics = DataProcessor.calculate_statistics([
                {"data": {point["metric_name"]: point["metric_value"]}}
                for point in data_points
            ])
            
            # 分析性能
            performance = DataProcessor.analyze_performance([
                {"timestamp": point["timestamp"]}
                for point in data_points
            ])
            
            return {
                "success": True,
                "test_id": test_id,
                "data_points": formatted_points,
                "count": len(data_points),
                "statistics": statistics,
                "performance": performance,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "test_id": test_id,
                "data_points": [],
                "count": 0,
                "message": "No data points found",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get data points: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{test_id}")
async def export_test_results(test_id: str, format: str = "json"):
    """导出测试结果"""
    try:
        result = data_storage.get_test_result(test_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Test result not found: {test_id}")
        
        # 获取数据点
        data_points = data_storage.get_test_data_points(test_id)
        
        # 构建导出数据
        export_data = {
            "test_result": result,
            "data_points": data_points,
            "export_time": datetime.now().isoformat(),
            "export_format": format
        }
        
        # 根据格式返回数据
        if format == "json":
            return export_data
        elif format == "csv":
            # 转换为CSV格式（简化版）
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入标题
            writer.writerow(["timestamp", "metric_name", "metric_value"])
            
            # 写入数据
            for point in data_points:
                writer.writerow([
                    point["timestamp"],
                    point["metric_name"],
                    point["metric_value"]
                ])
            
            return {
                "success": True,
                "test_id": test_id,
                "csv_data": output.getvalue(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
    except Exception as e:
        logger.error(f"Failed to export test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform-comparison")
async def platform_comparison(test_id: Optional[str] = None):
    """平台对比分析"""
    try:
        if test_id:
            # 获取特定测试的对比
            result = data_storage.get_test_result(test_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Test result not found: {test_id}")
            
            results = result.get("results", {})
            real_result = results.get("real_robot", {})
            gazebo_result = results.get("gazebo", {})
            
            if not real_result or not gazebo_result:
                return {
                    "success": True,
                    "test_id": test_id,
                    "message": "Insufficient data for comparison",
                    "timestamp": datetime.now().isoformat()
                }
            
            comparison = DataProcessor.compare_results(real_result, gazebo_result)
            
            return {
                "success": True,
                "test_id": test_id,
                "comparison": comparison,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 获取所有测试的总体对比
            tests = data_storage.get_all_tests(limit=100)
            
            platform_stats = {
                "real_robot": data_storage.get_statistics("real_robot"),
                "gazebo": data_storage.get_statistics("gazebo")
            }
            
            return {
                "success": True,
                "platform_stats": platform_stats,
                "total_tests": len(tests),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to perform platform comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-metrics")
async def get_performance_metrics(metric_name: Optional[str] = None):
    """获取性能指标"""
    try:
        # 获取最近的测试
        tests = data_storage.get_all_tests(limit=20)
        
        metrics = []
        for test in tests:
            test_id = test.get("test_id")
            data_points = data_storage.get_test_data_points(test_id)
            
            if data_points:
                # 按指标分组
                metric_groups = {}
                for point in data_points:
                    name = point["metric_name"]
                    value = point["metric_value"]
                    
                    if name not in metric_groups:
                        metric_groups[name] = []
                    metric_groups[name].append(value)
                
                # 计算每个指标的统计信息
                for name, values in metric_groups.items():
                    if metric_name and name != metric_name:
                        continue
                    
                    stats = {
                        "test_id": test_id,
                        "metric_name": name,
                        "count": len(values),
                        "mean": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0
                    }
                    metrics.append(stats)
        
        return {
            "success": True,
            "metrics": metrics,
            "count": len(metrics),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_old_data(days: int = 30):
    """清理旧数据"""
    try:
        # 注意：实际清理逻辑需要根据数据库设计实现
        # 这里只是一个示例
        message = f"Cleanup scheduled for data older than {days} days"
        
        logger.info(f"Data cleanup requested: {message}")
        
        return {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup data: {e}")
        raise HTTPException(status_code=500, detail=str(e))