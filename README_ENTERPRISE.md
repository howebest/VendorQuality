# 供应链质量智能分析平台 - 企业版

## 🏭 项目概述

这是第二代企业级供应链质量管理分析平台，专为制造业质量管控打造的智能化解决方案。平台集成了实时预警、AI预测、问题闭环管理等核心功能，帮助企业实现质量管理的数字化转型。

## 🚀 核心功能特性

### 1. 四道红线实时预警系统 🚨
- **超规检测**：实时监控测量值是否超出规格限
- **CPK能力监控**：自动计算过程能力指数，识别能力不足风险
- **连续趋势分析**：检测连续3批次均值的异常上升/下降趋势
- **箱线图偏移监测**：识别供应商间的数据分布偏移

### 2. AI智能预测引擎 🔮
- **良率趋势预测**：基于历史数据预测未来良率走势
- **风险提前预警**：计算良率跌破目标值的时间点
- **因果关联分析**：分析计量型数据波动对不良率的影响
- **智能推荐机制**：根据预测结果推荐预防措施

### 3. 问题闭环管理系统 📋
- **双轨工单体系**：自动生成纠正工单和预防工单
- **优先级智能判定**：根据风险等级自动分配处理优先级
- **全流程跟踪**：从问题发现到解决的完整生命周期管理
- **效果评估反馈**：量化改善措施的有效性

### 4. 企业级数据可视化 📊
- **交互式仪表板**：多维度数据实时展示
- **专业图表库**：趋势图、控制图、帕累托图等
- **移动端适配**：响应式设计支持各种设备访问
- **权限分级管理**：不同角色查看不同层级数据

## 🛠️ 技术架构

### 前端技术栈
- **Streamlit 1.29.0**：企业级Web应用框架
- **Plotly 5.15.0**：专业级数据可视化库
- **Custom CSS**：企业级UI/UX设计

### 后端分析引擎
- **Pandas 1.5.3**：数据处理和分析
- **NumPy 1.24.3**：数值计算
- **Scikit-learn 1.6.1**：机器学习预测模型
- **Joblib 1.3.2**：模型持久化

### 数据存储
- **Excel/OpenPyXL**：本地数据文件处理
- **内存缓存**：提升交互响应速度

## 📁 项目结构

```
enterprise_supply_chain_analytics.py  # 主应用文件
requirements_enterprise.txt           # 企业版依赖包
supply_chain_data.csv                 # 计量型数据（可选）
counting_data.csv                     # 计数型数据（可选）
README_ENTERPRISE.md                  # 企业版使用文档
```

## 🎯 核心模块详解

### QualityAnalyticsEngine（质量分析引擎）
```python
class QualityAnalyticsEngine:
    def calculate_cpk(self, data, usl, lsl)  # CPK计算
    def detect_red_line_violations(self, data)  # 四道红线检测
    def _detect_consecutive_trends(self, values)  # 连续趋势分析
    def _detect_boxplot_shifts(self, data)  # 箱线图偏移检测
```

### AIPredictionEngine（AI预测引擎）
```python
class AIPredictionEngine:
    def predict_yield_trend(self, data, days_ahead=7)  # 良率趋势预测
    def predict_defect_correlation(self, metric_data, counting_data)  # 因果关联分析
    def _calculate_confidence(self, r_squared)  # 预测置信度评估
```

### WorkOrderManager（工单管理器）
```python
class WorkOrderManager:
    def create_corrective_order(self, violation_data, supplier, characteristic)  # 纠正工单
    def create_preventive_order(self, prediction_data, supplier, process)  # 预防工单
    def _determine_priority(self, violation_data)  # 优先级判定
```

## 📊 数据格式规范

