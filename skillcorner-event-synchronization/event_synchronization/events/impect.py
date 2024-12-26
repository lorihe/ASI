from event_synchronization.constants import GENERIC_EVENT, PASS_EVENT, SHOT_EVENT
from event_synchronization.events.event import Event
from event_synchronization.events.players_mapping_manager import SkcPlayersMapping

KEY_JNO = 'shirtNumber'
PASS_TYPE_ID = 'PASS'
SHOT_TYPE_ID = 'SHOT'
HEAD_TYPE_ID = 'HEAD'
FIRST_TOUCH_PRIMARY_TYPES = ['RECEPTION', 'CLEARANCE', 'BLOCK', 'INTERCEPTION']
NO_IS_MATCHED_APPLICABLE_LIST = ['NO_VIDEO', 'FINAL_WHISTLE', 'KICK_OFF', 'OUT']
OFFSET_FORCE_REFINE = 15  # offset to refine for force refine events (in frame)
OFFSET_REFINE = 5  # offset to refine for events to refine (in frame)
POSSIBLE_PERIOD_ID = [1, 2, 3, 4]
NO_PERIOD_ID = -1
PERIOD_STARTS_IN_SEC = {
    1: 0.0,
    2: 10000.0,
    3: 20000.0,
    4: 23333.33,
}


class ImpectEvents:
    def __init__(self, raw_impect_events, impect_match_data, match_data):
        self.raw_events = raw_impect_events
        self.impect_match_data = impect_match_data
        self.match_data = match_data

        self.impect_team_id_to_skc_team_id, self.impect_ply_id_to_skc_ply_id = get_impect_id_to_skc_id(
            match_data, impect_match_data
        )
        self.event_provider = 'impect'
        self.previous_event_type_name = None

    def get_impect_player_id(self, event):
        """Get impect player id

        Args:
            event: raw impect event

        Returns:
            player_id (int): player id
        """

        if event['player'] is None:
            return None
        return event['player']['id']

    def get_player_id(self, impect_player_id):
        """Get SKC player id

        Args:
            impeact_player_id: impect player id

        Returns:
            player_id (int): player id
        """

        return self.impect_ply_id_to_skc_ply_id.get(impect_player_id, None)

    def get_impect_team_id(self, event):
        """Get impect team id

        Args:
            event: raw impect event

        Returns:
            team_id (int): team id
        """

        return int(event.get('squadId', None)) if event.get('squadId', None) is not None else None

    def get_team_id(self, impect_team_id):
        """Get SKC team id

        Args:
            impect_team_id: impect team id

        Returns:
            team_id (int): team id
        """

        return self.impect_team_id_to_skc_team_id.get(impect_team_id, None)

    def get_timestamp(self, event):
        """Get event timestamp

        Args:
            event: raw impect event

        Returns:
            timestamp (float): timestamp of the event
        """

        return event['gameTime']['gameTimeInSec'] - PERIOD_STARTS_IN_SEC[int(event['periodId'])]

    def get_event_location(self, event):
        """Get event location

        Args:
            event: raw impect event

        Returns:
            x_event (float): x coordinate of the event in SKC coordinates system
            y_event (float): y coordinate of the event in SKC coordinates system
        """

        event_location = event.get('start', None)
        if event_location is not None:
            event_location = event_location.get('coordinates', None)
        if event_location is None:
            return 'unknown', 'unknown'
        try:
            x_event, y_event = float(event_location['x']), float(event_location['y'])
        except (TypeError, ValueError):
            return 'unknown', 'unknown'
        x_event = x_event * self.match_data['pitch_length'] / 105
        y_event = y_event * self.match_data['pitch_width'] / 68

        return x_event, y_event

    def get_generic_event_type(self, event):
        """Get generic event type

        Args:
            event: raw impect event

        Returns:
            event_type (str): event type
        """

        if event['actionType'] == PASS_TYPE_ID:
            return PASS_EVENT
        elif event['actionType'] == SHOT_TYPE_ID:
            return SHOT_EVENT
        else:
            return GENERIC_EVENT

    def get_event_type_name(self, event):
        """Get event type name

        Args:
            event: raw impect event

        Returns:
            event_type_name (str): event type name
        """

        return event.get('actionType')

    def get_is_first_touch_event(self, event):
        """Get whether the event is a first touch event or not

        Args:
            raw_event: raw wyscout event

        Returns:
            is_first_touch_event (bool): whether the event is a first touch event or not
        """

        return event['actionType'] in FIRST_TOUCH_PRIMARY_TYPES

    def standardize_events(self):
        """Convert raw impect events to standardized events

        Returns:
            standardized_events (list[event_synchronization.events.events.Event])
        """

        standardized_events = []
        for raw_event in self.raw_events:
            # ignore penalty shootout events
            if int(raw_event.get('periodId', NO_PERIOD_ID)) not in POSSIBLE_PERIOD_ID:
                continue

            # impect player and team id
            impect_player_id = self.get_impect_player_id(raw_event)
            impect_team_id = self.get_impect_team_id(raw_event)

            # get event location
            x_event, y_event = self.get_event_location(raw_event)

            # get standardized event
            standardized_event = Event(
                event_id=raw_event['id'],
                period=int(raw_event['periodId']),
                timestamp=self.get_timestamp(raw_event),
                generic_event_type=self.get_generic_event_type(raw_event),
                player_id=self.get_player_id(impect_player_id),
                provider_player_id=impect_player_id,
                team_id=self.get_team_id(impect_team_id),
                provider_team_id=impect_team_id,
                x=x_event,
                y=y_event,
                event_type_name=self.get_event_type_name(raw_event),
                touch_type=self.get_is_first_touch_event(raw_event),
                to_refine=(self.get_generic_event_type(raw_event) in [PASS_EVENT, SHOT_EVENT]),
                force_to_refine=force_to_refine(raw_event, self.previous_event_type_name),
                is_head=(raw_event['bodyPart'] == HEAD_TYPE_ID),
                is_matched_applicable=self.get_event_type_name(raw_event) not in NO_IS_MATCHED_APPLICABLE_LIST,
            )
            standardized_event.offset_refine = get_offset_refine(standardized_event)

            self.previous_event_type_name = standardized_event.event_type_name
            standardized_events.append(standardized_event)
        return standardized_events


