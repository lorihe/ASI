from datetime import datetime

from event_synchronization.constants import GENERIC_EVENT, PASS_EVENT, SHOT_EVENT
from event_synchronization.events.event import Event
from event_synchronization.events.players_mapping_manager import SkcPlayersMapping

KEY_JNO = 'jersey_number'
PASS_TYPE_ID = 30
SHOT_TYPE_ID = 16
STB_LENGTH = 120
STB_WIDTH = 80
NO_IS_MATCHED_APPLICABLE_LIST = [
    'Tactical Shift',
    'Substitution',
    'Referee Ball-Drop',
    'Player Off',
    'Player On',
    'Injury Stoppage',
    'Half End',
    'Half Start',
    'Starting XI',
]
OFFSET_REFINE = 5  # offset to refine for events to refine (in frame)
POSSIBLE_PERIOD_ID = [1, 2, 3, 4]
NO_PERIOD_ID = -1


class StatsbombEvents:
    def __init__(self, raw_statsbomb_events, statsbomb_lineup, statsbomb_home_team_id, match_data):
        self.raw_events = raw_statsbomb_events
        self.statsbomb_lineup = statsbomb_lineup
        self.match_data = match_data

        self.stb_team_id_to_skc_team_id, self.stb_ply_id_to_skc_ply_id = get_stb_id_to_skc_id(
            match_data, statsbomb_lineup, int(statsbomb_home_team_id)
        )
        self.event_provider = 'statsbomb'

    def get_stb_player_id(self, event):
        """Get statsbomb player id

        Args:
            event: raw statsbomb event

        Returns:
            player_id (int): player id
        """

        return event.get('player', {}).get('id', None)

    def get_player_id(self, stb_player_id):
        """Get SKC player id

        Args:
            stb_player_id: statsbomb player id

        Returns:
            player_id (int): player id
        """

        return self.stb_ply_id_to_skc_ply_id.get(stb_player_id, None)

    def get_stb_team_id(self, event):
        """Get statsbomb team id

        Args:
            event: raw statsbomb event

        Returns:
            team_id (int): team id
        """

        stb_team_id = event.get('team', {}).get('id', None)
        return int(stb_team_id) if stb_team_id is not None else None

    def get_team_id(self, stb_team_id):
        """Get SKC team id

        Args:
            stb_team_id: statsbomb team id

        Returns:
            team_id (int): team id
        """

        return self.stb_team_id_to_skc_team_id.get(stb_team_id, None)

    def get_timestamp(self, event):
        """Get event timestamp

        Args:
            event: raw statsbomb event

        Returns:
            timestamp (float): timestamp of the event
        """

        event_datetime = datetime.strptime(event['timestamp'], '%H:%M:%S.%f')
        return event_datetime.minute * 60 + event_datetime.second + event_datetime.microsecond / 10**6

    def get_event_location(self, event):
        """Get event location

        Args:
            event: raw statsbomb event

        Returns:
            x_event (float): x coordinate of the event in SKC coordinates system
            y_event (float): y coordinate of the event in SKC coordinates system
        """

        pitch_length = self.match_data['pitch_length']
        pitch_width = self.match_data['pitch_width']

        event_location = event.get('location', None)
        if event_location is None:
            return 'unknown', 'unknown'
        try:
            x_event, y_event = map(float, event_location)
            x_event = (x_event - (STB_LENGTH / 2)) * pitch_length / STB_LENGTH
            y_event = -(y_event - (STB_WIDTH / 2)) * pitch_width / STB_WIDTH
            return x_event, y_event
        except (TypeError, ValueError):
            return 'unknown', 'unknown'

    def get_generic_event_type(self, event):
        """Get generic event type

        Args:
            event: raw stb event

        Returns:
            event_type (str): event type
        """

        type_id = event['type']['id'] if 'type' in event else event['type.id']
        if type_id == PASS_TYPE_ID:
            return PASS_EVENT
        elif type_id == SHOT_TYPE_ID:
            return SHOT_EVENT
        else:
            return GENERIC_EVENT

    def get_event_type_name(self, event):
        """Get event type name

        Args:
            event: raw statsbomb event

        Returns:
            event_type_name (str): event type name
        """

        return event['type']['name'] if 'type' in event else event['type.name']

    def standardize_events(self):
        """
        Convert raw statsbomb events to standardized events

        Returns:
            standardized_events (list[event_synchronization.events.events.Event])
        """

        standardized_events = []
        for raw_event in self.raw_events:
            # ignore penalty shootout events
            if int(raw_event.get('period', NO_PERIOD_ID)) not in POSSIBLE_PERIOD_ID:
                continue

            # get stb player and team id
            stb_player_id = self.get_stb_player_id(raw_event)
            stb_team_id = self.get_stb_team_id(raw_event)

            # get event location
            x_event, y_event = self.get_event_location(raw_event)

            # get standardized event
            standardized_event = Event(
                event_id=raw_event['id'],
                period=int(raw_event['period']),
                timestamp=self.get_timestamp(raw_event),
                generic_event_type=self.get_generic_event_type(raw_event),
                player_id=self.get_player_id(stb_player_id),
                provider_player_id=stb_player_id,
                team_id=self.get_team_id(stb_team_id),
                provider_team_id=stb_team_id,
                x=x_event,
                y=y_event,
                event_type_name=self.get_event_type_name(raw_event),
                to_refine=(self.get_generic_event_type(raw_event) in [PASS_EVENT, SHOT_EVENT]),
                is_matched_applicable=self.get_event_type_name(raw_event) not in NO_IS_MATCHED_APPLICABLE_LIST,
            )
            standardized_event.offset_refine = get_offset_refine(standardized_event)

            standardized_events.append(standardized_event)
        return standardized_events


