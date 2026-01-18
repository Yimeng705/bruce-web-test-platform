// 文件: main.js - 重新设计的状态驱动交互
// 全局状态管理
class StateManager {
    constructor() {
        this.state = {
            system: 'idle', // idle, connecting, connected, testing, error
            mode: 'novice', // novice, expert
            platforms: {
                real_robot: { connected: false, status: 'offline' },
                gazebo: { connected: false, status: 'offline' }
            },
            currentTest: null,
            testProgress: 0,
            logs: [],
            configuration: {
                gait_frequency: 2.0,
                stride_length: 25,
                selected_platforms: ['real_robot', 'gazebo'],
                test_preset: 'default'
            }
        };
        
        this.observers = [];
        this.websocket = null;
        this.charts = {};
        this.scene = null;
        this.renderer = null;
        this.camera = null;
        this.robotModel = null;
    }
    
    subscribe(observer) {
        this.observers.push(observer);
    }
    
    notify() {
        this.observers.forEach(observer => observer(this.state));
    }
    
    updateState(newState) {
        Object.assign(this.state, newState);
        this.notify();
        this.updateUI();
    }
    
    async connectWebSocket() {
        try {
            this.updateState({ system: 'connecting' });
            
            // 模拟WebSocket连接
            this.websocket = {
                send: (data) => {
                    console.log('WebSocket send:', data);
                    this.simulateWebSocketResponse(data);
                },
                close: () => {
                    console.log('WebSocket closed');
                    this.websocket = null;
                }
            };
            
            // 模拟连接延迟
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.updateState({
                system: 'connected',
                platforms: {
                    real_robot: { connected: true, status: 'online' },
                    gazebo: { connected: true, status: 'online' }
                }
            });
            
            this.addLog('WebSocket连接成功', 'success');
            
        } catch (error) {
            this.updateState({ system: 'error' });
            this.addLog(`连接失败: ${error.message}`, 'error');
        }
    }
    
    simulateWebSocketResponse(data) {
        // 模拟服务器响应
        setTimeout(() => {
            if (data.command === 'start_test') {
                this.simulateTestExecution(data);
            } else if (data.command === 'stop_test') {
                this.stopTestSimulation();
            }
        }, 500);
    }
    
    async simulateTestExecution(data) {
        this.updateState({
            system: 'testing',
            currentTest: data.test_id,
            testProgress: 0
        });
        
        const steps = data.platforms.length * 10;
        let currentStep = 0;
        
        const interval = setInterval(() => {
            if (currentStep >= steps) {
                clearInterval(interval);
                this.completeTest(data);
                return;
            }
            
            currentStep++;
            const progress = (currentStep / steps) * 100;
            this.updateState({ testProgress: progress });
            
            // 模拟实时数据更新
            this.updateCharts();
            
            // 添加进度日志
            this.addLog(`步骤 ${currentStep}/${steps} 完成`, 'info');
            
        }, 500);
        
        this.testInterval = interval;
    }
    
    completeTest(data) {
        const results = {
            test_id: data.test_id,
            timestamp: new Date().toISOString(),
            summary: {
                success_rate: 0.95,
                execution_time: 120,
                consistency: 0.92
            },
            platforms: {}
        };
        
        data.platforms.forEach(platform => {
            results.platforms[platform] = {
                success: Math.random() > 0.2,
                metrics: {
                    latency: Math.random() * 100,
                    accuracy: 0.85 + Math.random() * 0.1,
                    stability: 0.9 + Math.random() * 0.08
                },
                details: Array.from({length: 10}, (_, i) => ({
                    step: i + 1,
                    status: Math.random() > 0.1 ? 'success' : 'failed',
                    timestamp: new Date().toISOString()
                }))
            };
        });
        
        this.updateState({
            system: 'connected',
            testProgress: 100,
            currentTest: null
        });
        
        this.showResultsModal(results);
        this.addLog('测试完成', 'success');
    }
    