def get_impect_ply_id_to_ply(impect_match_data):
    return {
        ply['id']: {**ply, 'team_id': impect_match_data[team_type]['id']}
        for team_type in ['squadHome', 'squadAway']
        for ply in impect_match_data[team_type]['players']
    }


def get_skc_team_id_to_impect_team_id(match_data, impect_match_data):
    return {
        match_data['home_team']['id']: impect_match_data['squadHome']['id'],
        match_data['away_team']['id']: impect_match_data['squadAway']['id'],
    }


def get_impect_id_to_skc_id(match_data, impect_match_data):
    impect_ply_id_to_ply = get_impect_ply_id_to_ply(impect_match_data)
    skc_team_id_to_impect_team_id = get_skc_team_id_to_impect_team_id(match_data, impect_match_data)
    impect_team_id_to_skc_team_id = {v: k for k, v in skc_team_id_to_impect_team_id.items()}
    impect_ply_id_to_skc_ply_id = SkcPlayersMapping(
        match_data
    ).get_provider_ply_id_to_skc_ply_id_with_known_team_id_mapping(
        impect_ply_id_to_ply, skc_team_id_to_impect_team_id, key_jno=KEY_JNO
    )
    return impect_team_id_to_skc_team_id, impect_ply_id_to_skc_ply_id


def force_to_refine(event, previous_event_type_name):
    return (
        (event.get('actionType', 'unknown') == 'PASS')
        & (previous_event_type_name in ['RECEPTION', 'LOOSE_BALL_REGAIN', 'INTERCEPTION'])
        & (event.get('bodyPart', None) != 'HEAD')
    )


def get_offset_refine(standardized_event):
    if standardized_event.force_to_refine:
        return OFFSET_FORCE_REFINE
    elif standardized_event.to_refine:
        return OFFSET_REFINE
    else:
        return None