def get_stb_ply_id_to_ply(stb_lineup):
    has_positions_key = all('positions' in ply_info for team_info in stb_lineup for ply_info in team_info['lineup'])

    # old format where stb lineup contains only active players
    if not has_positions_key:
        return {
            ply_info['player_id']: {**ply_info, 'team_id': team_info['team_id']}
            for team_info in stb_lineup
            for ply_info in team_info['lineup']
        }

    # new format where stb lineup contains all players (event if they are not active = len(positions) == 0)
    else:
        return {
            ply_info['player_id']: {**ply_info, 'team_id': team_info['team_id']}
            for team_info in stb_lineup
            for ply_info in team_info['lineup']
            if len(ply_info.get('positions'))
        }


def get_skc_team_id_to_stb_team_id(match_data, stb_lineup, statsbomb_home_team_id):
    if statsbomb_home_team_id == stb_lineup[0]['team_id']:
        return {
            match_data['home_team']['id']: stb_lineup[0]['team_id'],
            match_data['away_team']['id']: stb_lineup[1]['team_id'],
        }
    elif statsbomb_home_team_id == stb_lineup[1]['team_id']:
        return {
            match_data['home_team']['id']: stb_lineup[1]['team_id'],
            match_data['away_team']['id']: stb_lineup[0]['team_id'],
        }
    else:
        raise ValueError('Statsbomb home team id does not match any team id in lineup')


def get_stb_id_to_skc_id(match_data, stb_match_data, statsbomb_home_team_id):
    stb_ply_id_to_ply = get_stb_ply_id_to_ply(stb_match_data)
    skc_team_id_to_stb_team_id = get_skc_team_id_to_stb_team_id(match_data, stb_match_data, statsbomb_home_team_id)
    stb_team_id_to_skc_team_id = {v: k for k, v in skc_team_id_to_stb_team_id.items()}
    stb_ply_id_to_skc_ply_id = SkcPlayersMapping(
        match_data
    ).get_provider_ply_id_to_skc_ply_id_with_known_team_id_mapping(
        stb_ply_id_to_ply, skc_team_id_to_stb_team_id, key_jno=KEY_JNO
    )
    return stb_team_id_to_skc_team_id, stb_ply_id_to_skc_ply_id


def get_offset_refine(standardized_event):
    return OFFSET_REFINE if standardized_event.to_refine else None
