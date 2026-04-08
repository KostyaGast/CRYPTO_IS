"""
Модуль визуализации графиков с Plotly.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_candlestick_chart(
    df: pd.DataFrame, 
    title: str = "График цены",
    coin_color: str = "#F7931A"
) -> go.Figure:
    """
    Создаёт свечной график с объёмами и скользящими средними.
    
    Args:
        df: DataFrame с колонками date, open, high, low, close, volume
        title: заголовок графика
        coin_color: основной цвет (BTC - оранжевый, ETH - синий)
    
    Returns:
        Plotly Figure
    """
    # Создаём подграфики: свечи (70%) и объёмы (30%)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, "Объём торгов")
    )
    
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
        ),
        row=1, col=1
    )
    
    # === Скользящие средние ===
    df["MA7"] = df["close"].rolling(window=7).mean()
    df["MA25"] = df["close"].rolling(window=25).mean()
    
    fig.add_trace(
        go.Scatter(
            x=df["date"], 
            y=df["MA7"],
            mode="lines",
            name="MA 7",
            line=dict(color="#ffaa00", width=2, dash="solid")
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df["date"], 
            y=df["MA25"],
            mode="lines",
            name="MA 25",
            line=dict(color="#aa44ff", width=2, dash="dot")
        ),
        row=1, col=1
    )
    
    # === Объёмы ===
    colors = [
        "#00ff88" if row["close"] >= row["open"] else "#ff4444" 
        for _, row in df.iterrows()
    ]
    
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["volume"],
            name="Объём",
            marker_color=colors,
            opacity=0.5,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # === Настройки оформления ===
    fig.update_layout(
        template="plotly_dark",
        height=700,
        hovermode="x unified",
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Оси
    fig.update_xaxes(
        title_text="Дата",
        row=2, col=1,
        gridcolor="#333333"
    )
    fig.update_yaxes(
        title_text="Цена (USD)",
        row=1, col=1,
        gridcolor="#333333",
        tickformat="$,.0f"
    )
    fig.update_yaxes(
        title_text="Объём",
        row=2, col=1,
        gridcolor="#333333",
        tickformat=",.0s"
    )
    
    # Убираем слайдер диапазона
    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    
    return fig


def create_performance_chart(df: pd.DataFrame, title: str = "Динамика цены") -> go.Figure:
    """
    График доходности (нормированный к 100% на начало периода).
    """
    # Нормируем цену к первому значению
    first_price = df["close"].iloc[0]
    df["normalized"] = (df["close"] / first_price) * 100
    
    fig = go.Figure()
    
    # Зона прибыли/убытка
    fig.add_hrect(
        y0=100, y1=df["normalized"].max(),
        fillcolor="green", opacity=0.1,
        line_width=0
    )
    fig.add_hrect(
        y0=df["normalized"].min(), y1=100,
        fillcolor="red", opacity=0.1,
        line_width=0
    )
    
    # Линия цены
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["normalized"],
            mode="lines+markers",
            name="Доходность",
            line=dict(color="#00ff88", width=3),
            fill="tozeroy",
            fillcolor="rgba(0,255,136,0.1)"
        )
    )
    
    # Линия 100%
    fig.add_hline(
        y=100, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="Начало периода"
    )
    
    fig.update_layout(
        template="plotly_dark",
        title=title,
        xaxis_title="Дата",
        yaxis_title="Доходность (%)",
        height=400,
        hovermode="x unified"
    )
    
    return fig


def create_volume_profile(df: pd.DataFrame) -> go.Figure:
    """
    Профиль объёма (гистограмма распределения цены по объёму).
    """
    # Разбиваем цены на бины
    price_bins = np.linspace(df["low"].min(), df["high"].max(), 30)
    volume_profile = []
    
    for i in range(len(price_bins) - 1):
        mask = (df["close"] >= price_bins[i]) & (df["close"] < price_bins[i+1])
        volume_profile.append(df.loc[mask, "volume"].sum())
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=volume_profile,
            y=[(price_bins[i] + price_bins[i+1]) / 2 for i in range(len(price_bins)-1)],
            orientation="h",
            name="Объём",
            marker_color="#00ff88",
            opacity=0.7
        )
    )
    
    # Текущая цена
    current_price = df["close"].iloc[-1]
    fig.add_hline(
        y=current_price,
        line_dash="solid",
        line_color="white",
        line_width=2,
        annotation_text=f"Текущая: ${current_price:,.0f}"
    )
    
    fig.update_layout(
        template="plotly_dark",
        title="Профиль объёма",
        xaxis_title="Объём торгов",
        yaxis_title="Цена (USD)",
        height=400,
        showlegend=False
    )
    
    return fig