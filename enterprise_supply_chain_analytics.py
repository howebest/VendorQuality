import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import warnings
from typing import Dict, List, Tuple, Optional
import json
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib
warnings.filterwarnings('ignore')

# 企业级页面配置
st.set_page_config(
    page_title="供应链质量智能分析平台 - 企业版",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.quality-analytics.com/help',
        'Report a bug': "https://www.quality-analytics.com/bug-report",
        'About': "供应链质量智能分析平台 v2.0 - 企业级质量管理解决方案"
    }
)

# 企业级CSS样式
st.markdown("""
<style>
    /* 主题色彩 */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #d62728;
        --info-color: #9467bd;
        --light-bg: #f8f9fa;
        --dark-text: #212529;
    }
    
    /* 头部样式 */
    .main-header {
        font-size: 2.8rem;
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* KPI卡片样式 */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-color);
        transition: transform 0.3s ease;
        height: 120px;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* 警告卡片样式 */
    .warning-card {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border-left: 5px solid var(--warning-color);
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(214, 39, 40, 0.2);
    }
    
    .success-card {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-left: 5px solid var(--success-color);
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(44, 160, 44, 0.2);
    }
    
    .info-card {
        background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
        border-left: 5px solid var(--info-color);
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(148, 103, 189, 0.2);
    }
    
    /* 预警级别样式 */
    .alert-critical {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 5px solid #dc2626;
        animation: pulse 2s infinite;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid #f59e0b;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 5px solid #3b82f6;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }
    
    /* 仪表板网格 */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 1rem 0;
    }
    
    /* 工单表单样式 */
    .workorder-form {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class QualityAnalyticsEngine:
    """质量分析引擎 - 核心计算类"""
    
    def __init__(self):
        self.red_line_rules = {
            'cpk_threshold': 1.33,
            'consecutive_batches': 3,
            'trend_threshold': 0.05
        }
    
    def calculate_cpk(self, data: pd.Series, usl: float, lsl: float) -> float:
        """计算过程能力指数CPK"""
        if pd.isna(usl) or pd.isna(lsl):
            if pd.isna(usl):
                cpk = (data.mean() - lsl) / (3 * data.std()) if not pd.isna(lsl) else np.nan
            else:
                cpk = (usl - data.mean()) / (3 * data.std()) if not pd.isna(usl) else np.nan
        else:
            cpu = (usl - data.mean()) / (3 * data.std())
            cpl = (data.mean() - lsl) / (3 * data.std())
            cpk = min(cpu, cpl)
        
        return round(cpk, 4) if not np.isnan(cpk) else np.nan
    
    def detect_red_line_violations(self, filtered_data: pd.DataFrame) -> Dict:
        """检测四道红线违规情况"""
        violations = {
            '超规检测': [],
            'CPK不足': [],
            '连续趋势': [],
            '箱线图偏移': []
        }
        
        # 1. 超规检测
        ooc_mask = (
            (filtered_data['实际测量值'] > filtered_data['规格上限']) |
            (filtered_data['实际测量值'] < filtered_data['规格下限'])
        )
        if ooc_mask.any():
            violations['超规检测'] = filtered_data[ooc_mask].to_dict('records')
        
        # 2. CPK不足检测
        if len(filtered_data) > 0:
            usl = filtered_data['规格上限'].iloc[0]
            lsl = filtered_data['规格下限'].iloc[0]
            cpk = self.calculate_cpk(filtered_data['实际测量值'], usl, lsl)
            if not np.isnan(cpk) and cpk < self.red_line_rules['cpk_threshold']:
                violations['CPK不足'] = [{
                    'cpk_value': cpk,
                    'threshold': self.red_line_rules['cpk_threshold']
                }]
        
        # 3. 连续趋势检测
        if len(filtered_data) >= self.red_line_rules['consecutive_batches']:
            # 按日期分组计算均值
            daily_means = filtered_data.groupby('日期')['实际测量值'].mean()
            if len(daily_means) >= self.red_line_rules['consecutive_batches']:
                trends = self._detect_consecutive_trends(daily_means.values)
                if trends:
                    violations['连续趋势'] = trends
        
        # 4. 箱线图偏移检测
        boxplot_violations = self._detect_boxplot_shifts(filtered_data)
        if boxplot_violations:
            violations['箱线图偏移'] = boxplot_violations
        
        return violations
    
    def _detect_consecutive_trends(self, values: np.array) -> List:
        """检测连续上升/下降趋势"""
        trends = []
        for i in range(len(values) - self.red_line_rules['consecutive_batches'] + 1):
            window = values[i:i + self.red_line_rules['consecutive_batches']]
            diffs = np.diff(window)
            
            # 检查是否连续上升或下降
            if all(diffs > self.red_line_rules['trend_threshold']):
                trends.append({
                    'start_index': i,
                    'end_index': i + self.red_line_rules['consecutive_batches'] - 1,
                    'trend': '上升',
                    'values': window.tolist()
                })
            elif all(diffs < -self.red_line_rules['trend_threshold']):
                trends.append({
                    'start_index': i,
                    'end_index': i + self.red_line_rules['consecutive_batches'] - 1,
                    'trend': '下降',
                    'values': window.tolist()
                })
        
        return trends
    
    def _detect_boxplot_shifts(self, data: pd.DataFrame) -> List:
        """检测箱线图偏移"""
        shifts = []
        # 按供应商分组分析
        for supplier in data['供应商名称'].unique():
            supplier_data = data[data['供应商名称'] == supplier]
            if len(supplier_data) >= 10:  # 需要足够数据点
                q1 = supplier_data['实际测量值'].quantile(0.25)
                q3 = supplier_data['实际测量值'].quantile(0.75)
                iqr = q3 - q1
                
                # 检测异常偏移
                outliers = supplier_data[
                    (supplier_data['实际测量值'] < q1 - 1.5 * iqr) |
                    (supplier_data['实际测量值'] > q3 + 1.5 * iqr)
                ]
                
                if len(outliers) > len(supplier_data) * 0.1:  # 超过10%为异常
                    shifts.append({
                        'supplier': supplier,
                        'outlier_count': len(outliers),
                        'total_count': len(supplier_data),
                        'shift_percentage': len(outliers) / len(supplier_data) * 100
                    })
        
        return shifts

class AIPredictionEngine:
    """AI预测引擎"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
    
    def predict_yield_trend(self, counting_data: pd.DataFrame, days_ahead: int = 7) -> Dict:
        """预测良率趋势"""
        predictions = {}
        
        # 按供应商和工序分组预测
        for supplier in counting_data['供应商名称'].unique():
            for process in counting_data['工序'].unique():
                group_data = counting_data[
                    (counting_data['供应商名称'] == supplier) & 
                    (counting_data['工序'] == process)
                ].sort_values('日期')
                
                if len(group_data) >= 5:  # 需要至少5个数据点
                    X = np.arange(len(group_data)).reshape(-1, 1)
                    y = group_data['合格率(%)'].values
                    
                    # 线性回归预测
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    # 预测未来几天
                    future_X = np.arange(len(group_data), len(group_data) + days_ahead).reshape(-1, 1)
                    future_predictions = model.predict(future_X)
                    
                    # 检测跌破风险
                    target_yield = group_data['合格率目标(%)'].iloc[-1]
                    risk_days = []
                    for i, pred in enumerate(future_predictions):
                        if pred < target_yield:
                            risk_days.append({
                                'day': i + 1,
                                'predicted_yield': round(pred, 2),
                                'target_yield': target_yield
                            })
                    
                    if risk_days:
                        predictions[f"{supplier}_{process}"] = {
                            'trend_slope': model.coef_[0],
                            'current_yield': y[-1],
                            'target_yield': target_yield,
                            'risk_days': risk_days,
                            'confidence': self._calculate_confidence(model.score(X, y))
                        }
        
        return predictions
    
    def predict_defect_correlation(self, metric_data: pd.DataFrame, counting_data: pd.DataFrame) -> Dict:
        """预测计量型数据波动对计数型不良的影响"""
        correlations = {}
        
        # 检查是否有计量型数据
        if len(metric_data) == 0:
            return correlations
            
        # 分析各质量特性与不良的关系
        characteristics = metric_data['质量特性'].unique()
        defect_types = counting_data[counting_data['不良主要问题'] != '无']['不良主要问题'].unique()
        
        for char in characteristics:
            char_data = metric_data[metric_data['质量特性'] == char]
            char_std = char_data['实际测量值'].std()
            
            # 如果波动较大，分析可能影响的不良类型
            if char_std > char_data['规格'].iloc[0] * 0.1:  # 超过规格的10%
                correlations[char] = {
                    '波动程度': char_std,
                    '可能影响的不良类型': self._map_characteristic_to_defects(char),
                    '风险等级': self._assess_risk_level(char_std)
                }
        
        return correlations
    
    def _calculate_confidence(self, r_squared: float) -> str:
        """计算预测置信度"""
        if r_squared > 0.8:
            return "高"
        elif r_squared > 0.6:
            return "中"
        else:
            return "低"
    
    def _map_characteristic_to_defects(self, characteristic: str) -> List[str]:
        """映射质量特性到可能的不良类型"""
        mapping = {
            '阻抗': ['电测开短路', '信号完整性问题'],
            '线宽': ['线路断路', '线路短路', '蚀刻不良'],
            '插损': ['信号衰减', '传输性能下降'],
            '背钻偏心度': ['钻孔偏移', '层间对准不良'],
            '背钻stub': ['信号反射', '阻抗不匹配']
        }
        return mapping.get(characteristic, ['未知相关不良'])
    
    def _assess_risk_level(self, std_value: float) -> str:
        """评估风险等级"""
        if std_value > 0.5:
            return "高风险"
        elif std_value > 0.2:
            return "中风险"
        else:
            return "低风险"

class WorkOrderManager:
    """工单管理系统"""
    
    def __init__(self):
        self.work_orders = []
        self.order_counter = 1
    
    def create_corrective_order(self, violation_data: Dict, supplier: str, characteristic: str) -> Dict:
        """创建纠正工单"""
        order = {
            'order_id': f"COR-{self.order_counter:04d}",
            'type': '纠正工单',
            'created_time': datetime.now(),
            'supplier': supplier,
            'characteristic': characteristic,
            'violation_details': violation_data,
            'status': '待处理',
            'priority': self._determine_priority(violation_data),
            'deadline': datetime.now() + timedelta(days=3)
        }
        self.order_counter += 1
        self.work_orders.append(order)
        return order
    
    def create_preventive_order(self, prediction_data: Dict, supplier: str, process: str) -> Dict:
        """创建预防工单"""
        order = {
            'order_id': f"PRE-{self.order_counter:04d}",
            'type': '预防工单',
            'created_time': datetime.now(),
            'supplier': supplier,
            'process': process,
            'prediction_details': prediction_data,
            'status': '待处理',
            'priority': self._determine_prediction_priority(prediction_data),
            'deadline': datetime.now() + timedelta(days=5)
        }
        self.order_counter += 1
        self.work_orders.append(order)
        return order
    
    def _determine_priority(self, violation_data: Dict) -> str:
        """确定工单优先级"""
        if '超规检测' in violation_data and violation_data['超规检测']:
            return '紧急'
        elif 'CPK不足' in violation_data and violation_data['CPK不足']:
            return '高'
        else:
            return '中'
    
    def _determine_prediction_priority(self, prediction_data: Dict) -> str:
        """确定预测工单优先级"""
        if prediction_data.get('risk_days'):
            days_until_risk = min([r['day'] for r in prediction_data['risk_days']])
            if days_until_risk <= 2:
                return '紧急'
            elif days_until_risk <= 5:
                return '高'
        return '中'

def load_enhanced_sample_data():
    """生成增强版示例数据"""
    # 生成更多样化的数据以支持AI预测
    dates = pd.date_range(start='2026-03-01', end='2026-03-31', freq='D')
    suppliers = ['中航三鑫', '鹏鼎控股', '建滔', '景旺电子', '生益', '深南电路', '华正新材']
    characteristics = ['阻抗', '线宽', '插损', '背钻偏心度', '背钻stub']
    processes = ['SMT', 'DIP', '电测试', '包装检验', '终检']
    
    # 计量型数据
    metric_data = []
    for date in dates:
        for supplier in suppliers:
            # 模拟质量退化趋势
            degradation_factor = 1 + (date - dates[0]).days * 0.001
            
            for i in range(3):  # 每天3个批次
                lot_num = f"LOT{date.strftime('%Y%m%d')}{str(i+1).zfill(2)}"
                sn_start = len(metric_data) * 10 + 1
                
                for char_idx, char in enumerate(characteristics):
                    sn_num = f"SN{sn_start + char_idx:06d}"
                    
                    # 根据特性设置规格
                    if char == '阻抗':
                        spec_center, usl, lsl = 93, 99.51, 86.49
                        unit = 'Ω'
                        # 模拟逐渐偏离的趋势
                        actual = np.random.normal(93 * degradation_factor, 1.5)
                    elif char == '线宽':
                        spec_center, usl, lsl = 4, 4.4, 3.6
                        unit = 'mil'
                        actual = np.random.normal(4 * degradation_factor, 0.08)
                    elif char == '插损':
                        spec_center, usl, lsl = -0.68, np.nan, np.nan
                        unit = 'db'
                        actual = np.random.normal(-0.68 * degradation_factor, 0.03)
                    elif char == '背钻偏心度':
                        spec_center, usl, lsl = 0.9, 1.8, 0
                        unit = 'mil'
                        actual = np.random.uniform(0, 1.5 * degradation_factor)
                    else:  # 背钻stub
                        spec_center, usl, lsl = 5, 8, 2
                        unit = 'mil'
                        actual = np.random.uniform(2, 7 * degradation_factor)
                    
                    metric_data.append({
                        '日期': date,
                        '供应商名称': supplier,
                        '物料编码': 'V-09480052-100',
                        'DC': '202610',
                        'lot': lot_num,
                        'SN': sn_num,
                        '质量特性': char,
                        '单位': unit,
                        '规格': spec_center,
                        '实际测量值': round(actual, 3),
                        '规格中心': spec_center,
                        '规格上限': usl,
                        '规格下限': lsl
                    })
    
    # 计数型数据
    counting_data = []
    for date in dates:
        for supplier in suppliers:
            for process in processes:
                lot_num = f"P{date.strftime('%Y%m%d')}{supplier[:2]}{process[:1]}"
                
                # 模拟良率逐渐下降趋势
                base_yield = np.random.uniform(0.92, 0.98)
                degradation = (date - dates[0]).days * 0.002
                actual_yield = max(0.85, base_yield - degradation)
                
                production_qty = np.random.randint(800, 1500)
                合格_qty = int(production_qty * actual_yield)
                合格率 = round((合格_qty / production_qty) * 100, 2)
                合格率目标 = 95.0
                
                # 生成不良问题（随着良率下降增加不良）
                if 合格率 < 90:
                    不良问题 = np.random.choice([
                        '焊接不良', '元件偏移', '短路', '开路', '电测开短路', '线路断路'
                    ], p=[0.25, 0.2, 0.15, 0.15, 0.15, 0.1])
                elif 合格率 < 93:
                    不良问题 = np.random.choice(['焊接不良', '元件偏移', '无'], p=[0.4, 0.3, 0.3])
                else:
                    不良问题 = '无'
                
                counting_data.append({
                    '日期': date,
                    '供应商名称': supplier,
                    '物料编码': 'V-09480052-100',
                    '工序': process,
                    '批次号': lot_num,
                    '生产数量': production_qty,
                    '合格品数量': 合格_qty,
                    '合格率(%)': 合格率,
                    '合格率目标(%)': 合格率目标,
                    '不良主要问题': 不良问题
                })
    
    return pd.DataFrame(metric_data), pd.DataFrame(counting_data)

def main():
    st.markdown("<h1 class='main-header'>🏭 供应链质量智能分析平台 - 企业版</h1>", unsafe_allow_html=True)
    
    # 初始化引擎
    analytics_engine = QualityAnalyticsEngine()
    ai_engine = AIPredictionEngine()
    work_order_manager = WorkOrderManager()
    
    # 加载数据
    with st.spinner("🔄 正在初始化企业级数据分析引擎..."):
        try:
            metric_df = pd.read_csv("supply_chain_data.csv")  # 尝试读取真实数据
            counting_df = pd.read_csv("counting_data.csv")
        except FileNotFoundError:
            st.info("📋 未找到外部数据文件，使用增强版模拟数据进行演示")
            metric_df, counting_df = load_enhanced_sample_data()
    
    # 侧边栏筛选器
    with st.sidebar:
        st.header("⚙️ 智能筛选器")
        
        # 时间范围选择
        st.subheader("📅 时间筛选")
        min_date = metric_df['日期'].min().date()
        max_date = metric_df['日期'].max().date()
        start_date = st.date_input("开始日期", min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("结束日期", max_date, min_value=start_date, max_value=max_date)
        
        # 供应商选择
        st.subheader("🏢 供应商筛选")
        all_suppliers = sorted(metric_df['供应商名称'].unique())
        selected_suppliers = st.multiselect("选择供应商", all_suppliers, default=all_suppliers[:3])
        
        # 质量特性选择
        st.subheader("📏 计量特性")
        all_characteristics = sorted(metric_df['质量特性'].unique())
        selected_characteristic = st.selectbox("质量特性", all_characteristics)
        
        # 工序选择
        st.subheader("🔧 工序筛选")
        all_processes = sorted(counting_df['工序'].unique())
        selected_processes = st.multiselect("选择工序", all_processes, default=all_processes[:2])
        
        # 快速筛选按钮
        st.subheader("⚡ 快速操作")
        if st.button("📈 查看今日数据"):
            end_date = datetime.now().date()
            start_date = end_date
        if st.button("📊 重置所有筛选"):
            st.experimental_rerun()
    
    # 数据筛选
    filtered_metric = metric_df[
        (metric_df['日期'].dt.date >= start_date) & 
        (metric_df['日期'].dt.date <= end_date) &
        (metric_df['供应商名称'].isin(selected_suppliers)) &
        (metric_df['质量特性'] == selected_characteristic)
    ]
    
    filtered_counting = counting_df[
        (counting_df['日期'].dt.date >= start_date) & 
        (counting_df['日期'].dt.date <= end_date) &
        (counting_df['供应商名称'].isin(selected_suppliers)) &
        (counting_df['工序'].isin(selected_processes))
    ]
    
    # 主页面布局
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 核心指标与预警", 
        "📊 计量型深度分析", 
        "📈 计数型AI预测", 
        "📋 问题闭环管理"
    ])
    
    with tab1:
        render_kpi_dashboard(filtered_metric, filtered_counting, analytics_engine, ai_engine, work_order_manager)
    
    with tab2:
        render_metric_analysis(filtered_metric, analytics_engine)
    
    with tab3:
        render_counting_analysis(filtered_counting, filtered_metric, ai_engine)
    
    with tab4:
        render_work_order_management(work_order_manager)