    stopTestSimulation() {
        if (this.testInterval) {
            clearInterval(this.testInterval);
            this.testInterval = null;
        }
        
        this.updateState({
            system: 'connected',
            testProgress: 0,
            currentTest: null
        });
        
        this.addLog('测试已停止', 'warning');
    }
    
    addLog(message, level = 'info') {
        const logEntry = {
            timestamp: new Date().toLocaleTimeString(),
            message,
            level
        };
        
        this.state.logs.push(logEntry);
        if (this.state.logs.length > 100) {
            this.state.logs.shift();
        }
        
        this.updateLogUI(logEntry);
    }
    
    updateLogUI(logEntry) {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;
        
        const logElement = document.createElement('div');
        logElement.className = `log-entry ${logEntry.level}`;
        logElement.innerHTML = `
            <span class="log-time">${logEntry.timestamp}</span>
            <span class="log-message">${logEntry.message}</span>
        `;
        
        logContainer.appendChild(logElement);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    updateUI() {
        // 更新系统状态指示器
        document.body.className = `state-${this.state.system}`;
        document.getElementById('system-status').textContent = this.getStatusText(this.state.system);
        document.getElementById('global-status').className = `status-dot ${this.state.system}`;
        
        // 更新平台状态
        this.updatePlatformStatus();
        
        // 更新进度条
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${this.state.testProgress}%`;
        }
        
        // 更新当前测试显示
        const currentTestEl = document.getElementById('current-test');
        if (currentTestEl) {
            currentTestEl.textContent = this.state.currentTest 
                ? `测试中: ${this.state.currentTest}` 
                : '准备就绪';
        }
        
        // 更新连接时间
        this.updateConnectionTime();

        // 更新控制按钮状态
        try {
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');
            const pauseBtn = document.getElementById('pause-btn');

            if (this.state.system === 'testing') {
                if (startBtn) startBtn.disabled = true;
                if (stopBtn) stopBtn.disabled = false;
                if (pauseBtn) pauseBtn.disabled = false;
            } else {
                if (startBtn) startBtn.disabled = false;
                if (stopBtn) stopBtn.disabled = true;
                if (pauseBtn) {
                    pauseBtn.disabled = true;
                    pauseBtn.innerHTML = '<span class="btn-icon">⏸️</span>暂停';
                }
            }
        } catch (e) {
            console.warn('更新按钮状态失败', e);
        }
    }
    
    updatePlatformStatus() {
        const platforms = this.state.platforms;
        
        for (const [platform, info] of Object.entries(platforms)) {
            const elementId = `status-${platform.replace('_', '-')}`;
            const element = document.getElementById(elementId);
            
            if (element) {
                const dot = element.querySelector('.status-dot');
                const text = element.querySelector('span:last-child');
                
                dot.className = `status-dot ${info.status}`;
                text.textContent = platform === 'real_robot' ? '实机' : 'Gazebo';
                text.textContent += `: ${info.connected ? '在线' : '离线'}`;
            }
        }
    }
    
    getStatusText(status) {
        const statusMap = {
            idle: '空闲',
            connecting: '连接中',
            connected: '已连接',
            testing: '测试中',
            error: '错误'
        };
        return statusMap[status] || status;
    }
    
    updateConnectionTime() {
        const timeElement = document.getElementById('connection-time');
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleTimeString();
        }
    }
    
    updateCharts() {
        // 更新关节角度图表
        if (this.charts.joint) {
            const option = this.charts.joint.getOption();
            const series = option.series[0];
            
            // 生成模拟关节数据
            const newData = Array.from({length: 12}, () => 
                Math.sin(Date.now() / 1000 + Math.random()) * 45
            );
            
            series.data = newData;
            this.charts.joint.setOption({ series: [series] });
        }
        
        // 更新IMU数据图表
        if (this.charts.imu) {
            const option = this.charts.imu.getOption();
            const now = Date.now();
            
            option.series.forEach((series, idx) => {
                const value = Math.sin(now / 1000 + idx) * 2;
                series.data.push([now, value]);
                
                if (series.data.length > 100) {
                    series.data.shift();
                }
            });
            
            this.charts.imu.setOption(option);
        }
    }
    
    showResultsModal(results) {
        const modal = document.getElementById('results-modal');
        const content = document.getElementById('result-summary');
        
        if (!modal || !content) return;
        
        content.innerHTML = `
            <div class="result-summary">
                <h3>测试结果摘要</h3>
                <div class="result-metrics">
                    ${Object.entries(results.platforms).map(([platform, data]) => `
                        <div class="platform-result">
                            <h4>${platform === 'real_robot' ? '实机' : 'Gazebo'}</h4>
                            <div class="metric-row">
                                <span>状态:</span>
                                <span class="${data.success ? 'success' : 'error'}">
                                    ${data.success ? '成功' : '失败'}
                                </span>
                            </div>
                            <div class="metric-row">
                                <span>延迟:</span>
                                <span>${data.metrics.latency.toFixed(1)}ms</span>
                            </div>
                            <div class="metric-row">
                                <span>准确率:</span>
                                <span>${(data.metrics.accuracy * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="result-charts" style="height: 300px;"></div>
            </div>
        `;
        
        modal.style.display = 'flex';
    }
    
    init3DScene() {
        const canvas = document.getElementById('robot-canvas');
        if (!canvas) return;
        
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
        
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);
        this.renderer.setClearColor(0x000000);
        
        // 添加光源
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 1, 1);
        this.scene.add(directionalLight);
        
        // 创建机器人简单模型
        this.createRobotModel();
        
        this.camera.position.z = 5;
        
        // 添加轨道控制
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        
        this.animate();
    }
    
    createRobotModel() {
        const group = new THREE.Group();
        
        // 躯干
        const torso = new THREE.Mesh(
            new THREE.BoxGeometry(1, 1.5, 0.5),
            new THREE.MeshPhongMaterial({ color: 0x4361ee })
        );
        group.add(torso);
        
        // 头部
        const head = new THREE.Mesh(
            new THREE.SphereGeometry(0.3, 32, 32),
            new THREE.MeshPhongMaterial({ color: 0x3a0ca3 })
        );
        head.position.y = 1.2;
        group.add(head);
        
        // 腿部
        for (let i = 0; i < 4; i++) {
            const leg = new THREE.Mesh(
                new THREE.CylinderGeometry(0.1, 0.1, 1),
                new THREE.MeshPhongMaterial({ color: 0x4cc9f0 })
            );
            leg.position.x = (i < 2 ? -0.3 : 0.3);
            leg.position.y = -0.8;
            leg.position.z = (i % 2 === 0 ? -0.2 : 0.2);
            group.add(leg);
        }
        
        this.robotModel = group;
        this.scene.add(this.robotModel);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        if (this.robotModel && this.state.system === 'testing') {
            this.robotModel.rotation.y += 0.01;
            
            // 模拟行走动画
            this.robotModel.children.forEach((child, index) => {
                if (child.type === 'Mesh' && child.geometry.type === 'CylinderGeometry') {
                    child.rotation.x = Math.sin(Date.now() / 200 + index) * 0.5;
                }
            });
        }
        
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
    
    initCharts() {
        // 初始化关节角度图表
        const jointChart = echarts.init(document.getElementById('joint-chart'));
        const jointOption = {
            grid: { left: '3%', right: '3%', top: '5%', bottom: '15%' },
            xAxis: {
                type: 'category',
    
                data: Array.from({length: 12}, (_, i) => `关节 ${i+1}`),
                axisLabel: { fontSize: 10, rotate: 45 }
            },
            yAxis: { type: 'value', name: '角度(°)' },
            series: [{
                type: 'bar',
                data: Array.from({length: 12}, () => 0),
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#4361ee' },
                        { offset: 1, color: '#3a0ca3' }
                    ])
                }
            }]
        };
        jointChart.setOption(jointOption);
        this.charts.joint = jointChart;
        
