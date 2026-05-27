from __future__ import annotations

import matplotlib.pyplot as plt
from typing import Any

from .features import landing_attempt_declared

def generate_prediction_chart(
    launch: dict[str, Any],
    predictions: dict[str, float],
    output_path: str,
) -> str:
    """
    Generates a horizontal bar chart showing launch predictions and saves it.
    Returns the output path.
    """
    plt.style.use('dark_background')
    
    fig, ax = plt.subplots(figsize=(8, 4))
    
    launch_name = launch.get('name', 'Next Mission')
    
    labels = []
    values = []
    
    labels.append("Launch Success")
    values.append(predictions.get('launch_success', 0.0) * 100)
    
    if landing_attempt_declared(launch):
        labels.append("Landing Success")
        values.append(predictions.get('landing_success', 0.0) * 100)
    
    # Reverse to have Launch Success on top
    labels.reverse()
    values.reverse()
    
    # Colors: Green for > 85%, Yellow for > 50%, Red otherwise
    colors = []
    for v in values:
        if v >= 85:
            colors.append('#28a745')
        elif v >= 50:
            colors.append('#ffc107')
        else:
            colors.append('#dc3545')
            
    bars = ax.barh(labels, values, color=colors, height=0.5)
    
    ax.set_xlim(0, 100)
    ax.set_xlabel('Probability (%)', fontsize=12, labelpad=10)
    ax.set_title(f'Prediction for {launch_name}', fontsize=14, pad=20, fontweight='bold')
    
    # Add text labels on bars
    for bar in bars:
        width = bar.get_width()
        label_x_pos = width - 2 if width > 10 else width + 2
        text_color = 'white'
        align = 'right' if width > 10 else 'left'
        ax.text(
            label_x_pos, bar.get_y() + bar.get_height() / 2, 
            f'{width:.1f}%', va='center', ha=align, color=text_color, fontweight='bold', fontsize=12
        )
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_alpha(0.3)
    
    ax.tick_params(axis='y', which='both', length=0, labelsize=12)
    ax.tick_params(axis='x', labelsize=10, colors='#aaaaaa')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path
