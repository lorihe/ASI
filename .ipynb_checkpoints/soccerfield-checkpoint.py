import pandas as pd
import numpy as np
import plotly.graph_objects as go

def get_layout(length, width):
    
    field_shape = go.layout.Shape(
        type="rect",
        x0=0, y0=0, x1=length, y1=width,
        line=dict(color='darkgrey', width=1, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )    
    
    center_line = go.layout.Shape(
        type = 'line',
        x0 = length/2, y0 = 0, x1 = length/2, y1 = width,
        line=dict(color='darkgrey', width=0.5, dash='solid')
    )
    
    box_left = go.layout.Shape(
        type="rect",
        x0=0, y0=width/2-20.16, x1=16.5, y1=width/2+20.16,
        line=dict(color='darkgrey', width=0.6, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    box_right = go.layout.Shape(
        type="rect",
        x0=length-16.5, y0=width/2-20.16, x1=length, y1=width/2+20.16,
        line=dict(color='darkgrey', width=0.6, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    box_left_small = go.layout.Shape(
        type="rect",
        x0=0, y0=width/2-9.16, x1=5.5, y1=width/2+9.16,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    box_right_small = go.layout.Shape(
        type="rect",
        x0=length-5.5, y0=width/2-9.16, x1=length, y1=width/2+9.16,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )    
    
    center_circle = go.layout.Shape(
        type = 'circle',
        x0 = length/2-9.15, y0 = width/2-9.15, x1 = length/2+9.15, y1 = width/2+9.15,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    center_left = (11, width/2)
    radius = 9.15
    theta = np.linspace(np.arccos((16.5 - 11) / radius), -np.arccos((16.5 - 11) / radius), 100)
    x_left = 11 + radius * np.cos(theta)
    x_right = length-x_left   
    y = width/2 + radius * np.sin(theta)
    
    arc_left = go.layout.Shape(
        type="path",
        path=f"M {x_left[0]},{y[0]}"
             + " L" + " L".join([f"{x_val},{y_val}" for x_val, y_val in zip(x_left, y)])
             + f" L {x_left[-1]},{y[-1]}",
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    arc_right = go.layout.Shape(
        type="path",
        path=f"M {x_right[0]},{y[0]}"
             + " L" + " L".join([f"{x_val},{y_val}" for x_val, y_val in zip(x_right, y)])
             + f" L {x_right[-1]},{y[-1]}",
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )    
    
    goal_left = go.layout.Shape(
        type="rect",
        x0=-2, y0=width/2-3.66, x1=0, y1=width/2+3.66,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    goal_right = go.layout.Shape(
        type="rect",
        x0=length, y0=width/2-3.66, x1=length+2, y1=width/2+3.66,
        line=dict(color='darkgrey', width=0.5, dash='solid'),
        fillcolor='rgba(0, 0, 0, 0)'
    )
    
    layout = go.Layout(
        xaxis=dict(range=[-3, length+3], constrain='domain', showticklabels=False),
        yaxis=dict(range=[width, 0], scaleanchor="x", scaleratio=1, showticklabels=False),

        shapes = [field_shape, center_line, box_left, box_right, box_left_small, box_right_small,
                 center_circle, arc_left, arc_right, goal_left, goal_right]
    )
    return layout