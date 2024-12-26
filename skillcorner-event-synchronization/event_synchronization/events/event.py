class Event:
    def __init__(
        self,
        event_id,
        period,
        timestamp,
        generic_event_type,
        player_id,
        provider_player_id,
        team_id,
        provider_team_id,
        x,
        y,
        to_refine=False,
        is_head=False,
        touch_type=None,
        event_type_name=None,
        force_to_refine=False,
        is_matched_applicable=True,
        offset_refine=None,
    ):
        self.id = event_id
        self.period = period
        self.timestamp = timestamp
        self.generic_event_type = generic_event_type
        self.player_id = player_id
        self.provider_player_id = provider_player_id
        self.team_id = team_id
        self.provider_team_id = provider_team_id
        self.x = x
        self.y = y
        self.to_refine = to_refine
        self.is_head = is_head
        self.touch_type = touch_type
        self.event_type_name = event_type_name
        self.force_to_refine = force_to_refine
        self.is_matched_applicable = is_matched_applicable
        self.offset_refine = offset_refine
