"""Every Confirmation clause of ADR-0050 to ADR-0058, and what holds it.

ADR-0049, amended 2026-10-03: "Every Confirmation clause in a record is
either a test or explicitly marked as checkable only on live runs. None stays
as prose." ADR-0050's Confirmation said from 2026-09-28 that the closure test
must not fire on a board polled but not read back far enough, nothing
enforced it, and on 2026-10-01 and 10-02 it fired on 47 open rows.

Each clause is keyed by its bold lead, exactly as the record writes it, and
holds one of:
- `tests`: the tests that hold it, as `module.Class.method` under `tests/`;
- `live`: why it can only be seen on live runs or private data;
- `unbuilt`: why there is nothing to test yet.
`gap` adds what a clause claims that nothing holds, reported to the
architecture chat. A paragraph whose lead is "Live only:" declares itself.
`tests/test_fitness.py` checks this file against the records and the suite.
"""

LIVE_ONLY_LEAD = "Live only:"

CONFIRMATIONS = {
    "0050": {
        "The verify step must be seen refusing.": {"tests": [
            "test_sweep.TestStep2StoreVerifyDelete.test_the_verify_refuses_until_the_store_holds_the_row"]},
        "The skip must be seen both ways, and at the member level.": {"tests": [
            "test_projection.TestTheSkip.test_both_ways_against_a_hand_written_store",
            "test_projection.TestTheSkip.test_any_member_in_a_store_skips_the_whole_group",
            "test_projection.TestTheSkipOnARealGroup."
            "test_one_non_representative_member_in_a_store_suppresses_a_whole_speechify_group"]},
        "The skip must be seen reading by reason.": {"tests": [
            "test_projection.TestTheSkip.test_the_removal_store_is_read_by_reason_both_ways"]},
        "The closure test must not fire on a skipped board.": {"tests": [
            "test_closure.TestAbsence.test_four_evening_runs_with_himalayas_skipped_close_nothing",
            "test_sweep.TestSteps4And5Closed.test_four_skipped_evenings_mark_no_himalayas_row"]},
        "The closure test must not fire on a board that was polled but not read back far "
        "enough.": {"tests": [
            "test_closure.TestAbsence.test_a_paginated_run_that_stopped_short_did_not_reach_the_posting",
            "test_closure.TestAbsence.test_a_paginated_run_without_its_reach_recorded_never_counts",
            "test_sweep.TestSteps4And5Closed."
            "test_the_marks_the_pinned_posting_caused_clear_on_the_next_sweep"]},
        "`Closed` must be seen appearing and then retiring.": {"tests": [
            "test_sweep.TestSteps4And5Closed.test_closed_appears_then_retires",
            "test_closure.TestTheConfiguredCount.test_it_closes_on_the_twelfth_polled_run_and_not_the_eleventh"]},
        "A cleared `Status` must be seen removing nothing": {"tests": [
            "test_sweep.TestStep1Copy.test_a_cleared_status_removes_no_copy",
            "test_sweep.TestStep1Copy.test_a_status_changed_away_from_accepted_keeps_its_copy"]},
        "A superseded rejection copy must be seen saved before it goes": {"tests": [
            "test_sweep.TestStep1Copy.test_a_superseded_rejection_copy_is_saved_before_it_goes",
            "test_sweep.TestStep1Copy.test_a_superseded_copy_waits_while_its_record_is_not_on_origin"]},
        "The clock must not move on a projection write.": {"tests": [
            "test_sweep.TestNoClockMoves.test_neither_the_projection_nor_the_sweep_moves_a_clock"]},
        "`accepted` must be seen surviving.": {"tests": [
            "test_sweep.TestStep3RejectionTables.test_accepted_is_deleted_by_no_clock"]},
        "The month's count must be seen crossing the line.": {"tests": [
            "test_run.TestBudgetLine.test_past_sixty_percent_before_the_fifteenth_says_so"]},
    },
    "0051": {
        "The read-back must be seen refusing.": {"tests": [
            "test_private_store.TestTheFullBranch.test_the_read_back_refuses_a_file_the_branch_does_not_hold",
            "test_private_store.TestTheFullBranch.test_the_read_back_refuses_a_file_missing_after_the_push",
            "test_run.TestMain.test_a_failed_full_save_is_retried_by_the_next_run"]},
        "The partial fetch must be exercised against a real one.": {"tests": [
            "test_private_store.TestTheFullBranch.test_a_later_save_never_needs_an_earlier_files_contents"]},
        "On-demand downloads must be refused for the whole save": {"tests": [
            "test_private_store.TestTheFullBranch.test_no_command_of_a_save_may_download_on_demand"]},
        # Described from 2026-09-26 and missing until 2026-10-03, when the
        # operator said build it: `storage.commit_files` refuses it now.
        "The public branch must be seen refusing description text": {"tests": [
            "test_storage.TestDataBranch.test_the_public_branch_refuses_description_text",
            "test_storage.TestDataBranch.test_a_description_field_in_a_run_log_is_refused",
            "test_normalise.TestRowShape.test_no_description_field_exists_on_a_row"]},
        "A `pending: 0` run must write no file at all": {"tests": [
            "test_run.TestMain.test_every_posting_is_saved_whole_to_the_private_full_branch"]},
    },
    "0052": {
        "A posting exactly seven days old at first sight must be admitted, and one a second "
        "older must be dropped.": {"tests": [
            "test_filters.TestTheAgeRule.test_the_boundary_to_the_second_and_a_week_later",
            "test_filters.TestTheAgeRule.test_seven_days_old_at_first_sight_is_kept_and_a_minute_more_is_not"]},
        "An admitted row must still be admitted a week later.": {"tests": [
            "test_filters.TestTheAgeRule.test_the_boundary_to_the_second_and_a_week_later",
            "test_filters.TestTheAgeRule.test_admitted_once_it_stays_however_long_it_waits"]},
        "A Lever posting older than a week must be admitted": {"tests": [
            "test_filters.TestTheAgeRule.test_a_lever_posting_is_never_dropped_for_age"]},
        "Widening the limit must admit what it previously dropped.": {"tests": [
            "test_backfill.TestWideningTheAgeLimit."
            "test_widening_the_limit_admits_what_it_dropped_with_first_seen_intact"]},
        "No drop may be unlogged.": {"tests": [
            "test_filters.TestTheAgeRule.test_an_age_drop_names_both_dates",
            "test_filters.TestChainOrder.test_each_drop_names_exactly_one_rule"]},
    },
    "0053": {
        "The walk must not stop on a pinned posting.": {"tests": [
            "test_himalayas.TestStopRule.test_a_pinned_old_posting_does_not_stop_the_walk"]},
        "A posting browse already stored must not be new to search.": {"tests": [
            "test_himalayas.TestRunIntegration.test_a_posting_browse_stored_is_not_new_to_search"]},
        "The age limit must stop a walk, and must not stop it one posting early.": {"tests": [
            "test_himalayas.TestRunIntegration.test_with_no_mark_the_walk_stops_at_the_age_limit",
            "test_himalayas.TestRunIntegration.test_a_posting_exactly_at_the_age_limit_does_not_end_the_walk"]},
        "The snapshot assumption must be measured as a series, not once.": {
            "live": "a property of the live search endpoint across days; read from production "
                    "run logs, and found false on 2026-09-30"},
        "The agreement check must be seen disagreeing.": {"tests": [
            "test_himalayas.TestRunIntegration.test_the_agreement_check_is_seen_disagreeing"]},
        "Pages per morning must be reported for a week": {
            "live": "a count over a week of production mornings; each walk's pages are in its "
                    "run log"},
    },
    "0054": {
        "The pinned settings must be seen failing.": {"tests": [
            "test_workflow.TestWorkflow.test_no_waiting_run_is_ever_cancelled"]},
        "The run count against elapsed time must be readable in one command": {"tests": [
            "test_run_log_report.TestDistribution.test_the_span_is_measured_from_the_runs_not_the_files",
            "test_run_log_report.TestAgainstTheRealWriter.test_a_log_written_by_a_run_is_read_back"]},
    },
    "0055": {
        "A dry run must change nothing": {"tests": [
            "test_clearing.TestTheDryRun.test_a_dry_run_changes_nothing",
            "test_clearing.TestTheConfirmIsBoundToItsDryRun."
            "test_the_dry_runs_list_sits_outside_every_outcome_directory"]},
        "The confirmation must be required.": {"tests": [
            "test_clearing.TestTheConfirmation.test_a_confirmed_run_needs_a_recent_dry_run_of_the_same_request"]},
        "A removed row must not come back.": {"tests": [
            "test_clearing.TestRowsLeave.test_a_removed_row_does_not_come_back"]},
        "A rule-dropped row must still come back": {"tests": [
            "test_projection.TestTheSkip.test_the_removal_store_is_read_by_reason_both_ways",
            "test_projection.TestTheSkip.test_the_clock_and_the_tool_keep_a_row_out"]},
        "`accepted` must be seen surviving the tool.": {"tests": [
            "test_clearing.TestRowsLeave.test_the_tool_never_deletes_from_accepted"]},
        "The clock must be seen firing and not firing.": {"tests": [
            "test_sweep.TestTheClock.test_a_row_29_days_unreviewed_stays",
            "test_sweep.TestTheClock.test_at_31_days_it_is_stored_then_removed_on_a_later_run"]},
        "Every removal must be named in the run log": {"tests": [
            "test_clearing.TestRowsLeave.test_a_removed_row_does_not_come_back",
            "test_sweep.TestTheClock.test_an_aggregator_rows_identity_is_masked_in_the_log"]},
    },
    "0056": {
        "The week's measurement is the first check, and it is the one that decides the build.": {
            "live": "group counts over a clean week of production mornings, due 2026-10-05"},
        "When the delta is built, these must hold, each with a mutation that breaks it.": {
            "unbuilt": "the delta is built only if the week's measurement says so"},
        "The trigger arithmetic must be checkable from the run log alone": {"tests": [
            "test_projection.TestStages.test_each_stage_is_counted",
            "test_run.TestMain.test_a_committing_run_projects_and_logs_what_it_sent"]},
    },
    "0057": {
        "ADR-0041's case set must all be kept": {"tests": [
            "test_filters.TestTheLocationRule.test_karachi_sindh_is_not_dropped",
            "test_filters.TestTheLocationRule.test_karachi_punjab_pakistan_is_not_dropped",
            "test_filters.TestTheLocationRule.test_a_worldwide_remote_posting_is_not_dropped",
            "test_filters.TestTheLocationRule.test_an_absent_location_is_not_dropped"]},
        "A posting naming one open place among closed ones must be kept.": {"tests": [
            "test_filters.TestTheLocationRule.test_one_eligible_place_in_a_list_keeps_it",
            "test_filters.TestTheLocationRule.test_pakistan_anywhere_in_the_list_keeps_it"]},
        "The structured place must never keep a posting the text drops": {"tests": [
            "test_filters.TestTheSourcesOwnPlace."
            "test_a_posting_the_text_drops_is_never_kept_by_the_sources_place",
            "test_filters.TestTheSourcesOwnPlace."
            "test_a_city_the_rule_cannot_place_is_closed_by_the_sources_country"]},
        '"No visa sponsorship" must never drop a posting, and a working-hours time zone must '
        'never drop one.': {"tests": [
            "test_description.TestRequirements.test_no_visa_sponsorship_is_never_a_requirement",
            "test_filters.TestTheLocationRule.test_places_he_can_take_are_kept"]},
        "ADR-0041's corpus check stands as a regression check": {
            "live": "its 91 saved Himalayas postings are aggregator content, which ADR-0020 keeps "
                    "out of this repository, so it runs by hand against the private copy; exact "
                    "on 2026-09-30"},
        "Every drop must name its field and quote the home country from configuration": {"tests": [
            "test_filters.TestTheLocationRule.test_a_drop_names_the_field_and_the_home_country_from_configuration",
            "test_preference_audit.TestTheShippedTree.test_no_module_hard_codes_a_preference",
            "test_preference_audit.TestTheAuditCanFail.test_a_country_in_code_is_a_violation"]},
    },
    "0058": {
        "No derived value may be anything but a number, a configured place name or a flag.": {
            "tests": ["test_description.TestTheRowKeepsNoWords.test_greenhouse_reads_its_content",
                      "test_description.TestTheRowKeepsNoWords.test_lever_reads_its_sections",
                      "test_description.TestTheRowKeepsNoWords.test_himalayas_reads_its_description",
                      "test_description.TestTheRowKeepsNoWords."
                      "test_a_requirement_naming_no_known_place_is_left_out",
                      "test_storage.TestDataBranch.test_the_public_branch_refuses_description_text"]},
        "The experience rule's edges": {"tests": [
            "test_description.TestYears.test_a_range_counts_by_its_low_end",
            "test_description.TestYears.test_a_figure_glued_to_a_word_is_read",
            "test_description.TestYears.test_a_line_opened_to_fresh_graduates_is_not_a_minimum",
            "test_filters.TestTheExperienceRule.test_the_limit_itself_is_kept",
            "test_filters.TestTheExperienceRule.test_a_figure_over_the_limit_drops_and_says_so",
            "test_filters.TestTheExperienceRule.test_any_figure_over_drops_not_only_the_first"]},
        '"No visa sponsorship" must never set a required place.': {"tests": [
            "test_description.TestRequirements.test_no_visa_sponsorship_is_never_a_requirement"]},
        "A posting with no description must be kept.": {"tests": [
            "test_description.TestLines.test_nothing_to_read",
            "test_filters.TestTheExperienceRule.test_a_description_stating_no_figure_keeps"]},
    },
}
