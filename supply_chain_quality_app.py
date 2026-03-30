import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import warnings
warnings.filterwarnings('ignore')

# 设置页面配置
st.set_page_config(
    page_title="供应链质量智能分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .warning-card {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-card {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def calculate_cpk(data, usl, lsl, mean_val, std_val):
    """计算过程能力指数CPK"""
    if pd.isna(usl) or pd.isna(lsl):
        if pd.isna(usl):
            cpk = (mean_val - lsl) / (3 * std_val) if not pd.isna(lsl) else np.nan
        else:
            cpk = (usl - mean_val) / (3 * std_val) if not pd.isna(usl) else np.nan
    else:
        cpu = (usl - mean_val) / (3 * std_val)
        cpl = (mean_val - lsl) / (3 * std_val)
        cpk = min(cpu, cpl)
    
    return round(cpk, 4) if not np.isnan(cpk) else np.nan

def load_sample_data():
    """生成示例数据用于演示"""
    # 创建示例数据
    dates = pd.date_range(start='2026-03-01', end='2026-03-31', freq='D')
    suppliers = ['中航三鑫', '鹏鼎控股', '建滔', '景旺电子', '生益', '深南电路', '华正新材']
    characteristics = ['阻抗', '线宽', '插损', '背钻偏心度', '背钻stub']
    
    data_list = []
    
    for date in dates:
        for supplier in suppliers:
            for i in range(4):  # 每个供应商每天4个样本
                lot_num = f"LOT{date.strftime('%Y%m%d')}{str(i+1).zfill(2)}"
                sn_num = f"SN{str(len(data_list)+1).zfill(6)}"
                
                # 随机选择质量特性
                char = np.random.choice(characteristics)
                
                # 根据特性设置规格和实际值
                if char == '阻抗':
                    spec_center, usl, lsl = 93, 99.51, 86.49
                    unit = 'Ω'
                    actual = np.random.normal(93, 2)
                elif char == '线宽':
                    spec_center, usl, lsl = 4, 4.4, 3.6
                    unit = 'mil'
                    actual = np.random.normal(4, 0.1)
                elif char == '插损':
                    spec_center, usl, lsl = -0.68, np.nan, np.nan  # 只有上限
                    unit = 'db'
                    actual = np.random.normal(-0.68, 0.05)
                elif char == '背钻偏心度':
                    spec_center, usl, lsl = 6, 1.8, 0
                    unit = 'mil'
                    actual = np.random.uniform(0, 1.8)
                else:  # 背钻stub
                    spec_center, usl, lsl = 5, 8, 2
                    unit = 'mil'
                    actual = np.random.uniform(2, 8)
                
                data_list.append({
                    '日期': date,
                    '供应商名称': supplier,
                    '物料编码': 'V-09480052-100',
                    'DC': '202610',
                    'lot': lot_num,
                    'SN': sn_num,
                    '质量特性': char,
                    '单位': unit,
                    '规格': spec_center,
                    '实际测量值': round(actual, 2),
                    '规格中心': spec_center,
                    '规格上限': usl,
                    '规格下限': lsl
                })
    
    df = pd.DataFrame(data_list)
    
    # 添加计数型数据
    counting_data = []
    processes = ['SMT', 'DIP', '测试', '包装']
    
    for date in dates:
        for supplier in suppliers:
            for process in processes:
                lot_num = f"LOT{date.strftime('%Y%m%d')}{supplier[:2]}"
                production_qty = np.random.randint(800, 1200)
                合格_qty = int(production_qty * np.random.uniform(0.85, 0.98))
                合格率 = round((合格_qty / production_qty) * 100, 2)
                合格率目标 = 95.0
                
                # 随机生成不良问题
                if 合格率 < 90:
                    不良问题 = np.random.choice(['焊接不良', '元件偏移', '短路', '开路'], p=[0.4, 0.3, 0.2, 0.1])
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
    
    counting_df = pd.DataFrame(counting_data)
    
    return df, counting_df

def main():
    st.markdown("<h1 class='main-header'>📊 供应链质量智能分析平台</h1>", unsafe_allow_html=True)
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        try:
            # 尝试读取真实Excel文件
            metric_df = pd.read_excel("Expanded_PCB_Data_1000.xlsx", sheet_name="Sheet1")
            # 如果有计数型数据sheet也读取
            try:
                counting_df = pd.read_excel("Expanded_PCB_Data_1000.xlsx", sheet_name="计数型数据")
            except:
                # 如果没有计数型数据sheet，生成示例数据
                _, counting_df = load_sample_data()
        except FileNotFoundError:
            # 如果文件不存在，使用示例数据
            st.info("未找到Excel文件，使用示例数据进行演示")
            metric_df, counting_df = load_sample_data()
    
    # 侧边栏筛选器
    st.sidebar.header("🔍 数据筛选器")
    
    # 时间范围选择
    min_date = metric_df['日期'].min().date()
    max_date = metric_df['日期'].max().date()
    
    start_date = st.sidebar.date_input("开始日期", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("结束日期", max_date, min_value=start_date, max_value=max_date)
    
    # 供应商多选
    all_suppliers = sorted(metric_df['供应商名称'].unique())
    selected_suppliers = st.sidebar.multiselect("选择供应商", all_suppliers, default=all_suppliers)
    
    # 质量特性单选
    all_characteristics = sorted(metric_df['质量特性'].unique())
    selected_characteristic = st.sidebar.selectbox("选择质量特性", all_characteristics)
    
    # 工序选择（计数型数据）
    all_processes = sorted(counting_df['工序'].unique())
    selected_process = st.sidebar.selectbox("选择工序", all_processes)
    
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
        (counting_df['工序'] == selected_process)
    ]
    
    # 主页面布局
    tab1, tab2, tab3 = st.tabs(["📈 KPI概览", "📏 计量型分析", "📊 计数型分析"])
    
    with tab1:
        st.header("核心指标与预警概览")
        
        # KPI指标卡
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_production = filtered_counting['生产数量'].sum()
            st.metric("生产总数量", f"{total_production:,}")
            
        with col2:
            avg_yield = filtered_counting['合格率(%)'].mean()
            st.metric("平均合格率", f"{avg_yield:.2f}%")
            
        with col3:
            total_samples = len(filtered_metric)
            st.metric("检测样本数", f"{total_samples:,}")
            
        with col4:
            ooc_count = len(filtered_metric[
                (filtered_metric['实际测量值'] > filtered_metric['规格上限']) |
                (filtered_metric['实际测量值'] < filtered_metric['规格下限'])
            ])
            ooc_rate = (ooc_count / total_samples * 100) if total_samples > 0 else 0
            st.metric("超规率", f"{ooc_rate:.2f}%")
        
        # CPK预警分析
        st.subheader("智能预警分析")
        
        if len(filtered_metric) > 0:
            # 计算CPK
            mean_val = filtered_metric['实际测量值'].mean()
            std_val = filtered_metric['实际测量值'].std()
            usl = filtered_metric['规格上限'].iloc[0]
            lsl = filtered_metric['规格下限'].iloc[0]
            
            cpk = calculate_cpk(filtered_metric, usl, lsl, mean_val, std_val)
            
            # 显示CPK结果
            if not np.isnan(cpk):
                if cpk < 1.33:
                    st.error(f"⚠️ 制程能力不足 (CPK={cpk:.4f})，存在超规风险！")
                    
                    # 详细预警信息
                    for supplier in selected_suppliers:
                        supplier_data = filtered_metric[filtered_metric['供应商名称'] == supplier]
                        if len(supplier_data) > 0:
                            supplier_cpk = calculate_cpk(
                                supplier_data, 
                                supplier_data['规格上限'].iloc[0],
                                supplier_data['规格下限'].iloc[0],
                                supplier_data['实际测量值'].mean(),
                                supplier_data['实际测量值'].std()
                            )
                            if not np.isnan(supplier_cpk) and supplier_cpk < 1.33:
                                st.warning(f"🔸 {supplier} 的 {selected_characteristic} CPK = {supplier_cpk:.4f}")
                else:
                    st.success(f"✅ 制程能力良好 (CPK={cpk:.4f})")
            else:
                st.warning("无法计算CPK值，请检查规格限设置")
        else:
            st.info("暂无数据可分析")
    
    with tab2:
        st.header("计量型数据深度分析")
        
        if len(filtered_metric) > 0:
            # 趋势控制图
            st.subheader("趋势控制图")
            
            fig_trend = go.Figure()
            
            # 为每个供应商绘制数据
            for supplier in selected_suppliers:
                supplier_data = filtered_metric[filtered_metric['供应商名称'] == supplier]
                if len(supplier_data) > 0:
                    # 添加实际测量值
                    fig_trend.add_trace(go.Scatter(
                        x=supplier_data['日期'],
                        y=supplier_data['实际测量值'],
                        mode='markers+lines',
                        name=f'{supplier}',
                        marker=dict(size=8)
                    ))
            
            # 添加规格线
            spec_center = filtered_metric['规格中心'].iloc[0]
            usl = filtered_metric['规格上限'].iloc[0]
            lsl = filtered_metric['规格下限'].iloc[0]
            
            fig_trend.add_hline(y=spec_center, line_dash="solid", line_color="green", 
                              annotation_text="规格中心", annotation_position="top left")
            
            if not pd.isna(usl):
                fig_trend.add_hline(y=usl, line_dash="dash", line_color="red",
                                  annotation_text="USL", annotation_position="top right")
            
            if not pd.isna(lsl):
                fig_trend.add_hline(y=lsl, line_dash="dash", line_color="red",
                                  annotation_text="LSL", annotation_position="bottom right")
            
            # 标记超规点
            ooc_points = filtered_metric[
                (filtered_metric['实际测量值'] > filtered_metric['规格上限']) |
                (filtered_metric['实际测量值'] < filtered_metric['规格下限'])
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
                title=f"{selected_characteristic} 趋势控制图",
                xaxis_title="日期",
                yaxis_title=f"测量值 ({filtered_metric['单位'].iloc[0]})",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # CPK分布图
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("过程能力分布图")
                
                fig_hist = go.Figure()
                
                # 绘制直方图
                fig_hist.add_trace(go.Histogram(
                    x=filtered_metric['实际测量值'],
                    name='测量值分布',
                    nbinsx=30,
                    opacity=0.7
                ))
                
                # 添加正态分布拟合曲线
                x_norm = np.linspace(filtered_metric['实际测量值'].min(), 
                                   filtered_metric['实际测量值'].max(), 100)
                y_norm = np.exp(-0.5 * ((x_norm - mean_val) / std_val) ** 2) / (std_val * np.sqrt(2 * np.pi))
                y_norm = y_norm * len(filtered_metric) * (filtered_metric['实际测量值'].max() - filtered_metric['实际测量值'].min()) / 30
                
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
                    xaxis_title=f"测量值 ({filtered_metric['单位'].iloc[0]})",
                    yaxis_title="频次"
                )
                
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                st.subheader("统计指标")
                st.metric("样本均值", f"{mean_val:.4f}")
                st.metric("标准差", f"{std_val:.4f}")
                if not np.isnan(cpk):
                    st.metric("CPK值", f"{cpk:.4f}")
                else:
                    st.metric("CPK值", "N/A")
                
                # 供应商箱线图
                st.subheader("供应商对比")
                fig_box = px.box(filtered_metric, x='供应商名称', y='实际测量值',
                               title="各供应商测量值分布")
                fig_box.update_layout(showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("暂无计量型数据可分析")
    
    with tab3:
        st.header("计数型数据与良率分析")
        
        if len(filtered_counting) > 0:
            # 良率趋势图
            st.subheader("良率趋势对比")
            
            fig_yield = go.Figure()
            
            # 为每个供应商绘制良率
            for supplier in selected_suppliers:
                supplier_data = filtered_counting[filtered_counting['供应商名称'] == supplier]
                if len(supplier_data) > 0:
                    fig_yield.add_trace(go.Bar(
                        x=supplier_data['日期'],
                        y=supplier_data['合格率(%)'],
                        name=f'{supplier} 良率',
                        opacity=0.7
                    ))
            
            # 添加良率目标线
            yield_target = filtered_counting['合格率目标(%)'].iloc[0]
            fig_yield.add_hline(y=yield_target, line_dash="dash", line_color="orange",
                              annotation_text=f"目标良率 {yield_target}%", annotation_position="top right")
            
            fig_yield.update_layout(
                title=f"{selected_process} 工序良率趋势",
                xaxis_title="日期",
                yaxis_title="合格率 (%)",
                barmode='group'
            )
            
            st.plotly_chart(fig_yield, use_container_width=True)
            
            # 不良原因帕累托图
            st.subheader("不良原因分析 (帕累托图)")
            
            # 统计不良问题
            defect_data = filtered_counting[filtered_counting['不良主要问题'] != '无']
            
            if len(defect_data) > 0:
                defect_counts = defect_data['不良主要问题'].value_counts()
                
                # 计算累计百分比
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
                    title="不良原因帕累托分析",
                    xaxis_title="不良类型",
                    yaxis=dict(title="不良频次"),
                    yaxis2=dict(title="累计百分比 (%)", overlaying='y', side='right', range=[0, 100]),
                    legend=dict(x=0.7, y=0.9)
                )
                
                st.plotly_chart(fig_pareto, use_container_width=True)
                
                # 显示详细统计
                st.subheader("不良问题统计详情")
                defect_stats = pd.DataFrame({
                    '不良类型': defect_counts.index,
                    '发生次数': defect_counts.values,
                    '占比(%)': defect_percent.round(2),
                    '累计占比(%)': cumulative_percent.round(2)
                })
                st.dataframe(defect_stats, use_container_width=True)
            else:
                st.info("当前筛选条件下无不良记录")
        else:
            st.info("暂无计数型数据可分析")
    
    # 数据导出功能
    st.sidebar.header("💾 数据导出")
    
    if st.sidebar.button("导出异常数据"):
        # 筛选异常数据
        abnormal_metric = metric_df[
            (metric_df['实际测量值'] > metric_df['规格上限']) |
            (metric_df['实际测量值'] < metric_df['规格下限'])
        ]
        
        abnormal_counting = counting_df[
            counting_df['合格率(%)'] < counting_df['合格率目标(%)']
        ]
        
        if len(abnormal_metric) > 0 or len(abnormal_counting) > 0:
            # 创建Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if len(abnormal_metric) > 0:
                    abnormal_metric.to_excel(writer, sheet_name='计量型异常数据', index=False)
                if len(abnormal_counting) > 0:
                    abnormal_counting.to_excel(writer, sheet_name='计数型异常数据', index=False)
            
            output.seek(0)
            
            st.sidebar.download_button(
                label="📥 下载异常数据报告",
                data=output,
                file_name=f"质量异常数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.sidebar.success("异常数据已准备就绪！")
        else:
            st.sidebar.info("当前无异常数据需要导出")

if __name__ == "__main__":
    main()