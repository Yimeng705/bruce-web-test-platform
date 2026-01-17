/**
 * BRUCE机器人测试平台 - 模式切换系统
 * 实现新手模式和专家模式的界面切换和功能差异
 */

class ModeManager {
    constructor() {
        this.currentMode = 'novice'; // 'novice' 或 'expert'
        this.userRole = 'student'; // 'student' 或 'researcher'
        this.currentTask = null;
        this.isSwitching = false;
        
        // 初始化
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateInterface();
        this.setupAssistant();
        this.log('模式管理器已初始化', 'success');
    }
    
    bindEvents() {
        // 模式切换
        document.querySelectorAll('.mode-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode;
                console.log('[ModeManager] mode-option clicked ->', mode);
                this.switchMode(mode);
            });
        });
        
        // 新手模式任务开始
        document.querySelectorAll('.start-template').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const templateCard = e.target.closest('.template-card');
                const templateId = templateCard.dataset.template;
                this.startNoviceTask(templateId);
            });
        });
        
        // 新手模式任务预览
        document.querySelectorAll('.preview-template').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const templateCard = e.target.closest('.template-card');
                const templateId = templateCard.dataset.template;
                this.previewTask(templateId);
            });
        });
        
        // 专家模式脚本运行
        document.getElementById('run-script')?.addEventListener('click', () => {
            this.runExpertScript();
        });
        
        // 专家模式批量测试
        document.getElementById('batch-test')?.addEventListener('click', () => {
            this.openBatchTestConfig();
        });
        
        // 并行在所有选中平台上执行（专家一键并行）
        document.getElementById('start-all-platforms')?.addEventListener('click', () => {
            this.startParallelTests();
        });
        
        // 模态框关闭
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeAllModals();
            });
        });
        
        // 向导控制
        document.getElementById('next-step')?.addEventListener('click', () => {
            this.nextWizardStep();
        });
        
        document.getElementById('prev-step')?.addEventListener('click', () => {
            this.prevWizardStep();
        });
        
        // 快捷工具栏
        document.querySelectorAll('.toolbar-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.handleQuickAction(action);
            });
        });
        
        // 智能助手建议
        document.querySelectorAll('[data-action="suggest-test"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const templateId = btn.dataset.template;
                this.startNoviceTask(templateId);
            });
        });
    }
    
    switchMode(mode) {
        console.log('[ModeManager] switchMode invoked:', mode, 'currentMode=', this.currentMode, 'isSwitching=', this.isSwitching);
        if (this.isSwitching || this.currentMode === mode) {
            console.log('[ModeManager] switch aborted (same mode or switching)');
            return;
        }
        
        this.isSwitching = true;
        
        // 确认切换（如果是专家模式，需要确认）
        if (mode === 'expert') {
            if (!confirm('切换到专家模式将显示高级功能和复杂配置。您确定要切换吗？')) {
                this.isSwitching = false;
                return;
            }
        }
        
        this.showModeTransition(mode);
        
        // 更新当前模式
        setTimeout(() => {
            this.currentMode = mode;
            
            // 更新界面
            this.updateInterface();
            
            // 更新用户角色
            this.userRole = mode === 'novice' ? 'student' : 'researcher';
            
            // 更新模式指示器
            this.updateModeIndicator();
            
            // 记录日志
            this.log(`切换到${mode === 'novice' ? '新手' : '专家'}模式`, 'info');
            
            this.isSwitching = false;
        }, 500);
    }
    
    showModeTransition(newMode) {
        const transition = document.createElement('div');
        transition.className = 'mode-transition';
        transition.innerHTML = `
            <div class="transition-content">
                <div class="transition-icon">
                    <i class="fas fa-${newMode === 'novice' ? 'graduation-cap' : 'cogs'}"></i>
                </div>
                <div class="transition-text">
                    正在切换到${newMode === 'novice' ? '新手' : '专家'}模式...
                </div>
                <div class="transition-progress"></div>
            </div>
        `;
        
        document.body.appendChild(transition);
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            .mode-transition {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: var(--bg-primary);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                animation: fadeIn 0.3s ease;
            }
            
            .transition-content {
                text-align: center;
                max-width: 300px;
            }
            
            .transition-icon {
                font-size: 64px;
                color: var(--primary-color);
                margin-bottom: 20px;
                animation: bounce 1s infinite;
            }
            
            .transition-text {
                font-size: 18px;
                color: var(--text-primary);
                margin-bottom: 20px;
            }
            
            .transition-progress {
                width: 200px;
                height: 4px;
                background: var(--border-color);
                border-radius: 2px;
                overflow: hidden;
                position: relative;
            }
            
            .transition-progress::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                width: 100%;
                background: var(--primary-color);
                animation: progressBar 0.5s linear;
            }
            
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            
            @keyframes progressBar {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(0); }
            }
        `;
        
        document.head.appendChild(style);
        
        // 移除过渡效果
        setTimeout(() => {
            transition.remove();
            style.remove();
        }, 500);
    }
    
    updateInterface() {
        // 更新主内容区的data-mode属性
        const mainContent = document.querySelector('.main-content');
        if (!mainContent) return;

        // 如果主视图被替换（例如并行对比视图），优先尝试恢复备份内容
        if (!mainContent.querySelector('.novice-interface') && !mainContent.querySelector('.expert-interface')) {
            if (this._savedMainContent) {
                mainContent.innerHTML = this._savedMainContent;
                this._savedMainContent = null;
                // 重新绑定事件到恢复的 DOM
                this.bindEvents();
            } else {
                // 没有可恢复内容，跳过界面切换以避免异常
                console.warn('[ModeManager] updateInterface: 模式界面不存在，跳过更新。');
                return;
            }
        }

        mainContent.setAttribute('data-mode', this.currentMode);
        
        // 更新导航栏模式选项
        document.querySelectorAll('.mode-option').forEach(option => {
            option.classList.toggle('active', option.dataset.mode === this.currentMode);
        });
        
        // 显示/隐藏界面
        document.querySelectorAll('.novice-interface, .expert-interface').forEach(el => {
            el.classList.remove('active');
        });
        
        if (this.currentMode === 'novice') {
            document.querySelector('.novice-interface').classList.add('active');
        } else {
            document.querySelector('.expert-interface').classList.add('active');
        }
        
        // 更新用户信息
        const userModeElement = document.getElementById('current-mode');
        if (userModeElement) {
            userModeElement.textContent = this.currentMode === 'novice' ? '新手模式' : '专家模式';
        }
        
        // 更新快捷工具栏
        this.updateQuickToolbar();
        
        // 更新任务流指示器（专家模式显示更多步骤）
        this.updateTaskFlowIndicator();
    }
    
    updateModeIndicator() {
        const indicators = document.querySelectorAll('.mode-indicator');
        if (!indicators || indicators.length === 0) return;

        indicators.forEach(indicator => {
            const dot = indicator.querySelector('.indicator-dot');
            const text = indicator.querySelector('.indicator-text');

            if (dot) dot.style.background = this.currentMode === 'novice' ? 'var(--primary-color)' : 'var(--expert-primary)';
            if (text) text.textContent = this.currentMode === 'novice' ? '新手模式' : '专家模式';
        });
    }
    
    updateQuickToolbar() {
        // 根据模式更新快捷工具栏按钮
        if (this.currentMode === 'novice') {
            // 新手模式按钮
            document.querySelector('[data-action="new-test"] i').className = 'fas fa-plus';
            document.querySelector('[data-action="new-test"] span').textContent = '新建';
            
            document.querySelector('[data-action="run-test"] i').className = 'fas fa-play';
            document.querySelector('[data-action="run-test"] span').textContent = '运行';
        } else {
            // 专家模式按钮
            document.querySelector('[data-action="new-test"] i').className = 'fas fa-file-code';
            document.querySelector('[data-action="new-test"] span').textContent = '新建脚本';
            
            document.querySelector('[data-action="run-test"] i').className = 'fas fa-bolt';
            document.querySelector('[data-action="run-test"] span').textContent = '快速执行';
        }
    }
    
    updateTaskFlowIndicator() {
        const steps = document.querySelectorAll('.flow-step');
        
        if (this.currentMode === 'novice') {
            // 新手模式：简化步骤
            steps.forEach((step, index) => {
                const stepNum = index + 1;
                const stepLabel = step.querySelector('.step-label');
                
                if (stepNum === 1) stepLabel.textContent = '选择模板';
                if (stepNum === 2) stepLabel.textContent = '自动配置';
                if (stepNum === 3) stepLabel.textContent = '执行测试';
                if (stepNum === 4) stepLabel.textContent = '查看报告';
            });
        } else {
            // 专家模式：详细步骤
            steps.forEach((step, index) => {
                const stepNum = index + 1;
                const stepLabel = step.querySelector('.step-label');
                
                if (stepNum === 1) stepLabel.textContent = '创建项目';
                if (stepNum === 2) stepLabel.textContent = '参数配置';
                if (stepNum === 3) stepLabel.textContent = '平台设置';
                if (stepNum === 4) stepLabel.textContent = '执行与分析';
            });
        }
    }
    
    async startNoviceTask(templateId) {
        if (!this.validateNoviceTask(templateId)) return;
        
        // 获取模板信息
        const template = this.getTemplateInfo(templateId);
        if (!template) return;
        
        // 显示配置向导
        await this.showNoviceWizard(template);
    }
    
    validateNoviceTask(templateId) {
        // 检查系统连接状态
        const realStatus = document.querySelector('.real-robot .status-dot').classList.contains('online');
        
        if (!realStatus) {
            alert('实机机器人未连接，请先连接机器人再开始测试。');
            return false;
        }
        
        return true;
    }
    
    getTemplateInfo(templateId) {
        const templates = {
            'walking-test': {
                name: '步态稳定性测试',
                description: '验证机器人在平地和斜坡上的行走稳定性',
                duration: 120,
                platforms: ['real'],
                autoConfig: true,
                parameters: {
                    speed: 'normal',
                    terrain: 'flat',
                    safety: 'high'
                }
            },
            'joint-calibration': {
                name: '关节校准测试',
                description: '自动校准机器人所有关节的零点和极限位置',
                duration: 60,
                platforms: ['real'],
                autoConfig: true,
                parameters: {
                    calibrationType: 'full',
                    precision: 'high',
                    saveConfig: true
                }
            },
            'safety-check': {
                name: '安全功能测试',
                description: '验证紧急停止、碰撞检测等安全功能',
                duration: 90,
                platforms: ['real'],
                autoConfig: true,
                parameters: {
                    testEmergencyStop: true,
                    testCollisionDetection: true,
                    testOverloadProtection: true
                }
            }
        };
        
        return templates[templateId];
    }
    
    async showNoviceWizard(template) {
        // 打开向导模态框
        const modal = document.getElementById('wizard-modal');
        modal.style.display = 'flex';
        
        // 重置向导
        this.resetWizard();
        
        // 显示第一步
        this.showWizardStep(1, template);
        
        // 设置向导完成回调
        modal.querySelector('#finish-wizard').onclick = () => {
            this.finishNoviceConfiguration(template);
        };
    }
    
    resetWizard() {
        const steps = document.querySelectorAll('.progress-step');
        steps.forEach((step, index) => {
            step.classList.toggle('active', index === 0);
        });
        
        document.getElementById('prev-step').style.display = 'none';
        document.getElementById('next-step').style.display = 'flex';
        document.getElementById('finish-wizard').style.display = 'none';
    }
    
    showWizardStep(stepNum, template) {
        const content = document.getElementById('wizard-content');
        
        switch(stepNum) {
            case 1:
                content.innerHTML = this.getWizardStep1(template);
                break;
            case 2:
                content.innerHTML = this.getWizardStep2(template);
                break;
            case 3:
                content.innerHTML = this.getWizardStep3(template);
                break;
            case 4:
                content.innerHTML = this.getWizardStep4(template);
                break;
        }
        
        // 更新进度条
        const steps = document.querySelectorAll('.progress-step');
        steps.forEach((step, index) => {
            step.classList.toggle('active', index === stepNum - 1);
        });
        
        // 更新按钮状态
        document.getElementById('prev-step').style.display = stepNum > 1 ? 'flex' : 'none';
        document.getElementById('next-step').style.display = stepNum < 4 ? 'flex' : 'none';
        document.getElementById('finish-wizard').style.display = stepNum === 4 ? 'flex' : 'none';
    }
    
    getWizardStep1(template) {
        return `
            <div class="wizard-step-content">
                <h3>任务确认</h3>
                <p>请确认您要执行的测试任务：</p>
                
                <div class="task-confirm-card">
                    <div class="task-icon">
                        <i class="fas fa-${template.name.includes('步态') ? 'walking' : 'cogs'}"></i>
                    </div>
                    <div class="task-info">
                        <h4>${template.name}</h4>
                        <p>${template.description}</p>
                        <div class="task-details">
                            <div class="detail">
                                <i class="far fa-clock"></i>
                                <span>预计耗时: ${template.duration}秒</span>
                            </div>
                            <div class="detail">
                                <i class="fas fa-robot"></i>
                                <span>测试平台: 实机机器人</span>
                            </div>
                            <div class="detail">
                                <i class="fas fa-shield-alt"></i>
                                <span>安全模式: 已启用</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="wizard-note">
                    <i class="fas fa-info-circle"></i>
                    <p>系统将自动为您配置所有参数并执行安全检查。</p>
                </div>
            </div>
        `;
    }
    
    getWizardStep2(template) {
        return `
            <div class="wizard-step-content">
                <h3>平台检查</h3>
                <p>正在检查测试平台状态...</p>
                
                <div class="platform-check-list">
                    <div class="platform-check">
                        <div class="check-status success">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="check-info">
                            <h4>实机机器人</h4>
                            <p>连接正常，电池电量充足</p>
                        </div>
                        <div class="check-details">
                            <span class="detail">电量: 85%</span>
                            <span class="detail">温度: 32°C</span>
                        </div>
                    </div>
                    
                    <div class="platform-check">
                        <div class="check-status warning">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="check-info">
                            <h4>Gazebo仿真</h4>
                            <p>未连接（可选）</p>
                        </div>
                    </div>
                </div>
                
                <div class="safety-check">
                    <h4>安全检查</h4>
                    <div class="check-items">
                        <div class="check-item success">
                            <i class="fas fa-check"></i>
                            <span>紧急停止功能正常</span>
                        </div>
                        <div class="check-item success">
                            <i class="fas fa-check"></i>
                            <span>碰撞检测已启用</span>
                        </div>
                        <div class="check-item success">
                            <i class="fas fa-check"></i>
                            <span>关节限位正常</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getWizardStep3(template) {
        return `
            <div class="wizard-step-content">
                <h3>参数配置</h3>
                <p>系统已为您自动配置了推荐的参数：</p>
                
                <div class="auto-configuration">
                    <div class="config-card">
                        <h4><i class="fas fa-cogs"></i> 运动参数</h4>
                        <div class="config-details">
                            <div class="config-item">
                                <span class="label">行走速度</span>
                                <span class="value">中等速度</span>
                            </div>
                            <div class="config-item">
                                <span class="label">测试地形</span>
                                <span class="value">平地</span>
                            </div>
                            <div class="config-item">
                                <span class="label">采样频率</span>
                                <span class="value">100Hz</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="config-card">
                        <h4><i class="fas fa-shield-alt"></i> 安全设置</h4>
                        <div class="config-details">
                            <div class="config-item">
                                <span class="label">最大速度限制</span>
                                <span class="value">70%</span>
                            </div>
                            <div class="config-item">
                                <span class="label">碰撞检测</span>
                                <span class="value">已启用</span>
                            </div>
                            <div class="config-item">
                                <span class="label">紧急停止距离</span>
                                <span class="value">0.5m</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="wizard-note info">
                    <i class="fas fa-lightbulb"></i>
                    <p>这些参数是系统推荐的优化值，适合大多数测试场景。</p>
                </div>
            </div>
        `;
    }
    
    getWizardStep4(template) {
        return `
            <div class="wizard-step-content">
                <h3>准备开始</h3>
                <p>所有配置已完成，准备开始测试：</p>
                
                <div class="final-check">
                    <div class="check-summary">
                        <div class="summary-item success">
                            <i class="fas fa-check-circle"></i>
                            <div>
                                <h4>配置验证通过</h4>
                                <p>所有参数配置正确</p>
                            </div>
                        </div>
                        <div class="summary-item success">
                            <i class="fas fa-check-circle"></i>
                            <div>
                                <h4>安全检查通过</h4>
                                <p>所有安全功能正常</p>
                            </div>
                        </div>
                        <div class="summary-item success">
                            <i class="fas fa-check-circle"></i>
                            <div>
                                <h4>平台准备就绪</h4>
                                <p>实机机器人已连接</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="test-preview">
                        <h4>测试预览</h4>
                        <ul class="test-steps">
                            <li><i class="fas fa-play"></i> 初始化机器人</li>
                            <li><i class="fas fa-walking"></i> 执行步态测试</li>
                            <li><i class="fas fa-chart-line"></i> 收集性能数据</li>
                            <li><i class="fas fa-file-alt"></i> 生成测试报告</li>
                        </ul>
                    </div>
                </div>
                
                <div class="wizard-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>测试过程中请保持安全距离，随时准备使用紧急停止按钮。</p>
                </div>
            </div>
        `;
    }
    
    nextWizardStep() {
        const currentStep = this.getCurrentWizardStep();
        if (currentStep < 4) {
            this.showWizardStep(currentStep + 1);
        }
    }
    
    prevWizardStep() {
        const currentStep = this.getCurrentWizardStep();
        if (currentStep > 1) {
            this.showWizardStep(currentStep - 1);
        }
    }
    
    getCurrentWizardStep() {
        const activeStep = document.querySelector('.progress-step.active');
        const steps = document.querySelectorAll('.progress-step');
        return Array.from(steps).indexOf(activeStep) + 1;
    }
    
    finishNoviceConfiguration(template) {
        // 关闭向导
        this.closeAllModals();
        
        // 开始测试
        this.executeNoviceTest(template);
    }
    
    async executeNoviceTest(template) {
        // 更新任务流指示器
        this.updateFlowStep(3);
        
        // 显示测试执行界面
        this.showTestExecution(template);
        
        // 模拟测试执行
        await this.simulateTestExecution(template);
        
        // 测试完成
        this.showTestResults(template);
    }
    
    updateFlowStep(stepNum) {
        const steps = document.querySelectorAll('.flow-step');
        steps.forEach((step, index) => {
            step.classList.toggle('active', index === stepNum - 1);
        });
    }
    
    showTestExecution(template) {
        // 创建测试执行视图
        const executionView = document.createElement('div');
        executionView.className = 'test-execution-view';
        executionView.innerHTML = `
            <div class="execution-header">
                <h2><i class="fas fa-play-circle"></i> 测试执行中...</h2>
                <div class="execution-timer">00:00</div>
            </div>
            
            <div class="execution-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-text">正在初始化...</div>
            </div>
            
            <div class="execution-details">
                <div class="detail-card">
                    <h4><i class="fas fa-robot"></i> 实机状态</h4>
                    <div class="status-indicator online">
                        <i class="fas fa-circle"></i> 运行中
                    </div>
                </div>
                
                <div class="detail-card">
                    <h4><i class="fas fa-tasks"></i> 当前步骤</h4>
                    <div class="current-step">初始化机器人...</div>
                </div>
                
                <div class="detail-card">
                    <h4><i class="fas fa-chart-line"></i> 实时数据</h4>
                    <div class="real-time-data">
                        <div class="data-item">
                            <span>关节温度</span>
                            <span class="value">32°C</span>
                        </div>
                        <div class="data-item">
                            <span>电池电压</span>
                            <span class="value">24.3V</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="execution-controls">
                <button class="btn btn-danger" id="emergency-stop-btn">
                    <i class="fas fa-stop-circle"></i> 紧急停止
                </button>
            </div>
        `;
        
        // 插入到主内容区
        const mainContent = document.querySelector('.main-content');
        mainContent.innerHTML = '';
        mainContent.appendChild(executionView);
        
        // 绑定紧急停止按钮
        document.getElementById('emergency-stop-btn').addEventListener('click', () => {
            this.emergencyStopTest();
        });
        
        // 启动 Gazebo 按钮（示例行为：标记为在线并提示）
        document.getElementById('start-gazebo')?.addEventListener('click', () => {
            const gazeboCard = document.querySelector('.platform-card[data-platform="gazebo"]');
            if (gazeboCard) {
                const status = gazeboCard.querySelector('.platform-status');
                status.classList.remove('offline');
                status.classList.add('online');
                status.querySelector('span').textContent = '在线';
                const checkbox = gazeboCard.querySelector('.platform-enable');
                if (checkbox) checkbox.checked = true;
                this.showNotification('Gazebo仿真已启动并连接', 'success');
            }
        });
    }
    
    async simulateTestExecution(template) {
        const steps = [
            { name: '初始化机器人', duration: 2000 },
            { name: '安全自检', duration: 1500 },
            { name: '关节预热', duration: 3000 },
            { name: '执行步态测试', duration: 5000 },
            { name: '数据收集', duration: 2000 },
            { name: '生成报告', duration: 1000 }
        ];
        
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            
            // 更新进度
            const progress = ((i + 1) / steps.length) * 100;
            const progressFill = document.querySelector('.progress-fill');
            const progressText = document.querySelector('.progress-text');
            const currentStep = document.querySelector('.current-step');
            const timer = document.querySelector('.execution-timer');
            
            if (progressFill) progressFill.style.width = `${progress}%`;
            if (progressText) progressText.textContent = step.name;
            if (currentStep) currentStep.textContent = step.name;
            
            // 更新计时器
            const totalSeconds = (i + 1) * 2;
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            if (timer) timer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // 等待步骤完成
            await this.delay(step.duration);
        }
        
        // 更新任务流指示器
        this.updateFlowStep(4);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    showTestResults(template) {
        // 创建结果视图
        const resultsView = document.createElement('div');
        resultsView.className = 'test-results-view';
        resultsView.innerHTML = `
            <div class="results-header">
                <h2><i class="fas fa-check-circle"></i> 测试完成！</h2>
                <div class="results-badge success">测试通过</div>
            </div>
            
            <div class="results-summary">
                <div class="summary-card">
                    <div class="summary-icon">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <div class="summary-content">
                        <h3>${template.name}</h3>
                        <p>测试执行成功，所有指标均达标</p>
                        
                        <div class="summary-metrics">
                            <div class="metric">
                                <span class="label">成功率</span>
                                <span class="value success">98.5%</span>
                            </div>
                            <div class="metric">
                                <span class="label">执行时间</span>
                                <span class="value">2分15秒</span>
                            </div>
                            <div class="metric">
                                <span class="label">能耗</span>
                                <span class="value">245W</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="results-actions">
                <button class="btn btn-primary" id="view-report">
                    <i class="fas fa-file-alt"></i> 查看详细报告
                </button>
                <button class="btn btn-secondary" id="back-to-templates">
                    <i class="fas fa-arrow-left"></i> 返回模板选择
                </button>
                <button class="btn btn-success" id="run-again">
                    <i class="fas fa-redo"></i> 再次运行
                </button>
            </div>
        `;
        
        // 插入到主内容区
        const mainContent = document.querySelector('.main-content');
        mainContent.innerHTML = '';
        mainContent.appendChild(resultsView);
        
        // 绑定结果按钮
        document.getElementById('view-report').addEventListener('click', () => {
            this.viewDetailedReport(template);
        });
        
        document.getElementById('back-to-templates').addEventListener('click', () => {
            this.resetToNoviceInterface();
        });
        
        document.getElementById('run-again').addEventListener('click', () => {
            this.executeNoviceTest(template);
        });
    }

    // 并行在选中平台上运行测试并展示对比结果（演示用模拟数据）
    async startParallelTests() {
        // 收集选中的平台
        const platformCards = Array.from(document.querySelectorAll('.platform-card'));
        const selected = platformCards.filter(card => card.querySelector('.platform-enable')?.checked);

        if (selected.length === 0) {
            this.showNotification('请至少选择一个平台用于并行测试', 'warning');
            return;
        }

        // 使用当前任务或默认模板作为演示
        const templateId = this.currentTask || 'walking-test';
        const template = this.getTemplateInfo(templateId) || this.getTemplateInfo('walking-test');

        this.showNotification('正在在所选平台上并行启动测试...', 'info');
        this.updateFlowStep(3);

        const platformIds = selected.map(card => card.dataset.platform || card.getAttribute('data-platform'));

        const results = await this.simulateParallelRuns(template, platformIds);

        // 显示对比结果
        this.showComparisonResults(template, results);
    }

    // 模拟并行运行，多平台返回不同的性能指标
    async simulateParallelRuns(template, platforms) {
        const tasks = platforms.map(async (platformId) => {
            // 每个平台有不同的模拟时长与随机结果
            const base = platformId === 'real-robot' ? 1.0 : 0.9;
            const execTime = 5000 + Math.floor(Math.random() * 4000);
            await this.delay(execTime);

            const metrics = {
                platform: platformId,
                successRate: +(90 + Math.random() * 10 * base).toFixed(1),
                stability: +(80 + Math.random() * 15 * base).toFixed(1),
                energy: +(200 + Math.random() * 100 / base).toFixed(0),
                durationSec: Math.round((execTime / 1000) * (1 / base))
            };

            return metrics;
        });

        const results = await Promise.all(tasks);
        return results;
    }

    // 在主视图中展示并行测试对比（包含 ECharts 图表）
    showComparisonResults(template, results) {
        const mainContent = document.querySelector('.main-content');
        // 备份主内容（用于返回时恢复原始界面）
        try {
            this._savedMainContent = mainContent.innerHTML;
        } catch (e) {
            this._savedMainContent = null;
        }
        mainContent.innerHTML = '';

        const view = document.createElement('div');
        view.className = 'comparison-view';
        view.innerHTML = `
            <div class="results-header">
                <h2><i class="fas fa-exchange-alt"></i> 并行测试对比</h2>
                <div class="results-badge info">${template.name}</div>
            </div>
            <div style="display:flex;gap:20px;align-items:flex-start;">
                <div style="flex:1;min-height:300px;" id="comparison-chart"></div>
                <div style="width:360px;">
                    <div class="summary-card">
                        <h4>对比摘要</h4>
                        <div class="summary-list"></div>
                        <div style="margin-top:16px;display:flex;gap:12px;justify-content:flex-end;">
                            <button class="btn btn-secondary" id="back-to-templates-2">返回模板</button>
                            <button class="btn btn-primary" id="view-compare-report">查看对比报告</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        mainContent.appendChild(view);

        // 填充摘要列表
        const list = view.querySelector('.summary-list');
        results.forEach(r => {
            const node = document.createElement('div');
            node.style.padding = '8px 0';
            node.innerHTML = `
                <strong>${r.platform}</strong>
                <div>成功率: <span style="color:var(--success-color);">${r.successRate}%</span></div>
                <div>稳定性: ${r.stability}%</div>
                <div>能耗: ${r.energy}W</div>
                <div>耗时: ${r.durationSec}s</div>
            `;
            list.appendChild(node);
        });

        // 初始化 ECharts
        try {
            const chartDom = document.getElementById('comparison-chart');
            const myChart = echarts.init(chartDom);
            const categories = results.map(r => r.platform);
            const successSeries = results.map(r => r.successRate);
            const stabilitySeries = results.map(r => r.stability);

            const option = {
                tooltip: { trigger: 'axis' },
                legend: { data: ['成功率', '稳定性'] },
                xAxis: { type: 'category', data: categories },
                yAxis: { type: 'value' },
                series: [
                    { name: '成功率', type: 'bar', data: successSeries, itemStyle: { color: 'var(--primary-color)' } },
                    { name: '稳定性', type: 'line', data: stabilitySeries, itemStyle: { color: 'var(--expert-primary)' } }
                ]
            };

            myChart.setOption(option);
        } catch (e) {
            console.warn('ECharts 初始化失败：', e);
        }

        // 绑定按钮
        document.getElementById('back-to-templates-2').addEventListener('click', () => this.resetToNoviceInterface());
        document.getElementById('view-compare-report').addEventListener('click', () => {
            // 生成简单对比报告并下载
            let content = `并行测试对比报告 - ${template.name}\n生成时间：${new Date().toLocaleString()}\n\n`;
            results.forEach(r => {
                content += `平台: ${r.platform}\n 成功率: ${r.successRate}%\n 稳定性: ${r.stability}%\n 能耗: ${r.energy}W\n 耗时: ${r.durationSec}s\n\n`;
            });
            this.downloadTextFile(content, `${template.name}_并行对比报告.txt`);
            this.showNotification('对比报告已生成并下载', 'success');
        });
    }
    
    previewTask(templateId) {
        const template = this.getTemplateInfo(templateId);
        if (!template) return;
        
        const modal = document.getElementById('preview-modal');
        const content = document.getElementById('preview-content');
        
        content.innerHTML = `
            <div class="preview-container">
                <div class="preview-header">
                    <div class="preview-icon">
                        <i class="fas fa-${template.name.includes('步态') ? 'walking' : 'cogs'}"></i>
                    </div>
                    <div class="preview-title">
                        <h3>${template.name}</h3>
                        <p>${template.description}</p>
                    </div>
                </div>
                
                <div class="preview-details">
                    <div class="detail-section">
                        <h4><i class="fas fa-list-ol"></i> 测试步骤</h4>
                        <ol class="test-steps">
                            <li>系统自动进行安全检查</li>
                            <li>初始化机器人关节位置</li>
                            <li>执行预设测试动作序列</li>
                            <li>收集实时性能数据</li>
                            <li>生成测试报告</li>
                        </ol>
                    </div>
                    
                    <div class="detail-section">
                        <h4><i class="fas fa-chart-bar"></i> 输出结果</h4>
                        <ul class="output-list">
                            <li><i class="fas fa-check-circle"></i> 性能指标评分</li>
                            <li><i class="fas fa-check-circle"></i> 稳定性分析图表</li>
                            <li><i class="fas fa-check-circle"></i> 详细测试报告</li>
                            <li><i class="fas fa-check-circle"></i> 改进建议</li>
                        </ul>
                    </div>
                    
                    <div class="detail-section">
                        <h4><i class="fas fa-shield-alt"></i> 安全特性</h4>
                        <div class="safety-features">
                            <div class="feature">
                                <i class="fas fa-check-circle"></i>
                                <span>自动安全检查</span>
                            </div>
                            <div class="feature">
                                <i class="fas fa-check-circle"></i>
                                <span>紧急停止保护</span>
                            </div>
                            <div class="feature">
                                <i class="fas fa-check-circle"></i>
                                <span>碰撞检测</span>
                            </div>
                            <div class="feature">
                                <i class="fas fa-check-circle"></i>
                                <span>过热保护</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="preview-requirements">
                    <div class="requirement">
                        <i class="fas fa-clock"></i>
                        <div>
                            <strong>预计时间</strong>
                            <p>${template.duration}秒</p>
                        </div>
                    </div>
                    <div class="requirement">
                        <i class="fas fa-robot"></i>
                        <div>
                            <strong>所需平台</strong>
                            <p>实机机器人</p>
                        </div>
                    </div>
                    <div class="requirement">
                        <i class="fas fa-cogs"></i>
                        <div>
                            <strong>配置方式</strong>
                            <p>自动配置</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        modal.style.display = 'flex';
        
        // 绑定开始测试按钮
        document.getElementById('confirm-start').onclick = () => {
            modal.style.display = 'none';
            this.startNoviceTask(templateId);
        };
        
        document.getElementById('close-preview').onclick = () => {
            modal.style.display = 'none';
        };
    }
    
    runExpertScript() {
        const editor = document.getElementById('code-editor');
        const consoleOutput = document.getElementById('console-output');
        
        if (!editor.value.trim()) {
            this.showConsoleMessage('请先输入测试脚本！', 'warning');
            return;
        }
        
        // 模拟脚本执行
        this.showConsoleMessage('开始执行脚本...', 'info');
        this.showConsoleMessage('初始化机器人连接...', 'info');
        this.showConsoleMessage('执行测试序列...', 'info');
        
        setTimeout(() => {
            this.showConsoleMessage('脚本执行完成！', 'success');
            this.showConsoleMessage('生成测试报告...', 'info');
            this.showConsoleMessage('数据导出完成！', 'success');
        }, 2000);
        
        // 更新任务流指示器
        this.updateFlowStep(3);
    }
    
    showConsoleMessage(message, type = 'info') {
        const consoleOutput = document.getElementById('console-output');
        const time = new Date().toLocaleTimeString();
        const messageClass = type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'info';
        
        const messageElement = document.createElement('div');
        messageElement.className = `console-message ${messageClass}`;
        messageElement.innerHTML = `<span class="time">[${time}]</span> ${message}`;
        
        consoleOutput.appendChild(messageElement);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
    
    openBatchTestConfig() {
        const modal = document.getElementById('batch-modal');
        modal.style.display = 'flex';
    }
    
    handleQuickAction(action) {
        switch(action) {
            case 'new-test':
                if (this.currentMode === 'novice') {
                    this.resetToNoviceInterface();
                } else {
                    // 专家模式：新建脚本
                    document.getElementById('code-editor').value = '# 新建测试脚本\n# 在这里输入您的代码';
                    this.showConsoleMessage('创建新的测试脚本', 'info');
                }
                break;
                
            case 'quick-save':
                this.saveCurrentConfig();
                break;
                
            case 'run-test':
                if (this.currentMode === 'novice') {
                    alert('请先选择一个测试模板');
                } else {
                    this.runExpertScript();
                }
                break;
                
            case 'stop-test':
                this.emergencyStopTest();
                break;
                
            case 'export-data':
                this.exportTestData();
                break;
        }
    }
    
    saveCurrentConfig() {
        const message = this.currentMode === 'novice' 
            ? '当前配置已自动保存' 
            : '项目配置已保存到本地';
        
        this.showNotification(message, 'success');
    }
    
    emergencyStopTest() {
        if (confirm('确定要紧急停止当前测试吗？')) {
            this.showNotification('测试已紧急停止', 'warning');
            this.resetToNoviceInterface();
        }
    }
    
    exportTestData() {
        this.showNotification('数据导出中...', 'info');
        
        setTimeout(() => {
            this.showNotification('数据导出完成！', 'success');
        }, 1000);
    }
    
    resetToNoviceInterface() {
        // 重新加载新手界面
        const mainContent = document.querySelector('.main-content');
        // 如果主视图已被替换（例如并行对比视图），恢复备份的内容并重新绑定事件
        if (mainContent && !mainContent.querySelector('.novice-interface') && this._savedMainContent) {
            mainContent.innerHTML = this._savedMainContent;
            // 清除备份以避免重复恢复
            this._savedMainContent = null;
            // 重新绑定事件到新恢复的 DOM 元素
            this.bindEvents();
        }

        this.currentMode = 'novice';
        this.updateInterface();
        this.updateFlowStep(1);
    }
    
    viewDetailedReport(template) {
        // 在实际应用中，这里会打开详细的报告页面
        this.showNotification('正在生成详细报告...', 'info');
        
        setTimeout(() => {
            // 模拟报告生成
            const reportContent = `
                测试报告：${template.name}
                生成时间：${new Date().toLocaleString()}
                测试结果：通过
                成功率：98.5%
                执行时间：2分15秒
                能耗：245W
                稳定性评分：92/100
            `;
            
            // 下载报告
            this.downloadTextFile(reportContent, `${template.name}_报告.txt`);
            this.showNotification('报告已生成并下载', 'success');
        }, 1500);
    }
    
    downloadTextFile(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            </div>
            <div class="notification-content">${message}</div>
            <button class="notification-close">&times;</button>
        `;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 添加样式
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--bg-surface);
                    border: 1px solid var(--border-color);
                    border-radius: var(--radius-md);
                    padding: 16px 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    box-shadow: var(--shadow-lg);
                    z-index: 10000;
                    animation: slideInRight 0.3s ease;
                    max-width: 400px;
                }
                
                .notification.success {
                    border-left: 4px solid var(--success-color);
                }
                
                .notification.error {
                    border-left: 4px solid var(--danger-color);
                }
                
                .notification.warning {
                    border-left: 4px solid var(--warning-color);
                }
                
                .notification.info {
                    border-left: 4px solid var(--info-color);
                }
                
                .notification-icon {
                    font-size: 20px;
                }
                
                .notification.success .notification-icon {
                    color: var(--success-color);
                }
                
                .notification.error .notification-icon {
                    color: var(--danger-color);
                }
                
                .notification.warning .notification-icon {
                    color: var(--warning-color);
                }
                
                .notification.info .notification-icon {
                    color: var(--info-color);
                }
                
                .notification-content {
                    flex: 1;
                    font-size: 14px;
                    color: var(--text-primary);
                }
                
                .notification-close {
                    background: transparent;
                    border: none;
                    color: var(--text-secondary);
                    font-size: 20px;
                    cursor: pointer;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                }
                
                .notification-close:hover {
                    background: var(--bg-secondary);
                }
                
                @keyframes slideInRight {
                    from {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // 绑定关闭按钮
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        });
        
        // 自动消失
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    setupAssistant() {
        // 智能助手消息轮播
        const messages = [
            "您好！我是BRUCE助手，随时为您提供帮助。",
            "建议从'步态稳定性测试'开始，这是最常用的入门测试。",
            "切换到专家模式可以获得更多高级功能和自定义选项。",
            "测试前请确保机器人有足够的电量和安全空间。",
            "您可以使用批量测试功能同时运行多个测试任务。"
        ];
        
        let messageIndex = 0;
        
        setInterval(() => {
            const assistantMessages = document.getElementById('assistant-messages');
            if (assistantMessages && this.currentMode === 'novice') {
                const newMessage = document.createElement('div');
                newMessage.className = 'message bot';
                newMessage.innerHTML = `<p>${messages[messageIndex]}</p>`;
                
                assistantMessages.appendChild(newMessage);
                assistantMessages.scrollTop = assistantMessages.scrollHeight;
                
                messageIndex = (messageIndex + 1) % messages.length;
            }
        }, 30000);
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    log(message, level = 'info') {
        console.log(`[${level.toUpperCase()}] ${new Date().toLocaleTimeString()} - ${message}`);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const modeManager = new ModeManager();
    window.modeManager = modeManager; // 暴露到全局
    
    console.log('BRUCE机器人测试平台已启动');
    modeManager.log('系统初始化完成', 'success');
    
    // 初始消息
    setTimeout(() => {
        modeManager.showNotification('欢迎使用BRUCE机器人测试平台！', 'info');
    }, 1000);
});