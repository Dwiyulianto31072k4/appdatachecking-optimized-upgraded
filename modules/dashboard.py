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


# CONTINUATION OF dashboard.py - ADD THIS TO THE END OF PREVIOUS FILE
    
    def generate_pdf_report(self, stats, filename="Laporan_Validasi_KK.pdf"):
        """
        Generate laporan PDF lengkap
        
        Args:
            stats: Dictionary statistik validasi
            filename: Nama file PDF
        
        Returns:
            BytesIO: PDF file dalam memory
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        
        # Container untuk elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = styles['Normal']
        
        # Header/Title
        elements.append(Paragraph("LAPORAN VALIDASI DATA KARTU KELUARGA", title_style))
        elements.append(Spacer(1, 12))
        
        # Info tanggal
        date_text = f"Tanggal: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
        elements.append(Paragraph(date_text, normal_style))
        elements.append(Spacer(1, 20))
        
        # ===== RINGKASAN EKSEKUTIF =====
        elements.append(Paragraph("RINGKASAN EKSEKUTIF", heading_style))
        
        summary_data = [
            ['Metric', 'Jumlah', 'Persentase'],
            ['Total Data', f"{stats['total_records']:,}", '100%'],
            ['Data Valid (Semua Field)', f"{stats['all_valid']:,}", f"{stats['all_valid_pct']:.2f}%"],
            ['Data Tidak Valid', f"{stats['any_invalid']:,}", f"{stats['any_invalid_pct']:.2f}%"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # ===== HASIL VALIDASI PER KATEGORI =====
        elements.append(Paragraph("HASIL VALIDASI PER KATEGORI", heading_style))
        
        category_data = [['Kategori', 'Valid', '% Valid', 'Tidak Valid', '% Tidak Valid']]
        
        for name in self.validation_columns.values():
            category_data.append([
                name,
                f"{stats[f'{name}_valid']:,}",
                f"{stats[f'{name}_valid_pct']:.2f}%",
                f"{stats[f'{name}_invalid']:,}",
                f"{stats[f'{name}_invalid_pct']:.2f}%"
            ])
        
        category_table = Table(category_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(category_table)
        elements.append(Spacer(1, 20))
        
        # ===== ANALISIS TEMPAT LAHIR =====
        if 'level_administrasi' in self.data.columns:
            elements.append(PageBreak())
            elements.append(Paragraph("ANALISIS VALIDASI TEMPAT LAHIR", heading_style))
            
            # Distribusi Level Administrasi
            level_counts = self.data[self.data['valid_tempat_lahir']]['level_administrasi'].value_counts()
            
            level_data = [['Level Administrasi', 'Jumlah', 'Persentase']]
            total_valid_tempat = self.data['valid_tempat_lahir'].sum()
            
            for level, count in level_counts.items():
                level_data.append([
                    level.title(),
                    f"{count:,}",
                    f"{count/total_valid_tempat*100:.2f}%"
                ])
            
            level_table = Table(level_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            level_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(level_table)
            elements.append(Spacer(1, 20))
            
            # Confidence Score Statistics
            if 'confidence_score' in self.data.columns:
                valid_scores = self.data[self.data['valid_tempat_lahir']]['confidence_score']
                
                score_stats = [
                    ['Statistik', 'Nilai'],
                    ['Rata-rata Confidence Score', f"{valid_scores.mean():.2f}%"],
                    ['Median Confidence Score', f"{valid_scores.median():.2f}%"],
                    ['Score Minimum', f"{valid_scores.min():.2f}%"],
                    ['Score Maximum', f"{valid_scores.max():.2f}%"],
                ]
                
                score_table = Table(score_stats, colWidths=[3*inch, 3*inch])
                score_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                elements.append(score_table)
        
        # ===== KESIMPULAN DAN REKOMENDASI =====
        elements.append(PageBreak())
        elements.append(Paragraph("KESIMPULAN DAN REKOMENDASI", heading_style))
        
        # Kesimpulan berdasarkan data
        conclusion_text = f"""
        Berdasarkan hasil validasi terhadap {stats['total_records']:,} record data Kartu Keluarga, 
        ditemukan bahwa {stats['all_valid_pct']:.2f}% data telah valid di semua field yang divalidasi, 
        sementara {stats['any_invalid_pct']:.2f}% data masih memiliki satu atau lebih field yang tidak valid.
        """
        
        elements.append(Paragraph(conclusion_text, normal_style))
        elements.append(Spacer(1, 12))
        
        # Identifikasi kategori dengan error terbanyak
        error_ranking = []
        for name in self.validation_columns.values():
            error_ranking.append((name, stats[f'{name}_invalid'], stats[f'{name}_invalid_pct']))
        
        error_ranking.sort(key=lambda x: x[1], reverse=True)
        
        if error_ranking[0][1] > 0:
            rekomendasi = f"""
            <b>Rekomendasi Prioritas:</b><br/>
            1. <b>{error_ranking[0][0]}</b> memiliki jumlah error terbanyak ({error_ranking[0][1]:,} data / {error_ranking[0][2]:.2f}%). 
            Disarankan untuk melakukan validasi dan koreksi data pada field ini terlebih dahulu.<br/>
            2. Lakukan cross-check dengan data sumber untuk memastikan akurasi data.<br/>
            3. Terapkan validasi input data untuk mencegah error serupa di masa mendatang.
            """
            elements.append(Paragraph(rekomendasi, normal_style))
        
        elements.append(Spacer(1, 20))
        
        # Footer
        footer_text = "--- End of Report ---"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    def display_dashboard(self):
        """
        Tampilkan dashboard lengkap di Streamlit
        """
        st.title("📊 Dashboard Analytics Validasi Data KK")
        
        # Calculate statistics
        stats = self.calculate_statistics()
        
        # ===== SECTION 1: KEY METRICS =====
        st.header("📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Data",
                value=f"{stats['total_records']:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Data Valid",
                value=f"{stats['all_valid']:,}",
                delta=f"{stats['all_valid_pct']:.1f}%",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                label="Data Tidak Valid",
                value=f"{stats['any_invalid']:,}",
                delta=f"{stats['any_invalid_pct']:.1f}%",
                delta_color="inverse"
            )
        
        with col4:
            # Hitung tingkat keberhasilan validasi
            success_rate = stats['all_valid_pct']
            st.metric(
                label="Success Rate",
                value=f"{success_rate:.1f}%",
                delta="Target: 95%",
                delta_color="normal" if success_rate >= 95 else "inverse"
            )
        
        st.divider()
        
        # ===== SECTION 2: OVERVIEW CHARTS =====
        st.header("📊 Overview Validasi")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie Chart
            fig_pie = self.create_pie_chart()
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Error Analysis
            fig_error = self.create_error_analysis()
            st.plotly_chart(fig_error, use_container_width=True)
        
        # Bar Chart (Full Width)
        fig_overview = self.create_overview_chart()
        st.plotly_chart(fig_overview, use_container_width=True)
        
        st.divider()
        
        # ===== SECTION 3: VALIDATION DETAILS =====
        st.header("🔍 Detail Validasi per Kategori")
        
        # Buat 2 kolom untuk menampilkan detail
        col1, col2 = st.columns(2)
        
        for idx, (col, name) in enumerate(self.validation_columns.items()):
            with col1 if idx % 2 == 0 else col2:
                with st.container():
                    # Mini card untuk setiap kategori
                    valid_count = stats[f'{name}_valid']
                    valid_pct = stats[f'{name}_valid_pct']
                    invalid_count = stats[f'{name}_invalid']
                    
                    st.subheader(name)
                    
                    # Progress bar
                    st.progress(valid_pct / 100, text=f"{valid_pct:.1f}% Valid")
                    
                    # Metrics
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.metric("✅ Valid", f"{valid_count:,}")
                    with metric_col2:
                        st.metric("❌ Tidak Valid", f"{invalid_count:,}")
        
        st.divider()
        
        # ===== SECTION 4: TEMPAT LAHIR ANALYSIS =====
        st.header("🗺️ Analisis Khusus Tempat Lahir")
        
        tempat_lahir_figs = self.create_tempat_lahir_analysis()
        
        if 'level_distribution' in tempat_lahir_figs:
            st.plotly_chart(tempat_lahir_figs['level_distribution'], use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'confidence_distribution' in tempat_lahir_figs:
                st.plotly_chart(tempat_lahir_figs['confidence_distribution'], use_container_width=True)
        
        with col2:
            # Statistik confidence score
            if 'confidence_score' in self.data.columns:
                valid_scores = self.data[self.data['valid_tempat_lahir']]['confidence_score']
                
                st.subheader("Statistik Confidence Score")
                
                stat_col1, stat_col2 = st.columns(2)
                with stat_col1:
                    st.metric("Rata-rata", f"{valid_scores.mean():.2f}%")
                    st.metric("Minimum", f"{valid_scores.min():.2f}%")
                
                with stat_col2:
                    st.metric("Median", f"{valid_scores.median():.2f}%")
                    st.metric("Maximum", f"{valid_scores.max():.2f}%")
        
        if 'top_corrections' in tempat_lahir_figs:
            st.plotly_chart(tempat_lahir_figs['top_corrections'], use_container_width=True)
        
        st.divider()
        
        # ===== SECTION 5: HEATMAP =====
        st.header("🔥 Heatmap Validasi")
        st.info("Visualisasi pola validasi pada sample data. Hijau = Valid, Merah = Tidak Valid")
        
        fig_heatmap = self.create_validation_heatmap()
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        st.divider()
        
        # ===== SECTION 6: DOWNLOAD REPORTS =====
        st.header("📥 Download Laporan")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generate PDF
            if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    pdf_buffer = self.generate_pdf_report(stats)
                    
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_buffer,
                        file_name=f"Laporan_Validasi_KK_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    st.success("✅ PDF Report berhasil di-generate!")
        
        with col2:
            # Download Excel dengan statistik
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Sheet 1: Summary Statistics
                summary_df = pd.DataFrame([stats])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Sheet 2: Detailed Data
                self.data.to_excel(writer, sheet_name='Detailed Data', index=False)
                
                # Sheet 3: Per Category Stats
                category_stats = []
                for name in self.validation_columns.values():
                    category_stats.append({
                        'Kategori': name,
                        'Valid': stats[f'{name}_valid'],
                        '% Valid': stats[f'{name}_valid_pct'],
                        'Tidak Valid': stats[f'{name}_invalid'],
                        '% Tidak Valid': stats[f'{name}_invalid_pct']
                    })
                
                pd.DataFrame(category_stats).to_excel(writer, sheet_name='Per Category', index=False)
            
            excel_buffer.seek(0)
            
            st.download_button(
                label="⬇️ Download Excel Report",
                data=excel_buffer,
                file_name=f"Laporan_Validasi_KK_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )



