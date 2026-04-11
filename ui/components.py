"""Reusable UI components for QuendAward application."""

import concurrent.futures

import streamlit as st
from i18n import AVAILABLE_LANGUAGES, get_all_texts
import database as db


# Award images rarely change and can be several hundred KB each. Cache them
# aggressively so we do not pull BLOBs out of SQLite on every 5 second refresh.
@st.cache_data(ttl=300, show_spinner=False)
def _cached_award_image(award_id):
    return db.get_award_image(award_id)


def _show_block_modal(t, callsign, band, mode, award_id):
    """
    Show modal dialog to confirm blocking a band/mode combination.

    Args:
        t: Translations dictionary
        callsign: Operator's callsign
        band: Band to block
        mode: Mode to block
        award_id: Current award ID
    """
    @st.dialog(t.get('modal_block_title', 'Block Band/Mode'))
    def _block_dialog():
        st.write(f"### {t.get('confirm_block', 'Do you want to block')} {band}/{mode}?")
        st.write("")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ {t.get('confirm', 'Confirm')}", key="modal_confirm_block", type="primary", use_container_width=True):
                success, message = db.block_band_mode(callsign, band, mode, award_id)
                if success:
                    st.success(message)
                    st.session_state._click_version = st.session_state.get('_click_version', 0) + 1
                    st.rerun()
                else:
                    st.error(message)
        with col2:
            if st.button(f"❌ {t.get('cancel', 'Cancel')}", key="modal_cancel_block", use_container_width=True):
                st.session_state._click_version = st.session_state.get('_click_version', 0) + 1
                st.rerun()

    _block_dialog()


def _show_unblock_modal(t, callsign, band, mode, award_id):
    """
    Show modal dialog to confirm unblocking a band/mode combination.

    Args:
        t: Translations dictionary
        callsign: Operator's callsign
        band: Band to unblock
        mode: Mode to unblock
        award_id: Current award ID
    """
    @st.dialog(t.get('modal_unblock_title', 'Unblock Band/Mode'))
    def _unblock_dialog():
        st.write(f"### {t.get('confirm_unblock', 'Do you want to unblock')} {band}/{mode}?")
        st.write("")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ {t.get('confirm', 'Confirm')}", key="modal_confirm_unblock", type="primary", use_container_width=True):
                success, message = db.unblock_band_mode(callsign, band, mode, award_id)
                if success:
                    st.success(message)
                    st.session_state._click_version = st.session_state.get('_click_version', 0) + 1
                    st.rerun()
                else:
                    st.error(message)
        with col2:
            if st.button(f"❌ {t.get('cancel', 'Cancel')}", key="modal_cancel_unblock", use_container_width=True):
                st.session_state._click_version = st.session_state.get('_click_version', 0) + 1
                st.rerun()

    _unblock_dialog()


def render_language_selector(t, key_suffix=""):
    """
    Render a language selector dropdown.

    Args:
        t: Translations dictionary for current language
        key_suffix: Optional suffix for unique key generation

    Returns:
        None (updates session state and triggers rerun if language changes)
    """
    lang = st.selectbox(
        t['language'],
        options=list(AVAILABLE_LANGUAGES.keys()),
        format_func=lambda x: AVAILABLE_LANGUAGES[x],
        index=list(AVAILABLE_LANGUAGES.keys()).index(st.session_state.language),
        key=f"lang_selector{key_suffix}",
        label_visibility="collapsed" if key_suffix == "_panel" else "visible"
    )
    if lang != st.session_state.language:
        st.session_state.language = lang
        st.rerun()


