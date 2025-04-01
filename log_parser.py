import re
import os
from datetime import datetime, timedelta

# 进度阶段与关键词的映射
PROGRESS_STAGES = [
    {"keyword": "开始注册账号", "message": "开始注册账号", "percentage": 10},
    {"keyword": "正在填写个人信息", "message": "正在填写个人信息", "percentage": 20},
    {"keyword": "提交个人信息", "message": "提交个人信息", "percentage": 30},
    {"keyword": "正在检测 Turnstile 验证", "message": "正在检测Turnstile验证", "percentage": 40},
    {"keyword": "成功获取验证码", "message": "成功获取验证码", "percentage": 50},
    {"keyword": "验证码输入完成", "message": "验证码输入完成", "percentage": 60},
    {"keyword": "账号注册流程完成", "message": "账号注册流程完成", "percentage": 70},
    {"keyword": "获取Cookie中", "message": "获取Cookie中", "percentage": 80},
    {"keyword": "成功获取会话Token", "message": "成功获取会话Token", "percentage": 90},
    {"keyword": "注册流程完成", "message": "注册流程完成", "percentage": 100},
]

class LogParser:
    def __init__(self, log_file="app.log"):
        self.log_file = log_file
        self.last_position = 0
        self.current_stage = {"stage": 0, "message": "等待开始...", "percentage": 0}
        self.max_stage_reached = 0  # 记录最高阶段
        self.last_process_time = datetime.now()  # 记录上次处理时间
        self.registration_start_time = None  # 添加注册开始时间记录
        self.current_task_id = None  # 添加当前任务ID
        
    def parse_latest_logs(self):
        """解析最新的日志文件获取注册进度"""
        if not os.path.exists(self.log_file):
            return self.current_stage
            
        try:
            # 获取文件大小
            file_size = os.path.getsize(self.log_file)
            
            # 如果文件变小了(可能被轮转)，重置位置
            if file_size < self.last_position:
                self.last_position = 0
                
            # 检查是否有新内容
            if file_size <= self.last_position:
                return self.current_stage
                
            # 只读取新的内容
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = file_size
            
            # 解析新内容的每一行
            for line in new_content.splitlines():
                # 提取日志时间戳和内容
                timestamp, level, message = self._extract_log_parts(line)
                if not timestamp:
                    continue
                    
                # 严格按照任务开始时间过滤日志
                # 如果有注册开始时间，仅处理该时间点之后的日志
                if self.registration_start_time and timestamp < self.registration_start_time:
                    continue
                    
                # 检查每行日志中的进度关键词
                self._check_progress_keywords(message)
            
            # 更新最后处理时间
            self.last_process_time = datetime.now()
            return self.current_stage
            
        except Exception as e:
            print(f"解析日志错误: {str(e)}")
            return self.current_stage
    
    def _extract_log_parts(self, log_line):
        """从日志行中提取时间戳、级别和消息内容"""
        log_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (.+)'
        match = re.match(log_pattern, log_line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S'), level, message
            except ValueError:
                return None, None, None
        return None, None, None
    
    def _reset_current_task(self, timestamp):
        """重置当前任务的状态"""
        self.current_stage = {"stage": 0, "message": "注册任务已启动", "percentage": 0}
        self.max_stage_reached = 0
        self.registration_start_time = timestamp
        self.current_task_id = timestamp.strftime('%Y%m%d%H%M%S')  # 使用时间戳作为任务ID
        print(f"检测到新注册任务，重置进度 (任务ID: {self.current_task_id})")
            
    def _check_progress_keywords(self, message):
        """检查日志行是否包含进度关键词"""
        # 增加对会话Token和注册完成的检测
        if "成功获取会话Token" in message:
            self.current_stage = {
                "stage": 8,
                "message": "成功获取会话Token",
                "percentage": 90
            }
            self.max_stage_reached = 8
            return
            
        if "注册流程完成" in message or "注册成功" in message:
            self.current_stage = {
                "stage": 9,
                "message": "注册流程完成",
                "percentage": 100
            }
            self.max_stage_reached = 9
            return
        
        # 检查每个阶段的关键词
        for i, stage in enumerate(PROGRESS_STAGES):
            if stage["keyword"] in message:
                # 仅当新阶段大于或等于已达到的最大阶段时才更新
                # 这样可以防止因重复检测而退回到之前的阶段
                if i >= self.max_stage_reached:
                    self.current_stage = {
                        "stage": i,
                        "message": stage["message"],
                        "percentage": stage["percentage"]
                    }
                    self.max_stage_reached = i
                    
                    # 如果包含验证码，提取出来
                    if "成功获取验证码" in message:
                        code_match = re.search(r'成功获取验证码: (\d+)', message)
                        if code_match:
                            code = code_match.group(1)
                            self.current_stage["message"] = f"成功获取验证码: {code}"
                return

    def reset_progress(self, timestamp=None):
        """手动重置注册进度并设置新的任务开始时间点
        
        Args:
            timestamp: 可选的时间戳，如果不提供则使用当前时间
        """
        self.current_stage = {"stage": 0, "message": "等待开始...", "percentage": 0}
        self.max_stage_reached = 0
        self.last_position = 0
        
        # 使用传入的时间戳或当前时间
        if timestamp is None:
            timestamp = datetime.now()
        
        self.registration_start_time = timestamp
        self.current_task_id = timestamp.strftime('%Y%m%d%H%M%S')
        print(f"已重置注册进度追踪 (任务ID: {self.current_task_id})")
        
        return self.current_stage 