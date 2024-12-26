# Event Synchronization

The objective is to synchronize the events provided by Wyscout, {provider}, StatsBomb, and Impect with SkillCorner tracking data.

## Table of Contents

1. [Description](#description)
2. [Installation](#installation)
3. [Usage](#usage)
4. [License](#license)

## Description

The event synchronization process involves several key steps to ensure accurate alignment between event data and tracking data. The following sections detail each step:

### 1. Find a General Offset to Achieve Good Alignment
This step combines tracking and event timestamps to find the offset that best aligns the two datasets. By using player-ball distance, we statistically determine and refine the offset frame.

### 2. (Optional) Apply Refinement
This step refines the event frame using tracking data to pinpoint the exact moment of a pass or shot. It identifies a window where the distance between the player involved and the ball is less than 3 meters. Within this window, the frame with the highest ball acceleration is considered the exact event moment. If the acceleration data is unreliable, the frame identified using the general offset is retained.

### 3. Matching of Events
As each event is associated with a player, we have the possibility to compare the distance between the player involved in the event and the ball using our tracking data. A threshold of 3.5 meters is used within a window of ±5 frames around the event's frame. So if the distance player and ball is within 3.5 meters at least once during this window, then is_matched=True; otherwise, is_matched=False. This comparison helps create the `is_matched` binary flag, indicating whether the tracking data and events can be trusted at this frame.

### 4. Generate Reports and Freeze Frame Format
The synchronization process generates three outputs:

1. **report_by_event**: A CSV file where each row corresponds to an event. Columns include:
    - {provider}_event_id
    - {provider}_event_type
    - period
    - frame
    - player_id
    - {provider}_player_id
    - player_name
    - player_role
    - player_number
    - starting
    - team_id
    - {provider}_team_id
    - team_type
    - team_name
    - is_matched
    - is_player_detected
    - has_{provider}_player_id_attached
    - frame_tracking_data_available
    - is_matched_applicable
2. **report_by_event_type**: A CSV file grouping events by type with performance metrics related to `is_matched`. Columns include:
    - {provider}_event_type
    - nb_events
    - is_matched
    - %_is_matched
    - is_matched_is_player_detected
    - is_not_matched
    - is_not_matched_is_player_detected
    - is_not_matched_has_{provider}_player_id_attached
    - is_not_matched_frame_tracking_data_available
    - is_matched_applicable
3. **freeze_frame_format**: A list of dictionaries containing enriched tracking data. Example of an element:
    ```json
    {
        "frame": 35261,
        "timestamp": "00:53:28.10",
        "period": 2,
        "ball_data": {
            "x": -25.15,
            "y": -24.01,
            "z": 0.17,
            "is_detected": true
        },
        "player_data": [
            {
                "x": -46.05,
                "y": -2.62,
                "player_id": 11898,
                "is_detected": false,
                "speed_norm": 1.47,
                "vx": -1.45,
                "vy": -0.25,
                "acc_norm": 0.15
            },
            ...
            {
                "x": -19.12,
                "y": -13.14,
                "player_id": 17965,
                "is_detected": true,
                "speed_norm": 4.65,
                "vx": -4.2,
                "vy": 2.0,
                "acc_norm": 3.08
            }
        ],
        "{provider}_event_id": "2315178015",
        "{provider}_event_type": "Pass",
        "player_id": 34847,
        "{provider}_player_id": "426384",
        "team_id": 672,
        "{provider}_team_id": "596",
        "is_matched": true,
        "is_player_detected": true,
        "projected_{provider}_event_x": -21.6,
        "projected_{provider}_event_y": -22.27
    }
    ```

## Installation

To use the project, follow these steps:

1. Ensure you have Python >= 3.8 installed.
2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

To use the synchronization tool, follow these steps:

1. Ensure you are in the root of the folder
2. Run the event-synchronization:

##### For Impect

```sh
python -m tools.run_impect
    --match_data_path /path/to/skc_match_data.json \
    --tracking_data_path /path/to/skc_tracking_data.json \
    --impect_events_path /path/to/impect_events.json \
    --impect_match_data_path /path/to/impect_match_data.json \
    --save_outputs_dir /path/to/output_directory \
```

##### For Opta

```sh
python -m tools.run_opta \
    --match_data_path /path/to/skc_match_data.json \
    --tracking_data_path /path/to/skc_tracking_data.json \
    --opta_events_path /path/to/opta_events.json (or .xml) \
    --opta_match_data_path /path/to/opta_match_data.json (or .xml) \
    --save_outputs_dir /path/to/output_directory \
```

##### For StatsBomb

```sh
python -m tools.run_statsbomb \
    --match_data_path /path/to/skc_match_data.json \
    --tracking_data_path /path/to/skc_tracking_data.json \
    --statsbomb_events_path /path/to/statsbomb_events.json \
    --statsbomb_match_data_path /path/to/statsbomb_lineup.json \
    --statsbomb_home_team_id statsbomb_home_team_id \
    --save_outputs_dir /path/to/output_directory \
```

##### For Wyscout

```sh
python -m tools.run_wyscout \
    --match_data_path /path/to/skc_match_data.json \
    --tracking_data_path /path/to/skc_tracking_data.json \
    --wyscout_events_path /path/to/wyscout_events.json \
    --save_outputs_dir /path/to/output_directory \
```

Note:
You also have access to some notebook examples in: `tools/notebook_example` (Don't forget to install `skillcorner` to use `SkillcornerClient`).

## License

Distributed under the SkillCorner License.