def render_award_selector(active_awards, t):
    """
    Render special callsign selector dropdown and information expander.

    Args:
        active_awards: List of active award dictionaries
        t: Translations dictionary for current language

    Returns:
        None (updates session state)
    """
    if not st.session_state.current_award_id and active_awards:
        st.session_state.current_award_id = active_awards[0]['id']

    st.write("---")
    selected_award = st.selectbox(
        f"🏆 {t['select_special_callsign']}",
        options=[award['id'] for award in active_awards],
        format_func=lambda x: next((a['name'] for a in active_awards if a['id'] == x), ''),
        index=[award['id'] for award in active_awards].index(st.session_state.current_award_id)
              if st.session_state.current_award_id in [award['id'] for award in active_awards] else 0,
        key="award_selector"
    )

    if selected_award != st.session_state.current_award_id:
        st.session_state.current_award_id = selected_award
        st.rerun()

    # Show special callsign details if available
    current_award = next((a for a in active_awards if a['id'] == st.session_state.current_award_id), None)
    if current_award:
        # Check if there's an image, description, or QRZ link to show
        image_result = _cached_award_image(current_award['id'])
        has_content = current_award.get('description') or image_result or current_award.get('qrz_link')

        if has_content:
            with st.expander(f"ℹ️ {t['special_callsign_information']}", expanded=False):
                # Two-column layout: description left, image right
                if image_result:
                    col_left, col_right = st.columns([3, 2])
                    with col_left:
                        st.write(f"**{current_award['name']}**")
                        if current_award.get('description'):
                            st.write(current_award['description'])
                        if current_award.get('start_date'):
                            st.write(f"**{t['start_label']}:** {current_award['start_date']}")
                        if current_award.get('end_date'):
                            st.write(f"**{t['end_label']}:** {current_award['end_date']}")
                        if current_award.get('qrz_link'):
                            st.markdown(f"🔗 [{t['view_on_qrz']}]({current_award['qrz_link']})")
                    with col_right:
                        image_data, image_type = image_result
                        st.image(image_data, use_container_width=True)
                else:
                    # No image, single column layout
                    st.write(f"**{current_award['name']}**")
                    if current_award.get('description'):
                        st.write(current_award['description'])
                    if current_award.get('start_date'):
                        st.write(f"**{t['start_label']}:** {current_award['start_date']}")
                    if current_award.get('end_date'):
                        st.write(f"**{t['end_label']}:** {current_award['end_date']}")
                    if current_award.get('qrz_link'):
                        st.markdown(f"🔗 [{t['view_on_qrz']}]({current_award['qrz_link']})")


