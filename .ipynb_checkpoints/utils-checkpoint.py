import pandas as pd
import numpy as np
import json
import jsonlines
import math

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def load_jsonl_file(file_path):
    with jsonlines.open(file_path, 'r') as file:
        data = [line for line in file if line['timestamp'] is not None]
    return data

def explode_data(row):
    players = pd.DataFrame(row['player_data'])
    players['object'] = 'player'
    
    ball = pd.DataFrame([row['ball_data']])
    ball['object'] = 'ball'
    ball['player_id'] = 0  
   
    combined = pd.concat([players, ball], ignore_index=True)
    
    for col in row.index:
        if col not in ['player_data', 'ball_data']:
            combined[col] = row[col]   
    return combined

def euclidean_distance(x1, y1, x2, y2):
    """Calculate the Euclidean distance between two points."""
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def check_target_area(pitch_length, period, team, x, y, box_width = 40.3):
    third_boundary = pitch_length / 6  # Boundary for attacking third
    wide_channel_limit = box_width/2  # Wide channel boundary on y-axis

    if team == "home":
        if period ==1:
            return (x > third_boundary) and (
                abs(y) > wide_channel_limit)
        elif period ==2:
            return (x < -third_boundary) and (
                abs(y) > wide_channel_limit)  
    elif team == 'away':
        if period ==1:
            return (x < -third_boundary) and (
                abs(y) > wide_channel_limit)  
        elif period ==2:
            return (x > third_boundary) and (
                abs(y) > wide_channel_limit)  

def get_receive_frame(tracking_path, team, pitch_length, start_frame, end_frame, target_player_id, distance_threshold = 2):
    matching_line = None
    
    with jsonlines.open(tracking_path, 'r') as file:
        start_checking = False  # Flag to start processing lines after the starting frame
        
        for line in file:
            frame = line.get('frame')
            
            # Stop processing if end_frame is reached
            if frame and frame >= end_frame:
                break
            
            # Check if we've reached the starting frame
            if not start_checking:
                if frame == start_frame:
                    start_checking = True
                continue
    
            # Process lines after the starting frame
            period = line['period']
            player_data = line.get('player_data', [])
            if len(player_data) == 0:
                continue
            ball_data = line.get('ball_data', None)
    
            ball_x, ball_y = ball_data['x'], ball_data['y']
            if not ball_x or not ball_y:
                continue
            
            for player in player_data:
                if player.get('player_id') == target_player_id:
                    player_x, player_y = player['x'], player['y']
                    
                    dist = euclidean_distance(player_x, player_y, ball_x, ball_y)
                    if dist <= distance_threshold:
                        matching_line = line
                        break
            
            target_area = check_target_area(pitch_length, period, team, player_x, player_y)
                
            if matching_line:
                break    
    if matching_line:
        return period, matching_line['frame'], player_x, player_y, target_area
    else: return None, None, None, None, None