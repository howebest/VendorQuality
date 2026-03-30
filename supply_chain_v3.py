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

# 页面配置
st.set_page_config(
    page_title="供应链质量智能分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 美观简洁CSS样式
st.markdown("""
<style>
    /* 全局字体设置 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 14px !important;
    }
    
    * {
        font-size: 14px;
        line-height: 1.4;
    }
    
    /* 主标题 */
    .main-title {
        font-size: 1.6rem !important;
        color: #1565c0;
        text-align: center;
        margin: 0.2rem 0;
        font-weight: 700;
    }
    
    /* 页面标题 */
    h1 {
        font-size: 1.4rem !important;
        margin: 0.2rem 0 !important;
        font-weight: 700 !important;
    }
    
    h2 {
        font-size: 1.2rem !important;
        margin: 0.15rem 0 !important;
        font-weight: 600 !important;
    }
    
    h3 {
        font-size: 1.1rem !important;
        margin: 0.1rem 0 !important;
        font-weight: 600 !important;
    }
    
    h4 {
        font-size: 1rem !important;
        margin: 0.1rem 0 !important;
        font-weight: 500 !important;
    }
    
    /* KPI卡片 */
    .kpi-card {
        background: white;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #1565c0;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .kpi-card h3 {
        font-size: 0.9rem !important;
        margin: 0;
        color: #666;
        font-weight: 500;
    }
    
    .kpi-card h2 {
        font-size: 1.3rem !important;
        margin: 0.1rem 0;
        color: #333;
        font-weight: 700;
    }
    
    .kpi-card p {
        font-size: 0.85rem !important;
        margin: 0;
        color: #888;
    }
    
    /* 警告卡片 */
    .warning-card, .success-card, .info-card {
        padding: 0.6rem 0.8rem;
        border-radius: 6px;
        margin: 0.2rem 0;
        border-left: 4px solid;
    }
    
    .warning-card h3, .warning-card h4,
    .success-card h3, .success-card h4,
    .info-card h3, .info-card h4 {
        font-size: 1rem !important;
        margin: 0.05rem 0;
    }
    
    .warning-card p, .success-card p, .info-card p {
        font-size: 0.9rem !important;
        margin: 0.05rem 0;
    }
    
    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        padding: 0.6rem;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 1rem !important;
    }
    
    /* 标签页 */
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        padding: 0.4rem 0.8rem;
    }
    
    /* 表单元素 */
    div[data-baseweb="select"] > div {
        font-size: 0.95rem !important;
    }
    
    div[data-baseweb="input"] {
        font-size: 0.95rem !important;
    }
    
    /* 文本 */
    .stMarkdown, p, span, div {
        font-size: 0.95rem !important;
    }
    
    /* 按钮 */
    .stButton > button {
        font-size: 0.95rem !important;
        padding: 0.4rem 0.8rem;
    }
    
    /* 指标卡 */
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    /* 表格 */
    table {
        font-size: 0.9rem !important;
    }
    
    th, td {
        padding: 0.3rem 0.5rem !important;
    }
    
    /* Expander */
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 0.95rem !important;
    }
    
    /* 元素间距 */
    .element-container {
        margin-bottom: 0.3rem;
    }
    
    /* 列间距 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    
    /* 减少内边距 */
    .css-1adrfps {
        padding: 0.4rem;
    }
    
    /* 下拉菜单 */
    div[role="listbox"] {
        font-size: 0.95rem !important;
    }
    
    /* 日期选择器 */
    input[type="date"] {
        font-size: 0.95rem !important;
    }
    
    /* 分隔线 */
    hr {
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class QualityAnalyticsEngine:
    """质量分析引擎"""
    
    def calculate_cpk(self, data: pd.Series, usl: float, lsl: float) -> float:
        # 检查数据有效性
        if len(data) == 0 or data.std() == 0:
            return np.nan
        
        mean_val = data.mean()
        std_val = data.std()
        
        # 双侧规格限
        if pd.notna(usl) and pd.notna(lsl):
            cpu = (usl - mean_val) / (3 * std_val)
            cpl = (mean_val - lsl) / (3 * std_val)
            cpk = min(cpu, cpl)
        # 仅有上限
        elif pd.notna(usl):
            cpk = (usl - mean_val) / (3 * std_val)
        # 仅有下限
        elif pd.notna(lsl):
            cpk = (mean_val - lsl) / (3 * std_val)
        # 无规格限
        else:
            return np.nan
        
        return round(cpk, 4) if not np.isnan(cpk) else np.nan
    
    def detect_violations(self, data: pd.DataFrame) -> Dict:
        violations = {'超规检测': [], 'CPK不足': [], '连续趋势': []}
        
        if len(data) == 0:
            return violations
        
        # 超规检测 - 处理NaN规格限
        usl = data['规格上限'].iloc[0] if len(data) > 0 else None
        lsl = data['规格下限'].iloc[0] if len(data) > 0 else None
        
        if pd.notna(usl):
            ooc_upper = data['实际测量值'] > usl
            if ooc_upper.any():
                violations['超规检测'].extend(data[ooc_upper].to_dict('records'))
        
        if pd.notna(lsl):
            ooc_lower = data['实际测量值'] < lsl
            if ooc_lower.any():
                violations['超规检测'].extend(data[ooc_lower].to_dict('records'))
        
        # CPK检测
        cpk = self.calculate_cpk(data['实际测量值'], usl, lsl)
        if not np.isnan(cpk) and cpk < 1.33:
            violations['CPK不足'] = [{'cpk': cpk}]
        
        return violations

class AIPredictionEngine:
    """AI预测引擎"""
    
    def predict_yield_trend(self, counting_data: pd.DataFrame, days_ahead: int = 7) -> Dict:
        predictions = {}
        
        for supplier in counting_data['供应商名称'].unique():
            for process in counting_data['工序'].unique():
                group_data = counting_data[
                    (counting_data['供应商名称'] == supplier) & 
                    (counting_data['工序'] == process)
                ].sort_values('日期')
                
                if len(group_data) >= 5:
                    X = np.arange(len(group_data)).reshape(-1, 1)
                    y = group_data['合格率(%)'].values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    future_X = np.arange(len(group_data), len(group_data) + days_ahead).reshape(-1, 1)
                    future_predictions = model.predict(future_X)
                    
                    target_yield = group_data['合格率目标(%)'].iloc[-1]
                    risk_days = []
                    for i, pred in enumerate(future_predictions):
                        if pred < target_yield:
                            risk_days.append({'day': i + 1, 'predicted_yield': round(pred, 2)})
                    
                    if risk_days:
                        predictions[f"{supplier}_{process}"] = {
                            'trend_slope': model.coef_[0],
                            'current_yield': y[-1],
                            'target_yield': target_yield,
                            'risk_days': risk_days,
                            'confidence': '高' if model.score(X, y) > 0.8 else '中',
                            'r_squared': model.score(X, y)
                        }
        
        return predictions
    
    def get_yield_forecast_data(self, counting_data: pd.DataFrame, supplier: str, process: str, days_ahead: int = 7) -> Dict:
        """获取详细的良率预测数据，用于绘图"""
        group_data = counting_data[
            (counting_data['供应商名称'] == supplier) & 
            (counting_data['工序'] == process)
        ].sort_values('日期')
        
        if len(group_data) < 5:
            return None
        
        # 历史数据
        dates = group_data['日期'].values
        yields = group_data['合格率(%)'].values
        
        # 线性回归模型
        X = np.arange(len(group_data)).reshape(-1, 1)
        y = yields
        model = LinearRegression()
        model.fit(X, y)
        
        # 预测未来
        future_X = np.arange(len(group_data), len(group_data) + days_ahead).reshape(-1, 1)
        future_y = model.predict(future_X)
        
        # 生成未来日期
        last_date = pd.to_datetime(dates[-1])
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days_ahead)
        
        # 计算置信区间（简化版本）
        y_pred_history = model.predict(X)
        residuals = y - y_pred_history
        std_error = np.std(residuals)
        
        # 95% 置信区间
        upper_bound = future_y + 1.96 * std_error
        lower_bound = future_y - 1.96 * std_error
        
        target_yield = group_data['合格率目标(%)'].iloc[-1]
        
        return {
            'historical_dates': dates,
            'historical_yields': yields,
            'future_dates': future_dates,
            'predicted_yields': future_y,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound,
            'target_yield': target_yield,
            'trend_slope': model.coef_[0],
            'r_squared': model.score(X, y),
            'model': model
        }
    
    def predict_defect_correlation(self, metric_data: pd.DataFrame, counting_data: pd.DataFrame) -> Dict:
        if len(metric_data) == 0:
            return {}
        
        correlations = {}
        for char in metric_data['质量特性'].unique():
            char_data = metric_data[metric_data['质量特性'] == char]
            char_std = char_data['实际测量值'].std()
            
            if char_std > char_data['规格'].iloc[0] * 0.1:
                correlations[char] = {
                    '波动程度': round(char_std, 4),
                    '风险等级': '高风险' if char_std > 0.5 else '中风险'
                }
        
        return correlations

def load_sample_data():
    """生成示例数据"""
    dates = pd.date_range(start='2026-03-01', end='2026-03-31', freq='D')
    suppliers = ['中航三鑫', '鹏鼎控股', '建滔', '景旺电子', '生益']
    characteristics = ['阻抗', '线宽', '插损', '背钻偏心度', '背钻stub']
    processes = ['SMT', 'DIP', '电测试', '终检']
    
    metric_data = []
    for date in dates:
        for supplier in suppliers:
            for i in range(3):
                lot_num = f"LOT{date.strftime('%Y%m%d')}{i+1:02d}"
                for char in characteristics:
                    if char == '阻抗':
                        spec_center, usl, lsl = 93, 99.51, 86.49
                        actual = np.random.normal(93, 2)
                    elif char == '线宽':
                        spec_center, usl, lsl = 4, 4.4, 3.6
                        actual = np.random.normal(4, 0.1)
                    elif char == '插损':
                        # 插入损耗(dB)，负值，越小越好
                        spec_center, usl, lsl = -0.68, -0.3, -1.2
                        actual = np.random.normal(-0.68, 0.15)
                    elif char == '背钻偏心度':
                        spec_center, usl, lsl = 0.9, 1.8, 0
                        actual = np.random.uniform(0.3, 1.5)
                    else:  # 背钻stub
                        spec_center, usl, lsl = 5, 8, 2
                        actual = np.random.uniform(3, 6.5)
                    
                    metric_data.append({
                        '日期': date, '供应商名称': supplier, '物料编码': 'V-09480052-100',
                        'DC': '202610', 'lot': lot_num, 'SN': f"SN{len(metric_data)+1:06d}",
                        '质量特性': char, '单位': 'Ω' if char=='阻抗' else 'mil',
                        '规格': spec_center, '实际测量值': round(actual, 3),
                        '规格中心': spec_center, '规格上限': usl, '规格下限': lsl
                    })
    
    counting_data = []
    for date in dates:
        for supplier in suppliers:
            for process in processes:
                production_qty = np.random.randint(800, 1500)
                合格_qty = int(production_qty * np.random.uniform(0.88, 0.98))
                合格率 = round((合格_qty / production_qty) * 100, 2)
                不良问题 = '无' if 合格率 > 93 else np.random.choice(['焊接不良', '元件偏移', '短路'])
                
                counting_data.append({
                    '日期': date, '供应商名称': supplier, '物料编码': 'V-09480052-100',
                    '工序': process, '批次号': f"P{date.strftime('%Y%m%d')}{supplier[:2]}{process[:1]}",
                    '生产数量': production_qty, '合格品数量': 合格_qty,
                    '合格率(%)': 合格率, '合格率目标(%)': 95.0, '不良主要问题': 不良问题
                })
    
    return pd.DataFrame(metric_data), pd.DataFrame(counting_data)

def main():
    st.markdown('<p class="main-title">📊 供应链质量智能分析平台</p>', unsafe_allow_html=True)
    
    analytics_engine = QualityAnalyticsEngine()
    ai_engine = AIPredictionEngine()
    
    # 加载数据
    with st.spinner("加载数据中..."):
        try:
            metric_df = pd.read_csv("supply_chain_data.csv")
            counting_df = pd.read_csv("counting_data.csv")
        except FileNotFoundError:
            metric_df, counting_df = load_sample_data()
    
    # 侧边栏
    with st.sidebar:
        st.header("筛选")
        min_date = metric_df['日期'].min().date()
        max_date = metric_df['日期'].max().date()
        start_date = st.date_input("开始", min_date)
        end_date = st.date_input("结束", max_date)
        
        all_suppliers = sorted(metric_df['供应商名称'].unique())
        selected_suppliers = st.multiselect("供应商", all_suppliers, default=all_suppliers[:3])
        
        all_chars = sorted(metric_df['质量特性'].unique())
        selected_char = st.selectbox("质量特性", all_chars)
        
        all_processes = sorted(counting_df['工序'].unique())
        selected_processes = st.multiselect("工序", all_processes, default=all_processes[:2])
    
    # 筛选数据
    filtered_metric = metric_df[
        (metric_df['日期'].dt.date >= start_date) & 
        (metric_df['日期'].dt.date <= end_date) &
        (metric_df['供应商名称'].isin(selected_suppliers)) &
        (metric_df['质量特性'] == selected_char)
    ]
    
    filtered_counting = counting_df[
        (counting_df['日期'].dt.date >= start_date) & 
        (counting_df['日期'].dt.date <= end_date) &
        (counting_df['供应商名称'].isin(selected_suppliers)) &
        (counting_df['工序'].isin(selected_processes))
    ]
    
    # 主内容
    tab1, tab2, tab3, tab4 = st.tabs(["指标预警", "计量分析", "计数分析", "闭环管理"])
    
    with tab1:
        # 顶部统计概览
        st.markdown("### 📊 核心指标仪表盘")
        
        # 第一行：主要KPI指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem 1.2rem; border-radius: 10px; text-align: center; color: white; min-height: 90px;"><div style="font-size: 0.95rem; opacity: 0.9;">🔬 检测样本数</div><div style="font-size: 1.6rem; font-weight: 700; margin: 0.3rem 0;">{len(filtered_metric):,}</div><div style="font-size: 0.85rem; opacity: 0.8;">总检测点数</div></div>', unsafe_allow_html=True)
        
        with col2:
            if len(filtered_counting) > 0:
                avg_yield = filtered_counting['合格率(%)'].mean()
                target_yield = 95.0
                yield_color = "#10b981" if avg_yield >= target_yield else "#f59e0b"
                yield_icon = "✅" if avg_yield >= target_yield else "⚠️"
                st.markdown(f'<div style="background: linear-gradient(135deg, {yield_color} 0%, #059669 100%); padding: 1rem 1.2rem; border-radius: 10px; text-align: center; color: white; min-height: 90px;"><div style="font-size: 0.95rem; opacity: 0.9;">{yield_icon} 平均良率</div><div style="font-size: 1.6rem; font-weight: 700; margin: 0.3rem 0;">{avg_yield:.2f}%</div><div style="font-size: 0.85rem; opacity: 0.8;">目标: {target_yield}%</div></div>', unsafe_allow_html=True)
        
        with col3:
            ooc_count = len(filtered_metric[
                (filtered_metric['实际测量值'] > filtered_metric['规格上限']) |
                (filtered_metric['实际测量值'] < filtered_metric['规格下限'])
            ])
            ooc_rate = (ooc_count / len(filtered_metric) * 100) if len(filtered_metric) > 0 else 0
            ooc_color = "#10b981" if ooc_rate == 0 else "#ef4444" if ooc_rate > 5 else "#f59e0b"
            st.markdown(f'<div style="background: linear-gradient(135deg, {ooc_color} 0%, #dc2626 100%); padding: 1rem 1.2rem; border-radius: 10px; text-align: center; color: white; min-height: 90px;"><div style="font-size: 0.95rem; opacity: 0.9;">⚠️ 超规率</div><div style="font-size: 1.6rem; font-weight: 700; margin: 0.3rem 0;">{ooc_rate:.2f}%</div><div style="font-size: 0.85rem; opacity: 0.8;">异常样本: {ooc_count}</div></div>', unsafe_allow_html=True)
        
        with col4:
            if len(filtered_metric) > 0:
                usl = filtered_metric['规格上限'].iloc[0]
                lsl = filtered_metric['规格下限'].iloc[0]
                cpk = analytics_engine.calculate_cpk(filtered_metric['实际测量值'], usl, lsl)
                cpk_val = f"{cpk:.3f}" if not np.isnan(cpk) else "N/A"
                cpk_color = "#10b981" if not np.isnan(cpk) and cpk >= 1.33 else "#ef4444"
                cpk_status = "优秀" if not np.isnan(cpk) and cpk >= 1.33 else "需改善"
                st.markdown(f'<div style="background: linear-gradient(135deg, {cpk_color} 0%, #059669 100%); padding: 1rem 1.2rem; border-radius: 10px; text-align: center; color: white; min-height: 90px;"><div style="font-size: 0.95rem; opacity: 0.9;">📈 过程能力CPK</div><div style="font-size: 1.6rem; font-weight: 700; margin: 0.3rem 0;">{cpk_val}</div><div style="font-size: 0.85rem; opacity: 0.8;">状态: {cpk_status}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 第二行：CPK仪表盘和良率仪表盘
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**CPK能力仪表盘**")
            if len(filtered_metric) > 0:
                usl = filtered_metric['规格上限'].iloc[0]
                lsl = filtered_metric['规格下限'].iloc[0]
                
                # 检查规格限是否有效
                if pd.isna(usl) and pd.isna(lsl):
                    st.warning("该质量特性无规格限，无法计算CPK")
                else:
                    cpk = analytics_engine.calculate_cpk(filtered_metric['实际测量值'], usl, lsl)
                    
                    if not np.isnan(cpk):
                        # 创建仪表盘图
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = cpk,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            delta = {'reference': 1.33, 'increasing': {'color': "green"}},
                            gauge = {
                                'axis': {'range': [0, 3], 'tickwidth': 1, 'tickcolor': "darkblue"},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 1], 'color': "rgba(255, 0, 0, 0.3)"},
                                    {'range': [1, 1.33], 'color': "rgba(255, 165, 0, 0.3)"},
                                    {'range': [1.33, 2], 'color': "rgba(0, 255, 0, 0.3)"},
                                    {'range': [2, 3], 'color': "rgba(0, 128, 0, 0.5)"}],
                                'threshold': {
                                    'line': {'color': "red", 'width': 3},
                                    'thickness': 0.75,
                                    'value': 1.33
                                }
                            },
                            title = {'text': f"CPK = {cpk:.3f}", 'font': {'size': 14}}
                        ))
                        fig_gauge.update_layout(height=240, margin=dict(l=30, r=30, t=40, b=10))
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                        # 显示规格限信息
                        spec_info = f"规格中心: {filtered_metric['规格中心'].iloc[0]}"
                        if not pd.isna(usl):
                            spec_info += f" | 上限: {usl}"
                        if not pd.isna(lsl):
                            spec_info += f" | 下限: {lsl}"
                        st.caption(spec_info)
                    else:
                        st.info("无法计算CPK（数据标准差为0）")
            else:
                st.info("请选择筛选条件查看CPK")
        
        with col2:
            st.markdown("**良率达成仪表盘**")
            if len(filtered_counting) > 0:
                avg_yield = filtered_counting['合格率(%)'].mean()
                target_yield = 95.0
                
                # 创建仪表盘图
                fig_yield_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = avg_yield,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    delta = {'reference': target_yield},
                    gauge = {
                        'axis': {'range': [80, 100]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [80, 90], 'color': "rgba(255, 0, 0, 0.3)"},
                            {'range': [90, 95], 'color': "rgba(255, 165, 0, 0.3)"},
                            {'range': [95, 100], 'color': "rgba(0, 255, 0, 0.3)"}],
                        'threshold': {
                            'line': {'color': "red", 'width': 3},
                            'thickness': 0.75,
                            'value': target_yield
                        }
                    },
                    title = {'text': f"良率 = {avg_yield:.2f}%", 'font': {'size': 12}}
                ))
                fig_yield_gauge.update_layout(height=220, margin=dict(l=30, r=30, t=40, b=10))
                st.plotly_chart(fig_yield_gauge, use_container_width=True)
        
        st.markdown("---")
        
        # 第三行：供应商对比雷达图和预警统计
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**供应商质量综合评分**")
            if len(filtered_metric) > 0 and len(selected_suppliers) > 0:
                # 计算各供应商得分
                supplier_scores = []
                for supplier in selected_suppliers:
                    s_data = filtered_metric[filtered_metric['供应商名称'] == supplier]
                    s_counting = filtered_counting[filtered_counting['供应商名称'] == supplier]
                    
                    if len(s_data) > 0:
                        # CPK得分
                        usl = s_data['规格上限'].iloc[0]
                        lsl = s_data['规格下限'].iloc[0]
                        cpk = analytics_engine.calculate_cpk(s_data['实际测量值'], usl, lsl)
                        cpk_score = min(cpk / 2.0 * 100, 100) if not np.isnan(cpk) else 50
                        
                        # 良率得分
                        yield_score = s_counting['合格率(%)'].mean() if len(s_counting) > 0 else 85
                        
                        # 超规率得分（越低越好）
                        ooc_count = len(s_data[(s_data['实际测量值'] > s_data['规格上限']) | (s_data['实际测量值'] < s_data['规格下限'])])
                        ooc_rate = (ooc_count / len(s_data) * 100) if len(s_data) > 0 else 0
                        ooc_score = max(100 - ooc_rate * 10, 0)
                        
                        # 稳定性得分
                        std_score = max(100 - s_data['实际测量值'].std() * 20, 0)
                        
                        supplier_scores.append({
                            'supplier': supplier,
                            'CPK能力': cpk_score,
                            '良率水平': yield_score,
                            '超规控制': ooc_score,
                            '过程稳定': std_score
                        })
                
                if supplier_scores:
                    # 创建雷达图
                    categories = ['CPK能力', '良率水平', '超规控制', '过程稳定']
                    fig_radar = go.Figure()
                    
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                    for i, score in enumerate(supplier_scores[:5]):
                        fig_radar.add_trace(go.Scatterpolar(
                            r = [score['CPK能力'], score['良率水平'], score['超规控制'], score['过程稳定']],
                            theta = categories,
                            fill = 'toself',
                            name = score['supplier'],
                            line_color = colors[i % len(colors)]
                        ))
                    
                    fig_radar.update_layout(
                        polar = dict(radialaxis = dict(visible = True, range = [0, 100])),
                        showlegend = True,
                        height = 280,
                        margin=dict(l=40, r=40, t=20, b=20),
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(size=9))
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
        
        with col2:
            st.markdown("**四道红线预警状态**")
            
            if len(filtered_metric) > 0:
                violations = analytics_engine.detect_violations(filtered_metric)
                
                # 计算各指标状态
                ooc_count = len(violations.get('超规检测', []))
                cpk_issues = violations.get('CPK不足', [])
                
                # 预警状态卡片
                status_cards = [
                    ("超规检测", ooc_count == 0, str(ooc_count) if ooc_count > 0 else ""),
                    ("CPK能力", len(cpk_issues) == 0, f"{cpk_issues[0]['cpk']:.2f}" if cpk_issues else ""),
                    ("趋势监控", True, ""),
                    ("分布稳定", True, "")
                ]
                
                status_html = '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">'
                for name, is_ok, extra in status_cards:
                    color = "#10b981" if is_ok else "#ef4444"
                    icon = "✅" if is_ok else "⚠️"
                    status_text = "正常" if is_ok else "预警"
                    status_html += f'<div style="background: {color}; padding: 0.6rem 0.8rem; border-radius: 8px; text-align: center; color: white;"><div style="font-size: 0.9rem;">{icon} {name}</div><div style="font-size: 1rem; font-weight: 600;">{status_text}</div><div style="font-size: 0.8rem; opacity: 0.9;">{extra}</div></div>'
                status_html += '</div>'
                st.markdown(status_html, unsafe_allow_html=True)
                
                # 预警详情
                if ooc_count > 0:
                    st.markdown(f"<div style='background:#fee2e2; padding:0.5rem 0.7rem; border-radius:6px; font-size:0.9rem; margin-top:0.5rem;'>⚠️ 发现 {ooc_count} 个超规数据点</div>", unsafe_allow_html=True)
                
                if cpk_issues:
                    st.markdown(f"<div style='background:#fee2e2; padding:0.5rem 0.7rem; border-radius:6px; font-size:0.9rem; margin-top:0.4rem;'>🔴 CPK不足: {cpk_issues[0]['cpk']:.3f}，需要改进</div>", unsafe_allow_html=True)
            else:
                st.info("请选择筛选条件查看预警状态")
        
        st.markdown("---")
        
        # 第四行：AI预测和趋势
        st.markdown("### 🤖 AI智能预警")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if len(filtered_counting) > 0:
                predictions = ai_engine.predict_yield_trend(filtered_counting)
                
                if predictions:
                    pred_html = '<div style="display: grid; gap: 0.5rem;">'
                    for key, pred in list(predictions.items())[:4]:
                        parts = key.split('_')
                        supplier = parts[0] if len(parts) > 0 else key
                        process = '_'.join(parts[1:]) if len(parts) > 1 else ""
                        
                        if pred.get('risk_days'):
                            days = pred['risk_days'][0]['day']
                            pred_yield = pred['risk_days'][0]['predicted_yield']
                            confidence = pred.get('confidence', '中')
                            
                            pred_html += f'<div style="background: linear-gradient(90deg, #fff3e0 0%, #ffe0b2 100%); padding: 0.7rem 1rem; border-radius: 8px; border-left: 4px solid #f57c00;"><div style="font-size: 1rem; font-weight: 600;">📉 {supplier} - {process}</div><div style="font-size: 0.95rem; color: #666;">预测 <b>{days}天后</b> 跌破目标，预计良率: <b>{pred_yield:.2f}%</b></div><div style="font-size: 0.85rem; color: #999;">置信度: {confidence}</div></div>'
                    pred_html += '</div>'
                    st.markdown(pred_html, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background: #ecfdf5; padding: 0.8rem 1rem; border-radius: 8px; border-left: 4px solid #10b981;"><div style="font-size: 1rem; color: #065f46; font-weight: 600;">✅ 良率状态稳定</div><div style="font-size: 0.9rem; color: #047857;">各供应商工序良率预测正常，暂无跌破风险</div></div>', unsafe_allow_html=True)
            else:
                st.info("请选择筛选条件查看AI预警")
        
        with col2:
            st.markdown("**风险等级分布**")
            if len(filtered_counting) > 0:
                risk_counts = filtered_counting.groupby('供应商名称').apply(
                    lambda x: len(x[x['合格率(%)'] < 95])
                ).reset_index()
                risk_counts.columns = ['供应商', '风险批次']
                
                if risk_counts['风险批次'].sum() > 0:
                    fig_risk = px.bar(risk_counts, x='供应商', y='风险批次',
                                     color='风险批次',
                                     color_continuous_scale='RdYlGn_r',
                                     title='各供应商风险批次数')
                    fig_risk.update_layout(height=260, margin=dict(l=30, r=30, t=40, b=30))
                    st.plotly_chart(fig_risk, use_container_width=True)
                else:
                    st.markdown('<div style="background: #f0fdf4; padding: 1.2rem; border-radius: 8px; text-align: center;"><div style="font-size: 1rem; color: #16a34a;">✅ 所有供应商良率达标</div><div style="font-size: 0.9rem; color: #15803d;">无风险批次</div></div>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("趋势控制图")
        
        if len(filtered_metric) > 0:
            fig = go.Figure()
            
            for supplier in selected_suppliers:
                data = filtered_metric[filtered_metric['供应商名称'] == supplier]
                if len(data) > 0:
                    fig.add_trace(go.Scatter(
                        x=data['日期'], y=data['实际测量值'],
                        mode='markers', name=supplier, marker=dict(size=6)
                    ))
            
            spec_center = filtered_metric['规格中心'].iloc[0]
            usl = filtered_metric['规格上限'].iloc[0]
            lsl = filtered_metric['规格下限'].iloc[0]
            
            fig.add_hline(y=spec_center, line_color="green", line_dash="solid")
            if not pd.isna(usl):
                fig.add_hline(y=usl, line_color="red", line_dash="dash")
            if not pd.isna(lsl):
                fig.add_hline(y=lsl, line_color="red", line_dash="dash")
            
            fig.update_layout(height=350, margin=dict(l=40, r=40, t=30, b=30))
            st.plotly_chart(fig, use_container_width=True)
            
            # 箱线图
            fig_box = px.box(filtered_metric, x='供应商名称', y='实际测量值')
            fig_box.update_layout(height=300, margin=dict(l=40, r=40, t=30, b=30))
            st.plotly_chart(fig_box, use_container_width=True)
    
    with tab3:
        st.subheader("良率趋势与预测")
        
        if len(filtered_counting) > 0:
            # 历史良率趋势图 - 先按日期和供应商聚合
            trend_data = filtered_counting.groupby(['日期', '供应商名称']).agg({
                '合格率(%)': 'mean',
                '生产数量': 'sum',
                '合格品数量': 'sum',
                '合格率目标(%)': 'first'
            }).reset_index()
            
            # 重新计算聚合后的合格率
            trend_data['合格率(%)'] = round(trend_data['合格品数量'] / trend_data['生产数量'] * 100, 2)
            
            fig = px.bar(trend_data, x='日期', y='合格率(%)', color='供应商名称',
                        barmode='group', title='历史良率趋势')
            target = trend_data['合格率目标(%)'].iloc[0]
            fig.add_hline(y=target, line_color="red", line_dash="dash",
                         annotation_text=f"目标 {target}%")
            fig.update_layout(height=280, margin=dict(l=40, r=40, t=30, b=30),
                            yaxis=dict(range=[80, 100]))  # 限制Y轴范围
            st.plotly_chart(fig, use_container_width=True)
            
            # 良率预测部分
            st.subheader("AI良率趋势预测")
            
            # 预测参数设置
            col1, col2 = st.columns([3, 1])
            with col2:
                predict_days = st.select_slider("预测天数", options=[3, 5, 7, 10, 14], value=7)
            
            # 获取预测数据并展示
            suppliers_to_predict = st.multiselect(
                "选择预测供应商", 
                filtered_counting['供应商名称'].unique(),
                default=filtered_counting['供应商名称'].unique()[:2]
            )
            
            if suppliers_to_predict and len(selected_processes) > 0:
                process_to_predict = selected_processes[0]  # 默认第一个工序
                
                for supplier in suppliers_to_predict:
                    forecast_data = ai_engine.get_yield_forecast_data(
                        filtered_counting, supplier, process_to_predict, predict_days
                    )
                    
                    if forecast_data:
                        st.markdown(f"**{supplier} - {process_to_predict}**")
                        
                        # 创建预测图表
                        fig_pred = go.Figure()
                        
                        # 历史数据
                        fig_pred.add_trace(go.Scatter(
                            x=forecast_data['historical_dates'],
                            y=forecast_data['historical_yields'],
                            mode='markers+lines',
                            name='历史良率',
                            line=dict(color='#1f77b4', width=2),
                            marker=dict(size=6)
                        ))
                        
                        # 预测数据
                        fig_pred.add_trace(go.Scatter(
                            x=forecast_data['future_dates'],
                            y=forecast_data['predicted_yields'],
                            mode='lines+markers',
                            name='预测良率',
                            line=dict(color='#ff7f0e', width=2, dash='dot'),
                            marker=dict(size=6, symbol='diamond')
                        ))
                        
                        # 置信区间上界
                        fig_pred.add_trace(go.Scatter(
                            x=forecast_data['future_dates'],
                            y=forecast_data['upper_bound'],
                            mode='lines',
                            name='95%置信上界',
                            line=dict(color='#ff7f0e', width=1, dash='dash'),
                            showlegend=False
                        ))
                        
                        # 置信区间下界
                        fig_pred.add_trace(go.Scatter(
                            x=forecast_data['future_dates'],
                            y=forecast_data['lower_bound'],
                            mode='lines',
                            name='95%置信区间',
                            line=dict(color='#ff7f0e', width=1, dash='dash'),
                            fill='tonexty',
                            fillcolor='rgba(255, 127, 14, 0.1)'
                        ))
                        
                        # 目标线
                        fig_pred.add_hline(
                            y=forecast_data['target_yield'],
                            line_color="red",
                            line_dash="solid",
                            annotation_text=f"目标 {forecast_data['target_yield']}%"
                        )
                        
                        # 标记跌破风险点
                        for i, pred_yield in enumerate(forecast_data['predicted_yields']):
                            if pred_yield < forecast_data['target_yield']:
                                fig_pred.add_annotation(
                                    x=forecast_data['future_dates'][i],
                                    y=pred_yield,
                                    text="⚠️跌破风险",
                                    showarrow=True,
                                    arrowhead=2,
                                    arrowcolor="red",
                                    font=dict(color="red", size=10)
                                )
                                break
                        
                        fig_pred.update_layout(
                            height=280,
                            margin=dict(l=40, r=40, t=20, b=30),
                            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                            xaxis_title="日期",
                            yaxis_title="良率 (%)"
                        )
                        
                        st.plotly_chart(fig_pred, use_container_width=True)
                        
                        # 预测统计信息
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            trend_icon = "📈" if forecast_data['trend_slope'] > 0 else "📉"
                            trend_text = "上升" if forecast_data['trend_slope'] > 0 else "下降"
                            st.metric("趋势", f"{trend_icon} {trend_text}", f"{forecast_data['trend_slope']:.3f}%/天")
                        with col2:
                            st.metric("R²拟合度", f"{forecast_data['r_squared']:.2%}")
                        with col3:
                            last_pred = forecast_data['predicted_yields'][-1]
                            st.metric(f"{predict_days}天后预测", f"{last_pred:.2f}%")
                        with col4:
                            days_to_risk = None
                            for i, pred in enumerate(forecast_data['predicted_yields']):
                                if pred < forecast_data['target_yield']:
                                    days_to_risk = i + 1
                                    break
                            if days_to_risk:
                                st.metric("跌破风险", f"{days_to_risk}天后", delta_color="inverse")
                            else:
                                st.metric("跌破风险", "暂无", delta_color="normal")
                        
                        st.markdown("---")
            
            # 帕累托图
            st.subheader("不良原因分析")
            defect_data = filtered_counting[filtered_counting['不良主要问题'] != '无']
            if len(defect_data) > 0:
                defect_counts = defect_data['不良主要问题'].value_counts()
                defect_pct = defect_counts / defect_counts.sum() * 100
                cumulative_pct = defect_pct.cumsum()
                
                fig_pareto = go.Figure()
                fig_pareto.add_trace(go.Bar(
                    x=defect_counts.index,
                    y=defect_counts.values,
                    name='不良频次',
                    marker_color='#1f77b4'
                ))
                fig_pareto.add_trace(go.Scatter(
                    x=defect_counts.index,
                    y=cumulative_pct,
                    name='累计百分比',
                    yaxis='y2',
                    mode='lines+markers',
                    marker=dict(color='#d62728', size=6)
                ))
                
                fig_pareto.update_layout(
                    height=280,
                    margin=dict(l=40, r=40, t=20, b=30),
                    yaxis=dict(title='不良频次'),
                    yaxis2=dict(title='累计百分比(%)', overlaying='y', side='right', range=[0, 105]),
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.4)
                )
                
                st.plotly_chart(fig_pareto, use_container_width=True)
                
                # 不良统计表
                with st.expander("详细不良统计", expanded=False):
                    defect_df = pd.DataFrame({
                        '不良类型': defect_counts.index,
                        '发生次数': defect_counts.values,
                        '占比(%)': defect_pct.round(2).values,
                        '累计占比(%)': cumulative_pct.round(2).values
                    })
                    st.dataframe(defect_df, use_container_width=True, hide_index=True)
            else:
                st.success("当前无不良记录")
        else:
            st.info("暂无计数型数据")
    
    with tab4:
        st.subheader("工单管理")
        
        # 简化工单表单
        with st.form("work_order"):
            st.selectbox("工单类型", ["纠正工单", "预防工单"])
            st.text_area("问题描述", height=80)
            st.text_area("改善措施", height=80)
            st.select_slider("优先级", options=["低", "中", "高", "紧急"])
            submitted = st.form_submit_button("提交工单")
            if submitted:
                st.success("工单已提交")
        
        # 数据导出
        st.subheader("数据导出")
        if st.button("导出异常数据"):
            abnormal = filtered_metric[
                (filtered_metric['实际测量值'] > filtered_metric['规格上限']) |
                (filtered_metric['实际测量值'] < filtered_metric['规格下限'])
            ]
            
            if len(abnormal) > 0:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    abnormal.to_excel(writer, index=False)
                output.seek(0)
                
                st.download_button(
                    label="下载Excel",
                    data=output,
                    file_name=f"异常数据_{datetime.now().strftime('%Y%m%d')}.xlsx"
                )
            else:
                st.info("暂无异常数据")

if __name__ == "__main__":
    main()