def render_block_unblock_section(t, callsign, award_id):
    """
    Render the block/unblock band/mode section for operators.

    Args:
        t: Translations dictionary
        callsign: Operator's callsign
        award_id: Current award ID

    Returns:
        None
    """
    from config import BANDS, MODES

    if not award_id:
        st.warning(f"⚠️ {t['error_no_special_callsign_selected']}")
        return

    st.info(t['block_info'])

    col1, col2 = st.columns(2)
    with col1:
        band_to_block = st.selectbox(t['select_band'], BANDS, key="block_band")
    with col2:
        mode_to_block = st.selectbox(t['select_mode'], MODES, key="block_mode")

    if st.button(t['block'], type="primary"):
        success, message = db.block_band_mode(callsign, band_to_block, mode_to_block, award_id)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    # Show current blocks
    st.divider()
    st.subheader(t['your_current_blocks'])

    my_blocks = db.get_operator_blocks(callsign, award_id)

    if my_blocks:
        for block in my_blocks:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{block['band']}**")
            with col2:
                st.write(f"**{block['mode']}**")
            with col3:
                if st.button(t['unblock'], key=f"unblock_{block['id']}"):
                    success, message = db.unblock_band_mode(callsign, block['band'], block['mode'], award_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info(t['no_active_blocks'])


def _render_dx_cluster_spot_section(t, award_id, callsign):
    """
    Render the DX Cluster spotting section below the heatmap.

    Operators can send spots only when they have an active block.
    Band/mode are autofilled from the block; frequency and comment are manual.
    Cluster connection settings come from environment variables.

    Args:
        t: Translations dictionary
        award_id: Current award ID
        callsign: Current user's callsign
    """
    from config import (
        DX_CLUSTER_HOST, DX_CLUSTER_PORT, DX_CLUSTER_CALLSIGN,
        DX_CLUSTER_PASSWORD, BAND_FREQUENCIES,
    )

    if not callsign or not award_id:
        return

    # Get operator's active block for this award
    my_blocks = db.get_operator_blocks(callsign, award_id)
    active_block = my_blocks[0] if my_blocks else None

    st.divider()
    with st.expander(f"📡 {t.get('dx_cluster_spot', 'DX Cluster Spot')}", expanded=False):
        st.caption(t.get('dx_cluster_spot_info', 'Send a spot to a DX Cluster node to announce activity.'))

        # Gate: require an active block
        if not active_block:
            st.warning(t.get('dx_no_block_warning', 'You must block a band/mode before sending a spot.'))
        else:
            blocked_band = active_block['band']
            blocked_mode = active_block['mode']

            # Show autofilled band/mode (read-only)
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.text_input(
                    t.get('band_label', 'Band'),
                    value=blocked_band,
                    disabled=True,
                    key="dx_block_band",
                )
            with info_col2:
                st.text_input(
                    t.get('mode_label', 'Mode'),
                    value=blocked_mode,
                    disabled=True,
                    key="dx_block_mode",
                )

            # Spotted callsign (manual for testing; future: auto from award)
            spotted_callsign = st.text_input(
                t.get('dx_spotted_callsign', 'Spotted Callsign'),
                value=st.session_state.get('dx_spotted_cs', ''),
                help=t.get('dx_spotted_callsign_help', 'The callsign to spot (e.g. the special callsign)'),
                key="dx_input_spotted_cs",
            ).upper().strip()

            # Frequency (manual input, default from band/mode mapping)
            default_freq = BAND_FREQUENCIES.get(blocked_band, {}).get(blocked_mode, 14000.0)
            frequency = st.number_input(
                t.get('dx_frequency', 'Frequency (kHz)'),
                value=default_freq,
                min_value=0.1,
                max_value=999999.9,
                step=0.1,
                format="%.1f",
                key="dx_input_freq",
            )

            # Comment
            comment = st.text_input(
                t.get('dx_comment', 'Comment'),
                value=f"QRV {blocked_mode}",
                max_chars=30,
                help=t.get('dx_comment_help', 'Max 30 characters'),
                key="dx_input_comment",
            )

            # Send button
            if st.button(f"📡 {t.get('dx_send_spot', 'Send Spot')}", type="primary", key="dx_send_btn"):
                if not DX_CLUSTER_HOST or not DX_CLUSTER_CALLSIGN:
                    st.error(t.get('dx_cluster_not_configured', 'DX Cluster not configured. Set DX_CLUSTER_HOST and DX_CLUSTER_CALLSIGN environment variables.'))
                elif not spotted_callsign:
                    st.error(t.get('dx_fill_required', 'Please fill in the spotted callsign.'))
                else:
                    from features.dx_cluster import send_spot_async, log_spot
                    # Kick off the telnet send on a worker thread so the
                    # Streamlit script isn't blocked for up to 15 seconds.
                    future = send_spot_async(
                        host=DX_CLUSTER_HOST,
                        port=DX_CLUSTER_PORT,
                        login_callsign=DX_CLUSTER_CALLSIGN,
                        spotted_callsign=spotted_callsign,
                        frequency=frequency,
                        comment=comment,
                        password=DX_CLUSTER_PASSWORD,
                    )
                    with st.spinner(t.get('dx_sending_spot', 'Connecting to DX Cluster...')):
                        try:
                            success, message = future.result(timeout=20)
                        except concurrent.futures.TimeoutError:
                            success, message = False, "Spot sending timed out"

                    # Log the spot attempt
                    log_spot(
                        award_id=award_id,
                        operator_callsign=callsign,
                        spotted_callsign=spotted_callsign,
                        band=blocked_band,
                        mode=blocked_mode,
                        frequency=frequency,
                        cluster_host=f"{DX_CLUSTER_HOST}:{DX_CLUSTER_PORT}",
                        success=success,
                        cluster_response=message,
                    )

                    if success:
                        st.success(f"{t.get('dx_spot_success', 'Spot sent successfully!')} {message}")
                    else:
                        st.error(f"{t.get('dx_spot_error', 'Error sending spot')}: {message}")

        # Recent spots log (always visible)
        recent_spots = db.get_recent_spots(award_id=award_id, limit=5)
        if recent_spots:
            st.caption(t.get('dx_recent_spots', 'Recent Spots'))
            for spot in recent_spots:
                status_icon = "✅" if spot['success'] else "❌"
                time_str = spot['spotted_at'][:16] if spot.get('spotted_at') else ""
                freq_str = f"{spot['frequency']:.1f}" if spot.get('frequency') else ""
                st.caption(
                    f"{status_icon} {time_str} | "
                    f"{spot.get('spotted_callsign', '')} | "
                    f"{freq_str} kHz | "
                    f"{spot.get('cluster_response', '')[:60]}"
                )


def render_activity_dashboard(t, award_id, callsign=None):
    """
    Render the activity dashboard with heatmap and statistics.
    Includes interactive click-to-block/unblock functionality.

    Args:
        t: Translations dictionary
        award_id: Current award ID
        callsign: Current user's callsign (optional, for click handling)

    Returns:
        None
    """
    from ui.charts import create_availability_heatmap, create_blocks_by_band_chart
    from streamlit_plotly_events import plotly_events
    from config import BANDS, MODES

    if not award_id:
        st.warning(f"⚠️ {t['error_no_special_callsign_selected']}")
        return

    all_blocks = db.get_all_blocks(award_id)

    # Skip the Plotly rebuild if nothing has actually changed since the last
    # fragment tick. Rebuilding the heatmap allocates ~90 annotation objects
    # for a 15x6 grid, which is wasted work every 5 seconds when idle.
    blocks_fingerprint = (
        award_id,
        st.session_state.language,
        tuple(
            (b['operator_callsign'], b['operator_name'], b['band'], b['mode'], b['blocked_at'])
            for b in all_blocks
        ),
    )
    prev_fingerprint = st.session_state.get('_blocks_fingerprint')
    cached_fig = st.session_state.get('_cached_heatmap_fig')
    if blocks_fingerprint != prev_fingerprint or cached_fig is None:
        fig = create_availability_heatmap(all_blocks, t)
        st.session_state._blocks_fingerprint = blocks_fingerprint
        st.session_state._cached_heatmap_fig = fig
    else:
        fig = cached_fig

    # Disable modebar in figure config
    fig.update_layout(
        modebar={'orientation': 'v', 'bgcolor': 'rgba(0,0,0,0)', 'color': 'rgba(0,0,0,0)', 'activecolor': 'rgba(0,0,0,0)'}
    )

    # Use plotly_events to capture clicks
    # Versioned key forces component reset after each confirm/cancel,
    # eliminating stale click data that caused wrong modals to appear
    click_version = st.session_state.get('_click_version', 0)
    selected_points = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=550,
        override_width="100%",
        key=f"heatmap_events_{click_version}"
    )

    # Handle click events
    if selected_points and callsign:
        point = selected_points[0]
        # Get the clicked band and mode from pointIndex
        # plotly_events returns pointIndex as [y, x] for heatmaps
        if 'pointIndex' in point:
            y_idx = point['pointIndex'][0]
            x_idx = point['pointIndex'][1]
        else:
            # Fallback to x, y if pointIndex not available
            y_idx = point.get('y', 0)
            x_idx = point.get('x', 0)

        clicked_band = BANDS[y_idx]
        clicked_mode = MODES[x_idx]

        # Check if this combination is blocked
        block_info = next((b for b in all_blocks if b['band'] == clicked_band and b['mode'] == clicked_mode), None)

        if block_info:
            # Cell is blocked
            if block_info['operator_callsign'] == callsign:
                # User's own block - show unblock modal
                _show_unblock_modal(t, callsign, clicked_band, clicked_mode, award_id)
            else:
                # Someone else's block
                st.warning(f"⚠️ {clicked_band}/{clicked_mode} {t.get('already_blocked_by', 'is already blocked by')} {block_info['operator_name']} ({block_info['operator_callsign']})")
        else:
            # Cell is free - show block modal
            _show_block_modal(t, callsign, clicked_band, clicked_mode, award_id)

    # DX Cluster spotting section
    _render_dx_cluster_spot_section(t, award_id, callsign)

    # Show summary statistics
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t['total_blocks_label'], len(all_blocks))
    with col2:
        unique_operators = set(block['operator_callsign'] for block in all_blocks)
        st.metric(t['active_operators_label'], len(unique_operators))
    with col3:
        unique_bands = set(block['band'] for block in all_blocks)
        st.metric(t['bands_in_use_label'], len(unique_bands))

    # Blocks by band chart
    if all_blocks:
        st.subheader(t['blocks_by_band_label'])
        fig_bar = create_blocks_by_band_chart(all_blocks, t)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})


