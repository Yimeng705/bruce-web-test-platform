# 安装和运行说明

1. 快速启动

```bash
# 克隆项目
git clone https://github.com/Yimeng705/bruce-web-test-platform
cd bruce-web-test-platform
```

## 安装依赖

```bash
conda create -n bruce-web-test-platform python=3.9
conda activate bruce-web-test-platform
pip install -r requirements.txt
```

## 配置平台连接信息

编辑 config/platforms.yaml

## 启动后端服务

```bash
python -m backend.main
```

## 在浏览器中打开

http://localhost:8000/static/index.html

2. 使用Docker启动

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

3. 主要功能

平台连接管理：一键连接/断开实机和Gazebo

测试用例选择：从预定义测试用例中选择执行

并行测试：同时在多个平台上执行测试

实时监控：查看平台状态和测试进度

数据可视化：图表对比测试结果

日志记录：详细的执行日志

结果导出：导出测试数据为JSON格式

4. 配置文件说明

config/platforms.yaml: 平台连接配置

config/tests.yaml: 测试用例配置

config/bruce_config.yaml: BRUCE特定配置