        // 初始化IMU图表
        const imuChart = echarts.init(document.getElementById('imu-chart'));
        const imuOption = {
            grid: { left: '3%', right: '3%', top: '5%', bottom: '15%' },
            xAxis: { type: 'time' },
            yAxis: { type: 'value', name: '值' },
            series: [
                { name: '加速度X', type: 'line', data: [], smooth: true },
                { name: '加速度Y', type: 'line', data: [], smooth: true },
                { name: '加速度Z', type: 'line', data: [], smooth: true }
            ],
            legend: { top: 'bottom' }
        };
        imuChart.setOption(imuOption);
        this.charts.imu = imuChart;
        
        // 窗口大小变化时重绘图表
        window.addEventListener('resize', () => {
            jointChart.resize();
            imuChart.resize();
        });
    }
}

// 全局状态管理器实例
let stateManager;

// 初始化函数
document.addEventListener('DOMContentLoaded', () => {
    stateManager = new StateManager();
    stateManager.initCharts();
    
    // 初始化事件监听器
    initEventListeners();
    
    // 初始化3D场景
    stateManager.init3DScene();
    
    // 更新最后更新时间
    setInterval(() => {
        const timeElement = document.getElementById('last-update');
        if (timeElement) {
            timeElement.textContent = `最后更新: ${new Date().toLocaleTimeString()}`;
        }
    }, 1000);
});