### 计量型数据字段
| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| 日期 | datetime | 检测日期 | 2026-03-01 |
| 供应商名称 | string | 供应商公司名 | 中航三鑫 |
| 物料编码 | string | 产品编号 | V-09480052-100 |
| 质量特性 | string | 检测项目 | 阻抗、线宽、插损 |
| 单位 | string | 测量单位 | Ω、mil、db |
| 规格 | float | 规格要求 | 93 |
| 实际测量值 | float | 实测数据 | 92.35 |
| 规格中心 | float | 目标值 | 93 |
| 规格上限 | float/null | USL | 99.51 |
| 规格下限 | float/null | LSL | 86.49 |

### 计数型数据字段
| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| 日期 | datetime | 生产日期 | 2026-03-01 |
| 供应商名称 | string | 供应商公司名 | 鹏鼎控股 |
| 工序 | string | 生产工序 | SMT、电测试 |
| 批次号 | string | 生产批次 | LOT2026030101 |
| 生产数量 | integer | 总产量 | 1000 |
| 合格品数量 | integer | 合格数量 | 950 |
| 合格率(%) | float | 合格百分比 | 95.0 |
| 合格率目标(%) | float | 目标良率 | 95.0 |
| 不良主要问题 | string | 主要不良类型 | 焊接不良、电测开短路 |

## 🔧 部署指南

### 环境要求
- Python 3.7+
- 4GB RAM以上
- 现代浏览器支持

### 安装步骤
```bash
# 克隆项目
git clone <repository-url>
cd supply_chain_quality_platform

# 安装企业版依赖
pip install -r requirements_enterprise.txt

# 启动应用
streamlit run enterprise_supply_chain_analytics.py --server.port 8502
```

### 访问地址
- 本地访问：http://localhost:8502
- 网络访问：http://your-server-ip:8502

## 💡 使用最佳实践

### 1. 日常监控流程
1. 登录系统查看首页KPI概览
2. 关注红色预警区域的实时提醒
3. 定期查看AI预测的高危清单
4. 及时处理生成的工单任务

### 2. 数据分析策略
- **计量型数据**：重点关注CPK值和趋势控制图
- **计数型数据**：关注良率趋势和不良帕累托分析
- **交叉验证**：结合两种数据类型进行综合判断

### 3. 预警响应机制
- **紧急预警**：2小时内响应并制定临时措施
- **高优先级**：当日内完成根本原因分析
- **中优先级**：3个工作日内完成改善计划

### 4. 持续改进循环
1. 数据收集 → 2. 分析诊断 → 3. 预警触发 → 4. 工单生成 → 5. 措施实施 → 6. 效果验证 → 7. 标准固化

## 🛡️ 安全与权限

### 用户权限分级
- **管理员**：全部功能访问权限
- **质量工程师**：数据分析和工单处理权限
- **生产主管**：实时监控和预警查看权限
- **高层管理**：KPI概览和报表导出权限

### 数据安全措施
- 本地数据存储，确保信息安全
- 访问日志记录
- 敏感数据脱敏处理
- 定期备份机制

## 📈 性能优化建议

### 系统优化
- 启用Streamlit缓存机制
- 合理设置数据采样频率
- 优化图表渲染性能
- 实施懒加载策略

### 硬件建议
- CPU：4核以上
- 内存：8GB以上
- 存储：SSD硬盘
- 网络：千兆带宽

## 🆘 技术支持

### 常见问题解答
1. **应用启动失败**：检查Python环境和依赖包版本
2. **数据显示异常**：确认数据格式符合规范要求
3. **预测准确性低**：确保有足够的历史数据（建议30天以上）
4. **工单系统异常**：检查浏览器兼容性和网络连接

### 维护计划
- 每月定期更新预测模型
- 季度性能评估和优化
- 年度功能升级和扩展
- 持续用户反馈收集

## 📞 联系我们

- **技术支持邮箱**：support@quality-analytics.com
- **产品咨询热线**：400-XXX-XXXX
- **官方网站**：www.quality-analytics.com
- **在线文档**：docs.quality-analytics.com

---
*供应链质量智能分析平台企业版 v2.0*
*© 2026 Quality Analytics Corporation. All rights reserved.*