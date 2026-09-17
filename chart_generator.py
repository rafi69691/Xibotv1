import os
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

def generate_signal_chart(
    pair="USDMXN-OTC",
    df=None,
    direction="CALL",
    accuracy="86%",
    timeframe="M1",
    bot_name="XT AI PRO V5",
    output_path="signal_chart.png"
):
    """
    Generates a dark-themed high-tech candlestick chart matching the Quotex signal bot style.
    """
    if df is None:
        n_candles = 42
        now = datetime.now()
        timestamps = pd.date_range(end=now, periods=n_candles, freq='1min')
        
        np.random.seed(42)
        base_price = 19.8350
        changes = np.random.normal(0.0001, 0.0008, n_candles)
        changes[-9:-4] = -0.0014
        changes[-4:] = 0.0013 if direction.upper() in ["CALL", "BUY"] else -0.0013
        
        closes = base_price + np.cumsum(changes)
        highs = closes + np.random.uniform(0.0002, 0.0009, n_candles)
        lows = closes - np.random.uniform(0.0002, 0.0009, n_candles)
        opens = np.roll(closes, 1)
        opens[0] = base_price
        volumes = np.random.randint(180, 880, n_candles)
        
        df = pd.DataFrame({
            'time': timestamps,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })

    # Indicators
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

    # Color palette
    bg_color = "#080d17"
    card_bg = "#0f172a"
    grid_color = "#162032"
    text_muted = "#64748b"
    text_bright = "#f8fafc"
    bull_color = "#00e676"  # Vibrant Neon Green
    bear_color = "#ff3366"  # Vibrant Coral Red
    ema9_color = "#ff9800"  # Orange
    ema21_color = "#00d2ff" # Neon Cyan

    fig = plt.figure(figsize=(10.5, 5.8), dpi=150, facecolor=bg_color)
    gs = fig.add_gridspec(
        3, 1,
        height_ratios=[0.55, 3.8, 0.95],
        hspace=0.08,
        left=0.05,
        right=0.94,
        top=0.94,
        bottom=0.08
    )

    ax_header = fig.add_subplot(gs[0])
    ax_main = fig.add_subplot(gs[1])
    ax_vol = fig.add_subplot(gs[2], sharex=ax_main)

    for ax in [ax_header, ax_main, ax_vol]:
        ax.set_facecolor(bg_color)

    # 1. HEADER SECTION
    ax_header.set_xlim(0, 100)
    ax_header.set_ylim(0, 10)
    ax_header.axis('off')

    # Card background for header
    head_rect = patches.FancyBboxPatch(
        (0.5, 0.5), 99, 9,
        boxstyle="round,pad=0.3",
        facecolor=card_bg,
        edgecolor="#1e293b",
        linewidth=1.2
    )
    ax_header.add_patch(head_rect)

    # Left: Bot brand
    ax_header.text(
        4, 5, f"⚡ {bot_name} ⚡",
        color="#38bdf8",
        fontsize=11.5,
        fontweight='bold',
        va='center'
    )

    # Center: Pair badge
    pair_display = pair.replace("-", " ")
    pair_badge = patches.FancyBboxPatch(
        (40, 1.5), 20, 7,
        boxstyle="round,pad=0.2",
        facecolor="#182338",
        edgecolor="#f59e0b",
        linewidth=1.2
    )
    ax_header.add_patch(pair_badge)
    ax_header.text(
        50, 5, pair_display,
        color="#ffffff",
        fontsize=11.5,
        fontweight='bold',
        va='center',
        ha='center'
    )

    # Right: CALL/PUT & Accuracy badge
    is_call = direction.upper() in ["CALL", "BUY", "UP"]
    dir_label = "▲ CALL" if is_call else "▼ PUT"
    dir_border = bull_color if is_call else bear_color
    dir_fill = "#064e3b" if is_call else "#7f1d1d"

    badge_right = patches.FancyBboxPatch(
        (80, 1.5), 18, 7,
        boxstyle="round,pad=0.2",
        facecolor=dir_fill,
        edgecolor=dir_border,
        linewidth=1.2
    )
    ax_header.add_patch(badge_right)
    ax_header.text(
        89, 5, f"{dir_label}  {accuracy}",
        color=dir_border,
        fontsize=10.5,
        fontweight='bold',
        va='center',
        ha='center'
    )

    # 2. MAIN CANDLESTICK CHART
    ax_main.text(
        0.5, 0.5, f"{bot_name.upper()}",
        transform=ax_main.transAxes,
        fontsize=38,
        fontweight='bold',
        color='#0f1c2e',
        alpha=0.6,
        ha='center',
        va='center',
        rotation=-12,
        zorder=0
    )

    indices = np.arange(len(df))
    width = 0.58

    for i, idx in enumerate(indices):
        o = df['open'].iloc[i]
        c = df['close'].iloc[i]
        h = df['high'].iloc[i]
        l = df['low'].iloc[i]
        v = df['volume'].iloc[i]
        color = bull_color if c >= o else bear_color

        # Candle wicks
        ax_main.plot([idx, idx], [l, h], color=color, linewidth=1.2, zorder=2)
        # Candle body
        lower = min(o, c)
        height = max(abs(c - o), 0.00004)
        rect = patches.Rectangle((idx - width/2, lower), width, height, facecolor=color, edgecolor=color, zorder=3)
        ax_main.add_patch(rect)

        # Volume bars
        vol_rect = patches.Rectangle((idx - width/2, 0), width, v, facecolor=color, alpha=0.65, zorder=2)
        ax_vol.add_patch(vol_rect)

    # Plot EMAs
    ax_main.plot(indices, df['ema9'], color=ema9_color, linewidth=1.8, label="EMA 9", zorder=4)
    ax_main.plot(indices, df['ema21'], color=ema21_color, linewidth=1.8, label="EMA 21", zorder=4)

    # Legend inside chart (Top-Left)
    ax_main.plot([], [], color=ema9_color, label="EMA 9", lw=1.5)
    ax_main.plot([], [], color=ema21_color, label="EMA 21", lw=1.5)
    ax_main.legend(
        loc='upper left',
        facecolor="#0c1424",
        edgecolor="#1e293b",
        fontsize=7.5,
        labelcolor=text_bright
    )

    # Support / Resistance levels
    last_close = df['close'].iloc[-1]
    support_lvl = df['low'].tail(25).min()
    resistance_lvl = df['high'].tail(25).max()

    ax_main.axhline(resistance_lvl, color="#f43f5e", linestyle="--", linewidth=0.9, alpha=0.55, zorder=1)
    ax_main.axhline(support_lvl, color="#10b981", linestyle="--", linewidth=0.9, alpha=0.55, zorder=1)

    # Signal callout arrow & box
    target_idx = indices[-1]
    if is_call:
        ax_main.annotate(
            f'▲ CALL ({accuracy})',
            xy=(target_idx, last_close),
            xytext=(target_idx - 4.2, last_close - (resistance_lvl - support_lvl)*0.2),
            arrowprops=dict(facecolor=bull_color, edgecolor=bull_color, arrowstyle="->", lw=2),
            bbox=dict(boxstyle="round,pad=0.4", fc="#022c22", ec=bull_color, lw=1.5),
            color="#ffffff",
            fontweight="bold",
            fontsize=10,
            zorder=6
        )
    else:
        ax_main.annotate(
            f'▼ PUT ({accuracy})',
            xy=(target_idx, last_close),
            xytext=(target_idx - 4.2, last_close + (resistance_lvl - support_lvl)*0.2),
            arrowprops=dict(facecolor=bear_color, edgecolor=bear_color, arrowstyle="->", lw=2),
            bbox=dict(boxstyle="round,pad=0.4", fc="#450a0a", ec=bear_color, lw=1.5),
            color="#ffffff",
            fontweight="bold",
            fontsize=10,
            zorder=6
        )

    # Latest price tag on Y axis
    tag_bg = "#0284c7" if is_call else "#e11d48"
    ax_main.text(
        indices[-1] + 0.8, last_close, f" {last_close:.5f} ",
        color="#ffffff",
        backgroundcolor=tag_bg,
        fontsize=8.5,
        fontweight="bold",
        va="center",
        bbox=dict(boxstyle="square,pad=0.3", fc=tag_bg, ec="none")
    )

    # Grid & styling
    ax_main.grid(True, linestyle=":", alpha=0.18, color=grid_color)
    ax_vol.grid(True, linestyle=":", alpha=0.12, color=grid_color)

    ax_main.set_xlim(-1, len(df) + 3)
    ax_vol.set_ylim(0, df['volume'].max() * 1.3)

    for spine in ax_main.spines.values():
        spine.set_color(grid_color)
    for spine in ax_vol.spines.values():
        spine.set_color(grid_color)

    ax_main.tick_params(colors=text_muted, labelsize=8)
    ax_vol.tick_params(colors=text_muted, labelsize=7.5)
    plt.setp(ax_main.get_xticklabels(), visible=False)

    # Time labels on volume axis
    step = 6
    x_ticks = indices[::step]
    x_labels = [df['time'].iloc[i].strftime('%H:%M') for i in x_ticks]
    ax_vol.set_xticks(x_ticks)
    ax_vol.set_xticklabels(x_labels, color=text_muted)

    # Footer Watermark
    fig.text(
        0.05, 0.02, f"Powered by {bot_name} • Real-time Terminal",
        fontsize=7.5,
        color=text_muted
    )
    fig.text(
        0.94, 0.02, "Algorithmic Market Intelligence",
        fontsize=7.5,
        color=text_muted,
        ha="right"
    )

    plt.savefig(output_path, dpi=150, facecolor=bg_color, bbox_inches='tight')
    plt.close()
    return output_path

if __name__ == "__main__":
    out = generate_signal_chart(
        pair="USDMXN-OTC",
        direction="CALL",
        accuracy="86%",
        output_path="test_signal_chart2.png"
    )
    print("New test chart generated:", out)