def render_announcements_operator_tab(t, operator_callsign):
    """
    Render the announcements tab for operators.
    Marks announcements as read when tab is viewed.

    Args:
        t: Translations dictionary
        operator_callsign: Current operator's callsign
    """
    st.subheader(f"📢 {t['announcements']}")

    # Get announcements with read status
    announcements = db.get_announcements_with_read_status(operator_callsign)

    if not announcements:
        st.info(t['no_announcements_available'])
        return

    # Display announcements - user can click to mark individual ones as read
    for ann in announcements:
        is_read = ann.get('is_read')
        read_indicator = "" if is_read else "🔵 "

        with st.expander(f"{read_indicator}{ann['title']}", expanded=not is_read):
            st.write(ann['content'])
            st.caption(f"{t['posted_on']}: {ann['created_at']} | {t['by']}: {ann['created_by']}")

            # Only show "Mark as read" button for unread announcements
            if not is_read:
                if st.button(t.get('mark_as_read', 'Mark as read'), key=f"mark_read_{ann['id']}"):
                    db.mark_announcement_read(ann['id'], operator_callsign)
                    st.rerun()


# ---------------------------------------------------------------------------
# QSO log
# ---------------------------------------------------------------------------

_QSO_PAGE_SIZE = 25


def render_qso_log_tab(t, award_id, operator_callsign, is_admin=False):
    """Render the QSO log tab: upload, stats, paginated view, export.

    Designed to stay responsive on mobile:
      - single spinner while the background ingest runs
      - paginated display (never dumps the whole log into st.dataframe)
      - summary-first, details on demand
    """
    if not award_id:
        st.warning(f"⚠️ {t['error_no_special_callsign_selected']}")
        return

    st.subheader(f"📋 {t.get('qso_log_title', 'QSO Log')}")

    # Current award for display name + export filename
    award = db.get_award_by_id(award_id)
    award_name = award['name'] if award else "qso_log"

    # --- Scope toggle (admin can see everyone's QSOs, operator is always own)
    scope_is_own = True
    if is_admin:
        scope_choice = st.radio(
            t.get('qso_scope_label', 'Scope'),
            options=['own', 'all'],
            format_func=lambda s: (
                t.get('qso_scope_own', 'My QSOs') if s == 'own'
                else t.get('qso_scope_all', 'All operators')
            ),
            horizontal=True,
            key=f"qso_scope_{award_id}",
        )
        scope_is_own = (scope_choice == 'own')
    scoped_operator = operator_callsign if scope_is_own else None

    # --- Upload section
    _render_qso_upload_section(t, award_id, operator_callsign, award_name)

    st.divider()

    # --- Stats
    stats = db.get_qso_stats(award_id, operator_callsign=scoped_operator)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t.get('qso_total', 'Total QSOs'), stats['total'])
    with col2:
        st.metric(t.get('qso_unique_calls', 'Unique Calls'), stats['unique_calls'])
    with col3:
        top_band = next(iter(stats['by_band']), None) if stats['by_band'] else None
        st.metric(
            t.get('qso_top_band', 'Top Band'),
            top_band if top_band else "—",
        )

    if stats['by_band'] or stats['by_mode']:
        bcol, mcol = st.columns(2)
        with bcol:
            st.caption(t.get('qso_by_band', 'By Band'))
            for band, cnt in stats['by_band'].items():
                st.write(f"**{band}** — {cnt}")
        with mcol:
            st.caption(t.get('qso_by_mode', 'By Mode'))
            for mode, cnt in stats['by_mode'].items():
                st.write(f"**{mode}** — {cnt}")

    st.divider()

    # --- Filters + paginated log view
    _render_qso_log_view(
        t, award_id, scoped_operator, award_name, stats['total']
    )

    # --- Upload history (own batches, undo)
    st.divider()
    _render_qso_batches_section(t, award_id, operator_callsign, is_admin)


