import logging

import pandas as pd

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

TH_MATCHED = 40  # th (in %) of matched events
ACCEPTABLE_NEGATIVE_TH = -100  # acceptable negative th for period start estimation


class WarningManager:
    """
    A manager class responsible for handling warnings
    """

    def __init__(self):
        pass

    def warning_negative_period_start_estimation(self, refined_period_start_frame: tuple) -> None:
        """Warn if the period start estimation is highly negative (below ACCEPTABLE_NEGATIVE_TH)

        Args:
            refined_period_start_frame (tuple): refined period start frame
        """

        if refined_period_start_frame[1] < ACCEPTABLE_NEGATIVE_TH:
            msg = f'Events Synchro: Negative period start estimation: {refined_period_start_frame}'
            info_msg = '\n   - Probably due to a problem in the video, in the events or in the tracking data'
            logging.warning(msg + info_msg)

    def warning_low_is_matched(self, report_by_event: pd.DataFrame) -> None:
        """Warn if the number of matched events is too low

        Args:
            report_by_event (pd.DataFrame): report by event type
        """

        report_by_event = report_by_event.copy()
        report_by_event['nb_events'] = 1

        # ignore all events with no player_id
        report_by_event_filtered = report_by_event[report_by_event['is_matched_applicable']]

        # Total Percent of Event Matched
        tpem = report_by_event_filtered['is_matched'].sum() / report_by_event_filtered['nb_events'].sum() * 100
        tpem = round(tpem, 1)
        if tpem < TH_MATCHED:
            msg = f'Events Synchro: Number of matched events is too low ({tpem} %)'
            info_msg = '\n   - Probably due to a problem in the video, in the events or in the tracking data'
            logging.warning(msg + info_msg)

    def warning_mapping_player_id(self, report_by_event: pd.DataFrame, event_provider: str) -> None:
        """Warn if there is a problem of mapping for the provider_player_id

        Args:
            report_by_event (pd.DataFrame): report by event type
        """

        no_mapping_df = report_by_event[
            report_by_event[f'{event_provider}_player_id'].notna() & report_by_event['player_id'].isna()
        ]
        if len(list(no_mapping_df[f'{event_provider}_player_id'].unique())) > 0:
            list_no_mapped_ply_id = [
                int(player_id) for player_id in list(no_mapping_df[f'{event_provider}_player_id'].unique())
            ]

            # specific case for wyscout (player_id = 0 is not a "problem")
            if event_provider == 'wyscout':
                list_no_mapped_ply_id = [ply_id for ply_id in list_no_mapped_ply_id if ply_id > 0]

            if len(list_no_mapped_ply_id) > 0:
                msg = f'Problem of mapping for the following {event_provider}_player_id: {list_no_mapped_ply_id}'
                info_msg = '\n   - Probably due to a problem in the events or in the match_data'
                logging.warning(msg + info_msg)
