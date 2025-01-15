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

def check_target_area(home_start, pitch_length, period, team, x, y, box_width = 40.3):
    if home_start == 'right_to_left':
        x = -x  # Flip the x-coordinate to normalize direction

    # Define boundaries
    third_boundary = pitch_length / 6  # Boundary for attacking third
    wide_channel_limit = box_width / 2  # Wide channel boundary on y-axis

    # Normalize periods so home team attacks left-to-right in both periods
    if team == 'home':
        in_final_third = (x > third_boundary) if period == 1 else (x < -third_boundary)
    elif team == 'away':
        in_final_third = (x < -third_boundary) if period == 1 else (x > third_boundary)
    else:
        return False

    # Check if the player is in the wide channel
    is_in_wide_channel = abs(y) > wide_channel_limit

    return in_final_third and is_in_wide_channel

def get_receive_frame(tracking_path, team, home_start, pitch_length, start_frame, end_frame, target_player_id, distance_threshold = 2):
    matching_line = None
    
    # Load tracking data in bulk for efficiency
    data = []
    with jsonlines.open(tracking_path, 'r') as file:
        for line in file:
            frame = line.get('frame')
            # Only process relevant frames
            if start_frame <= frame <= end_frame:
                data.append(line)
            elif frame > end_frame:
                break

    # Convert to DataFrame for faster filtering
    df = pd.DataFrame(data)
    if df.empty:
        return None, None, None, None, None

    # Extract relevant columns
    df = df.explode('player_data').reset_index(drop=True)
    df['player_data'] = df['player_data'].apply(lambda x: x or {})  # Handle missing player_data
    
    # Filter out rows without valid ball data
    df = df[df['ball_data'].notna()]
    df['ball_x'] = df['ball_data'].apply(lambda x: x['x'])
    df['ball_y'] = df['ball_data'].apply(lambda x: x['y'])
    df = df[df[['ball_x', 'ball_y']].notnull().all(axis=1)]

    # Extract target player information
    df['player_id'] = df['player_data'].apply(lambda x: x.get('player_id', None))
    df['player_x'] = df['player_data'].apply(lambda x: x.get('x', None))
    df['player_y'] = df['player_data'].apply(lambda x: x.get('y', None))
    df = df[df['player_id'] == target_player_id]

    # Compute distance between player and ball
    df['distance'] = np.sqrt((df['player_x'] - df['ball_x'])**2 + (df['player_y'] - df['ball_y'])**2)
    df = df[df['distance'] <= distance_threshold]

    if df.empty:
        return None, None, None, None, None

    # Get the first matching row
    match = df.iloc[0]
    player_x, player_y = match['player_x'], match['player_y']
    target_area = check_target_area(home_start, pitch_length, match['period'], team, player_x, player_y)

    return match['period'], match['frame'], player_x, player_y, target_area

def find_ball(match_id, frame):
    tracking_path = f'data/FA/tracking/{match_id}.jsonl'
    with jsonlines.open(tracking_path, 'r') as file:
        data = [line for line in file if line['frame'] == frame][0]
        ball_data = data['ball_data']
    return ball_data['x'], ball_data['y']
        