def _render_qso_upload_section(t, award_id, operator_callsign, award_name):
    """Upload an ADIF file and ingest it in the background."""
    from features.qso_log import MAX_ADIF_UPLOAD_BYTES

    st.markdown(f"**📤 {t.get('qso_upload_heading', 'Upload ADIF log')}**")
    st.caption(
        t.get(
            'qso_upload_help',
            'Upload an ADIF file exported from your logger (N1MM, Log4OM, etc.). '
            'Duplicates are skipped automatically. Max 10 MB per upload.'
        )
    )

    uploaded = st.file_uploader(
        t.get('qso_upload_label', 'ADIF file'),
        type=['adi', 'adif', 'txt'],
        key=f"qso_adif_upload_{award_id}",
        accept_multiple_files=False,
    )

    if uploaded is None:
        return

    if uploaded.size > MAX_ADIF_UPLOAD_BYTES:
        st.error(
            t.get(
                'qso_upload_too_large',
                f'File too large (max {MAX_ADIF_UPLOAD_BYTES // (1024*1024)} MB).'
            )
        )
        return

    if st.button(
        f"📥 {t.get('qso_upload_button', 'Ingest log')}",
        type="primary",
        key=f"qso_ingest_btn_{award_id}",
    ):
        from features.qso_log import ingest_adif_async

        future = ingest_adif_async(
            award_id=award_id,
            operator_callsign=operator_callsign,
            file_bytes=uploaded.getvalue(),
            filename=uploaded.name,
        )
        size_kb = max(1, uploaded.size // 1024)
        processing_template = t.get('qso_upload_processing', 'Processing {size_kb} KB…')
        try:
            spinner_text = processing_template.format(size_kb=size_kb)
        except (KeyError, IndexError):
            spinner_text = processing_template
        with st.spinner(spinner_text):
            try:
                result = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                st.warning(
                    t.get(
                        'qso_upload_timeout',
                        'Still processing in the background — refresh in a moment.'
                    )
                )
                return
            except ValueError as e:
                st.error(str(e))
                return
            except Exception:
                logger_ = _get_logger()
                logger_.exception("QSO ingest failed")
                st.error(t.get('qso_upload_failed', 'Ingest failed.'))
                return

        st.success(
            t.get(
                'qso_upload_result',
                '✅ {inserted} new QSOs, {duplicates} duplicates, {errors} errors'
            ).format(
                inserted=result['inserted'],
                duplicates=result['duplicates'],
                errors=result['errors'],
            )
        )
        st.rerun()


def _render_qso_log_view(
    t, award_id, scoped_operator, award_name, total_count
):
    """Filtered + paginated log view with ADIF export button."""
    from config import BANDS, MODES

    if total_count == 0:
        st.info(t.get('qso_no_qsos', 'No QSOs uploaded yet.'))
        return

    st.markdown(f"**📒 {t.get('qso_recent_heading', 'Log')}**")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        band_filter = st.selectbox(
            t.get('qso_filter_band', 'Band'),
            options=['*'] + BANDS,
            format_func=lambda s: t.get('qso_all', 'All') if s == '*' else s,
            key=f"qso_flt_band_{award_id}",
        )
    with filter_col2:
        mode_filter = st.selectbox(
            t.get('qso_filter_mode', 'Mode'),
            options=['*'] + MODES,
            format_func=lambda s: t.get('qso_all', 'All') if s == '*' else s,
            key=f"qso_flt_mode_{award_id}",
        )
    with filter_col3:
        # Pagination control: reset to 0 when filters change
        filter_key = f"qso_page_{award_id}_{band_filter}_{mode_filter}"
        page = st.number_input(
            t.get('qso_page', 'Page'),
            min_value=1,
            value=1,
            step=1,
            key=filter_key,
        )

    band_sel = None if band_filter == '*' else band_filter
    mode_sel = None if mode_filter == '*' else mode_filter

    filtered_total = db.count_qsos(
        award_id=award_id,
        operator_callsign=scoped_operator,
        band=band_sel,
        mode=mode_sel,
    )
    total_pages = max(1, (filtered_total + _QSO_PAGE_SIZE - 1) // _QSO_PAGE_SIZE)
    page = min(int(page), total_pages)
    offset = (page - 1) * _QSO_PAGE_SIZE

    qsos = db.get_qsos_page(
        award_id=award_id,
        operator_callsign=scoped_operator,
        limit=_QSO_PAGE_SIZE,
        offset=offset,
        band=band_sel,
        mode=mode_sel,
    )

    st.caption(
        t.get(
            'qso_page_info',
            'Showing {shown} of {total} QSOs — page {page} of {pages}'
        ).format(
            shown=len(qsos),
            total=filtered_total,
            page=page,
            pages=total_pages,
        )
    )

    if qsos:
        display_rows = []
        for q in qsos:
            row = {
                t.get('qso_col_date', 'Date'): q.get('qso_date', ''),
                t.get('qso_col_time', 'UTC'): q.get('time_on', ''),
                t.get('qso_col_call', 'Call'): q.get('call', ''),
                t.get('qso_col_band', 'Band'): q.get('band', ''),
                t.get('qso_col_mode', 'Mode'): q.get('mode', ''),
                t.get('qso_col_rst_s', 'S'): q.get('rst_sent') or '',
                t.get('qso_col_rst_r', 'R'): q.get('rst_rcvd') or '',
            }
            if scoped_operator is None:
                row[t.get('qso_col_op', 'Op')] = q.get('operator_callsign', '')
            display_rows.append(row)
        st.dataframe(
            display_rows,
            use_container_width=True,
            hide_index=True,
        )

        # ADIF export: pull everything matching the current filter, not just
        # the visible page. Capped at 50k to avoid runaway downloads.
        export_qsos = db.get_qsos_page(
            award_id=award_id,
            operator_callsign=scoped_operator,
            limit=50000,
            offset=0,
            band=band_sel,
            mode=mode_sel,
        )
        adif_text = db.export_qsos_to_adif(
            export_qsos,
            station_callsign=award_name,
        )
        st.download_button(
            label=f"📥 {t.get('qso_export_adif', 'Export ADIF')}",
            data=adif_text.encode('utf-8'),
            file_name=f"{award_name}_qsos.adi",
            mime="text/plain",
            key=f"qso_export_btn_{award_id}_{band_filter}_{mode_filter}",
        )


def _render_qso_batches_section(t, award_id, operator_callsign, is_admin):
    """Upload history with per-batch undo."""
    st.markdown(f"**🗂️ {t.get('qso_upload_history', 'Upload history')}**")

    # Non-admin operators only see their own batches. Admins see everything.
    scope_op = None if is_admin else operator_callsign
    batches = db.get_upload_batches(
        award_id=award_id,
        operator_callsign=scope_op,
        limit=10,
    )
    if not batches:
        st.caption(t.get('qso_no_batches', 'No uploads yet.'))
        return

    for batch in batches:
        ts = (batch.get('uploaded_at') or '')[:16]
        fname = batch.get('filename') or 'upload.adi'
        inserted = batch.get('inserted', 0)
        duplicates = batch.get('duplicates', 0)
        errors = batch.get('errors', 0)
        owner = batch.get('operator_callsign', '')

        label = f"{ts} — {fname} — {owner}"
        with st.expander(label, expanded=False):
            st.write(
                f"**{t.get('qso_batch_inserted', 'Inserted')}:** {inserted} · "
                f"**{t.get('qso_batch_duplicates', 'Duplicates')}:** {duplicates} · "
                f"**{t.get('qso_batch_errors', 'Errors')}:** {errors}"
            )
            # Only owner or admin can undo a batch
            can_delete = is_admin or (owner == operator_callsign.upper())
            if can_delete:
                confirm_key = f"qso_undo_batch_confirm_{batch['id']}"
                if st.session_state.get(confirm_key):
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        if st.button(
                            t.get('confirm_delete', 'Yes, delete'),
                            type="primary",
                            key=f"qso_undo_yes_{batch['id']}",
                        ):
                            del st.session_state[confirm_key]
                            scope = None if is_admin else operator_callsign
                            ok, removed = db.delete_batch(batch['id'], scope)
                            if ok:
                                st.success(
                                    t.get(
                                        'qso_batch_undone',
                                        'Removed {n} QSOs from this batch'
                                    ).format(n=removed)
                                )
                                st.rerun()
                            else:
                                st.error(
                                    t.get(
                                        'qso_batch_undo_failed',
                                        'Could not remove this batch'
                                    )
                                )
                    with no_col:
                        if st.button(
                            t.get('cancel', 'Cancel'),
                            key=f"qso_undo_no_{batch['id']}",
                        ):
                            del st.session_state[confirm_key]
                            st.rerun()
                else:
                    if st.button(
                        f"🗑️ {t.get('qso_batch_undo', 'Undo this upload')}",
                        key=f"qso_undo_btn_{batch['id']}",
                    ):
                        st.session_state[confirm_key] = True
                        st.rerun()


def _get_logger():
    """Small helper so we don't need to import logging at module top."""
    import logging
    return logging.getLogger(__name__)
