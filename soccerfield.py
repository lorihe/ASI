import numpy as np
import plotly.graph_objects as go

def get_layout(length, width):
    # Field boundary
    field_shape = go.layout.Shape(
        type="rect",
        x0=-length/2, y0=-width/2, x1=length/2, y1=width/2,
        line=dict(color='darkgrey', width=1, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Center line
    center_line = go.layout.Shape(
        type='line',
        x0=0, y0=-width/2, x1=0, y1=width/2,
        line=dict(color='darkgrey', width=0.5, dash='solid')
    )
    
    # Left penalty box
    box_left = go.layout.Shape(
        type="rect",
        x0=-length/2, y0=-20.16, x1=-length/2 + 16.5, y1=20.16,
        line=dict(color='darkgrey', width=0.6, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Right penalty box
    box_right = go.layout.Shape(
        type="rect",
        x0=length/2 - 16.5, y0=-20.16, x1=length/2, y1=20.16,
        line=dict(color='darkgrey', width=0.6, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Small left penalty box
    box_left_small = go.layout.Shape(
        type="rect",
        x0=-length/2, y0=-9.16, x1=-length/2 + 5.5, y1=9.16,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Small right penalty box
    box_right_small = go.layout.Shape(
        type="rect",
        x0=length/2 - 5.5, y0=-9.16, x1=length/2, y1=9.16,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Center circle
    center_circle = go.layout.Shape(
        type='circle',
        x0=-9.15, y0=-9.15, x1=9.15, y1=9.15,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Left arc
    center_left = (-length/2 + 11, 0)
    radius = 9.15
    theta = np.linspace(
        np.arccos((16.5 - 11) / radius), -np.arccos((16.5 - 11) / radius), 100
    )
    x_left = center_left[0] + radius * np.cos(theta)
    y_left = center_left[1] + radius * np.sin(theta)
    
    arc_left = go.layout.Shape(
        type="path",
        path=f"M {x_left[0]},{y_left[0]}"
             + " L" + " L".join([f"{x},{y}" for x, y in zip(x_left, y_left)])
             + f" L {x_left[-1]},{y_left[-1]}",
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Right arc
    center_right = (length/2 - 11, 0)
    x_right = center_right[0] - radius * np.cos(theta)
    y_right = center_right[1] + radius * np.sin(theta)
    
    arc_right = go.layout.Shape(
        type="path",
        path=f"M {x_right[0]},{y_right[0]}"
             + " L" + " L".join([f"{x},{y}" for x, y in zip(x_right, y_right)])
             + f" L {x_right[-1]},{y_right[-1]}",
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Left goal
    goal_left = go.layout.Shape(
        type="rect",
        x0=-length/2 - 2, y0=-3.66, x1=-length/2, y1=3.66,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Right goal
    goal_right = go.layout.Shape(
        type="rect",
        x0=length/2, y0=-3.66, x1=length/2 + 2, y1=3.66,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    # Layout
    layout = go.Layout(
        xaxis=dict(range=[-length/2 - 3, length/2 + 3], constrain='domain', showticklabels=False),
        yaxis=dict(range=[-width/2 - 3, width/2 + 3], scaleanchor="x", scaleratio=1, showticklabels=False),
        shapes=[field_shape, center_line, box_left, box_right, box_left_small, box_right_small,
                center_circle, arc_left, arc_right, goal_left, goal_right]
    )
    return layout
