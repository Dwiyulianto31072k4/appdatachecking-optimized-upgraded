import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# Set style untuk plots
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'

class ValidationDashboard:
    """
    Class untuk membuat dashboard analytics validasi data KK
    """
    
    def __init__(self, data):
        """
        Inisialisasi dashboard dengan data hasil validasi
        
        Args:
            data: DataFrame dengan hasil validasi
        """
        self.data = data
        self.total_records = len(data)
        self.validation_columns = {
            'valid_kk_no': 'KK_NO',
            'valid_nik': 'NIK',
            'valid_custname': 'Nama',
            'valid_jenis_kelamin': 'Jenis Kelamin',
            'valid_tempat_lahir': 'Tempat Lahir',
            'valid_tanggal_lahir': 'Tanggal Lahir'
        }
    
    def calculate_statistics(self):
        """
        Hitung statistik validasi
        
        Returns:
            dict: Statistik validasi
        """
        stats = {
            'total_records': self.total_records,
            'all_valid': int(self.data['all_valid'].sum()),
            'all_valid_pct': float(self.data['all_valid'].sum() / self.total_records * 100),
            'any_invalid': int(self.total_records - self.data['all_valid'].sum()),
            'any_invalid_pct': float((self.total_records - self.data['all_valid'].sum()) / self.total_records * 100)
        }
        
        # Per kategori
        for col, name in self.validation_columns.items():
            valid_count = int(self.data[col].sum())
            stats[f'{name}_valid'] = valid_count
            stats[f'{name}_valid_pct'] = float(valid_count / self.total_records * 100)
            stats[f'{name}_invalid'] = int(self.total_records - valid_count)
            stats[f'{name}_invalid_pct'] = float((self.total_records - valid_count) / self.total_records * 100)
        
        return stats
    
    def create_overview_chart(self):
        """
        Buat chart overview validasi menggunakan Plotly
        
        Returns:
            plotly figure
        """
        # Data untuk chart
        categories = []
        valid_counts = []
        invalid_counts = []
        
        for col, name in self.validation_columns.items():
            categories.append(name)
            valid_counts.append(self.data[col].sum())
            invalid_counts.append(self.total_records - self.data[col].sum())
        
        # Create figure
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Valid',
            x=categories,
            y=valid_counts,
            marker_color='#2ecc71',
            text=valid_counts,
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Valid: %{y:,}<br>Persentase: %{customdata:.2f}%<extra></extra>',
            customdata=[v/self.total_records*100 for v in valid_counts]
        ))
        
        fig.add_trace(go.Bar(
            name='Tidak Valid',
            x=categories,
            y=invalid_counts,
            marker_color='#e74c3c',
            text=invalid_counts,
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Tidak Valid: %{y:,}<br>Persentase: %{customdata:.2f}%<extra></extra>',
            customdata=[v/self.total_records*100 for v in invalid_counts]
        ))
        
        fig.update_layout(
            title='Hasil Validasi per Kategori',
            xaxis_title='Kategori',
            yaxis_title='Jumlah Data',
            barmode='stack',
            hovermode='x unified',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_pie_chart(self):
        """
        Buat pie chart untuk overall validation
        
        Returns:
            plotly figure
        """
        values = [
            self.data['all_valid'].sum(),
            self.total_records - self.data['all_valid'].sum()
        ]
        labels = ['Data Valid', 'Data Tidak Valid']
        colors_pie = ['#2ecc71', '#e74c3c']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors_pie,
            textinfo='label+percent+value',
            texttemplate='<b>%{label}</b><br>%{value:,} (%{percent})',
            hovertemplate='<b>%{label}</b><br>Jumlah: %{value:,}<br>Persentase: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title='Distribusi Overall Validasi',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    
    def create_validation_heatmap(self):
        """
        Buat heatmap untuk melihat pola validasi
        
        Returns:
            plotly figure
        """
        # Sample data untuk heatmap (ambil 1000 record pertama untuk performa)
        sample_size = min(1000, len(self.data))
        sample_data = self.data.head(sample_size)
        
        # Prepare data untuk heatmap
        validation_matrix = []
        for col in self.validation_columns.keys():
            validation_matrix.append(sample_data[col].astype(int).values)
        
        fig = go.Figure(data=go.Heatmap(
            z=validation_matrix,
            x=list(range(1, sample_size + 1)),
            y=list(self.validation_columns.values()),
            colorscale=[[0, '#e74c3c'], [1, '#2ecc71']],
            showscale=True,
            hovertemplate='Record: %{x}<br>Field: %{y}<br>Status: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Heatmap Validasi (Sample {sample_size} Data)',
            xaxis_title='Index Record',
            yaxis_title='Kategori Validasi',
            height=400
        )
        
        return fig
    
    def create_tempat_lahir_analysis(self):
        """
        Analisis khusus untuk validasi tempat lahir
        
        Returns:
            dict: Multiple plotly figures
        """
        figures = {}
        
        # 1. Distribusi Level Administrasi
        if 'level_administrasi' in self.data.columns:
            level_counts = self.data[self.data['valid_tempat_lahir']]['level_administrasi'].value_counts()
            
            fig1 = go.Figure(data=[go.Bar(
                x=level_counts.index,
                y=level_counts.values,
                marker_color='#3498db',
                text=level_counts.values,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Jumlah: %{y:,}<extra></extra>'
            )])
            
            fig1.update_layout(
                title='Distribusi Level Administrasi Tempat Lahir',
                xaxis_title='Level Administrasi',
                yaxis_title='Jumlah',
                height=400
            )
            
            figures['level_distribution'] = fig1
        
        # 2. Distribusi Confidence Score
        if 'confidence_score' in self.data.columns:
            valid_tempat = self.data[self.data['valid_tempat_lahir']]
            
            fig2 = go.Figure(data=[go.Histogram(
                x=valid_tempat['confidence_score'],
                nbinsx=20,
                marker_color='#9b59b6',
                hovertemplate='Score Range: %{x}<br>Count: %{y}<extra></extra>'
            )])
            
            fig2.update_layout(
                title='Distribusi Confidence Score Tempat Lahir',
                xaxis_title='Confidence Score (%)',
                yaxis_title='Jumlah Data',
                height=400
            )
            
            figures['confidence_distribution'] = fig2
        
        # 3. Top 10 Koreksi Tempat Lahir
        if 'koreksi_tempat_lahir' in self.data.columns:
            corrections = self.data[
                (self.data['tempat_lahir_normalized'] != self.data['koreksi_tempat_lahir']) &
                (~self.data['koreksi_tempat_lahir'].isna())
            ]
            
            if len(corrections) > 0:
                top_corrections = corrections.groupby(['tempat_lahir_normalized', 'koreksi_tempat_lahir']).size().reset_index(name='count')
                top_corrections = top_corrections.sort_values('count', ascending=False).head(10)
                
                labels = [f"{row['tempat_lahir_normalized']}<br>→ {row['koreksi_tempat_lahir']}" 
                         for _, row in top_corrections.iterrows()]
                
                fig3 = go.Figure(data=[go.Bar(
                    y=labels,
                    x=top_corrections['count'],
                    orientation='h',
                    marker_color='#e67e22',
                    text=top_corrections['count'],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>Jumlah: %{x:,}<extra></extra>'
                )])
                
                fig3.update_layout(
                    title='Top 10 Koreksi Tempat Lahir',
                    xaxis_title='Jumlah Koreksi',
                    yaxis_title='Koreksi',
                    height=500,
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                figures['top_corrections'] = fig3
        
        return figures
    
    def create_error_analysis(self):
        """
        Analisis error per kategori
        
        Returns:
            plotly figure
        """
        error_counts = {}
        
        for col, name in self.validation_columns.items():
            error_counts[name] = self.total_records - self.data[col].sum()
        
        # Sort by error count
        sorted_errors = dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True))
        
        fig = go.Figure(data=[go.Bar(
            x=list(sorted_errors.keys()),
            y=list(sorted_errors.values()),
            marker_color='#e74c3c',
            text=list(sorted_errors.values()),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Error: %{y:,}<br>Persentase: %{customdata:.2f}%<extra></extra>',
            customdata=[v/self.total_records*100 for v in sorted_errors.values()]
        )])
        
        fig.update_layout(
            title='Ranking Error per Kategori (Terbanyak ke Tersedikit)',
            xaxis_title='Kategori',
            yaxis_title='Jumlah Error',
            height=400
        )
        
        return fig
