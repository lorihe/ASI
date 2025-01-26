import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.spatial import distance
from scipy.spatial import cKDTree
import math

import plotly.graph_objects as go

from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import ConvexHull, Delaunay
from scipy.spatial.distance import euclidean

def get_neighbors(points, target_point):
    """
    Identify the neighboring points of a given target point within a Voronoi diagram. The neighbors are identified 
    based on the Voronoi ridges between the target point and its adjacent points.

    Args:
    points (np.ndarray): A numpy array of points [[x1, y1], [x2, y2], ...], including the target point.
    target_point (np.ndarray): A numpy array representing the target point [x, y].

    Returns:
    np.ndarray: A numpy array of the neighboring points to the target point including the target point.

    """
    target_idx = np.where((points == target_point).all(axis=1))[0][0]
    vor = Voronoi(points)
    neighbor_indices = [i for i in range(len(points)) if 
                vor.ridge_points[np.isin(vor.ridge_points, target_idx).any(1)].flatten().tolist().count(i) > 0]  
    vor_np_n = points[neighbor_indices]
    return vor_np_n

def order_polygon_points(points):
    """
    Order a numpy array representing a polygon's coordinates.

    Args:
    points (np.ndarray): A numpy array of points [[x1, y1], [x2, y2], ...] as the polygon's vertices.

    Returns:
    np.ndarray: The ordered coordinates of the polygon.
    """
    # Calculate centroid
    centroid_x = np.mean(points[:, 0])
    centroid_y = np.mean(points[:, 1])

    # Sort the points based on angle from centroid
    sorted_points = sorted(points, key=lambda point: math.atan2(point[1] - centroid_y, point[0] - centroid_x))

    return np.array(sorted_points)

def get_vertices(points, target_point):
    """
    Computes and orders the vertices of the Voronoi cell corresponding to a specified point.

    Args:
    points (np.ndarray): An ORDERED numpy array of points [[x1, y1], [x2, y2], ...] as the polygon's vertices.
    target_point (np.ndarray): A numpy array representing the target point [x, y].

    Returns:
    np.ndarray: An ordered numpy array of the vertices.
    """
    vor = Voronoi(points)
    vertices = vor.vertices
    
    target_point_idx = np.where((points == target_point).all(axis=1))[0][0]
    region_index = vor.point_region[target_point_idx]
    region_vertices = vor.regions[region_index]
    vertices = np.array([v for i,v in enumerate(vertices) if i in region_vertices])
    vertices = order_polygon_points(vertices)
    
    return vertices    

def calculate_area(points):
    """
    Calculate the area of a polygon given its vertices using shoelace formula.
    
    Args:
    points (np.ndarray): An ORDERED numpy array of points [[x1, y1], [x2, y2], ...] as the polygon's vertices.

    Returns:
    float: The area of the polygon.
    """
    n = len(points)  
    area = 0.0

    for i in range(n):
        j = (i + 1) % n  
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    area = abs(area) / 2.0
    return area

def get_areas(vertices, target_point, factor_x, pitch_length):
    """
    Calculates the areas of the sub polygons formed by dividing a polygon with a vertical line through a given point.

    Args:
    points (np.ndarray): A numpy array of points [[x1, y1], [x2, y2], ...] as the polygon's vertices, known that 
    the target_point is within the polygon.
    target_point (np.ndarray): A numpy array representing the target point [x, y].

    Returns:
    tuple: A tuple containing the area of the left polygon, the area of the right polygon, 
           vertices of the left polygon, and vertices of the right polygon.
    """
    intersections, vertices_inside, vertices_outside = get_intersections_and_divide(vertices, target_point, pitch_length)

    vertices_inside = np.vstack([vertices_inside, intersections])
    vertices_inside = order_polygon_points(vertices_inside)
    area_inside = calculate_area(vertices_inside)

    vertices_outside = np.vstack([vertices_outside, intersections])
    vertices_outside = order_polygon_points(vertices_outside)
    area_outside = calculate_area(vertices_outside)

    return area_inside, area_outside, vertices_inside, vertices_outside
    
