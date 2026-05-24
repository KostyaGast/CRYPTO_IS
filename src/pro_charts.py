"""
Pro-графики в стиле Т-Банк Инвестиции.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_pro_chart(
    df: pd.DataFrame,
    title: str = "График цены",
    color: str = "#F7931A",
    show_rsi: bool = True,
    show_macd: bool = True,
    show_ma: bool = True
) -> go.Figure:
    """
    Создаёт профессиональный график в стиле Т-Банк:
    - Свечной график с объёмами
    - Скользящие средние (MA7, MA25, MA99)
    - RSI (индекс относительной силы)
    - MACD (схождение/расхождение скользящих средних)
    """
    
    # Определяем количество панелей
    rows = 1  # Основной график
    if show_ma or True:  # Всегда показываем объёмы
        rows = 2  # + Объёмы
    if show_rsi:
        rows += 1
    if show_macd:
        rows += 1
    
    # Распределение высот
    row_heights = [0.5]  # Основной график
    if rows >= 2:
        row_heights = [0.5, 0.2]  # + Объёмы
    if rows >= 3:
        row_heights = [0.45, 0.2, 0.15]  # + RSI
    if rows >= 4:
        row_heights = [0.4, 0.2, 0.15, 0.15]  # + MACD
    
    subplot_titles = [title]
    if rows >= 2:
        subplot_titles.append("Объём")
    if rows >= 3:
        subplot_titles.append("RSI (14)")
    if rows >= 4:
        subplot_titles.append("MACD")
    
    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=subplot_titles
    )
    
    # ===== 1. СВЕЧНОЙ ГРАФИК =====
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Цена",
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444',
            whiskerwidth=0.5,
            showlegend=True
        ),
        row=1, col=1
    )
    
    # ===== 2. СКОЛЬЗЯЩИЕ СРЕДНИЕ =====
    colors_ma = {"MA7": "#ffaa00", "MA25": "#aa44ff", "MA99": "#00aaff"}
    
    for period, ma_color in [("MA7", "#ffaa00"), ("MA25", "#aa44ff"), ("MA99", "#00aaff")]:
        if len(df) >= int(period[2:]):
            df[period] = df["close"].rolling(window=int(period[2:])).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[period],
                    mode="lines",
                    name=period,
                    line=dict(color=ma_color, width=1.5),
                    opacity=0.8
                ),
                row=1, col=1
            )
    
    # ===== 3. ОБЪЁМЫ =====
    if rows >= 2:
        colors_volume = [
            '#00ff88' if df["close"].iloc[i] >= df["open"].iloc[i] else '#ff4444'
            for i in range(len(df))
        ]
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                name="Объём",
                marker_color=colors_volume,
                opacity=0.4,
                showlegend=False
            ),
            row=2, col=1
        )
    
    # ===== 4. RSI (14) =====
    if show_rsi and rows >= 3:
        rsi = calculate_rsi(df["close"], period=14)
        rsi_row = 3
        
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=rsi,
                mode="lines",
                name="RSI",
                line=dict(color="#00aaff", width=1.5),
                showlegend=False
            ),
            row=rsi_row, col=1
        )
        
        # Уровни перекупленности/перепроданности
        fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", opacity=0.3, row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", opacity=0.3, row=rsi_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#888888", opacity=0.2, row=rsi_row, col=1)
        
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=rsi_row, col=1)
    
    # ===== 5. MACD =====
    if show_macd and rows >= 4:
        macd_line, signal_line, histogram = calculate_macd(df["close"])
        macd_row = 4
        
        # Гистограмма
        colors_hist = ['#00ff88' if val >= 0 else '#ff4444' for val in histogram]
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=histogram,
                name="Гистограмма",
                marker_color=colors_hist,
                opacity=0.5,
                showlegend=False
            ),
            row=macd_row, col=1
        )
        
        # Линия MACD
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=macd_line,
                mode="lines",
                name="MACD",
                line=dict(color="#00aaff", width=1.5),
                showlegend=False
            ),
            row=macd_row, col=1
        )
        
        # Сигнальная линия
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=signal_line,
                mode="lines",
                name="Signal",
                line=dict(color="#ffaa00", width=1),
                showlegend=False
            ),
            row=macd_row, col=1
        )
        
        fig.add_hline(y=0, line_dash="solid", line_color="#888888", opacity=0.3, row=macd_row, col=1)
        fig.update_yaxes(title_text="MACD", row=macd_row, col=1)
    
    # ===== ОФОРМЛЕНИЕ =====
    fig.update_layout(
        template="plotly_dark",
        height=250 * rows,  # 250px на каждую панель
        hovermode="x unified",
        font=dict(family="Arial, sans-serif", size=11),
        margin=dict(l=60, r=30, t=60, b=40),
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Настройка осей
    fig.update_xaxes(
        gridcolor="#1a1c23",
        showgrid=True,
        row=1, col=1
    )
    fig.update_yaxes(
        title_text="Цена (USD)",
        gridcolor="#1a1c23",
        tickformat="$,.0f",
        row=1, col=1
    )
    
    if rows >= 2:
        fig.update_yaxes(title_text="Объём", gridcolor="#1a1c23", row=2, col=1)
    
    # Убираем слайдер
    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    
    return fig


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Расчёт RSI (Relative Strength Index)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Расчёт MACD."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
def create_order_book(
    df: pd.DataFrame,
    title: str = "Стакан (Order Book)",
    color: str = "#00ff88"
) -> go.Figure:
    """
    Создаёт вертикальный стакан в стиле бирж.
    Бары идут сверху вниз.
    Слева — покупка (Bid), справа — продажа (Ask).
    """
    
    current_price = df['close'].iloc[-1]
    
    # Разделяем на Buy и Sell
    buy_df = df[df['close'] <= current_price].copy()
    sell_df = df[df['close'] > current_price].copy()
    
    # Шаг цены
    price_range = df['high'].max() - df['low'].min()
    if price_range > 10000:
        step = 500
    elif price_range > 1000:
        step = 50
    elif price_range > 100:
        step = 10
    else:
        step = 1
    
    buy_df['level'] = (buy_df['close'] // step) * step
    sell_df['level'] = (sell_df['close'] // step) * step
    
    buy_volume = buy_df.groupby('level')['volume'].sum().reset_index()
    sell_volume = sell_df.groupby('level')['volume'].sum().reset_index()
    
    # Сортируем по убыванию цены (сверху вниз)
    buy_volume = buy_volume.sort_values('level', ascending=False).head(20)
    sell_volume = sell_volume.sort_values('level', ascending=False).head(20)
    
    fig = go.Figure()
    
    # === ПОКУПКА (BID) — СЛЕВА, ЗЕЛЁНЫЕ ===
    fig.add_trace(
        go.Bar(
            x=buy_volume['volume'],
            y=[f"${x:,.0f}" for x in buy_volume['level']],
            orientation='h',
            marker_color='#00ff88',
            opacity=0.8,
            name='🟢 Покупка (Bid)',
            text=[f" {v:,.0f} " if v > 0 else "" for v in buy_volume['volume']],
            textposition='outside',
            textfont=dict(color='#00ff88', size=10),
            hovertemplate='Цена: %{y}<br>Объём: %{x:,.0f}<extra></extra>',
            base=0
        )
    )
    
    # === ПРОДАЖА (ASK) — СПРАВА, КРАСНЫЕ ===
    fig.add_trace(
        go.Bar(
            x=[-v for v in sell_volume['volume']],  # Отрицательные значения = слева
            y=[f"${x:,.0f}" for x in sell_volume['level']],
            orientation='h',
            marker_color='#ff4444',
            opacity=0.8,
            name='🔴 Продажа (Ask)',
            text=[f" {v:,.0f} " if v > 0 else "" for v in sell_volume['volume']],
            textposition='outside',
            textfont=dict(color='#ff4444', size=10),
            hovertemplate='Цена: %{y}<br>Объём: %{x:,.0f}<extra></extra>',
            base=0
        )
    )
    
    # === ЛИНИЯ ТЕКУЩЕЙ ЦЕНЫ ===
    fig.add_hline(
        y=len(buy_volume) - 0.5,
        line_dash="solid",
        line_color="white",
        line_width=2.5,
        annotation_text=f"  ${current_price:,.0f}  ",
        annotation_position="right",
        annotation_font=dict(color="white", size=13, family="Arial Black"),
        annotation_bgcolor="rgba(0,0,0,0.7)"
    )
    
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=18),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="← Покупка (Bid) | Продажа (Ask) →",
        yaxis_title="Цена",
        height=600,
        barmode='overlay',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Arial, sans-serif", size=11),
        margin=dict(l=80, r=80, t=80, b=40),
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117'
    )
    
    fig.update_xaxes(
        gridcolor="#1a1c23", 
        showgrid=True, 
        zeroline=True, 
        zerolinecolor="#333",
        tickformat=",.0f"
    )
    fig.update_yaxes(gridcolor="#1a1c23", showgrid=True, categoryorder='array', categoryarray=[f"${x:,.0f}" for x in sorted(list(buy_volume['level']) + list(sell_volume['level']), reverse=True)])
    
    return fig