// 事件监听器初始化
function initEventListeners() {
    // 模式切换（带确认提示以防误操作）
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            const current = document.body.dataset.mode || 'novice';

            // 如果选择相同模式，无需操作
            if (mode === current) return;

            // 根据目标模式展示确认信息
            let msg = '';
            if (mode === 'expert') {
                msg = '切换到专家模式将显示高级配置并允许修改底层参数，可能影响当前任务。是否确认切换？';
            } else {
                msg = '切换到新手模式将隐藏高级配置并恢复简化界面，可能重置部分设置。是否确认切换？';
            }

            if (!confirm(msg)) return;

            // 执行切换
            switchMode(mode);
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.body.dataset.mode = mode;
        });
    });
    
    // 任务选择
    document.querySelectorAll('.task-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.task-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            
            const task = card.dataset.task;
            stateManager.addLog(`选择了任务: ${task}`, 'info');
            
            // 更新新手引导
            updateGuidance(2);
        });
    });
    
    // 配置选项卡
    document.querySelectorAll('.config-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            
            document.querySelectorAll('.config-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 这里可以根据选项卡切换内容
            stateManager.addLog(`切换到 ${tabName} 配置`, 'info');
        });
    });
    
    // 滑块数值显示
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        slider.addEventListener('input', () => {
            // 映射滑块 id 到显示元素及配置键名
            const displayMap = {
                'gait-frequency': 'frequency-value',
                'stride-length': 'stride-value'
            };

            const configKeyMap = {
                'gait-frequency': 'gait_frequency',
                'stride-length': 'stride_length'
            };

            const valueDisplay = document.getElementById(displayMap[slider.id] || (slider.id + '-value'));
            if (valueDisplay) {
                valueDisplay.textContent = slider.value;
            }

            // 更新状态管理器的配置（使用映射的配置键）
            const cfgKey = configKeyMap[slider.id] || slider.id;
            if (stateManager && stateManager.state && stateManager.state.configuration) {
                stateManager.state.configuration[cfgKey] = parseFloat(slider.value);
            }
        });
    });
    
    // 视图切换
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (view === '3d') {
                document.getElementById('robot-3d-view').style.display = 'block';
                document.getElementById('data-charts').style.display = 'none';
            } else {
                document.getElementById('robot-3d-view').style.display = 'none';
                document.getElementById('data-charts').style.display = 'grid';
            }
        });
    });
    
    // 配置预设选择
    const configSelect = document.getElementById('config-preset');
    if (configSelect) {
        configSelect.addEventListener('change', () => {
            const preset = configSelect.value;
            stateManager.addLog(`切换到预设: ${preset}`, 'info');
            
            // 这里可以根据预设更新配置
            switch (preset) {
                case 'high_speed':
                    updateSlider('gait-frequency', 3.5);
                    updateSlider('stride-length', 40);
                    break;
                case 'stability':
                    updateSlider('gait-frequency', 1.2);
                    updateSlider('stride-length', 20);
                    break;
            }
        });
    }
}

