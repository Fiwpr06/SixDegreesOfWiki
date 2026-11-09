"""Streamlit interface for Wikipedia path searches."""

import json
from collections import deque

import streamlit as st

from config import Settings
from core.bidirectional_ids import bidirectional_ids
from core.ids_search import standard_ids
from core.search_types import SearchLimits, SearchProgress, SearchResult
from core.visualizer import global_theme_css, graph_html, path_stepper_html
from core.wiki_api import WikiAPI, WikiAPIError
from database import Database
from database.history import list_searches, save_search
from utils.exporter import article_url, report_from_history, report_from_result, to_json
from utils.helpers import parse_article_reference


st.set_page_config(page_title="Six Degrees of Wiki", layout="wide")


@st.cache_resource
def get_database() -> Database:
    return Database()


@st.cache_data(ttl=3600, show_spinner=False)
def suggestions(prefix: str, lang: str) -> list[str]:
    return WikiAPI(get_database()).suggest_titles(prefix, lang)


def title_input(label: str, key: str, lang: str) -> str:
    typed = st.text_input(label, key=key, placeholder="Tên bài viết hoặc URL Wikipedia")
    if len(typed.strip()) < 2:
        return typed
    try:
        parsed_title, url_lang = parse_article_reference(typed)
    except ValueError:
        return typed
    if url_lang:
        st.caption(f"Đã nhận URL Wikipedia ({url_lang}): {parsed_title}")
        return typed
    try:
        options = suggestions(parsed_title, lang)
    except WikiAPIError:
        st.caption("Không tải được gợi ý; bạn vẫn có thể dùng tên đã nhập.")
        return typed
    if not options:
        return typed
    chosen = st.selectbox(f"Gợi ý cho {label.lower()}", ["Dùng tên đã nhập", *options], key=f"{key}_suggestion")
    return typed if chosen == "Dùng tên đã nhập" else chosen


def render_result(result: SearchResult, index: int, theme_key: str = "cosmic") -> None:
    st.subheader(result.algorithm)
    if result.status == "found":
        st.success("Đã tìm thấy đường đi ngắn nhất trong giới hạn tìm kiếm.")
    elif result.status == "not_found":
        st.info("Chưa tìm thấy đường đi trong độ sâu đã chọn.")
    elif result.status == "timeout":
        st.warning("Đã hết thời gian. Kết quả chưa xác định.")
    else:
        st.warning("Đã đạt giới hạn số nút. Kết quả chưa xác định.")

    columns = st.columns(5)
    columns[0].metric("Độ sâu", result.depth if result.found else "—")
    columns[1].metric("Bài trung gian", result.intermediate_count if result.found else "—")
    columns[2].metric("Thời gian", f"{result.elapsed_seconds:.2f}s")
    columns[3].metric("Nút đã thăm", result.visited_nodes)
    columns[4].metric("Cache hit", f"{result.cache_hit_rate:.1f}%")
    st.caption(f"Nút mở rộng: {result.expanded_nodes} · Cache hit/miss: {result.cache_hits}/{result.cache_misses}")

    if result.found:
        st.html(path_stepper_html(result, theme_key))
        st.iframe(graph_html(result, theme_key), height=580)

    st.download_button(
        "Tải báo cáo JSON", to_json(report_from_result(result)),
        file_name=f"sixdegrees_report_{index + 1}.json", mime="application/json",
        key=f"download_result_{index}",
    )


