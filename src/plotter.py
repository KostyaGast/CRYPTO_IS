"""
Модуль визуализации графиков с Plotly.
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def create_candlestick_chart(
    df: pd.DataFrame, 
    title: str = "График цены",
    coin_color: str = "#F7931A"
) -> go.Figure:
    """
    Создаёт свечной график (без объёмов).
    """
    fig = go.Figure()
    
    # === Свечной график ===
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
            increasing_line_color="#00ff88",
            decreasing_line_color="#ff4444",
            showlegend=False
        )
    )
    
    # === Скользящие средние ===
    if len(df) >= 7:
        df["MA7"] = df["close"].rolling(window=7).mean()
        fig.add_trace(
            go.Scatter(
                x=df["date"], 
                y=df["MA7"],
                mode="lines",
                name="MA 7",
                line=dict(color="#ffaa00", width=2, dash="solid")
            )
        )
    
    if len(df) >= 25:
        df["MA25"] = df["close"].rolling(window=25).mean()
        fig.add_trace(
            go.Scatter(
                x=df["date"], 
                y=df["MA25"],
                mode="lines",
                name="MA 25",
                line=dict(color="#aa44ff", width=2, dash="dot")
            )
        )
    
    # === Настройки оформления ===
    fig.update_layout(
        template="plotly_dark",
        height=600,
        hovermode="x unified",
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=40, t=80, b=50),
        title=dict(
            text=title,
            font=dict(size=20),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Дата",
        yaxis_title="Цена (USD)",
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117'
    )
    
    fig.update_xaxes(gridcolor="#333333")
    fig.update_yaxes(gridcolor="#333333", tickformat="$,.0f")
    
    return fig


def create_performance_chart(df: pd.DataFrame, title: str = "Динамика цены") -> go.Figure:
    """
    График доходности (нормированный к 100% на начало периода).
    """
    first_price = df["close"].iloc[0]
    df = df.copy()
    df["normalized"] = (df["close"] / first_price) * 100
    
    fig = go.Figure()
    
    max_val = df["normalized"].max()
    min_val = df["normalized"].min()
    
    fig.add_hrect(
        y0=100, y1=max_val,
        fillcolor="green", opacity=0.1,
        line_width=0
    )
    fig.add_hrect(
        y0=min_val, y1=100,
        fillcolor="red", opacity=0.1,
        line_width=0
    )
    
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["normalized"],
            mode="lines+markers",
            name="Доходность",
            line=dict(color="#00ff88", width=3),
            marker=dict(size=6, color="#00ff88"),
            fill="tozeroy",
            fillcolor="rgba(0,255,136,0.08)"
        )
    )
    
    fig.add_hline(
        y=100, 
        line_dash="dash", 
        line_color="#888888",
        line_width=1.5,
        annotation_text="Начало периода",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=title,
            font=dict(size=20),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Дата",
        yaxis_title="Доходность (%)",
        height=500,
        hovermode="x unified",
        font=dict(family="Arial, sans-serif", size=13),
        margin=dict(l=60, r=40, t=80, b=50),
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117'
    )
    
    fig.update_xaxes(gridcolor="#333333")
    fig.update_yaxes(gridcolor="#333333", ticksuffix="%")
    
    return fig


def create_volume_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Создаёт таблицу с объёмами торгов по дням.
    """
    volume_df = df[['date', 'volume']].copy()
    volume_df['date'] = pd.to_datetime(volume_df['date']).dt.strftime('%Y-%m-%d')
    volume_df['volume'] = volume_df['volume'].apply(lambda x: f"{x:,.0f}")
    volume_df.columns = ['Дата', 'Объём торгов']
    return volume_df