// 工具函数
function switchMode(mode) {
    const novicePanel = document.getElementById('novice-templates');
    const expertPanel = document.getElementById('expert-config');
    
    if (mode === 'novice') {
        novicePanel.style.display = 'block';
        expertPanel.style.display = 'none';
        stateManager.addLog('切换到新手模式', 'info');
        updateGuidance(1);
    } else {
        novicePanel.style.display = 'none';
        expertPanel.style.display = 'block';
        stateManager.addLog('切换到专家模式', 'info');
        updateGuidance(0);
    }
}

function updateGuidance(step) {
    const guidanceText = document.getElementById('guidance-text');
    const steps = document.querySelectorAll('.guidance-steps .step');
    
    const guidanceMap = {
        0: '欢迎使用专家模式！您可以使用高级配置进行自定义测试。',
        1: '选择一个预设任务模板，或切换到专家模式进行高级配置。',
        2: '点击"连接所有平台"按钮，建立与机器人平台的连接。',
        3: '点击"开始测试"按钮执行选定的测试任务。',
        4: '测试完成后，您可以查看详细结果并导出报告。'
    };
    
    if (guidanceText) {
        guidanceText.textContent = guidanceMap[step] || guidanceMap[1];
    }
    
    steps.forEach((stepEl, index) => {
        if (index <= step) {
            stepEl.classList.add('active');
        } else {
            stepEl.classList.remove('active');
        }
    });
}

function updateSlider(id, value) {
    const slider = document.getElementById(id);
    const displayMap = {
        'gait-frequency': 'frequency-value',
        'stride-length': 'stride-value'
    };
    const valueDisplay = document.getElementById(displayMap[id] || (id + '-value'));

    if (slider) {
        slider.value = value;
    }
    if (valueDisplay) {
        valueDisplay.textContent = value;
    }

    // 触发input事件以更新状态
    if (slider) slider.dispatchEvent(new Event('input'));
}

// 全局控制函数
async function connectAll() {
    stateManager.addLog('正在连接所有平台...', 'info');
    await stateManager.connectWebSocket();
    updateGuidance(3);
}

function startTest() {
    const mode = document.body.dataset.mode;
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    if (!stateManager.websocket) {
        stateManager.addLog('请先连接平台', 'warning');
        return;
    }
    
    let testConfig = {
        command: 'start_test',
        test_id: `test_${Date.now()}`,
        timestamp: new Date().toISOString()
    };
    
    if (mode === 'novice') {
        const selectedTask = document.querySelector('.task-card.selected');
        if (!selectedTask) {
            stateManager.addLog('请先选择一个测试任务', 'warning');
            return;
        }
        
        testConfig.task = selectedTask.dataset.task;
        testConfig.platforms = ['real_robot', 'gazebo'];
        testConfig.preset = 'default';
        
    } else {
        const realChecked = document.getElementById('platform-real-expert').checked;
        const gazeboChecked = document.getElementById('platform-gazebo-expert').checked;
        
        if (!realChecked && !gazeboChecked) {
            stateManager.addLog('请至少选择一个平台', 'warning');
            return;
        }
        
        testConfig.platforms = [];
        if (realChecked) testConfig.platforms.push('real_robot');
        if (gazeboChecked) testConfig.platforms.push('gazebo');
        
        testConfig.config = stateManager.state.configuration;
    }
    
    // 更新按钮状态
    startBtn.disabled = true;
    stopBtn.disabled = false;
    const pauseBtn = document.getElementById('pause-btn');
    if (pauseBtn) pauseBtn.disabled = false;
    
    // 发送测试命令
    stateManager.websocket.send(testConfig);
    stateManager.addLog('测试开始执行', 'success');
}

function stopTest() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    if (!stateManager.websocket) return;
    
    stateManager.websocket.send({
        command: 'stop_test',
        timestamp: new Date().toISOString()
    });
    
    startBtn.disabled = false;
    stopBtn.disabled = true;
}

function pauseTest() {
    const pauseBtn = document.getElementById('pause-btn');
    const isPaused = pauseBtn.textContent.includes('继续');
    
    if (isPaused) {
        pauseBtn.innerHTML = '<span class="btn-icon">⏸️</span>暂停';
        stateManager.addLog('测试继续', 'info');
    } else {
        pauseBtn.innerHTML = '<span class="btn-icon">▶️</span>继续';
        stateManager.addLog('测试暂停', 'warning');
    }
}

function clearLogs() {
    const logContainer = document.getElementById('log-container');
    if (logContainer) {
        logContainer.innerHTML = '';
        stateManager.state.logs = [];
        stateManager.addLog('日志已清空', 'info');
    }
}

function toggleLogs() {
    const logBtn = document.querySelector('.log-controls .log-btn:last-child');
    const isPaused = logBtn.textContent === '继续';
    
    if (isPaused) {
        logBtn.textContent = '暂停';
        stateManager.addLog('日志恢复', 'info');
    } else {
        logBtn.textContent = '继续';
        stateManager.addLog('日志暂停', 'warning');
    }
}

function exportReport() {
    const report = {
        export_time: new Date().toISOString(),
        system_state: stateManager.state,
        test_results: null // 这里可以添加实际的测试结果
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `bruce_test_report_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    stateManager.addLog('报告已导出', 'success');
}

function showDetails() {
    stateManager.showResultsModal({
        test_id: 'demo_test',
        platforms: {
            real_robot: {
                success: true,
                metrics: { latency: 42.5, accuracy: 0.92, stability: 0.94 }
            },
            gazebo: {
                success: true,
                metrics: { latency: 18.2, accuracy: 0.88, stability: 0.91 }
            }
        }
    });
}

function closeModal() {
    const modal = document.getElementById('results-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function loadConfig() {
    // 模拟配置导入
    const config = {
        gait_frequency: 2.5,
        stride_length: 30,
        selected_platforms: ['real_robot', 'gazebo']
    };
    
    updateSlider('gait-frequency', config.gait_frequency);
    updateSlider('stride-length', config.stride_length);
    
    stateManager.addLog('配置已导入', 'success');
}

function exportConfig() {
    const config = stateManager.state.configuration;
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `bruce_config_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    stateManager.addLog('配置已导出', 'success');
}

function showHelp() {
    stateManager.addLog('帮助信息: 请参考用户手册获取详细信息', 'info');
    alert('帮助信息:\n1. 新手模式: 选择预设任务一键测试\n2. 专家模式: 自定义参数进行高级测试\n3. 支持实机和Gazebo并行测试\n4. 测试结果会自动对比并生成报告');
}

function resetSystem() {
    if (confirm('确定要重置系统吗？所有当前状态将被清除。')) {
        location.reload();
    }
}

// 3D模型控制函数
function rotateModel() {
    if (stateManager.robotModel) {
        stateManager.robotModel.rotation.y += Math.PI / 4;
    }
}

function zoomIn() {
    if (stateManager.camera) {
        stateManager.camera.position.z -= 1;
    }
}

function zoomOut() {
    if (stateManager.camera) {
        stateManager.camera.position.z += 1;
    }
}