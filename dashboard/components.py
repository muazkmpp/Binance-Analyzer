"""
Dashboard Components Module
Reusable components for the crypto dashboard
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DashboardComponents:
    """Reusable dashboard components"""
    
    @staticmethod
    def metric_card(title, value, delta=None, delta_color="normal", color="blue"):
        """Create a styled metric card"""
        color_map = {
            "blue": "#667eea",
            "green": "#48bb78", 
            "red": "#f56565",
            "purple": "#9f7aea",
            "orange": "#ed8936"
        }
        
        bg_color = color_map.get(color, "#667eea")
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {bg_color} 0%, {bg_color}aa 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin: 0.5rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0; font-size: 1rem; opacity: 0.9;">{title}</h4>
            <h2 style="margin: 0.5rem 0; font-size: 2rem;">{value}</h2>
            {f'<p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">{delta}</p>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def progress_ring(percentage, title, color="blue"):
        """Create a circular progress indicator"""
        color_map = {
            "blue": "#667eea",
            "green": "#48bb78",
            "red": "#f56565",
            "orange": "#ed8936"
        }
        
        stroke_color = color_map.get(color, "#667eea")
        
        fig = go.Figure(data=[go.Pie(
            values=[percentage, 100-percentage],
            hole=0.7,
            showlegend=False,
            textinfo='none',
            marker=dict(colors=[stroke_color, '#e2e8f0'])
        )])
        
        fig.add_annotation(
            text=f"{percentage:.1f}%",
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False
        )
        
        fig.update_layout(
            title=title,
            height=200,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def alert_box(message, alert_type="info"):
        """Create a styled alert box"""
        type_map = {
            "info": ("📊", "#667eea"),
            "success": ("✅", "#48bb78"),
            "warning": ("⚠️", "#ed8936"),
            "error": ("❌", "#f56565")
        }
        
        icon, color = type_map.get(alert_type, ("📊", "#667eea"))
        
        st.markdown(f"""
        <div style="
            background: {color}20;
            border-left: 4px solid {color};
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <strong>{icon} {message}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def mini_chart(data, title, chart_type="line", color="blue"):
        """Create a small chart for cards"""
        color_map = {
            "blue": "#667eea",
            "green": "#48bb78",
            "red": "#f56565",
            "purple": "#9f7aea"
        }
        
        line_color = color_map.get(color, "#667eea")
        
        if chart_type == "line":
            fig = px.line(data, x=data.index, y=data.values, 
                         title=title, color_discrete_sequence=[line_color])
        elif chart_type == "bar":
            fig = px.bar(data, x=data.index, y=data.values,
                        title=title, color_discrete_sequence=[line_color])
        
        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def comparison_table(data1, data2, title1, title2):
        """Create a side-by-side comparison table"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(title1)
            st.dataframe(data1, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader(title2)
            st.dataframe(data2, use_container_width=True, hide_index=True)
    
    @staticmethod
    def heatmap_chart(data, title):
        """Create a heatmap chart"""
        fig = px.imshow(data, title=title, color_continuous_scale='RdYlGn')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def gauge_chart(value, title, max_value=100, thresholds=None):
        """Create a gauge chart"""
        if thresholds is None:
            thresholds = {"low": 33, "medium": 66, "high": 100}
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title},
            delta = {'reference': thresholds["medium"]},
            gauge = {
                'axis': {'range': [None, max_value]},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, thresholds["low"]], 'color': "lightgray"},
                    {'range': [thresholds["low"], thresholds["medium"]], 'color': "yellow"},
                    {'range': [thresholds["medium"], thresholds["high"]], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': thresholds["high"]
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

class AdvancedCharts:
    """Advanced chart components"""
    
    @staticmethod
    def candlestick_chart(data, title):
        """Create a candlestick chart"""
        fig = go.Figure(data=go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close']
        ))
        
        fig.update_layout(
            title=title,
            yaxis_title='Price',
            xaxis_title='Date',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def correlation_heatmap(data, title):
        """Create correlation heatmap"""
        corr_matrix = data.corr()
        
        fig = px.imshow(
            corr_matrix,
            title=title,
            color_continuous_scale='RdBu',
            aspect="auto"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def distribution_plot(data, title, bins=30):
        """Create distribution plot with statistics"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Histogram', 'Box Plot'),
            vertical_spacing=0.1
        )
        
        # Histogram
        fig.add_trace(
            go.Histogram(x=data, nbinsx=bins, name='Distribution'),
            row=1, col=1
        )
        
        # Box plot
        fig.add_trace(
            go.Box(x=data, name='Box Plot'),
            row=2, col=1
        )
        
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def waterfall_chart(data, title):
        """Create waterfall chart"""
        fig = go.Figure(go.Waterfall(
            name="Waterfall",
            orientation="v",
            measure=["relative"] * len(data),
            x=data.index,
            y=data.values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        
        fig.update_layout(
            title=title,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

class DataFilters:
    """Advanced filtering components"""
    
    @staticmethod
    def multi_select_filter(df, column, label):
        """Create multi-select filter with search"""
        if column not in df.columns:
            return []
        
        options = sorted(df[column].unique())
        selected = st.multiselect(
            label,
            options=options,
            default=options[:5] if len(options) > 5 else options
        )
        
        return selected
    
    @staticmethod
    def range_slider_filter(df, column, label):
        """Create range slider filter"""
        if column not in df.columns:
            return None, None
        
        min_val = df[column].min()
        max_val = df[column].max()
        
        selected_range = st.slider(
            label,
            min_value=float(min_val),
            max_value=float(max_val),
            value=(float(min_val), float(max_val))
        )
        
        return selected_range
    
    @staticmethod
    def date_range_filter(df, column, label):
        """Create date range filter"""
        if column not in df.columns:
            return None, None
        
        df[column] = pd.to_datetime(df[column])
        min_date = df[column].min().date()
        max_date = df[column].max().date()
        
        selected_range = st.date_input(
            label,
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        return selected_range

class ExportComponents:
    """Export and sharing components"""
    
    @staticmethod
    def export_buttons(df, filename_prefix):
        """Create export buttons for different formats"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"{filename_prefix}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel Export
            excel_buffer = pd.ExcelWriter(io.BytesIO(), engine='openpyxl')
            df.to_excel(excel_buffer, index=False)
            excel_data = excel_buffer.book
            excel_buffer.close()
            
            st.download_button(
                label="📊 Excel",
                data=excel_data,
                file_name=f"{filename_prefix}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            # JSON Export
            json_data = df.to_json(orient='records')
            st.download_button(
                label="📄 JSON",
                data=json_data,
                file_name=f"{filename_prefix}.json",
                mime="application/json"
            )
    
    @staticmethod
    def share_section():
        """Create sharing section"""
        st.subheader("🔗 مشاركة التقرير")
        
        # Generate share link
        share_link = f"https://crypto-dashboard.app/share/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.code(share_link)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.button("📧 إرسال بالبريد")
            st.button("📱 مشاركة WhatsApp")
        
        with col2:
            st.button("🔗 نسخ الرابط")
            st.button("📸 مشاركة كصورة")

# Utility functions
def format_number(num, decimals=2):
    """Format number with thousands separator"""
    if pd.isna(num):
        return "0"
    return f"{num:,.{decimals}f}"

def format_currency(amount, currency="USD"):
    """Format currency amount"""
    return f"{currency} {format_number(amount)}"

def calculate_percent_change(old_value, new_value):
    """Calculate percentage change"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100

def get_trend_indicator(value, threshold=0):
    """Get trend indicator emoji"""
    if value > threshold:
        return "📈"
    elif value < threshold:
        return "📉"
    else:
        return "➡️"