def render_kpi_dashboard(metric_data, counting_data, analytics_engine, ai_engine, work_order_manager):
    """渲染KPI与预警概览面板"""
    st.header("🎯 核心指标与双驱动预警系统")
    
    # 基础KPI指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_samples = len(metric_data)
        st.markdown(f"""
        <div class="kpi-card">
            <h3>🔬 检测样本数</h3>
            <h2>{total_samples:,}</h2>
            <p style="color: #666;">总检测点数</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if len(counting_data) > 0:
            avg_yield = counting_data['合格率(%)'].mean()
            yield_target = counting_data['合格率目标(%)'].iloc[0]
            yield_status = "🟢" if avg_yield >= yield_target else "🔴"
            st.markdown(f"""
            <div class="kpi-card">
                <h3>📊 平均良率</h3>
                <h2>{yield_status} {avg_yield:.2f}%</h2>
                <p style="color: #666;">目标: {yield_target}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        ooc_count = len(metric_data[
            (metric_data['实际测量值'] > metric_data['规格上限']) |
            (metric_data['实际测量值'] < metric_data['规格下限'])
        ])
        ooc_rate = (ooc_count / len(metric_data) * 100) if len(metric_data) > 0 else 0
        st.markdown(f"""
        <div class="kpi-card">
            <h3>⚠️ 超规率</h3>
            <h2>{ooc_rate:.2f}%</h2>
            <p style="color: #666;">异常样本: {ooc_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if len(metric_data) > 0:
            usl = metric_data['规格上限'].iloc[0]
            lsl = metric_data['规格下限'].iloc[0]
            cpk = analytics_engine.calculate_cpk(metric_data['实际测量值'], usl, lsl)
            cpk_status = "🟢" if cpk >= 1.33 else "🔴"
            st.markdown(f"""
            <div class="kpi-card">
                <h3>🔢 过程能力(CPK)</h3>
                <h2>{cpk_status} {cpk:.3f}</h2>
                <p style="color: #666;">目标: ≥1.33</p>
            </div>
            """, unsafe_allow_html=True)
    
    # 四道红线实时预警
    st.subheader("🚨 四道红线实时预警系统")
    
    if len(metric_data) > 0:
        violations = analytics_engine.detect_red_line_violations(metric_data)
        
        # 显示预警卡片
        warning_cols = st.columns(2)
        
        with warning_cols[0]:
            if violations['超规检测']:
                st.markdown(f"""
                <div class="warning-card alert-critical">
                    <h3>🔴 超规检测预警</h3>
                    <p>发现 {len(violations['超规检测'])} 个超规数据点</p>
                    <p><strong>立即处理建议：</strong>暂停相关批次生产，进行根本原因分析</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="success-card">
                    <h3>🟢 超规检测正常</h3>
                    <p>所有测量值均在规格范围内</p>
                </div>
                """, unsafe_allow_html=True)
        
        with warning_cols[1]:
            if violations['CPK不足']:
                st.markdown(f"""
                <div class="warning-card alert-warning">
                    <h3>🟡 CPK能力不足</h3>
                    <p>当前CPK = {violations['CPK不足'][0]['cpk_value']:.3f} < 1.33</p>
                    <p><strong>改善建议：</strong>优化工艺参数，加强过程控制</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="success-card">
                    <h3>🟢 CPK能力充足</h3>
                    <p>过程能力满足要求</p>
                </div>
                """, unsafe_allow_html=True)
        
        # 连续趋势和箱线图偏移预警
        trend_cols = st.columns(2)
        
        with trend_cols[0]:
            if violations['连续趋势']:
                st.markdown(f"""
                <div class="warning-card alert-info">
                    <h3>🔵 连续趋势预警</h3>
                    <p>检测到 {len(violations['连续趋势'])} 个连续趋势</p>
                    <p><strong>关注要点：</strong>监控过程稳定性变化</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-card">
                    <h3>🔵 趋势分析正常</h3>
                    <p>未发现显著连续趋势</p>
                </div>
                """, unsafe_allow_html=True)
        
        with trend_cols[1]:
            if violations['箱线图偏移']:
                st.markdown(f"""
                <div class="warning-card alert-warning">
                    <h3>🟠 分布偏移预警</h3>
                    <p>{len(violations['箱线图偏移'])} 个供应商存在分布偏移</p>
                    <p><strong>处理建议：</strong>检查设备校准和工艺一致性</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-card">
                    <h3>🟠 分布稳定</h3>
                    <p>各供应商数据分布正常</p>
                </div>
                """, unsafe_allow_html=True)
        
        # 生成纠正工单
        if any(violations.values()):
            st.subheader("📋 自动生成纠正工单")
            if st.button("📝 生成纠正措施工单"):
                for violation_type, details in violations.items():
                    if details:
                        order = work_order_manager.create_corrective_order(
                            {violation_type: details},
                            metric_data['供应商名称'].iloc[0],
                            selected_characteristic
                        )
                        st.success(f"✅ 已生成工单 {order['order_id']} - {order['type']}")
    
    # AI下周高危预警清单
    st.subheader("🔮 AI下周高危预警清单")
    
    with st.expander("🔍 查看AI预测的高风险物料与缺陷类型", expanded=True):
        # 进行AI预测
        yield_predictions = ai_engine.predict_yield_trend(counting_data)
        defect_correlations = ai_engine.predict_defect_correlation(metric_data, counting_data)
        
        if yield_predictions:
            st.markdown("### ⚠️ 良率跌破风险预测")
            for key, prediction in yield_predictions.items():
                supplier, process = key.split('_')
                st.markdown(f"""
                <div class="warning-card alert-critical">
                    <h4>🔴 {supplier} - {process} 工序</h4>
                    <p><strong>风险等级：</strong> 高风险</p>
                    <p><strong>当前良率：</strong> {prediction['current_yield']:.2f}%</p>
                    <p><strong>目标良率：</strong> {prediction['target_yield']:.2f}%</p>
                    <p><strong>预测跌破时间：</strong> {prediction['risk_days'][0]['day']} 天后</p>
                    <p><strong>置信度：</strong> {prediction['confidence']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-card">
                <h3>🟢 近期无良率跌破风险</h3>
                <p>AI预测显示各工序良率稳定</p>
            </div>
            """, unsafe_allow_html=True)
        
        if defect_correlations:
            st.markdown("### 🔗 计量波动与不良关联预测")
            for char, correlation in defect_correlations.items():
                st.markdown(f"""
                <div class="info-card">
                    <h4>📊 {char} 特性波动分析</h4>
                    <p><strong>波动程度：</strong> {correlation['波动程度']:.3f}</p>
                    <p><strong>风险等级：</strong> {correlation['风险等级']}</p>
                    <p><strong>可能影响：</strong> {', '.join(correlation['可能影响的不良类型'])}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # 生成预防工单
        if yield_predictions or defect_correlations:
            if st.button("🛡️ 生成预防措施工单"):
                for key, prediction in yield_predictions.items():
                    supplier, process = key.split('_')
                    order = work_order_manager.create_preventive_order(
                        prediction, supplier, process
                    )
                    st.success(f"✅ 已生成预防工单 {order['order_id']} - {order['type']}")

def render_metric_analysis(metric_data, analytics_engine):
    """渲染计量型数据分析"""
    st.header("📊 计量型数据深度分析")
    
    if len(metric_data) > 0:
        # 趋势控制图
        st.subheader("📈 趋势控制图")
        
        fig_trend = go.Figure()
        
        # 为每个供应商绘制数据
        for supplier in metric_data['供应商名称'].unique():
            supplier_data = metric_data[metric_data['供应商名称'] == supplier]
            if len(supplier_data) > 0:
                fig_trend.add_trace(go.Scatter(
                    x=supplier_data['日期'],
                    y=supplier_data['实际测量值'],
                    mode='markers+lines',
                    name=f'{supplier}',
                    marker=dict(size=8)
                ))
        
        # 添加规格线
        spec_center = metric_data['规格中心'].iloc[0]
        usl = metric_data['规格上限'].iloc[0]
        lsl = metric_data['规格下限'].iloc[0]
        
        fig_trend.add_hline(y=spec_center, line_dash="solid", line_color="green", 
                          annotation_text="规格中心", annotation_position="top left")
        
        if not pd.isna(usl):
            fig_trend.add_hline(y=usl, line_dash="dash", line_color="red",
                              annotation_text="USL", annotation_position="top right")
        
        if not pd.isna(lsl):
            fig_trend.add_hline(y=lsl, line_dash="dash", line_color="red",
                              annotation_text="LSL", annotation_position="bottom right")
        
        # 标记超规点
        ooc_points = metric_data[
            (metric_data['实际测量值'] > metric_data['规格上限']) |
            (metric_data['实际测量值'] < metric_data['规格下限'])
        ]
        
        if len(ooc_points) > 0:
            fig_trend.add_trace(go.Scatter(
                x=ooc_points['日期'],
                y=ooc_points['实际测量值'],
                mode='markers',
                name='超规点',
                marker=dict(color='red', size=12, symbol='x'),
                showlegend=True
            ))
        
        fig_trend.update_layout(
            title=f"{metric_data['质量特性'].iloc[0]} 趋势控制图",
            xaxis_title="日期",
            yaxis_title=f"测量值 ({metric_data['单位'].iloc[0]})",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # CPK分析和箱线图
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔢 过程能力分布分析")
            
            fig_hist = go.Figure()
            
            # 绘制直方图
            fig_hist.add_trace(go.Histogram(
                x=metric_data['实际测量值'],
                name='测量值分布',
                nbinsx=30,
                opacity=0.7
            ))
            
            # 添加正态分布拟合曲线
            mean_val = metric_data['实际测量值'].mean()
            std_val = metric_data['实际测量值'].std()
            x_norm = np.linspace(metric_data['实际测量值'].min(), 
                               metric_data['实际测量值'].max(), 100)
            y_norm = np.exp(-0.5 * ((x_norm - mean_val) / std_val) ** 2) / (std_val * np.sqrt(2 * np.pi))
            y_norm = y_norm * len(metric_data) * (metric_data['实际测量值'].max() - metric_data['实际测量值'].min()) / 30
            
            fig_hist.add_trace(go.Scatter(
                x=x_norm,
                y=y_norm,
                mode='lines',
                name='正态分布拟合',
                line=dict(color='red', width=2)
            ))
            
            # 添加规格线
            fig_hist.add_vline(x=spec_center, line_dash="solid", line_color="green")
            if not pd.isna(usl):
                fig_hist.add_vline(x=usl, line_dash="dash", line_color="red")
            if not pd.isna(lsl):
                fig_hist.add_vline(x=lsl, line_dash="dash", line_color="red")
            
            fig_hist.update_layout(
                title="测量值分布与过程能力",
                xaxis_title=f"测量值 ({metric_data['单位'].iloc[0]})",
                yaxis_title="频次",
                height=400
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            st.subheader("📈 统计指标")
            st.metric("样本均值", f"{mean_val:.4f}")
            st.metric("标准差", f"{std_val:.4f}")
            
            usl_val = metric_data['规格上限'].iloc[0]
            lsl_val = metric_data['规格下限'].iloc[0]
            cpk = analytics_engine.calculate_cpk(metric_data['实际测量值'], usl_val, lsl_val)
            st.metric("CPK值", f"{cpk:.4f}" if not np.isnan(cpk) else "N/A")
            
            # 供应商箱线图
            st.subheader("🏢 供应商对比")
            fig_box = px.box(metric_data, x='供应商名称', y='实际测量值',
                           title="各供应商测量值分布")
            fig_box.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_box, use_container_width=True)

def render_counting_analysis(counting_data, metric_data, ai_engine):
    """渲染计数型数据分析"""
    st.header("📈 计数型数据与AI不良预测分析")
    
    if len(counting_data) > 0:
        # 良率趋势预测图
        st.subheader("🔮 良率破线预测分析")
        
        fig_yield = go.Figure()
        
        # 为每个供应商-工序组合绘制数据
        combinations = counting_data.groupby(['供应商名称', '工序']).size().index
        for supplier, process in combinations:
            combo_data = counting_data[
                (counting_data['供应商名称'] == supplier) & 
                (counting_data['工序'] == process)
            ].sort_values('日期')
            
            if len(combo_data) > 0:
                fig_yield.add_trace(go.Bar(
                    x=combo_data['日期'],
                    y=combo_data['合格率(%)'],
                    name=f'{supplier}-{process}',
                    opacity=0.7
                ))
        
        # 添加良率目标线
        yield_target = counting_data['合格率目标(%)'].iloc[0]
        fig_yield.add_hline(y=yield_target, line_dash="dash", line_color="orange",
                          annotation_text=f"目标良率 {yield_target}%", annotation_position="top right")
        
        # AI预测延伸线
        predictions = ai_engine.predict_yield_trend(counting_data)
        for key, pred_data in predictions.items():
            if pred_data['risk_days']:
                supplier, process = key.split('_')
                # 找到最后一个数据点
                last_data = counting_data[
                    (counting_data['供应商名称'] == supplier) & 
                    (counting_data['工序'] == process)
                ].sort_values('日期').iloc[-1]
                
                # 添加预测线
                risk_day = pred_data['risk_days'][0]
                future_date = last_data['日期'] + timedelta(days=risk_day['day'])
                
                fig_yield.add_trace(go.Scatter(
                    x=[last_data['日期'], future_date],
                    y=[last_data['合格率(%)']],  # 只有一个点，需要补充
                    mode='lines',
                    name=f'{supplier}-{process} 预测',
                    line=dict(dash='dot', color='red', width=2)
                ))
        
        fig_yield.update_layout(
            title="良率趋势与AI预测",
            xaxis_title="日期",
            yaxis_title="合格率 (%)",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig_yield, use_container_width=True)
        
        # 不良原因帕累托图和AI关联分析
        st.subheader("🔗 因果关联分析与帕累托图")
        
        defect_data = counting_data[counting_data['不良主要问题'] != '无']
        
        if len(defect_data) > 0:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 帕累托图
                defect_counts = defect_data['不良主要问题'].value_counts()
                defect_percent = defect_counts / defect_counts.sum() * 100
                cumulative_percent = defect_percent.cumsum()
                
                fig_pareto = go.Figure()
                
                # 添加柱状图
                fig_pareto.add_trace(go.Bar(
                    x=defect_counts.index,
                    y=defect_counts.values,
                    name='不良频次',
                    yaxis='y'
                ))
                
                # 添加累计百分比线
                fig_pareto.add_trace(go.Scatter(
                    x=defect_counts.index,
                    y=cumulative_percent,
                    mode='lines+markers',
                    name='累计百分比',
                    yaxis='y2',
                    line=dict(color='red', width=2)
                ))
                
                fig_pareto.update_layout(
                    title="不良原因帕累托分析 (80/20法则)",
                    xaxis_title="不良类型",
                    yaxis=dict(title="不良频次"),
                    yaxis2=dict(title="累计百分比 (%)", overlaying='y', side='right', range=[0, 100]),
                    legend=dict(x=0.7, y=0.9),
                    height=400
                )
                
                st.plotly_chart(fig_pareto, use_container_width=True)
            
            with col2:
                # AI因果关联提示
                st.markdown("### 🤖 AI因果关联分析")
                
                correlations = ai_engine.predict_defect_correlation(
                    pd.DataFrame(), counting_data  # 简化处理
                )
                
                if correlations:
                    for char, correlation in correlations.items():
                        st.markdown(f"""
                        <div class="info-card">
                            <h4>{char}</h4>
                            <p><strong>风险等级：</strong> {correlation['风险等级']}</p>
                            <p><strong>可能影响：</strong></p>
                            <ul>
                                {''.join([f'<li>{impact}</li>' for impact in correlation['可能影响的不良类型']])}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("当前无显著因果关联发现")
        else:
            st.info("当前筛选条件下无不良记录")

def render_work_order_management(work_order_manager):
    """渲染问题闭环管理层"""
    st.header("📋 数据异常闭环管理")
    
    # 工单状态概览
    if work_order_manager.work_orders:
        st.subheader("🎫 工单状态概览")
        
        # 统计各类工单
        order_stats = {
            '纠正工单': len([o for o in work_order_manager.work_orders if o['type'] == '纠正工单']),
            '预防工单': len([o for o in work_order_manager.work_orders if o['type'] == '预防工单']),
            '待处理': len([o for o in work_order_manager.work_orders if o['status'] == '待处理']),
            '处理中': len([o for o in work_order_manager.work_orders if o['status'] == '处理中']),
            '已完成': len([o for o in work_order_manager.work_orders if o['status'] == '已完成'])
        }
        
        stat_cols = st.columns(5)
        stat_labels = ['纠正工单', '预防工单', '待处理', '处理中', '已完成']
        stat_values = [order_stats[label] for label in stat_labels]
        stat_colors = ['#ff6b6b', '#4ecdc4', '#ffd93d', '#6bcf7f', '#45b7d1']
        
        for i, (col, label, value, color) in enumerate(zip(stat_cols, stat_labels, stat_values, stat_colors)):
            col.markdown(f"""
            <div class="kpi-card" style="border-left-color: {color};">
                <h3>{label}</h3>
                <h2>{value}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # 工单详情列表
        st.subheader("📄 工单详情")
        
        for order in work_order_manager.work_orders:
            with st.expander(f"🎫 {order['order_id']} - {order['type']} ({order['status']})", 
                           expanded=order['status'] == '待处理'):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **基本信息：**
                    - 创建时间：{order['created_time'].strftime('%Y-%m-%d %H:%M')}
                    - 供应商：{order['supplier']}
                    - 优先级：{order['priority']}
                    - 截止时间：{order['deadline'].strftime('%Y-%m-%d')}
                    """)
                
                with col2:
                    if order['type'] == '纠正工单':
                        st.markdown("**违规详情：**")
                        for violation_type, details in order['violation_details'].items():
                            if details:
                                st.write(f"- {violation_type}: {len(details)} 项")
                    else:
                        st.markdown("**预测详情：**")
                        if 'risk_days' in order['prediction_details']:
                            risk_info = order['prediction_details']['risk_days'][0]
                            st.write(f"- 预测跌破时间：{risk_info['day']} 天后")
                            st.write(f"- 预测良率：{risk_info['predicted_yield']}%")
                
                # 工单处理表单
                st.markdown("---")
                st.markdown("### 📝 工单处理")
                
                with st.form(f"order_form_{order['order_id']}"):
                    action_taken = st.text_area("已采取的改善措施", 
                                              placeholder="详细描述已实施的改善行动...")
                    root_cause = st.text_area("根本原因分析", 
                                            placeholder="分析问题产生的根本原因...")
                    effectiveness = st.slider("措施有效性评估", 1, 10, 5)
                    status_update = st.selectbox("更新状态", 
                                               ["处理中", "已完成", "延期"], 
                                               index=["处理中", "已完成", "延期"].index(order['status']))
                    
                    submitted = st.form_submit_button("💾 保存工单更新")
                    if submitted:
                        order['status'] = status_update
                        order['updated_time'] = datetime.now()
                        st.success(f"✅ 工单 {order['order_id']} 已更新")
                        st.experimental_rerun()
    else:
        st.info("📭 暂无工单记录")
    
    # 数据导出功能
    st.sidebar.header("💾 数据导出")
    
    if st.sidebar.button("📦 导出异常与高风险数据"):
        # 筛选异常数据
        abnormal_metric = metric_df[
            (metric_df['实际测量值'] > metric_df['规格上限']) |
            (metric_df['实际测量值'] < metric_df['规格下限'])
        ]
        
        abnormal_counting = counting_df[
            counting_df['合格率(%)'] < counting_df['合格率目标(%)']
        ]
        
        if len(abnormal_metric) > 0 or len(abnormal_counting) > 0:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if len(abnormal_metric) > 0:
                    abnormal_metric.to_excel(writer, sheet_name='计量型异常数据', index=False)
                if len(abnormal_counting) > 0:
                    abnormal_counting.to_excel(writer, sheet_name='计数型异常数据', index=False)
                
                # 添加工单数据
                if work_order_manager.work_orders:
                    orders_df = pd.DataFrame(work_order_manager.work_orders)
                    orders_df.to_excel(writer, sheet_name='工单记录', index=False)
            
            output.seek(0)
            
            st.sidebar.download_button(
                label="📥 下载完整分析报告",
                data=output,
                file_name=f"质量分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.sidebar.success("📊 完整分析报告已准备就绪！")
        else:
            st.sidebar.info("当前无异常数据需要导出")

if __name__ == "__main__":
    main()