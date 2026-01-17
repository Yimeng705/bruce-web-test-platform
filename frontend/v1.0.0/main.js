// WebSocket连接管理
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.messageHandlers = new Map();
        this.connectionStatus = 'disconnected';
    }

    connect(url) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;
        }

        this.connectionStatus = 'connecting';
        this.updateConnectionUI();

        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
            console.log('✅ WebSocket连接已建立');
            this.connectionStatus = 'connected';
            this.reconnectAttempts = 0;
            this.updateConnectionUI();
            this.log('WebSocket连接已建立', 'success');
            
            // 订阅状态更新
            this.send({ command: 'subscribe_status' });
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('消息解析错误:', error);
            }
        };

        this.socket.onclose = (event) => {
            console.log('🔌 WebSocket连接已断开');
            this.connectionStatus = 'disconnected';
            this.updateConnectionUI();
            
            if (event.code !== 1000) {
                this.attemptReconnect(url);
            }
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket错误:', error);
            this.connectionStatus = 'error';
            this.updateConnectionUI();
            this.log(`WebSocket错误: ${error}`, 'error');
        };
    }

    attemptReconnect(url) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            
            this.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'warning');
            
            setTimeout(() => {
                this.connect(url);
            }, delay);
        } else {
            this.log('重连尝试已用完', 'error');
        }
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
            return true;
        } else {
            console.warn('WebSocket未连接，无法发送消息');
            return false;
        }
    }

    on(event, handler) {
        if (!this.messageHandlers.has(event)) {
            this.messageHandlers.set(event, []);
        }
        this.messageHandlers.get(event).push(handler);
    }

    off(event, handler) {
        const handlers = this.messageHandlers.get(event);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    handleMessage(data) {
        const eventType = data.type;
        const handlers = this.messageHandlers.get(eventType) || [];
        
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`事件处理器错误 (${eventType}):`, error);
            }
        });
    }

    updateConnectionUI() {
        const timeElement = document.getElementById('connection-time');
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString();
        }
    }

    log(message, level = 'info') {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// 平台管理器
class PlatformManager {
    constructor() {
        this.platforms = {
            real_robot: {
                name: '实机',
                connected: false,
                elementId: 'status-real'
            },
            gazebo: {
                name: 'Gazebo',
                connected: false,
                elementId: 'status-gazebo'
            }
        };
    }

    async connect(platform) {
        const platformConfig = this.platforms[platform];
        if (!platformConfig) {
            this.log(`未知平台: ${platform}`, 'error');
            return;
        }

        this.log(`正在连接${platformConfig.name}...`, 'info');

        try {
            const endpoint = platform === 'real_robot' 
                ? '/api/real-robot/connect' 
                : '/api/gazebo/connect';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.updatePlatformStatus(platform, true);
                this.log(`${platformConfig.name}连接成功`, 'success');
            } else {
                this.log(`${platformConfig.name}连接失败: ${result.message || '未知错误'}`, 'error');
            }
        } catch (error) {
            this.log(`${platformConfig.name}连接失败: ${error.message}`, 'error');
        }
    }

    async disconnect(platform) {
        const platformConfig = this.platforms[platform];
        if (!platformConfig) return;

        this.log(`正在断开${platformConfig.name}连接...`, 'info');

        try {
            const endpoint = platform === 'real_robot' 
                ? '/api/real-robot/disconnect' 
                : '/api/gazebo/disconnect';

            const response = await fetch(endpoint, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.updatePlatformStatus(platform, false);
                this.log(`${platformConfig.name}已断开连接`, 'warning');
            }
        } catch (error) {
            this.log(`断开${platformConfig.name}连接失败: ${error.message}`, 'error');
        }
    }

    async disconnectAll() {
        this.log('正在断开所有平台连接...', 'warning');
        
        for (const platform in this.platforms) {
            await this.disconnect(platform);
        }
    }

    updatePlatformStatus(platform, connected) {
        const platformConfig = this.platforms[platform];
        if (!platformConfig) return;

        platformConfig.connected = connected;
        const element = document.getElementById(platformConfig.elementId);
        
        if (element) {
            const statusDot = element.querySelector('.status-dot');
            const statusText = element.querySelector('span:last-child');
            
            if (connected) {
                statusDot.className = 'status-dot online';
                statusText.textContent = `${platformConfig.name}: 在线`;
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = `${platformConfig.name}: 离线`;
            }
        }
    }

    getSelectedPlatforms() {
        const platforms = [];
        
        if (document.getElementById('platform-real').checked) {
            platforms.push('real_robot');
        }
        if (document.getElementById('platform-gazebo').checked) {
            platforms.push('gazebo');
        }
        
        return platforms;
    }

    log(message, level = 'info') {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// 测试管理器
class TestManager {
    constructor() {
        this.currentTestId = null;
        this.chartInstance = null;
        this.testCases = [];
        this.initChart();
    }

    async initChart() {
        const chartDom = document.getElementById('comparison-chart');
        if (!chartDom) return;

        this.chartInstance = echarts.init(chartDom);
        
        const option = {
            title: {
                text: '平台性能对比',
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            legend: {
                data: ['实机', 'Gazebo'],
                top: 30,
                textStyle: {
                    fontSize: 12
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: ['成功率(%)', '执行时间(秒)', '数据一致性(%)'],
                axisLabel: {
                    fontSize: 11
                }
            },
            yAxis: {
                type: 'value',
                name: '数值',
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                }
            },
            series: [
                {
                    name: '实机',
                    type: 'bar',
                    data: [0, 0, 0],
                    itemStyle: {
                        color: '#5470c6'
                    }
                },
                {
                    name: 'Gazebo',
                    type: 'bar',
                    data: [0, 0, 0],
                    itemStyle: {
                        color: '#91cc75'
                    }
                }
            ]
        };
        
        this.chartInstance.setOption(option);
    }

    async loadTestCases() {
        try {
            const response = await fetch('/api/test/test-cases');
            const result = await response.json();
            
            if (result.success) {
                this.testCases = result.test_cases;
                this.populateTestSelect();
            }
        } catch (error) {
            this.log(`加载测试用例失败: ${error.message}`, 'error');
        }
    }

    populateTestSelect() {
        const select = document.getElementById('test-select');
        if (!select) return;

        // 清空现有选项
        select.innerHTML = '<option value="">选择测试用例...</option>';
        
        // 添加测试用例选项
        for (const [id, testCase] of Object.entries(this.testCases)) {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = testCase.name;
            select.appendChild(option);
        }

        // 添加事件监听器
        select.addEventListener('change', (e) => {
            const testId = e.target.value;
            const testCase = this.testCases[testId];
            const descriptionElement = document.getElementById('test-description');
            
            if (descriptionElement && testCase) {
                descriptionElement.textContent = testCase.description || '暂无描述';
            }
        });
    }

    async startTest() {
        const testName = document.getElementById('test-select').value;
        if (!testName) {
            alert('请选择测试用例');
            return;
        }

        const platforms = platformManager.getSelectedPlatforms();
        if (platforms.length === 0) {
            alert('请至少选择一个平台');
            return;
        }

        this.currentTestId = `test_${Date.now()}`;
        
        // 更新UI状态
        this.updateTestStatus('running');
        this.clearResults();

        this.log(`开始测试: ${testName}`, 'info');

        try {
            // 首先从后端获取测试用例的完整配置
            const testCasesResponse = await fetch('/api/test/test-cases');
            const testCasesResult = await testCasesResponse.json();
            
            if (!testCasesResult.success) {
                throw new Error('无法获取测试用例配置');
            }

            // 获取选定测试用例的配置
            const testCases = testCasesResult.test_cases;
            const selectedTestCase = testCases[testName];
            
            if (!selectedTestCase) {
                throw new Error(`未找到测试用例: ${testName}`);
            }

            // 构建包含完整配置的测试请求
            const testConfig = {
                test_name: testName,
                platforms: platforms,
                test_id: this.currentTestId,
                ...selectedTestCase  // 展开测试用例的配置
            };

            // 发送到正确的API端点
            const response = await fetch('/api/real-robot/run-test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(testConfig)
            });

            const result = await response.json();

            if (result.success) {
                this.log('测试已开始执行', 'success');
            } else {
                this.log(`测试启动失败: ${result.message}`, 'error');
                this.updateTestStatus('idle');
            }
        } catch (error) {
            this.log(`测试启动失败: ${error.message}`, 'error');
            this.updateTestStatus('idle');
        }
    }

    stopTest() {
        if (this.currentTestId && wsManager.socket && wsManager.socket.readyState === WebSocket.OPEN) {
            wsManager.socket.send(JSON.stringify({
                command: 'stop_test',
                test_id: this.currentTestId
            }));
            this.log('已发送停止测试命令', 'warning');
        }
    }

    updateTestStatus(status) {
        const startBtn = document.getElementById('start-test-btn');
        const stopBtn = document.getElementById('stop-test-btn');
        const currentTestElement = document.getElementById('current-test');
        const testProgressElement = document.getElementById('test-progress');

        switch (status) {
            case 'running':
                startBtn.disabled = true;
                stopBtn.disabled = false;
                if (currentTestElement) {
                    currentTestElement.textContent = `当前测试: ${this.currentTestId}`;
                }
                if (testProgressElement) {
                    testProgressElement.textContent = '状态: 运行中...';
                }
                break;
                
            case 'completed':
            case 'stopped':
            case 'idle':
                startBtn.disabled = false;
                stopBtn.disabled = true;
                if (currentTestElement) {
                    currentTestElement.textContent = '当前测试: 无';
                }
                if (testProgressElement) {
                    testProgressElement.textContent = '状态: 空闲';
                }
                break;
        }
    }

    displayTestResults(results) {
        // 更新各个平台的结果
        for (const [platform, result] of Object.entries(results)) {
            const elementId = platform === 'real_robot' ? 'result-real' : 'result-gazebo';
            const element = document.getElementById(elementId);
            
            if (element) {
                if (result.error) {
                    element.innerHTML = `
                        <div class="error">
                            <strong>错误:</strong> ${result.error}
                        </div>
                    `;
                } else {
                    const summary = result.summary || {};
                    const successRate = summary.success_rate ? (summary.success_rate * 100).toFixed(1) : '0';
                    
                    element.innerHTML = `
                        <div class="result-summary">
                            <div><strong>测试名称:</strong> ${result.test_name || '未知'}</div>
                            <div><strong>状态:</strong> ${result.success ? '成功' : '失败'}</div>
                            <div><strong>总步骤:</strong> ${summary.total_steps || 0}</div>
                            <div><strong>成功步骤:</strong> ${summary.successful_steps || 0}</div>
                            <div><strong>成功率:</strong> ${successRate}%</div>
                        </div>
                    `;
                }
            }
        }

        // 更新详细结果
        this.updateDetailedResults(results);
        
        // 更新图表
        this.updateComparisonChart(results);
    }

    updateDetailedResults(results) {
        const detailedElement = document.getElementById('detailed-results');
        if (detailedElement) {
            detailedElement.textContent = JSON.stringify(results, null, 2);
        }
    }

    updateComparisonChart(results) {
        if (!this.chartInstance) return;

        const realData = results.real_robot || {};
        const gazeboData = results.gazebo || {};
        
        const realSummary = realData.summary || {};
        const gazeboSummary = gazeboData.summary || {};

        const option = {
            series: [
                {
                    name: '实机',
                    data: [
                        realSummary.success_rate ? realSummary.success_rate * 100 : 0,
                        realData.execution_time || 0,
                        realData.consistency || 0
                    ]
                },
                {
                    name: 'Gazebo',
                    data: [
                        gazeboSummary.success_rate ? gazeboSummary.success_rate * 100 : 0,
                        gazeboData.execution_time || 0,
                        gazeboData.consistency || 0
                    ]
                }
            ]
        };
        
        this.chartInstance.setOption(option);
    }

    clearResults() {
        // 清空结果显示
        ['real', 'gazebo'].forEach(platform => {
            const element = document.getElementById(`result-${platform}`);
            if (element) {
                element.innerHTML = '<div class="placeholder">等待测试...</div>';
            }
        });

        // 清空详细结果
        const detailedElement = document.getElementById('detailed-results');
        if (detailedElement) {
            detailedElement.textContent = '选择测试以查看详细结果...';
        }

        // 重置图表
        if (this.chartInstance) {
            const option = {
                series: [
                    { data: [0, 0, 0] },
                    { data: [0, 0, 0] }
                ]
            };
            this.chartInstance.setOption(option);
        }
    }

    async exportResults() {
        if (!this.currentTestId) {
            alert('没有可导出的测试结果');
            return;
        }

        try {
            const response = await fetch(`/api/test/results/${this.currentTestId}`);
            const data = await response.json();

            if (data.success) {
                // 创建下载链接
                const blob = new Blob([JSON.stringify(data.result, null, 2)], { 
                    type: 'application/json' 
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `bruce_test_${this.currentTestId}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                this.log('结果已导出', 'success');
            } else {
                this.log(`导出失败: ${data.message}`, 'error');
            }
        } catch (error) {
            this.log(`导出失败: ${error.message}`, 'error');
        }
    }

    async executeCommand(command) {
        try {
            this.log(`执行命令: ${command}`, 'info');

            const platforms = platformManager.getSelectedPlatforms();
            if (platforms.length === 0) {
                alert('请至少选择一个平台');
                return;
            }

            for (const platform of platforms) {
                const endpoint = platform === 'real_robot' 
                    ? '/api/real-robot/execute' 
                    : '/api/gazebo/execute';

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        command: command
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    this.log(`${platform === 'real_robot' ? '实机' : 'Gazebo'}命令执行成功`, 'success');
                } else {
                    this.log(`${platform === 'real_robot' ? '实机' : 'Gazebo'}命令执行失败: ${result.message}`, 'error');
                }
            }
        } catch (error) {
            this.log(`命令执行失败: ${error.message}`, 'error');
        }
    }

    async compileAll() {
        try {
            this.log('开始编译所有平台...', 'info');
            
            const response = await fetch('/api/test/compile', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.log('编译任务已启动', 'success');
            } else {
                this.log(`编译启动失败: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`编译失败: ${error.message}`, 'error');
        }
    }

    async initializeRobot() {
        try {
            this.log('正在初始化实机...', 'info');
            
            const response = await fetch('/api/real-robot/initialize', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.log('实机初始化成功', 'success');
            } else {
                this.log(`实机初始化失败: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`初始化失败: ${error.message}`, 'error');
        }
    }

    async startGazebo() {
        try {
            this.log('正在启动Gazebo...', 'info');
            
            const response = await fetch('/api/gazebo/start', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.log('Gazebo启动成功', 'success');
            } else {
                this.log(`Gazebo启动失败: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`启动失败: ${error.message}`, 'error');
        }
    }

    log(message, level = 'info') {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// 全局实例
let wsManager;
let platformManager;
let testManager;
let logsPaused = false;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 初始化管理器
    wsManager = new WebSocketManager();
    platformManager = new PlatformManager();
    testManager = new TestManager();

    // 连接WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    wsManager.connect(wsUrl);

    // 设置WebSocket消息处理器
    wsManager.on('status_update', handleStatusUpdate);
    wsManager.on('test_complete', handleTestComplete);
    wsManager.on('test_stopped', handleTestStopped);

    // 加载测试用例
    await testManager.loadTestCases();

    // 更新连接时间
    updateConnectionTime();
    setInterval(updateConnectionTime, 1000);

    // 更新最后更新时间
    setInterval(updateLastUpdate, 1000);

    // 设置事件监听器
    setupEventListeners();
});

// WebSocket消息处理
function handleStatusUpdate(data) {
    const status = data.data;
    
    for (const [platform, platformStatus] of Object.entries(status)) {
        platformManager.updatePlatformStatus(platform, platformStatus.connected);
    }
}

function handleTestComplete(data) {
    testManager.displayTestResults(data.results);
    testManager.updateTestStatus('completed');
    testManager.log(`测试完成: ${data.test_id}`, 'success');
}

function handleTestStopped(data) {
    testManager.updateTestStatus('stopped');
    testManager.log(`测试已停止: ${data.test_id}`, 'warning');
}

// 事件监听器设置
function setupEventListeners() {
    // 清空日志按钮
    const clearLogsBtn = document.querySelector('.log-controls .btn:first-child');
    if (clearLogsBtn) {
        clearLogsBtn.addEventListener('click', () => {
            const logContainer = document.getElementById('log-container');
            if (logContainer) {
                logContainer.innerHTML = '<div class="log-entry">日志已清空</div>';
            }
        });
    }

    // 暂停/继续日志按钮
    const toggleLogsBtn = document.querySelector('.log-controls .btn:last-child');
    if (toggleLogsBtn) {
        toggleLogsBtn.addEventListener('click', () => {
            logsPaused = !logsPaused;
            const message = logsPaused ? '日志已暂停' : '日志已继续';
            testManager.log(message, 'warning');
            toggleLogsBtn.textContent = logsPaused ? '继续日志' : '暂停日志';
        });
    }
}

// 工具函数
function updateConnectionTime() {
    const timeElement = document.getElementById('connection-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString();
    }
}

function updateLastUpdate() {
    const timeElement = document.getElementById('last-update');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = `最后更新: ${now.toLocaleTimeString()}`;
    }
}

// 全局函数（供HTML按钮调用）
function connectPlatform(platform) {
    platformManager.connect(platform);
}

function disconnectAll() {
    platformManager.disconnectAll();
}

function startGazebo() {
    testManager.startGazebo();
}

function executeCommand(command) {
    if (typeof command === 'string') {
        testManager.executeCommand(command);
    } else {
        // 从事件对象获取命令
        const button = event.target;
        const command = button.getAttribute('data-command');
        if (command) {
            testManager.executeCommand(command);
        }
    }
}

function startTest() {
    testManager.startTest();
}

function stopTest() {
    testManager.stopTest();
}

function exportResults() {
    testManager.exportResults();
}