def main() -> None:
    settings = Settings.from_env()
    database = get_database()

    current_theme = st.session_state.get("app_theme_selection", "cosmic")
    st.html(global_theme_css(current_theme))

    st.title("Six Degrees of Wiki")
    st.caption("Tìm đường liên kết ngắn nhất giữa hai bài Wikipedia bằng Iterative Deepening Search")

    with st.sidebar:
        st.header("Thiết lập tìm kiếm")
        lang = st.selectbox("Ngôn ngữ", ["vi", "en"], format_func=lambda code: "Tiếng Việt" if code == "vi" else "English")
        algorithm = st.selectbox("Thuật toán", ["Bidirectional IDS", "Standard IDS", "So sánh cả hai"])
        unlimited = st.toggle("Không giới hạn độ sâu, thời gian và số nút", value=False)
        if unlimited:
            max_depth = timeout = max_nodes = None
            st.caption("Thuật toán sẽ tiếp tục tăng độ sâu cho đến khi tìm thấy đích hoặc bạn dừng phiên chạy.")
        else:
            max_depth = st.slider("Độ sâu tối đa", 0, 6, settings.default_max_depth)
            timeout = st.number_input("Giới hạn thời gian (giây)", min_value=1, max_value=3000,
                                      value=int(settings.default_timeout_seconds))
            max_nodes = st.number_input("Số nút thăm tối đa", min_value=10, max_value=100000,
                                        value=settings.default_max_visited_nodes, step=100)
        st.subheader("Giao diện & Phong cách")
        theme_names = {
            "cosmic": "Cosmic Deep Space (Tối vũ trụ)",
            "nier": "NieR: Automata (Sáng hoài niệm / YoRHa)",
            "cyberpunk": "Cyberpunk Slate (Tối công nghệ)",
            "paper": "Clean Paper (Sáng tối giản)",
        }
        theme_choice = st.selectbox(
            "Phong cách hiển thị",
            list(theme_names.keys()),
            format_func=lambda k: theme_names[k],
            index=0,
            key="app_theme_selection",
        )
        st.html(global_theme_css(theme_choice))
        st.info(f"CSDL: SQLite · {settings.sqlite_path.name}")

    search_tab, history_tab = st.tabs(["Tìm kiếm", "Lịch sử & báo cáo"])
    with search_tab:
        input_lang = lang
        for key in ("start_title", "target_title"):
            try:
                _, detected = parse_article_reference(st.session_state.get(key, ""))
                if detected:
                    input_lang = detected
                    break
            except ValueError:
                pass
        start = title_input("Bài viết bắt đầu", "start_title", input_lang)
        target = title_input("Bài viết đích", "target_title", input_lang)

        if st.button("Bắt đầu phân tích liên kết", type="primary", disabled=not start.strip() or not target.strip()):
            st.session_state["results"] = []
            progress = st.empty()
            progress.info("Đang xác thực bài viết...")
            with st.container(border=True):
                st.markdown("**Tiến trình tìm kiếm trực tiếp**")
                phase_box = st.empty()
                current_box = st.empty()
                metric_columns = st.columns(4)
                visited_box = metric_columns[0].empty()
                expanded_box = metric_columns[1].empty()
                cache_box = metric_columns[2].empty()
                elapsed_box = metric_columns[3].empty()
                st.caption("Mẫu 10 sự kiện gần nhất; giao diện không ghi từng nút để tránh làm chậm thuật toán.")
                recent_box = st.empty()
            recent_events: deque[str] = deque(maxlen=10)

            def show_trace(event: SearchProgress) -> None:
                maximum = "∞" if event.max_depth is None else str(event.max_depth)
                direction = {"forward": "xuôi", "backward": "ngược"}.get(event.side, event.side)
                phase_box.info(f"{event.algorithm} · mức sâu {event.iteration_depth}/{maximum} · "
                               f"{direction} · {event.phase}")
                current_box.write(f"Bài đang xử lý: {event.title} | Đường nhánh gần nhất: "
                                  + " → ".join(event.path_tail))
                visited_box.metric("Nút đã thăm", event.visited_nodes)
                expanded_box.metric("Nút mở rộng", event.expanded_nodes)
                cache_box.metric("Cache hit/miss", f"{event.cache_hits}/{event.cache_misses}")
                elapsed_box.metric("Thời gian", f"{event.elapsed_seconds:.1f}s")
                recent_events.append(f"{event.algorithm} | sâu {event.iteration_depth} | "
                                     f"{direction} | {event.title}")
                recent_box.code("\n".join(recent_events), language=None)

            try:
                start_title, start_lang = parse_article_reference(start)
                target_title, target_lang = parse_article_reference(target)
                url_languages = {code for code in (start_lang, target_lang) if code}
                if len(url_languages) > 1:
                    raise ValueError("Hai URL Wikipedia phải dùng cùng một ngôn ngữ.")
                search_lang = next(iter(url_languages), lang)
                if search_lang != lang:
                    st.info(f"Đã dùng ngôn ngữ {search_lang} theo URL Wikipedia đã nhập.")
                wiki = WikiAPI(database, settings)
                canonical_start = wiki.resolve_title(start_title, search_lang)
                canonical_target = wiki.resolve_title(target_title, search_lang)
                limits = (SearchLimits(None, None, None) if unlimited
                          else SearchLimits(max_depth, float(timeout), int(max_nodes)))
                runners = ([standard_ids, bidirectional_ids] if algorithm == "So sánh cả hai"
                           else [standard_ids] if algorithm == "Standard IDS" else [bidirectional_ids])
                results = []
                for runner in runners:
                    def update(depth: int, max_level: int | None) -> None:
                        if max_level is None:
                            progress.info(f"{runner.__name__}: đang thử độ sâu {depth} (không giới hạn)")
                        else:
                            progress.progress((depth + 1) / (max_level + 1),
                                              text=f"{runner.__name__}: đang thử độ sâu {depth}/{max_level}")
                    result = runner(wiki, canonical_start, canonical_target, search_lang,
                                    limits, update, show_trace)
                    save_search(database, result)
                    results.append(result)
                st.session_state["results"] = results
                progress.empty()
            except (ValueError, WikiAPIError) as exc:
                progress.empty()
                st.error(str(exc))

        results = st.session_state.get("results", [])
        if results:
            st.caption("Kết quả lần chạy gần nhất")
            if len(results) > 1:
                st.subheader("So sánh hiệu năng")
                st.dataframe([
                    {"Thuật toán": result.algorithm, "Trạng thái": result.status,
                     "Độ sâu": result.depth if result.found else None,
                     "Thời gian (s)": round(result.elapsed_seconds, 3),
                     "Nút thăm": result.visited_nodes,
                     "Nút mở rộng": result.expanded_nodes,
                     "Cache hit (%)": round(result.cache_hit_rate, 1)}
                    for result in results
                ], hide_index=True, width="stretch")
                st.caption("Thuật toán thứ hai có thể hưởng lợi từ cache do thuật toán thứ nhất vừa tạo.")
            for index, result in enumerate(results):
                render_result(result, index, theme_choice)
                if index < len(results) - 1:
                    st.divider()

    with history_tab:
        rows = list_searches(database)
        if not rows:
            st.info("Chưa có lịch sử tìm kiếm.")
        else:
            lang_col, algorithm_col, status_col = st.columns(3)
            with lang_col:
                filter_lang = st.selectbox("Lọc ngôn ngữ", ["Tất cả", "vi", "en"])
            with algorithm_col:
                filter_algorithm = st.selectbox("Lọc thuật toán", ["Tất cả", "Standard IDS", "Bidirectional IDS"])
            with status_col:
                filter_status = st.selectbox("Lọc trạng thái", ["Tất cả", "found", "not_found", "timeout", "node_limit"])
            visible = [row for row in rows
                       if (filter_lang == "Tất cả" or row.lang == filter_lang)
                       and (filter_algorithm == "Tất cả" or row.algorithm == filter_algorithm)
                       and (filter_status == "Tất cả" or row.status == filter_status)]
            st.dataframe([
                {"ID": row.id, "Thời gian (UTC)": row.created_at.isoformat(sep=" ", timespec="seconds"),
                 "Bắt đầu": row.start_title, "Đích": row.target_title, "Ngôn ngữ": row.lang,
                 "Thuật toán": row.algorithm, "Trạng thái": row.status,
                 "Độ sâu": row.depth if row.depth >= 0 else None,
                 "Thời gian (s)": round(row.execution_time, 3),
                 "Nút thăm": row.nodes_visited, "Cache hit (%)":
                 round(100 * row.cache_hits / (row.cache_hits + row.cache_misses), 1)
                 if row.cache_hits + row.cache_misses else 0.0}
                for row in visible
            ], hide_index=True, width="stretch")
            if visible:
                chosen_id = st.selectbox("Xem phiên tìm kiếm", [row.id for row in visible],
                                         format_func=lambda identifier: f"Phiên #{identifier}")
                chosen = next(row for row in visible if row.id == chosen_id)
                path = json.loads(chosen.path_json)
                if path:
                    st.write(" → ".join(path))
                st.download_button(
                    "Tải báo cáo của phiên này", to_json(report_from_history(chosen)),
                    file_name=f"sixdegrees_history_{chosen.id}.json", mime="application/json",
                )


if __name__ == "__main__":
    main()