def get_intersections_and_divide(points, target_point, pitch_length):
    """
    Find the intersection points of a polygon with a line perpendicular to the line between (x0, y0) and (xg, yg),
    and divide the points into groups closer to (xg, yg) or (x0, y0).

    Args:
    points (np.ndarray): An ORDERED numpy array of points [[x1, y1], [x2, y2], ...]
                         representing the polygon's vertices.
    target_point (tuple): Coordinates (x0, y0) of the point defining the target.
    pitch_length (float): Length of the pitch to determine (xg, yg).

    Returns:
    tuple:
        - numpy.ndarray: The intersection points with the perpendicular line.
        - numpy.ndarray: Points closer to (xg, yg).
        - numpy.ndarray: Points closer to (x0, y0).
    """
    x0, y0 = target_point
    factor_x = 1 if x0 > 0 else -1
    xg, yg = pitch_length / 2 * factor_x, 0
    intersections = []

    # Slope of the line between (x0, y0) and (xg, yg)
    slope = (yg - y0) / (xg - x0)
    perp_slope = -1 / slope

    def perpendicular_line(x):
        return perp_slope * (x - x0) + y0

    # Find intersections with the polygon edges
    for i in range(len(points)):
        start, end = points[i], points[(i + 1) % len(points)]

        # Edge: y = edge_slope * (x - x_start) + y_start
        if end[0] == start[0]:  # Vertical edge
            x_intersect = start[0]
            y_intersect = perpendicular_line(x_intersect)
        else:
            edge_slope = (end[1] - start[1]) / (end[0] - start[0])
            if perp_slope == edge_slope:  # Parallel lines
                continue
            # Solve for intersection
            x_intersect = (
                (perp_slope * x0 - edge_slope * start[0] + start[1] - y0)
                / (perp_slope - edge_slope)
            )
            y_intersect = edge_slope * (x_intersect - start[0]) + start[1]

        # Check if the intersection lies on the polygon edge
        if (
            min(start[0], end[0]) <= x_intersect <= max(start[0], end[0])
            and min(start[1], end[1]) <= y_intersect <= max(start[1], end[1])
        ):
            intersections.append([x_intersect, y_intersect])

    # Ensure there are exactly two intersections
    if len(intersections) != 2:
        raise Exception("Number of intersections not equal to two")

    intersections = np.array(intersections)

    # Divide points into closer and further groups
    closer_points = []
    further_points = []

    # Calculate the dividing line function
    for point in points:
        x, y = point
        # Plug point into the line 
        dx = xg - x0
        dy = yg - y0
        t = ((x - x0) * dx + (y - y0) * dy) / (dx**2 + dy**2)
    
        # Compute the projected point
        x_proj = x0 + t * dx
        y_proj = y0 + t * dy

        # Distance from the projection point to (xg, yg) and to (x0, y0)
        proj_to_goal = np.sqrt((x_proj - xg) ** 2 + (y_proj - yg) ** 2)
        ball_to_goal = np.sqrt((x0 - xg) ** 2 + (y0 - yg) ** 2)

        # Classify the point
        if proj_to_goal < ball_to_goal:
            closer_points.append(point)
        else:
            further_points.append(point)

    return intersections, np.array(closer_points), np.array(further_points)
    
def get_intersections(points, x_value):
    """
    Find the intersection points of a polygon with a vertical line x = x_value.

    Args:
    points (np.ndarray): An ORDERED numpy array of points [[x1, y1], [x2, y2], ...] as the polygon's vertices, known
    that x_value is between the min and max x values of points.
    x_value (float): The x-value of the vertical line.

    Returns:
    numpy array: The intersection points with the line x = x_value.
    """
    intersections = []

    for i in range(len(points)):
        start, end = points[i], points[(i + 1) % len(points)]

        if (start[0] <= x_value and end[0] >= x_value) or (end[0] <= x_value and start[0] >= x_value):
            if start[0] == end[0]: 
                if start[0] == x_value:
                    intersections.append([start, end])
            else:
                t = (x_value - start[0]) / (end[0] - start[0])
                y_intersect = start[1] + t * (end[1] - start[1])
                intersections.append([x_value, y_intersect])

    if len(intersections) != 2:
        raise Exception("number of intersections not equal to two")

    return np.array(intersections)

def plot_polygon(vertices, color='grey', alpha = 0.5):
    '''
    Fill a polygon in a plot.
    '''
    if len(vertices) > 0:
        x = vertices[:, 0].tolist() + [vertices[0, 0]]
        y = vertices[:, 1].tolist() + [vertices[0, 1]]
        return go.Scatter(x=x, y=y, fill='toself', fillcolor=color, opacity=alpha, 
                          mode='none', showlegend=False)

def plot_vor(points_nbs, ball_xy, boundary_points, vertices, 
             area_inside, area_outside):

    fig = go.Figure()
    vor = Voronoi(points_nbs)

    # Plot Voronoi edges
    for simplex in vor.ridge_vertices:
        simplex = np.asarray(simplex)
        if np.all(simplex >= 0):
            fig.add_trace(go.Scatter(x=vor.vertices[simplex, 0], y=vor.vertices[simplex, 1],
                                     mode='lines', line_color='grey', line_width=0.5, showlegend=False))

    # Separate defender points from carrier and boundary points
    defense_nbs_xy = np.array([p for i, p in enumerate(points_nbs) if 
                               not np.any((p == np.vstack([boundary_points, ball_xy])).all(axis=1))])

    # Plot polygons for divided Voronoi cell
    fig.add_trace(plot_polygon(area_inside, alpha=0.5))
    fig.add_trace(plot_polygon(area_outside, alpha=0.2))

    # Add scatter plots for different points
    fig.add_trace(go.Scatter(x=defense_nbs_xy[:, 0], y=defense_nbs_xy[:, 1], mode='markers',
                             marker=dict(color='darkblue', size=10), name='Defenders'))
    fig.add_trace(go.Scatter(x=[ball_xy[0]], y=[ball_xy[1]], mode='markers',
                             marker=dict(color='sienna', size=10), name='Ball'))
    
    points_plot = np.vstack([defense_nbs_xy, vertices])   
    max_y = np.max(points_plot[:, 1])
    min_y = np.min(points_plot[:, 1])
    max_x = np.max(points_plot[:, 0])
    min_x = np.min(points_plot[:, 0])
    ylim_top = max_y + 2 
    ylim_bot = min_y - 2

    # Set layout
    fig.update_layout(plot_bgcolor='white', xaxis=dict(range=[min_x-1, max_x+2], showticklabels = False),
                      yaxis=dict(range=[ylim_bot-1, ylim_top-1], showticklabels = False),
                      showlegend=True, legend=dict(x=0.9, y=1, font = dict(size=13)),
                      dragmode=False, width=400, height=300,
                      margin=dict(t=4, b=0, r=2))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, scaleanchor="x", scaleratio=1)    
    
    return fig