import os
import sys
import locale
import json
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton, QLabel,
    QSlider, QComboBox, QSplitter, QFrame, QSizePolicy, QFileDialog,
    QMessageBox, QStackedWidget, QDialog, QFormLayout, QDialogButtonBox,
    QMenu, QGridLayout, QGraphicsDropShadowEffect, QCheckBox
)
from PySide6.QtCore import Qt, QSize, QTimer, QObject, Signal, QThread, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QAction, QCursor, QKeySequence, QShortcut, QPainter, QPen

# Set locale for numeric formatting as required by libmpv
try:
    locale.setlocale(locale.LC_NUMERIC, 'C')
except Exception:
    pass

# Setup DLL search path for Windows to find libmpv DLLs
if sys.platform == 'win32':
    dll_dirs = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            dll_dirs.append(sys._MEIPASS)
        dll_dirs.append(os.path.dirname(sys.executable))
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dll_dirs.append(script_dir)
    
    # Remove duplicates preserving order
    seen = set()
    dll_dirs = [x for x in dll_dirs if x and x not in seen and not seen.add(x)]
    
    for d in dll_dirs:
        if os.path.exists(d):
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(d)
                except Exception:
                    pass
            os.environ['PATH'] = d + os.pathsep + os.environ['PATH']

# Import local modules
from m3u_parser import parse_m3u
import config_manager
import epg_manager

# FontAwesome 6 Solid is loaded dynamically inside K20IPTVPlayer.__init__ to prevent early Qt instantiation crash.

# Import mpv (with safe fallback check)
try:
    import mpv
    MPV_AVAILABLE = True
except OSError as e:
    print(f"Error loading libmpv DLL: {e}")
    MPV_AVAILABLE = False
except ImportError:
    MPV_AVAILABLE = False



TRANSLATIONS = {
    "vi": {
        "settings_title": "Cấu Hình IPTV Player",
        "settings_desc": "Tối ưu hóa bộ nhớ đệm, phần cứng và ngôn ngữ",
        "cache": "Bộ nhớ đệm (Cache):",
        "sleep_timer": "Hẹn giờ tắt (Sleep):",
        "hw_dec": "Giải mã phần cứng:",
        "hw_dec_checkbox": "Bật tăng tốc phần cứng (D3D11VA)",
        "language": "Ngôn ngữ (Language):",
        "cancel": "Hủy bỏ",
        "save": "Lưu cấu hình",
        "no_timer": "Không hẹn giờ",
        "minutes": "phút",
        "timer_set": "Đang hẹn giờ: {} phút",
        "timer_cancelled": "🕒 Đã hủy hẹn giờ tắt",
        "timer_set_msg": "🕒 Đã hẹn giờ tắt sau {} phút!",
        "timer_remaining_msg": "🕒 Tự động tắt sau {} giây",
        "timer_done": "🕒 Hết giờ! Đang tắt ứng dụng...",
        "hw_on": "HW: Bật",
        "hw_off": "HW: Tắt",
        "live_tv_title": "LIVE TV",
        "search_placeholder": "🔍 Tìm kiếm kênh...",
        "all_categories": "Tất cả các nhóm",
        "default_sort": "Mặc định",
        "az_sort": "Tên A-Z",
        "latency_sort": "Độ trễ thấp",
        "check_status": "Kiểm tra trạng thái & độ trễ các kênh",
        "all": "Tất cả",
        "live_tv_tooltip": "Live TV",
        "favorites_tooltip": "Yêu thích",
        "history_tooltip": "Lịch sử xem",
        "playlist_manager_tooltip": "Quản lý Playlist",
        "shortcuts_tooltip": "Hướng dẫn phím tắt (H)",
        "settings_tooltip": "Cài đặt",
        "hud_title": "⌨️ PHÍM TẮT ĐIỀU KHIỂN K20 PLAYER",
        "hud_close": "— Click bất kỳ đâu hoặc nhấn H để đóng bảng này —",
        "sh_space": "Phát / Tạm dừng video",
        "sh_f": "Bật / Tắt Toàn màn hình",
        "sh_m": "Tắt / Bật âm thanh nhanh",
        "sh_i": "Hiện / Ẩn thông tin luồng phát (Stats)",
        "sh_s": "Chụp ảnh màn hình",
        "sh_pip": "Chế độ cửa sổ thu nhỏ (PiP)",
        "sh_r": "Bật / Tắt ghi hình trực tiếp (Record)",
        "sh_f5": "Tải lại kênh / luồng phát",
        "sh_vol": "Tăng / Giảm 5% âm lượng",
        "sh_seek": "Tua lùi / Tua tiến 5 giây",
        "sh_h": "Đóng / Mở bảng phím tắt này",
        "sh_esc": "Thoát chế độ Toàn màn hình",
        "screenshot_saved": "📸 Đã lưu ảnh chụp màn hình",
        "copy_url_success": "📋 Đã sao chép URL luồng phát",
        
        # New translation keys
        "toggle_sidebar_tooltip": "Ẩn/Hiện danh sách kênh",
        "no_channel_playing": "Chưa phát kênh nào",
        "epg_schedule_btn": "📅 Lịch Chiếu",
        "epg_hide_btn": "📅 Ẩn Lịch",
        "toggle_epg_tooltip": "Ẩn/Hiện Lịch phát sóng",
        "seek_back_tooltip": "Lùi lại 5 giây (Left Arrow)",
        "seek_forward_tooltip": "Tiến tới 5 giây (Right Arrow)",
        "view_1_screen": "▣  1 Màn hình",
        "view_2_screens": "⬛  2 Màn hình",
        "view_4_screens": "⊞  4 Màn hình",
        "audio_tooltip": "Chọn luồng âm thanh",
        "subs_tooltip": "Chọn phụ đề",
        "epg_panel_title": "LỊCH PHÁT SÓNG",
        "favorites_title": "YÊU THÍCH ★",
        "recent_title": "GẦN ĐÂY 📜",
        "loading_playlist": "Đang tải danh sách phát... Vui lòng chờ ⏳",
        "loading_playlist_placeholder": "Đang tải danh sách...",
        "empty_playlist_error": "❌ Danh sách phát trống hoặc lỗi định dạng",
        "load_playlist_error": "❌ Lỗi tải danh sách: {}",
        "context_remove_fav": "❌ Xóa khỏi Yêu thích",
        "context_add_fav": "★ Thêm vào Yêu thích",
        "context_check_channel": "⚡ Kiểm tra kênh này",
        "context_copy_link": "📋 Sao chép Link Kênh",
        "no_audio_stream": "Không có luồng âm thanh",
        "turn_off_subs": "Tắt phụ đề",
        "subtitle_track": "Phụ đề {}",
        "player_stopped": "[Màn {}] - Đã dừng",
        "player_no_channel": "[Màn {}] - Chưa chọn kênh 📺",
        "epg_now_playing": "📺 Đang phát ({}-{}): {}",
        "epg_live_no_epg": "📺 Luồng Live TV (Không có lịch EPG)",
        "epg_no_details": "Không có lịch chiếu chi tiết",
        "reloading_stream": "🔄 Đang tải lại luồng...",
        "copied_link_msg": "📋 Đã sao chép link kênh vào Clipboard!",
        "libmpv_error": "❌ Không tải được thư viện libmpv (mpv-1.dll/mpv-2.dll).\n\nHãy chắc chắn bạn đã chạy tập tin download_mpv_dll.py thành công\nvà DLL đã được tải về nằm cùng thư mục với file main.py.",
        "single_view_name": "Góc Nhìn Đơn (1x1)",
        "multi_view_name": "Góc Nhìn Bốn (2x2)",
        "buffer_preset_1": "10 MB (Thấp - Mạng di động)",
        "buffer_preset_2": "50 MB (Mặc định - Bình thường)",
        "buffer_preset_3": "100 MB (Cao - HD/VOD)",
        "buffer_preset_4": "250 MB (Rất cao - 4K mượt)",
        "buffer_preset_5": "500 MB (Cực đại - Mạng yếu)",
        "status_online": "Kênh hoạt động tốt",
        "status_offline": "Kênh lỗi / offline",
        "status_untested": "Chưa kiểm tra trạng thái",
        "lost_connection": "⚠️ Mất kết nối! Đang thử lại ({}/{}) ...",
        "stats_loading": "Đang tải...",
        "stats_calculating": "Đang tính...",
        "stats_title": "⚡ THÔNG SỐ K20 PLAYER ⚡",
        "stats_recording": "🔴 ĐANG GHI",
        "stats_resolution": "Độ phân giải",
        "stats_framerate": "Tốc độ khung hình",
        "stats_video_codec": "Video Codec",
        "stats_bitrate": "Tốc độ bit (Bitrate)",
        "stats_net_speed": "Tốc độ mạng",
        "stats_dropped_frames": "Mất khung hình",
        "stats_decoder": "Trình giải mã",
        "stats_buffer_sec": "Bộ đệm (giây)",
        "screenshot_success": "📸 Đã lưu ảnh chụp màn hình!",
        "playlist_manager_title": "Quản Lý Playlist",
        "playlist_list_label": "Danh sách Playlist",
        "btn_add_file": "➕ Thêm File",
        "btn_add_url": "🌐 Thêm URL",
        "btn_add_xtream": "🔑 Thêm Xtream",
        "btn_edit": "✏️ Sửa",
        "btn_delete": "🗑️ Xóa",
        "pl_type_local": "Cục bộ",
        "pl_type_xtream": "Xtream",
        "pl_type_url": "URL",
        "select_m3u_file": "Chọn file playlist M3U",
        "add_url_title": "Thêm URL M3U",
        "placeholder_playlist_name": "Ví dụ: IPTV Vietnam",
        "label_playlist_name": "Tên Playlist:",
        "label_url_path": "Đường dẫn URL:",
        "add_xtream_title": "Thêm Xtream Codes API",
        "placeholder_xtream_name": "Ví dụ: Xtream VIP",
        "placeholder_username": "tên đăng nhập",
        "placeholder_password": "mật khẩu",
        "label_display_name": "Tên hiển thị:",
        "label_server_url": "Server URL (Host):",
        "label_username": "Tài khoản (User):",
        "label_password": "Mật khẩu (Pass):",
        "error_title": "Lỗi",
        "select_playlist_to_edit": "Vui lòng chọn một playlist để sửa.",
        "edit_xtream_title": "Sửa Xtream Codes API",
        "edit_url_title": "Sửa URL M3U",
        "edit_local_title": "Sửa Playlist Cục Bộ",
        "label_file_path": "Đường dẫn file:",
        "cannot_delete_only_playlist": "Không thể xóa playlist duy nhất.",
        "label_epg_url": "Đường dẫn EPG (Gộp nhiều EPG dùng dấu phẩy):"
    },
    "en": {
        "settings_title": "IPTV Player Settings",
        "settings_desc": "Optimize buffer size, hardware and language",
        "cache": "Buffer Size (Cache):",
        "sleep_timer": "Sleep Timer:",
        "hw_dec": "Hardware Decoding:",
        "hw_dec_checkbox": "Enable hardware acceleration (D3D11VA)",
        "language": "Language:",
        "cancel": "Cancel",
        "save": "Save Settings",
        "no_timer": "No Timer",
        "minutes": "mins",
        "timer_set": "Timer active: {} mins",
        "timer_cancelled": "🕒 Sleep timer cancelled",
        "timer_set_msg": "🕒 Sleep timer set for {} minutes!",
        "timer_remaining_msg": "🕒 Shutting down in {} seconds",
        "timer_done": "🕒 Time's up! Closing application...",
        "hw_on": "HW: On",
        "hw_off": "HW: Off",
        "live_tv_title": "LIVE TV",
        "search_placeholder": "🔍 Search channels...",
        "all_categories": "All Categories",
        "default_sort": "Default",
        "az_sort": "Name A-Z",
        "latency_sort": "Low Latency",
        "check_status": "Check status & latency of channels",
        "all": "All",
        "live_tv_tooltip": "Live TV",
        "favorites_tooltip": "Favorites",
        "history_tooltip": "Watch History",
        "playlist_manager_tooltip": "Playlist Manager",
        "shortcuts_tooltip": "Keyboard Shortcuts (H)",
        "settings_tooltip": "Settings",
        "hud_title": "⌨️ K20 PLAYER KEYBOARD SHORTCUTS",
        "hud_close": "— Click anywhere or press H to close —",
        "sh_space": "Play / Pause video",
        "sh_f": "Toggle Fullscreen",
        "sh_m": "Mute / Unmute audio",
        "sh_i": "Show / Hide stream info (Stats)",
        "sh_s": "Take screenshot",
        "sh_pip": "Picture-in-Picture mode",
        "sh_r": "Toggle live recording",
        "sh_f5": "Reload stream / channel",
        "sh_vol": "Volume Up / Down 5%",
        "sh_seek": "Seek Back / Forward 5s",
        "sh_h": "Toggle shortcuts guide",
        "sh_esc": "Exit Fullscreen",
        "screenshot_saved": "📸 Screenshot saved successfully",
        "copy_url_success": "📋 Stream URL copied to clipboard",
        
        # New translation keys
        "toggle_sidebar_tooltip": "Show/Hide Channel List",
        "no_channel_playing": "No channel playing",
        "epg_schedule_btn": "📅 Schedule",
        "epg_hide_btn": "📅 Hide Schedule",
        "toggle_epg_tooltip": "Show/Hide EPG Schedule",
        "seek_back_tooltip": "Rewind 5s (Left Arrow)",
        "seek_forward_tooltip": "Fast Forward 5s (Right Arrow)",
        "view_1_screen": "▣  1 Screen",
        "view_2_screens": "⬛  2 Screens",
        "view_4_screens": "⊞  4 Screens",
        "audio_tooltip": "Select Audio Stream",
        "subs_tooltip": "Select Subtitles",
        "epg_panel_title": "EPG SCHEDULE",
        "favorites_title": "FAVORITES ★",
        "recent_title": "RECENT 📜",
        "loading_playlist": "Loading playlist... Please wait ⏳",
        "loading_playlist_placeholder": "Loading playlist...",
        "empty_playlist_error": "❌ Empty playlist or invalid format",
        "load_playlist_error": "❌ Error loading playlist: {}",
        "context_remove_fav": "❌ Remove from Favorites",
        "context_add_fav": "★ Add to Favorites",
        "context_check_channel": "⚡ Check this channel",
        "context_copy_link": "📋 Copy Channel Link",
        "no_audio_stream": "No audio streams",
        "turn_off_subs": "Turn off Subtitles",
        "subtitle_track": "Subtitle {}",
        "player_stopped": "[Screen {}] - Stopped",
        "player_no_channel": "[Screen {}] - No channel selected 📺",
        "epg_now_playing": "📺 Playing ({}-{}): {}",
        "epg_live_no_epg": "📺 Live Stream (No EPG data)",
        "epg_no_details": "No detailed schedule available",
        "reloading_stream": "🔄 Reloading stream...",
        "copied_link_msg": "📋 Channel link copied to Clipboard!",
        "libmpv_error": "❌ Failed to load libmpv library (mpv-1.dll/mpv-2.dll).\n\nPlease make sure download_mpv_dll.py has completed successfully\nand the DLL is located in the same folder as main.py.",
        "single_view_name": "Single View (1x1)",
        "multi_view_name": "Quad View (2x2)",
        "buffer_preset_1": "10 MB (Low - Mobile Network)",
        "buffer_preset_2": "50 MB (Default - Normal)",
        "buffer_preset_3": "100 MB (High - HD/VOD)",
        "buffer_preset_4": "250 MB (Very High - Smooth 4K)",
        "buffer_preset_5": "500 MB (Maximum - Weak Network)",
        "status_online": "Channel active",
        "status_offline": "Channel offline/error",
        "status_untested": "Status unchecked",
        "lost_connection": "⚠️ Lost connection! Retrying ({}/{}) ...",
        "stats_loading": "Loading...",
        "stats_calculating": "Calculating...",
        "stats_title": "⚡ K20 PLAYER STATS ⚡",
        "stats_recording": "🔴 RECORDING",
        "stats_resolution": "Resolution",
        "stats_framerate": "Framerate",
        "stats_video_codec": "Video Codec",
        "stats_bitrate": "Bitrate",
        "stats_net_speed": "Net Speed",
        "stats_dropped_frames": "Drop Frames",
        "stats_decoder": "Decoder",
        "stats_buffer_sec": "Buffer/Sec",
        "screenshot_success": "📸 Screenshot saved successfully!",
        "playlist_manager_title": "Playlist Manager",
        "playlist_list_label": "Playlist List",
        "btn_add_file": "➕ Add File",
        "btn_add_url": "🌐 Add URL",
        "btn_add_xtream": "🔑 Add Xtream",
        "btn_edit": "✏️ Edit",
        "btn_delete": "🗑️ Delete",
        "pl_type_local": "Local",
        "pl_type_xtream": "Xtream",
        "pl_type_url": "URL",
        "select_m3u_file": "Select M3U Playlist File",
        "add_url_title": "Add M3U URL",
        "placeholder_playlist_name": "Example: IPTV Vietnam",
        "label_playlist_name": "Playlist Name:",
        "label_url_path": "URL Path:",
        "add_xtream_title": "Add Xtream Codes API",
        "placeholder_xtream_name": "Example: Xtream VIP",
        "placeholder_username": "username",
        "placeholder_password": "password",
        "label_display_name": "Display Name:",
        "label_server_url": "Server URL (Host):",
        "label_username": "Username:",
        "label_password": "Password:",
        "error_title": "Error",
        "select_playlist_to_edit": "Please select a playlist to edit.",
        "edit_xtream_title": "Edit Xtream Codes API",
        "edit_url_title": "Edit M3U URL",
        "edit_local_title": "Edit Local Playlist",
        "label_file_path": "File Path:",
        "cannot_delete_only_playlist": "Cannot delete the only playlist.",
        "label_epg_url": "EPG URL (Merge multiple EPGs with commas):"
    },
    "cn": {
        "settings_title": "IPTV 播放器设置",
        "settings_desc": "优化缓存大小、硬件和语言",
        "cache": "缓冲区大小 (缓存):",
        "sleep_timer": "睡眠定时器:",
        "hw_dec": "硬件解码:",
        "hw_dec_checkbox": "启用硬件加速 (D3D11VA)",
        "language": "语言 (Language):",
        "cancel": "取消",
        "save": "保存设置",
        "no_timer": "无定时器",
        "minutes": "分钟",
        "timer_set": "定时器激活: {} 分钟",
        "timer_cancelled": "🕒 睡眠定时器已取消",
        "timer_set_msg": "🕒 睡眠定时器已设置为 {} 分钟!",
        "timer_remaining_msg": "🕒 将在 {} 秒内关闭",
        "timer_done": "🕒 时间到！正在关闭应用程序...",
        "hw_on": "HW: 开启",
        "hw_off": "HW: 关闭",
        "live_tv_title": "电视直播",
        "search_placeholder": "🔍 搜索频道...",
        "all_categories": "所有分组",
        "default_sort": "默认",
        "az_sort": "名称 A-Z",
        "latency_sort": "低延迟",
        "check_status": "检查频道状态与延迟",
        "all": "全部",
        "live_tv_tooltip": "电视直播",
        "favorites_tooltip": "我的收藏",
        "history_tooltip": "播放历史",
        "playlist_manager_tooltip": "播放列表管理",
        "shortcuts_tooltip": "快捷键说明 (H)",
        "settings_tooltip": "系统设置",
        "hud_title": "⌨️ K20 播放器快捷键说明",
        "hud_close": "— 点击任意位置或按 H 键关闭 —",
        "sh_space": "播放 / 暂停视频",
        "sh_f": "开 / 关全屏",
        "sh_m": "静音 / 取消静音",
        "sh_i": "显示 / 隐藏流媒体信息",
        "sh_s": "保存屏幕截图",
        "sh_pip": "画中画模式",
        "sh_r": "开始 / 停止实时录制",
        "sh_f5": "重新加载频道 / 播放流",
        "sh_vol": "增加 / 减少 5% 音量",
        "sh_seek": "快退 / 快进 5 秒",
        "sh_h": "打开 / 关闭快捷键面板",
        "sh_esc": "退出全屏",
        "screenshot_saved": "📸 截图已成功保存",
        "copy_url_success": "📋 播放流链接已复制到剪贴板",
        
        # New translation keys
        "toggle_sidebar_tooltip": "显示/隐藏频道列表",
        "no_channel_playing": "未播放任何频道",
        "epg_schedule_btn": "📅 节目表",
        "epg_hide_btn": "📅 隐藏节目表",
        "toggle_epg_tooltip": "显示/隐藏 EPG 节目表",
        "seek_back_tooltip": "快退 5 秒 (左方向键)",
        "seek_forward_tooltip": "快进 5 秒 (右方向键)",
        "view_1_screen": "▣  单画面",
        "view_2_screens": "⬛  双画面",
        "view_4_screens": "⊞  四画面",
        "audio_tooltip": "选择音频流",
        "subs_tooltip": "选择字幕",
        "epg_panel_title": "电子节目表",
        "favorites_title": "我的收藏 ★",
        "recent_title": "播放历史 📜",
        "loading_playlist": "正在加载播放列表... 请稍候 ⏳",
        "loading_playlist_placeholder": "正在加载播放列表...",
        "empty_playlist_error": "❌ 播放列表为空或格式错误",
        "load_playlist_error": "❌ 加载列表错误: {}",
        "context_remove_fav": "❌ 从收藏中删除",
        "context_add_fav": "★ 添加到收藏",
        "context_check_channel": "⚡ 检查此频道",
        "context_copy_link": "📋 复制频道链接",
        "no_audio_stream": "无可用音频流",
        "turn_off_subs": "关闭字幕",
        "subtitle_track": "字幕 {}",
        "player_stopped": "[画面 {}] - 已停止",
        "player_no_channel": "[画面 {}] - 未选择频道 📺",
        "epg_now_playing": "📺 正在播放 ({}-{}): {}",
        "epg_live_no_epg": "📺 直播流 (无 EPG 数据)",
        "epg_no_details": "无详细节目表",
        "reloading_stream": "🔄 正在重新加载流...",
        "copied_link_msg": "📋 频道链接已复制到剪贴板！",
        "libmpv_error": "❌ 无法加载 libmpv 库 (mpv-1.dll/mpv-2.dll)。\n\n请确保已成功运行 download_mpv_dll.py\n并且 DLL 位于与 main.py 相同的文件夹中。",
        "single_view_name": "单画面 (1x1)",
        "multi_view_name": "四画面 (2x2)",
        "buffer_preset_1": "10 MB (低 - 移动网络)",
        "buffer_preset_2": "50 MB (默认 - 普通)",
        "buffer_preset_3": "100 MB (高 - 高清/点播)",
        "buffer_preset_4": "250 MB (很高 - 顺畅4K)",
        "buffer_preset_5": "500 MB (极高 - 弱网)",
        "status_online": "频道正常播放",
        "status_offline": "频道离线/错误",
        "status_untested": "未检查状态",
        "lost_connection": "⚠️ 连接断开！正在重试 ({}/{}) ...",
        "stats_loading": "加载中...",
        "stats_calculating": "计算中...",
        "stats_title": "⚡ K20 播放器统计信息 ⚡",
        "stats_recording": "🔴 正在录制",
        "stats_resolution": "分辨率",
        "stats_framerate": "帧率",
        "stats_video_codec": "视频解码",
        "stats_bitrate": "码率",
        "stats_net_speed": "网络速度",
        "stats_dropped_frames": "丢帧",
        "stats_decoder": "解码器",
        "stats_buffer_sec": "缓冲区 (秒)",
        "screenshot_success": "📸 截图已成功保存！",
        "playlist_manager_title": "播放列表管理",
        "playlist_list_label": "播放列表列表",
        "btn_add_file": "➕ 添加文件",
        "btn_add_url": "🌐 添加链接",
        "btn_add_xtream": "🔑 添加 Xtream",
        "btn_edit": "✏️ 编辑",
        "btn_delete": "🗑️ 删除",
        "pl_type_local": "本地",
        "pl_type_xtream": "Xtream",
        "pl_type_url": "URL",
        "select_m3u_file": "选择 M3U 播放列表文件",
        "add_url_title": "添加 M3U URL",
        "placeholder_playlist_name": "例如：IPTV 越南",
        "label_playlist_name": "播放列表名称:",
        "label_url_path": "URL 路径:",
        "add_xtream_title": "添加 Xtream Codes API",
        "placeholder_xtream_name": "例如：Xtream VIP",
        "placeholder_username": "用户名",
        "placeholder_password": "密码",
        "label_display_name": "显示名称:",
        "label_server_url": "服务器 URL (Host):",
        "label_username": "账号 (User):",
        "label_password": "密码 (Pass):",
        "error_title": "错误",
        "select_playlist_to_edit": "请选择要修改的播放列表。",
        "edit_xtream_title": "修改 Xtream Codes API",
        "edit_url_title": "修改 URL M3U",
        "edit_local_title": "修改本地播放列表",
        "label_file_path": "文件路径:",
        "cannot_delete_only_playlist": "无法删除唯一的播放列表。",
        "label_epg_url": "EPG 地址 (使用逗号合并多个 EPG):"
    }
}

CURRENT_LANG = "vi"

def load_app_language():
    global CURRENT_LANG
    try:
        cfg = config_manager.load_config()
        CURRENT_LANG = cfg.get("language", "vi").lower()
    except Exception:
        CURRENT_LANG = "vi"

def _t(key, default=""):
    return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["vi"]).get(key, default or key)

# Initialize application language on load
load_app_language()


def clean_search_string(s):
    if not s:
        return ""
    s = s.lower()
    s1 = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    s2 = 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd'
    trans = str.maketrans(s1, s2)
    return s.translate(trans)


class MpvSignals(QObject):
    pause_changed = Signal(bool)
    time_changed = Signal(float)
    duration_changed = Signal(float)
    volume_changed = Signal(int)
    file_loaded = Signal()
    buffering_event = Signal(bool)
    idle_changed = Signal(bool)


# Cache/buffer sizes preset configuration
CACHE_PRESETS = {
    1: ("10 MB (Thấp - Mạng di động)", 10 * 1024 * 1024),
    2: ("50 MB (Mặc định - Bình thường)", 50 * 1024 * 1024),
    3: ("100 MB (Cao - HD/VOD)", 100 * 1024 * 1024),
    4: ("250 MB (Rất cao - 4K mượt)", 250 * 1024 * 1024),
    5: ("500 MB (Cực đại - Mạng yếu)", 500 * 1024 * 1024)
}

# ── Logo cache ────────────────────────────────────────────────────────────────
import hashlib
from PySide6.QtGui import QPixmap

if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
_LOGO_CACHE_DIR = os.path.join(script_dir, "logo_cache")
os.makedirs(_LOGO_CACHE_DIR, exist_ok=True)
_logo_mem_cache: dict = {}  # url -> QPixmap (in-memory, per session)


def _logo_cache_path(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(_LOGO_CACHE_DIR, h + ".png")


def _load_logo_from_disk(url: str):
    path = _logo_cache_path(url)
    if os.path.exists(path):
        px = QPixmap(path)
        if not px.isNull():
            return px
    return None


_running_logo_workers = set()


class LogoFetchWorker(QThread):
    """Downloads a logo asynchronously, saves to disk cache, emits ready signal."""
    logo_ready = Signal(str, QPixmap)  # (url, pixmap)

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.finished.connect(self._cleanup)

    def start(self):
        _running_logo_workers.add(self)
        super().start()

    def _cleanup(self):
        _running_logo_workers.discard(self)

    def run(self):
        try:
            r = requests.get(self.url, timeout=5,
                             headers={"User-Agent": "Mozilla/5.0"}, stream=True)
            r.raise_for_status()
            px = QPixmap()
            if px.loadFromData(r.content):
                px.save(_logo_cache_path(self.url), "PNG")
                self.logo_ready.emit(self.url, px)
        except Exception:
            pass  # silently skip failed logos


class LogoManager(QObject):
    logo_downloaded = Signal(str, QPixmap)  # (url, pixmap)

    def __init__(self):
        super().__init__()
        self.queue = []
        self.active_downloads = 0
        self.max_concurrent = 4

    def fetch_logo(self, url):
        if not url:
            return
        if url in _logo_mem_cache:
            return
            
        px = _load_logo_from_disk(url)
        if px:
            _logo_mem_cache[url] = px
            self.logo_downloaded.emit(url, px)
            return
            
        if url not in self.queue:
            self.queue.append(url)
            self._process_queue()

    def _process_queue(self):
        if self.active_downloads >= self.max_concurrent:
            return
        if not self.queue:
            return
            
        url = self.queue.pop(0)
        self.active_downloads += 1
        
        worker = LogoFetchWorker(url)
        worker.logo_ready.connect(self._on_worker_logo_ready)
        worker.finished.connect(lambda: self._on_worker_finished(worker))
        worker.start()

    def _on_worker_logo_ready(self, url, px):
        _logo_mem_cache[url] = px
        self.logo_downloaded.emit(url, px)

    def _on_worker_finished(self, worker):
        self.active_downloads -= 1
        self._process_queue()


logo_manager = LogoManager()


class ChannelItemWidget(QWidget):

    def __init__(self, name, url, tvg_id="", is_alive=None, latency_ms=-1, logo_url="", current_program="", parent=None):
        super().__init__(parent)
        self.url = url
        self.is_alive = is_alive
        self.latency_ms = latency_ms
        self.has_epg = False
        self._logo_worker = None
        
        # Transparent background for custom widgets to inherit theme backgrounds
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Status indicator dot
        self.lbl_status = QLabel(self)
        self.lbl_status.setFixedSize(8, 8)
        self.set_status_style(is_alive)
        layout.addWidget(self.lbl_status)
        
        # ── Channel Logo ─────────────────────────────────────────────────────
        self.lbl_logo = QLabel(self)
        self.lbl_logo.setFixedSize(34, 34)
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setScaledContents(False)
        self._set_logo_placeholder(name)
        layout.addWidget(self.lbl_logo)
        
        if logo_url:
            # Check memory cache first
            if logo_url in _logo_mem_cache:
                self._apply_logo_pixmap(_logo_mem_cache[logo_url])
            else:
                self._logo_url = logo_url
                logo_manager.logo_downloaded.connect(self._on_global_logo_ready)
                logo_manager.fetch_logo(logo_url)
        
        # Text container for Name and EPG
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        # Channel Name
        self.lbl_name = QLabel(name, self)
        self.lbl_name.setStyleSheet("color: #e0e0e6; font-weight: 500; background: transparent; font-size: 12px;")
        self.lbl_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_layout.addWidget(self.lbl_name)
        
        # EPG program
        self.lbl_epg = QLabel(self)
        if current_program:
            self.lbl_epg.setText(current_program)
            self.lbl_epg.setStyleSheet("color: #00e5ff; background: transparent; font-size: 10px;")
        else:
            self.lbl_epg.setText("")
            self.lbl_epg.setStyleSheet("color: #888896; background: transparent; font-size: 10px;")
        self.lbl_epg.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        text_layout.addWidget(self.lbl_epg)
        
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Badges container layout
        self.badges_layout = QHBoxLayout()
        self.badges_layout.setContentsMargins(0, 0, 0, 0)
        self.badges_layout.setSpacing(4)
        layout.addLayout(self.badges_layout)
        
        # Add latency badge if active
        self.lbl_latency = QLabel(self)
        self.lbl_latency.setVisible(False)
        self.lbl_latency.setAlignment(Qt.AlignCenter)
        self.badges_layout.addWidget(self.lbl_latency)
        
        # Detect and add resolution / framerate badges
        badges = self.detect_badges(name)
        for badge_text, style in badges:
            lbl_badge = QLabel(badge_text, self)
            lbl_badge.setStyleSheet(style)
            lbl_badge.setAlignment(Qt.AlignCenter)
            self.badges_layout.addWidget(lbl_badge)
            
        if latency_ms > 0:
            self.set_latency(latency_ms)
            
        # Favorite star button
        self.btn_fav = QPushButton(self)
        self.btn_fav.setFixedSize(26, 26)
        self.btn_fav.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.is_fav = config_manager.is_favorite(url)
        self._update_star_icon()
        
        self.btn_fav.clicked.connect(self.toggle_favorite)
        layout.addWidget(self.btn_fav)

    def toggle_favorite(self):
        if self.is_fav:
            config_manager.remove_favorite(self.url)
            self.is_fav = False
        else:
            config_manager.add_favorite(self.lbl_name.text(), self.url)
            self.is_fav = True
            
        self._update_star_icon()
        
        # Trigger reload of main window if in favorites view
        parent_win = self.window()
        if parent_win and hasattr(parent_win, 'current_view') and parent_win.current_view == "favorites":
            parent_win.filter_channels()

    def _update_star_icon(self):
        if self.is_fav:
            self.btn_fav.setText("★")
            self.btn_fav.setStyleSheet("QPushButton { color: #ffd54f; font-size: 17px; background: transparent; border: none; } QPushButton:hover { color: #ffe082; }")
        else:
            self.btn_fav.setText("☆")
            self.btn_fav.setStyleSheet("QPushButton { color: rgba(220, 220, 240, 70); font-size: 17px; background: transparent; border: none; } QPushButton:hover { color: rgba(220, 220, 240, 200); }")

    def _set_logo_placeholder(self, name: str):
        """Show a stylised initials badge as placeholder until the real logo loads."""
        initial = name[0].upper() if name else "?"
        self.lbl_logo.setText(initial)
        self.lbl_logo.setFont(QFont("Outfit", 13, QFont.Bold))
        self.lbl_logo.setStyleSheet(
            "color: rgba(220,220,240,200);"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 rgba(50,40,80,180), stop:1 rgba(30,30,50,180));"
            "border: 1px solid rgba(255,255,255,30);"
            "border-radius: 8px;"
        )

    def _apply_logo_pixmap(self, px: QPixmap):
        """Scale & apply a logo pixmap with rounded-rect masking."""
        from PySide6.QtGui import QPainterPath, QPainter
        from PySide6.QtCore import QRectF
        scaled = px.scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # Create rounded mask
        rounded = QPixmap(34, 34)
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, 34, 34), 8, 8)
        painter.setClipPath(path)
        x_off = (34 - scaled.width()) // 2
        y_off = (34 - scaled.height()) // 2
        painter.drawPixmap(x_off, y_off, scaled)
        painter.end()
        self.lbl_logo.setPixmap(rounded)
        self.lbl_logo.setText("")
        self.lbl_logo.setStyleSheet(
            "background: rgba(20,20,28,160);"
            "border: 1px solid rgba(255,255,255,20);"
            "border-radius: 8px;"
        )

    def _on_global_logo_ready(self, url: str, px: QPixmap):
        if url == getattr(self, '_logo_url', None):
            self._apply_logo_pixmap(px)
            try:
                logo_manager.logo_downloaded.disconnect(self._on_global_logo_ready)
            except Exception:
                pass

    def detect_badges(self, name):
        name_upper = name.upper()
        detected = []
        
        # 4K / UHD
        if "4K" in name_upper or "UHD" in name_upper:
            detected.append(("4K", "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #b388ff); color: white; font-weight: bold; border-radius: 4px; padding: 2px 6px; font-size: 9px;"))
        # FHD / 1080p
        elif "FHD" in name_upper or "1080" in name_upper:
            detected.append(("FHD", "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b0ff, stop:1 #00e5ff); color: #121214; font-weight: bold; border-radius: 4px; padding: 2px 6px; font-size: 9px;"))
        # HD / 720p
        elif "HD" in name_upper or "720" in name_upper:
            detected.append(("HD", "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #69f0ae); color: #121214; font-weight: bold; border-radius: 4px; padding: 2px 6px; font-size: 9px;"))
            
        # FPS
        if "60FPS" in name_upper or "60 FPS" in name_upper:
            detected.append(("60FPS", "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6d00, stop:1 #ffab40); color: white; font-weight: bold; border-radius: 4px; padding: 2px 6px; font-size: 9px;"))
        elif "50FPS" in name_upper or "50 FPS" in name_upper:
            detected.append(("50FPS", "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff9100, stop:1 #ffd600); color: #121214; font-weight: bold; border-radius: 4px; padding: 2px 6px; font-size: 9px;"))
            
        return detected

    def set_status_style(self, is_alive):
        if is_alive is True:
            self.lbl_status.setStyleSheet("""
                background-color: #00e676;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            """)
            self.lbl_status.setToolTip(_t("status_online"))
        elif is_alive is False:
            self.lbl_status.setStyleSheet("""
                background-color: #ff1744;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            """)
            self.lbl_status.setToolTip(_t("status_offline"))
        else:
            self.lbl_status.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 4px;
            """)
            self.lbl_status.setToolTip(_t("status_untested"))

    def set_status(self, is_alive, latency_ms=-1):
        self.is_alive = is_alive
        self.set_status_style(is_alive)
        if latency_ms > 0:
            self.set_latency(latency_ms)

    def set_latency(self, latency_ms):
        self.latency_ms = latency_ms
        if latency_ms < 0:
            self.lbl_latency.setVisible(False)
            return
            
        self.lbl_latency.setText(f"{latency_ms}ms")
        self.lbl_latency.setVisible(True)
        
        # Dynamic color coding for low/med/high latency
        if latency_ms < 150:
            style = "background-color: #2e7d32; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 2px 5px; font-size: 9px; line-height: 12px;"
        elif latency_ms < 400:
            style = "background-color: #ef6c00; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 2px 5px; font-size: 9px; line-height: 12px;"
        else:
            style = "background-color: #c62828; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 2px 5px; font-size: 9px; line-height: 12px;"
            
        self.lbl_latency.setStyleSheet(style)


class PlaylistDownloadWorker(QThread):
    finished = Signal(list, str) # Emits (channels, epg_url)
    failed = Signal(str)
    
    def __init__(self, path_or_url):
        super().__init__()
        self.path_or_url = path_or_url
        
    def run(self):
        try:
            # 1. Try to parse using Xtream Codes JSON API if the URL contains username and password
            url_str = self.path_or_url
            if url_str.startswith("http://") or url_str.startswith("https://"):
                from urllib.parse import urlparse, parse_qs
                try:
                    parsed = urlparse(url_str)
                    qs = parse_qs(parsed.query)
                    username = qs.get("username", [None])[0]
                    password = qs.get("password", [None])[0]
                    
                    if not username or not password:
                        path_parts = [p.strip() for p in parsed.path.split('/') if p.strip()]
                        if len(path_parts) == 2:
                            username = path_parts[0]
                            password = path_parts[1]
                        elif len(path_parts) == 3 and path_parts[0] == 'get.php':
                            username = path_parts[1]
                            password = path_parts[2]
                            
                    if username and password:
                        host = f"{parsed.scheme}://{parsed.netloc}"
                        print(f"[+] Detected Xtream Codes URL. Fetching via player_api.php: {host}")
                        
                        headers = {"User-Agent": "Mozilla/5.0"}
                        
                        # Fetch Categories
                        category_map = {}
                        cat_url = f"{host.rstrip('/')}/player_api.php?username={username}&password={password}&action=get_live_categories"
                        try:
                            r = requests.get(cat_url, headers=headers, timeout=12)
                            if r.status_code == 200:
                                cats = r.json()
                                if isinstance(cats, list):
                                    for cat in cats:
                                        c_id = str(cat.get("category_id"))
                                        c_name = cat.get("category_name", "Default")
                                        category_map[c_id] = c_name
                        except Exception as cat_err:
                            print(f"[-] Failed to fetch Xtream categories: {cat_err}")
                            
                        # Fetch Live Streams
                        streams_url = f"{host.rstrip('/')}/player_api.php?username={username}&password={password}&action=get_live_streams"
                        r = requests.get(streams_url, headers=headers, timeout=25)
                        r.raise_for_status()
                        streams = r.json()
                        
                        channels = []
                        if isinstance(streams, list):
                            for s in streams:
                                stream_id = s.get("stream_id")
                                if not stream_id:
                                    continue
                                cat_id = str(s.get("category_id"))
                                group = category_map.get(cat_id, "Default")
                                
                                stream_url = f"{host.rstrip('/')}/live/{username}/{password}/{stream_id}.ts"
                                
                                channels.append({
                                    "name": s.get("name", "Unknown Channel"),
                                    "url": stream_url,
                                    "logo": s.get("stream_icon", ""),
                                    "group": group,
                                    "tvg-id": s.get("epg_channel_id", "")
                                })
                                
                        epg_url = f"{host.rstrip('/')}/xmltv.php?username={username}&password={password}"
                        print(f"[+] Loaded {len(channels)} channels via Xtream Codes JSON API.")
                        self.finished.emit(channels, epg_url)
                        return
                except Exception as xtream_err:
                    print(f"[-] Xtream API fetch failed, falling back to standard M3U: {xtream_err}")
            
            # 2. Fallback to standard M3U parsing
            channels, epg_url = parse_m3u(self.path_or_url)
            
            if not channels:
                # Fallback to script-relative path
                if getattr(sys, 'frozen', False):
                    script_dir = os.path.dirname(sys.executable)
                else:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                script_relative = os.path.join(script_dir, self.path_or_url)
                if os.path.exists(script_relative):
                    channels, epg_url = parse_m3u(script_relative)
                    
            if not channels:
                abs_path = os.path.abspath(self.path_or_url)
                if os.path.exists(abs_path):
                    channels, epg_url = parse_m3u(abs_path)
                    
            self.finished.emit(channels, epg_url or "")
        except Exception as e:
            self.failed.emit(str(e))


class LoadingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(16) # ~60 FPS
        self.setFixedSize(50, 50)
        
    def rotate(self):
        self.angle = (self.angle + 6) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background track
        pen_track = QPen(QColor(255, 255, 255, 20))
        pen_track.setWidth(4)
        painter.setPen(pen_track)
        painter.drawEllipse(4, 4, 42, 42)
        
        # Draw rotating arc
        pen_arc = QPen(QColor(0, 229, 255)) # neon blue/cyan
        pen_arc.setWidth(4)
        painter.setPen(pen_arc)
        painter.drawArc(4, 4, 42, 42, int(-self.angle * 16), int(120 * 16))


class PlayerOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Set up UI
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(15)
        
        # Container frame for glass effect
        self.container = QFrame(self)
        self.container.setObjectName("OverlayContainer")
        self.container.setStyleSheet("""
            QFrame#OverlayContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(24, 24, 30, 220),
                    stop:1 rgba(14, 14, 20, 240));
                border: 1px solid rgba(0, 229, 255, 80);
                border-radius: 16px;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setContentsMargins(30, 25, 30, 25)
        container_layout.setSpacing(12)
        
        # Spinner
        self.spinner = LoadingSpinner(self.container)
        container_layout.addWidget(self.spinner, 0, Qt.AlignCenter)
        
        # Text
        self.lbl_text = QLabel(_t("loading_channel"), self.container)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.lbl_text.setFont(QFont("Outfit", 12, QFont.Bold))
        self.lbl_text.setStyleSheet("color: #00e5ff; background: transparent; border: none;")
        container_layout.addWidget(self.lbl_text)
        
        self.layout.addWidget(self.container, 0, Qt.AlignCenter)
        self.hide() # Hidden by default

    def sync_to_parent(self):
        parent = self.parentWidget()
        if parent:
            self.setGeometry(parent.contentsRect())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        super().paintEvent(event)

    def show_loading(self, text=None):
        if text is None:
            text = _t("loading_channel")
        # Prevent showing overlay if the parent player frame is hidden
        if self.parent() and not self.parent().isVisible():
            return
        self.spinner.show()
        self.lbl_text.setText(text)
        self.lbl_text.setStyleSheet("color: #00e5ff; background: transparent; border: none;")
        self.container.setStyleSheet("""
            QFrame#OverlayContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(24, 24, 30, 220),
                    stop:1 rgba(14, 14, 20, 240));
                border: 1px solid rgba(0, 229, 255, 80);
                border-radius: 16px;
            }
        """)
        self.sync_to_parent()
        self.show()
        self.raise_()
        
    def show_error(self, text=None):
        if text is None:
            text = _t("channel_error_default")
        # Prevent showing overlay if the parent player frame is hidden
        if self.parent() and not self.parent().isVisible():
            return
        self.spinner.hide()
        self.lbl_text.setText(text)
        self.lbl_text.setStyleSheet("color: #ff3366; background: transparent; border: none;")
        self.container.setStyleSheet("""
            QFrame#OverlayContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 15, 20, 230),
                    stop:1 rgba(20, 10, 12, 245));
                border: 1px solid rgba(255, 51, 102, 100);
                border-radius: 16px;
            }
        """)
        self.sync_to_parent()
        self.show()
        self.raise_()


class MpvWidget(QWidget):
    double_clicked = Signal()
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WA_NativeWindow)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        
        self.signals = MpvSignals()
        self.signals.buffering_event.connect(self.on_buffering_state_changed)
        self.signals.idle_changed.connect(self.on_mpv_idle_changed)
        self.player = None
        
        self.config = config_manager.load_config()
        self.current_url = None
        self.current_channel = {}
        self.recording_path = None
        self.recording_start_time = None
        
        # Auto-reconnect configuration
        self.is_playing_state = False
        self.reconnect_count = 0
        self.max_reconnects = 3
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.reconnect_stream)
        
        self.stats_visible = False
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats_osd)
        
        # Loading timeout configuration (35 seconds)
        self.loading_timer = QTimer(self)
        self.loading_timer.setSingleShot(True)
        self.loading_timer.timeout.connect(self.on_loading_timeout)
        self.signals.file_loaded.connect(self.on_file_loaded)
        
        if MPV_AVAILABLE:
            try:
                cfg = config_manager.load_config()
                hwdec_mode = 'auto' if cfg.get("hwdec_enabled", True) else 'no'
                
                _mpv_kwargs = dict(
                    wid=str(int(self.winId())),
                    vo='gpu',
                    gpu_api='d3d11',
                    hwdec=hwdec_mode,
                    ytdl=False,
                    load_scripts=False,
                )
                
                self.player = mpv.MPV(**_mpv_kwargs)
                self.player.show_message = self.show_message
                try:
                    self.player['user-agent'] = "VLC/3.0.18 LibVLC/3.0.18"
                except Exception as e:
                    print(f"Could not set custom user-agent on mpv: {e}")
                    
                # Configure Cache / Buffer Size
                buffer_bytes = self.config.get("buffer_size_bytes", 50 * 1024 * 1024)
                try:
                    self.player['cache'] = 'yes'
                    self.player['demuxer-max-bytes'] = buffer_bytes
                    self.player['demuxer-readahead-secs'] = 30
                except Exception as e:
                    print(f"Could not configure cache settings on mpv: {e}")
                
                # Safely configure input settings without risking initialization failure
                for opt, val in [('input-default-bindings', 'no'), ('input-vo-keyboard', 'no'), ('input-vo-mouse', 'no')]:
                    try:
                        self.player[opt] = val
                    except Exception as e:
                        pass
                @self.player.property_observer('pause')
                def on_pause_change(_self, value):
                    self.signals.pause_changed.emit(bool(value))
                    
                @self.player.property_observer('time-pos')
                def on_time_change(_self, value):
                    if value is not None:
                        self.signals.time_changed.emit(float(value))
                        
                @self.player.property_observer('duration')
                def on_duration_change(_self, value):
                    if value is not None:
                        self.signals.duration_changed.emit(float(value))
                        
                @self.player.property_observer('volume')
                def on_volume_change(_self, value):
                    if value is not None:
                        self.signals.volume_changed.emit(int(value))
                        
                @self.player.property_observer('width')
                def on_width_change(_self, value):
                    if value is not None and value > 0:
                        self.signals.file_loaded.emit()
                        
                @self.player.property_observer('idle-active')
                def on_idle_change(_self, value):
                    if value is not None:
                        self.signals.idle_changed.emit(bool(value))
                            
                @self.player.property_observer('paused-for-cache')
                def on_cache_pause_change(_self, value):
                    if value is not None:
                        self.signals.buffering_event.emit(bool(value))
            except Exception as e:
                print(f"Failed to initialize MPV player: {e}")
                self.player = None

    def on_buffering_state_changed(self, is_buffering):
        if is_buffering and self.player:
            if not hasattr(self, 'buffering_count'):
                self.buffering_count = 0
            self.buffering_count += 1
            print(f"[!] Buffering event detected! Count: {self.buffering_count}")
            
            if self.buffering_count >= 2:
                try:
                    current_bytes = self.player['demuxer-max-bytes'] or (50 * 1024 * 1024)
                    new_bytes = min(current_bytes * 3, 500 * 1024 * 1024)
                    self.player['demuxer-max-bytes'] = new_bytes
                    self.player['demuxer-readahead-secs'] = 90
                    print(f"[+] Dynamic buffering triggered: Increased demuxer-max-bytes to {new_bytes / (1024*1024)}MB")
                    self.buffering_count = 0
                except Exception as e:
                    print(f"Could not dynamically adjust buffer: {e}")

    def on_mpv_idle_changed(self, is_idle):
        if is_idle and getattr(self, 'is_playing_state', False):
            if self.reconnect_count < self.max_reconnects:
                self.reconnect_timer.start(2000)

    def show_message(self, message, duration=3000):
        if self.player:
            try:
                self.player.show_text(message, duration)
            except Exception as e:
                print(f"[-] Error showing OSD message: {e}")

    def _get_overlay(self):
        """Return this widget's parent PlayerFrame overlay directly (avoids index lookup bugs)."""
        parent = self.parent()
        if parent and hasattr(parent, 'overlay'):
            return parent.overlay
        return None

    def play(self, url_or_channel):
        if self.player:
            try:
                if isinstance(url_or_channel, dict):
                    self.current_channel = url_or_channel
                    self.current_url = url_or_channel.get("url", "")
                else:
                    self.current_channel = {"url": url_or_channel}
                    self.current_url = url_or_channel
                    
                url = self.current_url
                ua = self.current_channel.get("user-agent", "")
                ref = self.current_channel.get("referer", "")
                
                self.is_playing_state = True
                self.reconnect_count = 0
                self.reconnect_timer.stop()
                
                # Native mpv surfaces on Windows do not compose reliably with Qt overlays.
                # Keep the old overlay hidden to avoid clipped/ghost loading cards.
                overlay = self._get_overlay()
                if overlay:
                    overlay.hide()
                
                # Start loading timer (35 seconds timeout)
                if hasattr(self, 'loading_timer'):
                    self.loading_timer.start(35000)
                
                # 1. Stop previous stream immediately to release the TCP socket
                try:
                    self.player.stop()
                except Exception:
                    pass
                
                # 2. Defer play call by 600ms to allow IPTV server to clear connection slot
                def do_play():
                    if getattr(self, 'is_playing_state', False) and self.current_url == url:
                        try:
                            if ua:
                                self.player['user-agent'] = ua
                            else:
                                self.player['user-agent'] = "VLC/3.0.18 LibVLC/3.0.18"
                                
                            if ref:
                                self.player['referrer'] = ref
                            else:
                                self.player['referrer'] = ""
                                
                            self.player.play(url)
                        except Exception as play_err:
                            print(f"Deferred play failed: {play_err}")
                            
                QTimer.singleShot(600, do_play)
                
            except Exception as e:
                print(f"Error playing stream: {e}")

    def stop(self):
        self.is_playing_state = False
        self.reconnect_timer.stop()
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
            
        overlay = self._get_overlay()
        if overlay:
            overlay.hide()
            
        if self.player:
            self.player.stop()

    def on_file_loaded(self):
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
            
        overlay = self._get_overlay()
        if overlay:
            overlay.hide()

    def on_loading_timeout(self):
        print(f"[-] Playback timeout for {self.current_url}")
        self.stop()
        if self.player:
            try:
                self.player.show_message(_t("channel_unavailable"), 3000)
            except Exception:
                pass

    def reconnect_stream(self):
        if not self.player or not getattr(self, 'is_playing_state', False) or not getattr(self, 'current_url', None):
            return
            
        self.reconnect_count += 1
        msg = _t("lost_connection").format(self.reconnect_count, self.max_reconnects)
        self.player.show_message(msg, 3000)
        print(f"[*] Stream lost. Reconnect attempt {self.reconnect_count}/{self.max_reconnects} for {self.current_url}")
        
        try:
            if hasattr(self, 'current_channel') and isinstance(self.current_channel, dict):
                ua = self.current_channel.get("user-agent", "")
                ref = self.current_channel.get("referer", "")
                if ua:
                    self.player['user-agent'] = ua
                else:
                    self.player['user-agent'] = "VLC/3.0.18 LibVLC/3.0.18"
                if ref:
                    self.player['referrer'] = ref
                else:
                    self.player['referrer'] = ""
            self.player.play(self.current_url)
        except Exception as e:
            print(f"[-] Reconnect play failed: {e}")

    def set_pause(self, state):
        if self.player:
            self.player.pause = state

    def toggle_pause(self):
        if self.player:
            self.player.pause = not self.player.pause

    def set_volume(self, value):
        if self.player:
            self.player.volume = value

    def set_aspect_ratio(self, ratio):
        if self.player:
            self.player['aspect'] = ratio

    def toggle_hwdec(self, enabled):
        if self.player:
            self.player['hwdec'] = 'auto' if enabled else 'no'

    def toggle_stats(self):
        if not self.player:
            return
        self.stats_visible = not self.stats_visible
        if self.stats_visible:
            # Configure clean OSD styles dynamically
            try:
                self.player['osd-font'] = 'Consolas'
                self.player['osd-font-size'] = 14
                self.player['osd-color'] = '#00ffcc'
                self.player['osd-shadow-color'] = '#000000'
                self.player['osd-shadow-offset'] = 1
                self.player['osd-align-x'] = 'left'
                self.player['osd-align-y'] = 'top'
            except Exception as e:
                print(f"Could not configure OSD style: {e}")
            
            self.update_stats_osd()
            self.stats_timer.start(1000)
        else:
            self.stats_timer.stop()
            try:
                self.player['osd-msg1'] = ""
            except:
                pass

    def update_stats_osd(self):
        if not self.player or not self.stats_visible:
            return
        try:
            w = self.player.get_property('width')
            h = self.player.get_property('height')
            fps = self.player.get_property('container-fps')
            if not fps:
                fps = self.player.get_property('estimated-vf-fps')
                
            bitrate = self.player.get_property('video-bitrate')
            if not bitrate:
                bitrate = self.player.get_property('file-size')
                
            hwdec = self.player.get_property('hwdec-current')
            cache = self.player.get_property('demuxer-cache-duration')
            
            # Additional advanced stats
            codec = self.player.get_property('video-codec')
            speed = self.player.get_property('download-speed') or 0
            dropped = self.player.get_property('frame-drop-count') or self.player.get_property('vo-drop-frame-count') or 0
            
            res_str = f"{w}x{h}" if w and h else _t("stats_loading")
            fps_str = f"{fps:.1f}" if fps else _t("stats_loading")
            hw_str = hwdec.upper() if hwdec and hwdec != "no" else "None (Software)"
            codec_str = codec.upper() if codec else _t("stats_loading")
            
            if bitrate:
                bitrate_str = f"{bitrate / 1_000_000:.2f} Mbps" if bitrate > 1000000 else f"{bitrate / 1000:.1f} Kbps"
            else:
                bitrate_str = _t("stats_calculating")
                
            if speed > 0:
                speed_mbps = (speed * 8) / 1_000_000
                if speed > 1024 * 1024:
                    speed_str = f"{speed / (1024 * 1024):.2f} MB/s ({speed_mbps:.1f} Mbps)"
                else:
                    speed_str = f"{speed / 1024:.1f} KB/s ({speed_mbps:.2f} Mbps)"
            else:
                speed_str = "0 Mbps"
                
            cache_str = f"{cache:.1f}s" if cache is not None else "0s"
            
            rec_line = ""
            if hasattr(self, 'recording_path') and self.recording_path:
                import time
                elapsed = int(time.time() - self.recording_start_time)
                mins, secs = divmod(elapsed, 60)
                hours, mins = divmod(mins, 60)
                time_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
                rec_line = f"{_t('stats_recording')} : {time_str}\n━━━━━━━━━━━━━━━━━━━━\n"
            
            text = (
                f"{_t('stats_title')}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{rec_line}"
                f"▶ {_t('stats_resolution')}  : {res_str}\n"
                f"▶ {_t('stats_framerate')}   : {fps_str} FPS\n"
                f"▶ {_t('stats_video_codec')} : {codec_str}\n"
                f"▶ {_t('stats_bitrate')}     : {bitrate_str}\n"
                f"▶ {_t('stats_net_speed')}   : {speed_str}\n"
                f"▶ {_t('stats_dropped_frames')} : {dropped}\n"
                f"▶ {_t('stats_decoder')}     : {hw_str}\n"
                f"▶ {_t('stats_buffer_sec')}  : {cache_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            self.player['osd-msg1'] = text
        except Exception as e:
            pass

    def start_recording(self, filepath, stream_url):
        if not self.player:
            return False
        try:
            import time
            self.recording_path = filepath
            self.recording_start_time = time.time()
            
            # Apply headers before reloading for recording
            if hasattr(self, 'current_channel') and isinstance(self.current_channel, dict):
                ua = self.current_channel.get("user-agent", "")
                ref = self.current_channel.get("referer", "")
                if ua:
                    self.player['user-agent'] = ua
                else:
                    self.player['user-agent'] = "VLC/3.0.18 LibVLC/3.0.18"
                if ref:
                    self.player['referrer'] = ref
                else:
                    self.player['referrer'] = ""
                    
            # Set record-file option before loading the stream
            self.player['record-file'] = filepath
            # Reload stream to start recording
            self.player.play(stream_url)
            
            # Start timer to update OSD
            if not hasattr(self, 'rec_timer'):
                self.rec_timer = QTimer(self)
                self.rec_timer.timeout.connect(self.update_recording_osd)
            self.rec_timer.start(1000)
            
            self.update_recording_osd()
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    def stop_recording(self, stream_url):
        if not self.player:
            return False
        try:
            self.recording_path = None
            if hasattr(self, 'rec_timer'):
                self.rec_timer.stop()
                
            # Apply headers before reloading to stop recording
            if hasattr(self, 'current_channel') and isinstance(self.current_channel, dict):
                ua = self.current_channel.get("user-agent", "")
                ref = self.current_channel.get("referer", "")
                if ua:
                    self.player['user-agent'] = ua
                else:
                    self.player['user-agent'] = "VLC/3.0.18 LibVLC/3.0.18"
                if ref:
                    self.player['referrer'] = ref
                else:
                    self.player['referrer'] = ""
            
            # Clear record-file option
            self.player['record-file'] = ""
            # Reload stream to stop recording
            self.player.play(stream_url)
            
            # Clear OSD
            self.player['osd-msg1'] = ""
            self.player.show_message(_t("record_stopped"), 2000)
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False

    def update_recording_osd(self):
        if not self.player or not self.recording_path:
            return
        try:
            import time
            elapsed = int(time.time() - self.recording_start_time)
            mins, secs = divmod(elapsed, 60)
            hours, mins = divmod(mins, 60)
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
            
            if self.stats_visible:
                self.update_stats_osd()
            else:
                self.player['osd-msg1'] = f"🔴 REC  {time_str}"
        except Exception:
            pass

    def seek(self, position):
        if self.player:
            self.player.seek(position, reference='absolute')

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def take_screenshot(self, filepath):
        if self.player:
            try:
                # Ensure the folder exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                self.player.command("screenshot-to-file", filepath)
                self.player.show_message(_t("screenshot_success"), 2000)
                return True
            except Exception as e:
                print(f"Error taking screenshot: {e}")
                return False
        return False

    def closeEvent(self, event):
        if self.player:
            try:
                self.player.terminate()
            except:
                pass
        super().closeEvent(event)


# Player Frame wrapper to handle selection outlines in Multi-view
class PlayerFrame(QFrame):
    clicked = Signal(int)
    double_clicked = Signal(int)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("PlayerFrame")
        self.is_active = False
        self.is_pip = False
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_NativeWindow, True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.mpv_widget = None
        self.overlay = PlayerOverlay(self)
        self.overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.sync_to_parent()
            if self.overlay.isVisible():
                self.overlay.raise_()

    def set_player(self, mpv_widget):
        self.mpv_widget = mpv_widget
        self.layout.addWidget(mpv_widget)
        
        # Forward click signals
        self.mpv_widget.clicked.connect(lambda: self.clicked.emit(self.index))
        self.mpv_widget.double_clicked.connect(lambda: self.double_clicked.emit(self.index))

    def set_active(self, active):
        self.is_active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        if event.button() == Qt.LeftButton and self.is_pip:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.is_pip and hasattr(self, '_drag_position'):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)


class ShortcutsHUD(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Outer layout to center the content card
        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignCenter)
        
        # Glass card container
        self.card = QFrame(self)
        self.card.setObjectName("HUDCard")
        self.card.setStyleSheet("""
            QFrame#HUDCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(24, 24, 32, 235),
                    stop:1 rgba(14, 14, 20, 250));
                border: 1px solid rgba(124, 77, 255, 100);
                border-radius: 20px;
            }
        """)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(15)
        
        # Title
        title = QLabel(_t("hud_title"), self.card)
        title.setFont(QFont("Outfit", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00e5ff; background: transparent; border: none;")
        card_layout.addWidget(title)
        
        # Grid of shortcuts
        grid_widget = QWidget(self.card)
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 5, 0, 5)
        
        shortcuts = [
            ("Space", _t("sh_space")),
            ("F / Double Click", _t("sh_f")),
            ("M", _t("sh_m")),
            ("I", _t("sh_i")),
            ("S / F12", _t("sh_s")),
            ("P", _t("sh_pip")),
            ("R", _t("sh_r")),
            ("F5", _t("sh_f5")),
            ("Up / Down", _t("sh_vol")),
            ("Left / Right", _t("sh_seek")),
            ("H", _t("sh_h")),
            ("Escape", _t("sh_esc"))
        ]
        
        for idx, (key, desc) in enumerate(shortcuts):
            row = idx // 2
            col = (idx % 2) * 2
            
            lbl_key = QLabel(key, grid_widget)
            lbl_key.setAlignment(Qt.AlignCenter)
            lbl_key.setFont(QFont("Consolas", 10, QFont.Bold))
            lbl_key.setStyleSheet("""
                QLabel {
                    background-color: #232329;
                    border: 1px solid #3e3e4b;
                    border-radius: 6px;
                    padding: 4px 10px;
                    color: #7c4dff;
                    min-width: 90px;
                }
            """)
            
            lbl_desc = QLabel(desc, grid_widget)
            lbl_desc.setStyleSheet("color: #e0e0e6; padding-left: 5px;")
            
            grid.addWidget(lbl_key, row, col)
            grid.addWidget(lbl_desc, row, col + 1)
            
        card_layout.addWidget(grid_widget)
        
        lbl_info = QLabel(_t("hud_close"), self.card)
        lbl_info.setFont(QFont("Outfit", 9, QFont.Bold))
        lbl_info.setAlignment(Qt.AlignCenter)
        lbl_info.setStyleSheet("color: #888896; background: transparent; border: none; margin-top: 5px;")
        card_layout.addWidget(lbl_info)
        
        outer_layout.addWidget(self.card)
        self.hide()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(8, 8, 12, 190))
        
    def show_hud(self):
        self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.setFocus()
        
    def mousePressEvent(self, event):
        self.hide()
        event.accept()
        
    def keyPressEvent(self, event):
        self.hide()
        event.accept()


# Background EPG Downloader Thread
class EPGDownloadWorker(QThread):
    finished = Signal(bool)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        success = epg_manager.download_epg(self.url)
        if success:
            epg_manager.load_epg_cache()
        self.finished.emit(success)


# Background Asynchronous Channel Live/Dead Checker Thread
class ChannelChecker(QThread):
    status_updated = Signal(str, bool, int) # url, is_alive, latency_ms
    
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.running = True
        
    def run(self):
        import time
        checked_urls = set()
        for c in self.channels:
            if not self.running:
                break
            url = c.get("url", "")
            if not url or url in checked_urls:
                continue
            checked_urls.add(url)
            
            is_alive = False
            latency_ms = -1
            start_time = time.perf_counter()
            try:
                # Quick check with HEAD request, timeout 2s
                r = requests.head(url, timeout=2.0, headers={"User-Agent": "VLC/3.0.18 LibVLC/3.0.18"}, allow_redirects=True)
                is_alive = (r.status_code < 400)
                latency_ms = int((time.perf_counter() - start_time) * 1000)
            except Exception:
                try:
                    start_time = time.perf_counter()
                    # Fallback to GET for stream links that reject HEAD requests
                    r = requests.get(url, timeout=2.0, headers={"User-Agent": "VLC/3.0.18 LibVLC/3.0.18"}, stream=True)
                    is_alive = (r.status_code < 400)
                    latency_ms = int((time.perf_counter() - start_time) * 1000)
                    r.close()
                except Exception:
                    is_alive = False
                    latency_ms = -1
                    
            self.status_updated.emit(url, is_alive, latency_ms)
            self.msleep(100) # Avoid overwhelming system/network
            
    def stop(self):
        self.running = False


class PlaylistItemWidget(QWidget):
    def __init__(self, pl, is_active, parent=None):
        super().__init__(parent)
        self.setObjectName("PlaylistItemWidget")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)
        
        # Icon Label
        self.icon_label = QLabel(self)
        self.icon_label.setFont(QFont("Font Awesome 6 Free", 14))
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        xtream = pl.get("xtream")
        is_local = pl.get("is_local")
        
        if xtream:
            self.icon_label.setText("\uf1e6") # Plug icon
            self.icon_label.setStyleSheet("color: #00e676; background: transparent;") # Neon green
            pl_type = _t("pl_type_xtream")
            badge_color = "#1b5e20"
        elif is_local:
            self.icon_label.setText("\uf07b") # Folder icon
            self.icon_label.setStyleSheet("color: #29b6f6; background: transparent;") # Light blue
            pl_type = _t("pl_type_local")
            badge_color = "#01579b"
        else:
            self.icon_label.setText("\uf0c1") # Link icon
            self.icon_label.setStyleSheet("color: #ab47bc; background: transparent;") # Purple
            pl_type = _t("pl_type_url")
            badge_color = "#4a148c"
            
        layout.addWidget(self.icon_label)
        
        # Details container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.name_label = QLabel(pl.get("name", ""), self)
        self.name_label.setFont(QFont("Outfit", 10, QFont.Bold))
        self.name_label.setStyleSheet("color: #ffffff; background: transparent;")
        text_layout.addWidget(self.name_label)
        
        url_text = pl.get("url", "")
        # Hide sensitive passwords in url for Xtream / urls
        import re
        if "password=" in url_text:
            url_text = re.sub(r'password=[^&]+', 'password=******', url_text)
            
        self.url_label = QLabel(url_text, self)
        self.url_label.setFont(QFont("Outfit", 8))
        self.url_label.setStyleSheet("color: #888899; background: transparent;")
        
        # Truncate
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(self.url_label.font())
        elided = metrics.elidedText(url_text, Qt.ElideRight, 260)
        self.url_label.setText(elided)
        text_layout.addWidget(self.url_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Type Badge
        self.badge = QLabel(pl_type, self)
        self.badge.setFont(QFont("Outfit", 8, QFont.Bold))
        self.badge.setStyleSheet(f"background-color: {badge_color}; color: #ffffff; padding: 2px 8px; border-radius: 4px;")
        self.badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.badge)
        
        # Active Checkmark/Star Icon
        if is_active:
            self.active_label = QLabel("⭐", self)
            self.active_label.setFont(QFont("Outfit", 10))
            self.active_label.setStyleSheet("background: transparent;")
            layout.addWidget(self.active_label)

# Playlist Management Dialog
class PlaylistManagerDialog(QDialog):
    playlist_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_t("playlist_manager_title"))
        self.config = config_manager.load_config()
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        self.resize(750, 480)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header Info
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_lbl = QLabel("📂", self)
        icon_lbl.setFont(QFont("Outfit", 18))
        header_layout.addWidget(icon_lbl)
        
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        
        title_lbl = QLabel(_t("playlist_manager_title"), self)
        title_lbl.setFont(QFont("Outfit", 14, QFont.Bold))
        title_lbl.setStyleSheet("color: #ffffff;")
        title_col.addWidget(title_lbl)
        
        sub_lbl = QLabel("Quản lý danh sách kênh IPTV và nguồn phát của bạn.", self)
        sub_lbl.setFont(QFont("Outfit", 9))
        sub_lbl.setStyleSheet("color: #888899;")
        title_col.addWidget(sub_lbl)
        
        header_layout.addLayout(title_col)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Splitter or horizontal layout for split view
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left side column: Search + List
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("🔍 Tìm kiếm playlist...")
        self.search_bar.setObjectName("PlaylistSearch")
        self.search_bar.textChanged.connect(self.populate_list)
        left_col.addWidget(self.search_bar)
        
        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("PlaylistList")
        left_col.addWidget(self.list_widget)
        
        content_layout.addLayout(left_col, 3) # Take 3/4 space
        
        # Right side column: Actions panel
        right_col = QVBoxLayout()
        right_col.setSpacing(10)
        
        actions_title = QLabel("Thao tác", self)
        actions_title.setFont(QFont("Outfit", 10, QFont.Bold))
        actions_title.setStyleSheet("color: #7c4dff;")
        right_col.addWidget(actions_title)
        
        self.btn_add_local = QPushButton(_t("btn_add_file"), self)
        self.btn_add_local.setObjectName("PlaylistActionBtn")
        self.btn_add_local.clicked.connect(self.add_local_playlist)
        right_col.addWidget(self.btn_add_local)
        
        self.btn_add_url = QPushButton(_t("btn_add_url"), self)
        self.btn_add_url.setObjectName("PlaylistActionBtn")
        self.btn_add_url.clicked.connect(self.add_url_playlist)
        right_col.addWidget(self.btn_add_url)
        
        self.btn_add_xtream = QPushButton(_t("btn_add_xtream"), self)
        self.btn_add_xtream.setObjectName("PlaylistActionBtn")
        self.btn_add_xtream.clicked.connect(self.add_xtream_playlist)
        right_col.addWidget(self.btn_add_xtream)
        
        # Horizontal line separator
        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("background-color: #282830; max-height: 1px;")
        right_col.addWidget(sep)
        
        self.btn_edit = QPushButton(_t("btn_edit"), self)
        self.btn_edit.setObjectName("PlaylistActionBtn")
        self.btn_edit.clicked.connect(self.edit_playlist)
        right_col.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton(_t("btn_delete"), self)
        self.btn_delete.setObjectName("PlaylistDeleteBtn")
        self.btn_delete.clicked.connect(self.delete_playlist)
        right_col.addWidget(self.btn_delete)
        
        right_col.addStretch()
        content_layout.addLayout(right_col, 1) # Take 1/4 space
        
        main_layout.addLayout(content_layout)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept_selection)
        self.button_box.rejected.connect(self.reject)
        bottom_layout.addWidget(self.button_box)
        
        main_layout.addLayout(bottom_layout)
        
        self.populate_list()

    def populate_list(self):
        self.list_widget.clear()
        active_url = self.config.get("active_playlist_url", "")
        search_query = self.search_bar.text().strip().lower()
        
        for pl in self.config.get("playlists", []):
            name = pl.get("name", "")
            url = pl.get("url", "")
            
            # Simple text filter
            if search_query and search_query not in name.lower() and search_query not in url.lower():
                continue
                
            is_active = (url == active_url)
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(450, 52))
            item.setData(Qt.UserRole, pl)
            
            self.list_widget.addItem(item)
            
            widget = PlaylistItemWidget(pl, is_active, self)
            self.list_widget.setItemWidget(item, widget)
            
            if is_active:
                self.list_widget.setCurrentItem(item)

    def add_local_playlist(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, _t("select_m3u_file"), "", "M3U Playlists (*.m3u *.m3u8);;All Files (*)"
        )
        if file_path:
            name = os.path.basename(file_path)
            dialog = QDialog(self)
            dialog.setWindowTitle(_t("btn_add_file"))
            dialog.resize(550, 320)
            dialog.setStyleSheet(self.styleSheet())
            
            d_layout = QVBoxLayout(dialog)
            d_layout.setContentsMargins(20, 20, 20, 20)
            d_layout.setSpacing(10)
            
            # Display Name
            lbl_name = QLabel(_t("label_playlist_name"), dialog)
            lbl_name.setFont(QFont("Outfit", 9, QFont.Bold))
            name_input = QLineEdit(dialog)
            name_input.setText(name)
            d_layout.addWidget(lbl_name)
            d_layout.addWidget(name_input)
            
            # File Path
            lbl_path = QLabel(_t("label_file_path"), dialog)
            lbl_path.setFont(QFont("Outfit", 9, QFont.Bold))
            path_input = QLineEdit(dialog)
            path_input.setText(file_path)
            path_input.setReadOnly(True)
            d_layout.addWidget(lbl_path)
            d_layout.addWidget(path_input)
            
            # EPG URL
            lbl_epg = QLabel(_t("label_epg_url"), dialog)
            lbl_epg.setFont(QFont("Outfit", 9, QFont.Bold))
            epg_input = QLineEdit(dialog)
            epg_input.setPlaceholderText("http://example.com/epg.xml")
            d_layout.addWidget(lbl_epg)
            d_layout.addWidget(epg_input)
            
            d_layout.addSpacing(10)
            
            bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            bbox.accepted.connect(dialog.accept)
            bbox.rejected.connect(dialog.reject)
            d_layout.addWidget(bbox)
            
            if dialog.exec() == QDialog.Accepted:
                name = name_input.text().strip()
                if name:
                    new_pl = {
                        "name": name,
                        "url": file_path,
                        "is_local": True,
                        "epg_url": epg_input.text().strip()
                    }
                    if any(p["url"] == file_path for p in self.config["playlists"]):
                        return
                    self.config["playlists"].append(new_pl)
                    config_manager.save_config(self.config)
                    self.populate_list()

    def add_url_playlist(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(_t("add_url_title"))
        dialog.resize(550, 320)
        dialog.setStyleSheet(self.styleSheet())
        
        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(10)
        
        # Name
        lbl_name = QLabel(_t("label_playlist_name"), dialog)
        lbl_name.setFont(QFont("Outfit", 9, QFont.Bold))
        name_input = QLineEdit(dialog)
        name_input.setPlaceholderText(_t("placeholder_playlist_name"))
        d_layout.addWidget(lbl_name)
        d_layout.addWidget(name_input)
        
        # URL
        lbl_url = QLabel(_t("label_url_path"), dialog)
        lbl_url.setFont(QFont("Outfit", 9, QFont.Bold))
        url_input = QLineEdit(dialog)
        url_input.setPlaceholderText("http://example.com/playlist.m3u")
        d_layout.addWidget(lbl_url)
        d_layout.addWidget(url_input)
        
        # EPG
        lbl_epg = QLabel(_t("label_epg_url"), dialog)
        lbl_epg.setFont(QFont("Outfit", 9, QFont.Bold))
        epg_input = QLineEdit(dialog)
        epg_input.setPlaceholderText("http://example.com/epg.xml")
        d_layout.addWidget(lbl_epg)
        d_layout.addWidget(epg_input)
        
        d_layout.addSpacing(10)
        
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        bbox.accepted.connect(dialog.accept)
        bbox.rejected.connect(dialog.reject)
        d_layout.addWidget(bbox)
        
        if dialog.exec() == QDialog.Accepted:
            name = name_input.text().strip()
            url = url_input.text().strip()
            if name and url:
                new_pl = {
                    "name": name,
                    "url": url,
                    "is_local": False,
                    "epg_url": epg_input.text().strip()
                }
                if any(p["url"] == url for p in self.config["playlists"]):
                    return
                self.config["playlists"].append(new_pl)
                config_manager.save_config(self.config)
                self.populate_list()

    def add_xtream_playlist(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(_t("add_xtream_title"))
        dialog.resize(550, 360)
        dialog.setStyleSheet(self.styleSheet())
        
        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(8)
        
        # Name
        lbl_name = QLabel(_t("label_display_name"), dialog)
        lbl_name.setFont(QFont("Outfit", 9, QFont.Bold))
        name_input = QLineEdit(dialog)
        name_input.setPlaceholderText(_t("placeholder_xtream_name"))
        d_layout.addWidget(lbl_name)
        d_layout.addWidget(name_input)
        
        # Host URL
        lbl_host = QLabel(_t("label_server_url"), dialog)
        lbl_host.setFont(QFont("Outfit", 9, QFont.Bold))
        host_input = QLineEdit(dialog)
        host_input.setPlaceholderText("http://domain.com:8080")
        d_layout.addWidget(lbl_host)
        d_layout.addWidget(host_input)
        
        # Username & Password side-by-side
        cred_layout = QHBoxLayout()
        cred_layout.setSpacing(10)
        
        user_col = QVBoxLayout()
        lbl_user = QLabel(_t("label_username"), dialog)
        lbl_user.setFont(QFont("Outfit", 9, QFont.Bold))
        user_input = QLineEdit(dialog)
        user_input.setPlaceholderText(_t("placeholder_username"))
        user_col.addWidget(lbl_user)
        user_col.addWidget(user_input)
        cred_layout.addLayout(user_col)
        
        pass_col = QVBoxLayout()
        lbl_pass = QLabel(_t("label_password"), dialog)
        lbl_pass.setFont(QFont("Outfit", 9, QFont.Bold))
        pass_input = QLineEdit(dialog)
        pass_input.setPlaceholderText(_t("placeholder_password"))
        pass_input.setEchoMode(QLineEdit.Password)
        pass_col.addWidget(lbl_pass)
        pass_col.addWidget(pass_input)
        cred_layout.addLayout(pass_col)
        
        d_layout.addLayout(cred_layout)
        d_layout.addSpacing(10)
        
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        bbox.accepted.connect(dialog.accept)
        bbox.rejected.connect(dialog.reject)
        d_layout.addWidget(bbox)
        
        if dialog.exec() == QDialog.Accepted:
            name = name_input.text().strip()
            host = host_input.text().strip()
            user = user_input.text().strip()
            pwd = pass_input.text().strip()
            
            if name and host and user and pwd:
                playlist_url = f"{host.rstrip('/')}/get.php?username={user}&password={pwd}&output=ts"
                epg_url = f"{host.rstrip('/')}/xmltv.php?username={user}&password={pwd}"
                
                new_pl = {
                    "name": name,
                    "url": playlist_url,
                    "is_local": False,
                    "xtream": {
                        "host": host,
                        "username": user,
                        "password": pwd
                    },
                    "epg_url": epg_url
                }
                
                if any(p["url"] == playlist_url for p in self.config["playlists"]):
                    return
                self.config["playlists"].append(new_pl)
                config_manager.save_config(self.config)
                self.populate_list()

    def edit_playlist(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, _t("error_title"), _t("select_playlist_to_edit"))
            return
            
        pl = current_item.data(Qt.UserRole)
        pl_idx = -1
        for idx, p in enumerate(self.config["playlists"]):
            if p["url"] == pl["url"]:
                pl_idx = idx
                break
                
        if pl_idx == -1:
            return
            
        old_url = pl.get("url", "")
        
        # 1. Edit Xtream Codes playlist
        if pl.get("xtream"):
            dialog = QDialog(self)
            dialog.setWindowTitle(_t("edit_xtream_title"))
            dialog.resize(550, 360)
            dialog.setStyleSheet(self.styleSheet())
            
            d_layout = QVBoxLayout(dialog)
            d_layout.setContentsMargins(20, 20, 20, 20)
            d_layout.setSpacing(8)
            
            lbl_name = QLabel(_t("label_display_name"), dialog)
            lbl_name.setFont(QFont("Outfit", 9, QFont.Bold))
            name_input = QLineEdit(dialog)
            name_input.setText(pl.get("name", ""))
            d_layout.addWidget(lbl_name)
            d_layout.addWidget(name_input)
            
            xtream_data = pl.get("xtream", {})
            lbl_host = QLabel(_t("label_server_url"), dialog)
            lbl_host.setFont(QFont("Outfit", 9, QFont.Bold))
            host_input = QLineEdit(dialog)
            host_input.setText(xtream_data.get("host", ""))
            d_layout.addWidget(lbl_host)
            d_layout.addWidget(host_input)
            
            # Credentials Row
            cred_layout = QHBoxLayout()
            cred_layout.setSpacing(10)
            
            user_col = QVBoxLayout()
            lbl_user = QLabel(_t("label_username"), dialog)
            lbl_user.setFont(QFont("Outfit", 9, QFont.Bold))
            user_input = QLineEdit(dialog)
            user_input.setText(xtream_data.get("username", ""))
            user_col.addWidget(lbl_user)
            user_col.addWidget(user_input)
            cred_layout.addLayout(user_col)
            
            pass_col = QVBoxLayout()
            lbl_pass = QLabel(_t("label_password"), dialog)
            lbl_pass.setFont(QFont("Outfit", 9, QFont.Bold))
            pass_input = QLineEdit(dialog)
            pass_input.setText(xtream_data.get("password", ""))
            pass_input.setEchoMode(QLineEdit.Password)
            pass_col.addWidget(lbl_pass)
            pass_col.addWidget(pass_input)
            cred_layout.addLayout(pass_col)
            
            d_layout.addLayout(cred_layout)
            d_layout.addSpacing(10)
            
            bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            bbox.accepted.connect(dialog.accept)
            bbox.rejected.connect(dialog.reject)
            d_layout.addWidget(bbox)
            
            if dialog.exec() == QDialog.Accepted:
                name = name_input.text().strip()
                host = host_input.text().strip()
                user = user_input.text().strip()
                pwd = pass_input.text().strip()
                
                if name and host and user and pwd:
                    playlist_url = f"{host.rstrip('/')}/get.php?username={user}&password={pwd}&output=ts"
                    epg_url = f"{host.rstrip('/')}/xmltv.php?username={user}&password={pwd}"
                    
                    self.config["playlists"][pl_idx] = {
                        "name": name,
                        "url": playlist_url,
                        "is_local": False,
                        "xtream": {
                            "host": host,
                            "username": user,
                            "password": pwd
                        },
                        "epg_url": epg_url
                    }
                    if self.config.get("active_playlist_url") == old_url:
                        self.config["active_playlist_url"] = playlist_url
                    config_manager.save_config(self.config)
                    self.populate_list()
                    
        # 2. Edit URL playlist
        elif not pl.get("is_local"):
            dialog = QDialog(self)
            dialog.setWindowTitle(_t("edit_url_title"))
            dialog.resize(550, 320)
            dialog.setStyleSheet(self.styleSheet())
            
            d_layout = QVBoxLayout(dialog)
            d_layout.setContentsMargins(20, 20, 20, 20)
            d_layout.setSpacing(10)
            
            lbl_name = QLabel(_t("label_playlist_name"), dialog)
            lbl_name.setFont(QFont("Outfit", 9, QFont.Bold))
            name_input = QLineEdit(dialog)
            name_input.setText(pl.get("name", ""))
            d_layout.addWidget(lbl_name)
            d_layout.addWidget(name_input)
            
            lbl_url = QLabel(_t("label_url_path"), dialog)
            lbl_url.setFont(QFont("Outfit", 9, QFont.Bold))
            url_input = QLineEdit(dialog)
            url_input.setText(pl.get("url", ""))
            d_layout.addWidget(lbl_url)
            d_layout.addWidget(url_input)
            
            lbl_epg = QLabel(_t("label_epg_url"), dialog)
            lbl_epg.setFont(QFont("Outfit", 9, QFont.Bold))
            epg_input = QLineEdit(dialog)
            epg_input.setText(pl.get("epg_url", ""))
            d_layout.addWidget(lbl_epg)
            d_layout.addWidget(epg_input)
            
            d_layout.addSpacing(10)
            
            bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            bbox.accepted.connect(dialog.accept)
            bbox.rejected.connect(dialog.reject)
            d_layout.addWidget(bbox)
            
            if dialog.exec() == QDialog.Accepted:
                name = name_input.text().strip()
                url = url_input.text().strip()
                epg = epg_input.text().strip()
                if name and url:
                    self.config["playlists"][pl_idx] = {
                        "name": name,
                        "url": url,
                        "is_local": False,
                        "epg_url": epg
                    }
                    if self.config.get("active_playlist_url") == old_url:
                        self.config["active_playlist_url"] = url
                    config_manager.save_config(self.config)
                    self.populate_list()
                    
        # 3. Edit Local playlist
        else:
            dialog = QDialog(self)
            dialog.setWindowTitle(_t("edit_local_title"))
            dialog.resize(550, 320)
            dialog.setStyleSheet(self.styleSheet())
            
            d_layout = QVBoxLayout(dialog)
            d_layout.setContentsMargins(20, 20, 20, 20)
            d_layout.setSpacing(10)
            
            lbl_name = QLabel(_t("label_display_name"), dialog)
            lbl_name.setFont(QFont("Outfit", 9, QFont.Bold))
            name_input = QLineEdit(dialog)
            name_input.setText(pl.get("name", ""))
            d_layout.addWidget(lbl_name)
            d_layout.addWidget(name_input)
            
            lbl_path = QLabel(_t("label_file_path"), dialog)
            lbl_path.setFont(QFont("Outfit", 9, QFont.Bold))
            path_input = QLineEdit(dialog)
            path_input.setText(pl.get("url", ""))
            d_layout.addWidget(lbl_path)
            d_layout.addWidget(path_input)
            
            lbl_epg = QLabel(_t("label_epg_url"), dialog)
            lbl_epg.setFont(QFont("Outfit", 9, QFont.Bold))
            epg_input = QLineEdit(dialog)
            epg_input.setText(pl.get("epg_url", ""))
            d_layout.addWidget(lbl_epg)
            d_layout.addWidget(epg_input)
            
            d_layout.addSpacing(10)
            
            bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            bbox.accepted.connect(dialog.accept)
            bbox.rejected.connect(dialog.reject)
            d_layout.addWidget(bbox)
            
            if dialog.exec() == QDialog.Accepted:
                name = name_input.text().strip()
                path = path_input.text().strip()
                epg = epg_input.text().strip()
                if name and path:
                    self.config["playlists"][pl_idx] = {
                        "name": name,
                        "url": path,
                        "is_local": True,
                        "epg_url": epg
                    }
                    if self.config.get("active_playlist_url") == old_url:
                        self.config["active_playlist_url"] = path
                    config_manager.save_config(self.config)
                    self.populate_list()

    def delete_playlist(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
            
        pl = current_item.data(Qt.UserRole)
        url = pl.get("url", "")
        
        if len(self.config["playlists"]) <= 1:
            QMessageBox.warning(self, "Lỗi", "Không thể xóa playlist duy nhất.")
            return
            
        self.config["playlists"] = [p for p in self.config["playlists"] if p["url"] != url]
        
        if self.config.get("active_playlist_url") == url:
            self.config["active_playlist_url"] = self.config["playlists"][0]["url"]
            
        config_manager.save_config(self.config)
        self.populate_list()

    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            pl = current_item.data(Qt.UserRole)
            self.config["active_playlist_url"] = pl.get("url", "")
            config_manager.save_config(self.config)
            self.playlist_changed.emit()
        self.accept()

    def apply_theme(self):
        style = """
            QDialog {
                background-color: #18181c;
                color: #e0e0e6;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit#PlaylistSearch {
                background-color: #121214;
                border: 1px solid #282830;
                border-radius: 6px;
                padding: 8px 12px;
                color: #ffffff;
                font-family: "Outfit";
                font-size: 13px;
            }
            QLineEdit#PlaylistSearch:focus {
                border: 1px solid #7c4dff;
            }
            QListWidget#PlaylistList {
                background-color: #121214;
                border: 1px solid #282830;
                border-radius: 8px;
                color: #e0e0e6;
                padding: 5px;
            }
            QListWidget#PlaylistList::item {
                border-bottom: 1px solid #1a1a20;
                border-radius: 6px;
                margin-bottom: 2px;
            }
            QListWidget#PlaylistList::item:hover {
                background-color: #232329;
            }
            QListWidget#PlaylistList::item:selected {
                background-color: #2a2240;
                border-left: 3px solid #7c4dff;
            }
            QPushButton#PlaylistActionBtn {
                background-color: #232329;
                border: 1px solid #282830;
                border-radius: 6px;
                color: #e0e0e6;
                padding: 8px 12px;
                font-family: "Outfit";
                font-size: 12px;
                text-align: left;
            }
            QPushButton#PlaylistActionBtn:hover {
                background-color: #2e2e38;
                border: 1px solid #3d3d4a;
                color: #ffffff;
            }
            QPushButton#PlaylistActionBtn:pressed {
                background-color: #1e1e24;
            }
            QPushButton#PlaylistDeleteBtn {
                background-color: #2a1b1b;
                border: 1px solid #4a2828;
                border-radius: 6px;
                color: #ff5252;
                padding: 8px 12px;
                font-family: "Outfit";
                font-size: 12px;
                text-align: left;
            }
            QPushButton#PlaylistDeleteBtn:hover {
                background-color: #3d2323;
                border: 1px solid #663333;
                color: #ff8a8a;
            }
            QPushButton#PlaylistDeleteBtn:pressed {
                background-color: #201313;
            }
            QDialogButtonBox QPushButton {
                background-color: #232329;
                border: 1px solid #282830;
                border-radius: 6px;
                color: #ffffff;
                padding: 6px 16px;
                font-family: "Outfit";
                min-width: 80px;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #2e2e38;
                border: 1px solid #3d3d4a;
            }
            QDialogButtonBox QPushButton[text="OK"], QDialogButtonBox QPushButton[text="Ok"] {
                background-color: #7c4dff;
                border: 1px solid #7c4dff;
            }
            QDialogButtonBox QPushButton[text="OK"]:hover, QDialogButtonBox QPushButton[text="Ok"]:hover {
                background-color: #9575cd;
            }
            QLineEdit {
                background-color: #121214;
                border: 1px solid #282830;
                border-radius: 6px;
                padding: 6px;
                color: #ffffff;
            }
        """
        self.setStyleSheet(style)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_t("settings_title"))
        self.config = config_manager.load_config()
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        self.setFixedSize(480, 420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Header Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_label = QLabel("⚙️", self)
        icon_label.setFont(QFont("Outfit", 16))
        header_layout.addWidget(icon_label)
        
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        
        title_label = QLabel(_t("settings_title"), self)
        title_label.setFont(QFont("Outfit", 13, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        
        desc_label = QLabel(_t("settings_desc"), self)
        desc_label.setFont(QFont("Outfit", 9))
        desc_label.setStyleSheet("color: #888896;")
        
        title_col.addWidget(title_label)
        title_col.addWidget(desc_label)
        header_layout.addLayout(title_col)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Separation Line
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.06); height: 1px; border: none;")
        layout.addWidget(line)
        
        # Form Container
        form_widget = QWidget(self)
        form_widget.setObjectName("FormContainer")
        form = QFormLayout(form_widget)
        form.setContentsMargins(15, 15, 15, 15)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Cache Preset Slider
        self.preset_slider = QSlider(Qt.Horizontal, self)
        self.preset_slider.setMinimum(1)
        self.preset_slider.setMaximum(5)
        self.preset_slider.setValue(self.config.get("buffer_size_preset", 2))
        
        slider_container = QHBoxLayout()
        slider_container.addWidget(self.preset_slider)
        
        self.preset_label = QLabel(self)
        self.preset_label.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 11px; min-width: 50px;")
        self.update_preset_text(self.preset_slider.value())
        self.preset_slider.valueChanged.connect(self.update_preset_text)
        slider_container.addWidget(self.preset_label)
        
        lbl_cache = QLabel(_t("cache"), self)
        lbl_cache.setStyleSheet("font-weight: 500;")
        form.addRow(lbl_cache, slider_container)
        
        # Sleep timer option
        self.sleep_combo = QComboBox(self)
        no_timer_text = _t("no_timer")
        minutes_text = _t("minutes")
        self.sleep_combo.addItems([
            no_timer_text,
            f"15 {minutes_text}",
            f"30 {minutes_text}",
            f"45 {minutes_text}",
            f"60 {minutes_text}",
            f"90 {minutes_text}",
            f"120 {minutes_text}"
        ])
        
        current_sleep_remaining = 0
        if self.parent() and hasattr(self.parent(), 'sleep_timer_remaining'):
            current_sleep_remaining = self.parent().sleep_timer_remaining
            
        if current_sleep_remaining > 0:
            minutes = round(current_sleep_remaining / 60)
            self.sleep_combo.addItem(_t("timer_set").format(minutes))
            self.sleep_combo.setCurrentIndex(self.sleep_combo.count() - 1)
            
        lbl_sleep = QLabel(_t("sleep_timer"), self)
        lbl_sleep.setStyleSheet("font-weight: 500;")
        form.addRow(lbl_sleep, self.sleep_combo)
        
        # Hardware acceleration
        self.chk_hwdec = QCheckBox(_t("hw_dec_checkbox"), self)
        self.chk_hwdec.setChecked(self.config.get("hwdec_enabled", True))
        
        lbl_hw = QLabel(_t("hw_dec"), self)
        lbl_hw.setStyleSheet("font-weight: 500;")
        form.addRow(lbl_hw, self.chk_hwdec)
        
        # Language Selection
        self.lang_combo = QComboBox(self)
        self.lang_combo.addItems([
            "Tiếng Việt (VI)",
            "English (EN)",
            "简体中文 (CN)"
        ])
        lang_code = self.config.get("language", "vi").lower()
        if lang_code == "en":
            self.lang_combo.setCurrentIndex(1)
        elif lang_code == "cn":
            self.lang_combo.setCurrentIndex(2)
        else:
            self.lang_combo.setCurrentIndex(0)
            
        lbl_lang = QLabel(_t("language"), self)
        lbl_lang.setStyleSheet("font-weight: 500;")
        form.addRow(lbl_lang, self.lang_combo)
        
        layout.addWidget(form_widget)
        
        # Separation Line
        line2 = QFrame(self)
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("background-color: rgba(255, 255, 255, 0.06); height: 1px; border: none;")
        layout.addWidget(line2)
        
        # Custom Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton(_t("cancel"), self)
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton(_t("save"), self)
        self.btn_save.setObjectName("BtnSave")
        self.btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_save.clicked.connect(self.save_settings)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def update_preset_text(self, value):
        text = _t(f"buffer_preset_{value}")
        self.preset_label.setText(text)

    def save_settings(self):
        preset_val = self.preset_slider.value()
        _, bytes_val = CACHE_PRESETS.get(preset_val)
        self.config["buffer_size_preset"] = preset_val
        self.config["buffer_size_bytes"] = bytes_val
        
        # Save HW Dec setting
        hwdec_val = self.chk_hwdec.isChecked()
        self.config["hwdec_enabled"] = hwdec_val
        
        # Save Language setting
        lang_idx = self.lang_combo.currentIndex()
        if lang_idx == 1:
            lang_code = "en"
        elif lang_idx == 2:
            lang_code = "cn"
        else:
            lang_code = "vi"
        self.config["language"] = lang_code
        
        config_manager.save_config(self.config)
        load_app_language()
        
        if self.parent():
            # Trigger language re-translation on main window immediately
            if hasattr(self.parent(), "retranslate_ui"):
                self.parent().retranslate_ui()
                
            if hasattr(self.parent(), "update_player_cache_settings"):
                self.parent().update_player_cache_settings()
            # Apply HW Dec state to all player frames immediately
            if hasattr(self.parent(), "player_frames"):
                for frame in self.parent().player_frames:
                    if frame.mpv_widget:
                        frame.mpv_widget.toggle_hwdec(hwdec_val)
                # Update controls bar badge state
                if hasattr(self.parent(), "btn_hwdec"):
                    self.parent().btn_hwdec.setChecked(hwdec_val)
                    self.parent().btn_hwdec.setText(_t("hw_on") if hwdec_val else _t("hw_off"))
            
        # Sleep timer selection (using indices to be language-independent)
        sleep_idx = self.sleep_combo.currentIndex()
        if self.parent() and hasattr(self.parent(), 'set_sleep_timer'):
            minutes = 0
            if sleep_idx == 1:
                minutes = 15
            elif sleep_idx == 2:
                minutes = 30
            elif sleep_idx == 3:
                minutes = 45
            elif sleep_idx == 4:
                minutes = 60
            elif sleep_idx == 5:
                minutes = 90
            elif sleep_idx == 6:
                minutes = 120
                
            if sleep_idx == 0:
                self.parent().cancel_sleep_timer()
            elif sleep_idx < 7:
                self.parent().set_sleep_timer(minutes)
                
        self.accept()

    def apply_theme(self):
        style = """
            QDialog {
                background-color: #0e0e12;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QLabel {
                color: #e0e0e6;
                font-family: 'Outfit';
                font-size: 12px;
            }
            QWidget#FormContainer {
                background-color: rgba(20, 20, 30, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 12px;
            }
            QComboBox {
                background-color: rgba(10, 10, 15, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px 12px;
                color: #ffffff;
                font-family: 'Outfit';
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: rgba(124, 77, 255, 0.5);
            }
            QComboBox:focus {
                border: 1px solid #7c4dff;
            }
            QComboBox::drop-down {
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
            }
            QComboBox QAbstractItemView {
                background-color: #121216;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                selection-background-color: #7c4dff;
                selection-color: #ffffff;
                color: #e0e0e6;
            }
            QCheckBox {
                spacing: 8px;
                color: #e0e0e6;
                font-family: 'Outfit';
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                background-color: rgba(30, 30, 38, 0.4);
            }
            QCheckBox::indicator:hover {
                border-color: #7c4dff;
                background-color: rgba(124, 77, 255, 0.05);
            }
            QCheckBox::indicator:checked {
                border-color: #7c4dff;
                background-color: #7c4dff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(255, 255, 255, 0.06);
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #7c4dff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #7c4dff;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #7c4dff;
                border-color: #b388ff;
            }
            QPushButton {
                font-family: 'Outfit';
                font-size: 12px;
                font-weight: 500;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton#BtnCancel {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #e0e0e6;
            }
            QPushButton#BtnCancel:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
            QPushButton#BtnSave {
                background-color: #7c4dff;
                border: none;
                color: #ffffff;
            }
            QPushButton#BtnSave:hover {
                background-color: #9e70ff;
            }
        """
        self.setStyleSheet(style)




class K20IPTVPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load FontAwesome 6 Solid Font for UI Icons
        from PySide6.QtGui import QFontDatabase
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                _script_dir = sys._MEIPASS
            else:
                _script_dir = os.path.dirname(sys.executable)
        else:
            _script_dir = os.path.dirname(os.path.abspath(__file__))
        fa_path = os.path.join(_script_dir, "fa-solid-900.ttf")
        if os.path.exists(fa_path):
            font_id = QFontDatabase.addApplicationFont(fa_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    print(f"[+] Loaded icon font family: {font_families[0]}")
                else:
                    print("[+] Loaded icon font family but name empty")
            else:
                print("[-] Failed to add FontAwesome application font")
        else:
            print(f"[-] FontAwesome font not found at {fa_path}")
            
        self.setWindowTitle("K20 IPTV Player")
        self.resize(1400, 800)
        self.setMinimumSize(1000, 600)
        
        self.config = config_manager.load_config()
        
        self.channels = []
        self.filtered_channels = []
        self.current_view = "live" # "live", "favorites", "history"
        self.current_playlist_path = ""
        self.is_fullscreen = False
        
        # Multi-view configurations
        self.active_player_idx = 0
        self.num_screens = 1 # 1 or 4
        self.player_frames = []
        self.is_app_muted = False
        self.current_player_duration = 0
        self._user_seeking = False
        self.connected_widget = None
        
        # Channel active/dead statuses and latencies
        self.channel_statuses = {}
        self.channel_latencies = {}
        self.checker_thread = None
        
        # EPG Setup
        self.epg_thread = None
        self.playlist_worker = None
        
        # Sleep Timer Setup
        self.sleep_timer_remaining = 0
        self.sleep_countdown_timer = QTimer(self)
        self.sleep_countdown_timer.setInterval(1000)
        self.sleep_countdown_timer.timeout.connect(self.update_sleep_timer)
        
        self.setup_ui()
        self.setup_players()
        # Position the glass controls bar now and after the first paint
        QTimer.singleShot(0, self._reposition_glass_controls)
        QTimer.singleShot(200, self._reposition_glass_controls)
        
        # Load active playlist
        active_url = self.config.get("active_playlist_url", "playlist.m3u")
        self.load_playlist(active_url)
        
        # Context menu
        self.channel_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.channel_list.customContextMenuRequested.connect(self.show_channel_context_menu)
        
        # Register window-level keyboard shortcuts to avoid native focus swallowing issues
        self.setup_shortcuts()
        
        # Restore last session state (channels, volume, layout, filters)
        self.restore_session_state()
        
        # Translate UI elements to active language
        self.retranslate_ui()

    def retranslate_ui(self):
        # Update Window Title
        self.setWindowTitle("K20 IPTV Player")
        
        # Sidebar Tooltips
        if hasattr(self, 'btn_live'):
            self.btn_live.setToolTip(_t("live_tv_tooltip"))
        if hasattr(self, 'btn_fav'):
            self.btn_fav.setToolTip(_t("favorites_tooltip"))
        if hasattr(self, 'btn_history'):
            self.btn_history.setToolTip(_t("history_tooltip"))
        if hasattr(self, 'btn_open'):
            self.btn_open.setToolTip(_t("playlist_manager_tooltip"))
        if hasattr(self, 'btn_help'):
            self.btn_help.setToolTip(_t("shortcuts_tooltip"))
        if hasattr(self, 'btn_settings'):
            self.btn_settings.setToolTip(_t("settings_tooltip"))
            
        # Channel Panel
        if hasattr(self, 'lbl_view_title'):
            view_name = getattr(self, 'current_view', 'live')
            if view_name == 'favorites':
                self.lbl_view_title.setText(_t("favorites_title").upper())
            elif view_name == 'history':
                self.lbl_view_title.setText(_t("recent_title").upper())
            else:
                self.lbl_view_title.setText(_t("live_tv_title").upper())
                
        if hasattr(self, 'search_bar'):
            if getattr(self, 'playlist_worker', None) and self.playlist_worker.isRunning():
                self.search_bar.setPlaceholderText(_t("loading_playlist_placeholder"))
            else:
                self.search_bar.setPlaceholderText(_t("search_placeholder"))
            
        if hasattr(self, 'cat_selector'):
            if self.cat_selector.count() > 0:
                self.cat_selector.setItemText(0, _t("all_categories"))
                
        if hasattr(self, 'sort_selector'):
            self.sort_selector.blockSignals(True)
            current_sort = self.sort_selector.currentIndex()
            self.sort_selector.clear()
            self.sort_selector.addItems([
                _t("default_sort"),
                _t("az_sort"),
                _t("latency_sort")
            ])
            if current_sort >= 0 and current_sort < self.sort_selector.count():
                self.sort_selector.setCurrentIndex(current_sort)
            self.sort_selector.blockSignals(False)
            
        if hasattr(self, 'btn_check_status'):
            self.btn_check_status.setToolTip(_t("check_status"))
            
        # Resolution filter buttons
        if hasattr(self, 'res_buttons'):
            for key, btn in self.res_buttons.items():
                if key == "all":
                    btn.setText(_t("all"))
                    
        # Header bar items
        if hasattr(self, 'btn_toggle_sidebar'):
            self.btn_toggle_sidebar.setToolTip(_t("toggle_sidebar_tooltip"))
        if hasattr(self, 'lbl_channel_title'):
            t_text = self.lbl_channel_title.text()
            if "Chưa phát kênh nào" in t_text or "No channels playing" in t_text or "未播放任何频道" in t_text or _t("no_channel_playing") in t_text:
                self.lbl_channel_title.setText(_t("no_channel_playing"))
            elif "Chưa chọn kênh" in t_text or "No channel selected" in t_text or "未选择频道" in t_text or "📺" in t_text:
                self.lbl_channel_title.setText(_t("player_no_channel").format(self.active_player_idx + 1))
            elif "Đã dừng" in t_text or "Stopped" in t_text or "已停止" in t_text:
                self.lbl_channel_title.setText(_t("player_stopped").format(self.active_player_idx + 1))
        if hasattr(self, 'btn_toggle_epg'):
            self.btn_toggle_epg.setToolTip(_t("toggle_epg_tooltip"))
            epg_visible = getattr(self, 'epg_panel', None) and self.epg_panel.isVisible()
            self.btn_toggle_epg.setText(_t("epg_hide_btn") if epg_visible else _t("epg_schedule_btn"))
            
        # Controls bar items
        if hasattr(self, 'btn_seek_back'):
            self.btn_seek_back.setToolTip(_t("seek_back_tooltip"))
        if hasattr(self, 'btn_seek_forward'):
            self.btn_seek_forward.setToolTip(_t("seek_forward_tooltip"))
        if hasattr(self, 'view_combo'):
            self.view_combo.blockSignals(True)
            current_view_idx = self.view_combo.currentIndex()
            self.view_combo.clear()
            self.view_combo.addItems([_t("view_1_screen"), _t("view_2_screens"), _t("view_4_screens")])
            if current_view_idx >= 0 and current_view_idx < self.view_combo.count():
                self.view_combo.setCurrentIndex(current_view_idx)
            self.view_combo.blockSignals(False)
        if hasattr(self, 'btn_audio'):
            self.btn_audio.setToolTip(_t("audio_tooltip"))
        if hasattr(self, 'btn_subs'):
            self.btn_subs.setToolTip(_t("subs_tooltip"))
        if hasattr(self, 'btn_screenshot'):
            self.btn_screenshot.setToolTip(_t("screenshot_tooltip"))
        if hasattr(self, 'btn_stats'):
            self.btn_stats.setToolTip(_t("stats_tooltip"))
            
        # EPG panel title
        if hasattr(self, 'epg_panel'):
            for child in self.epg_panel.findChildren(QLabel):
                if child.objectName() == "ViewTitleLabel":
                    child.setText(_t("epg_panel_title"))
                    
        # Shortcuts HUD
        if hasattr(self, 'hud') and self.hud:
            self.hud.deleteLater()
            self.hud = ShortcutsHUD(self.central_widget)

    def setup_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Left Sidebar
        self.setup_sidebar()
        
        # Splitter to divide Middle Panel, Right Player Area, and EPG Schedule Panel
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.main_layout.addWidget(self.splitter)
        
        # 2. Middle Panel (Channel List)
        self.setup_channel_panel()
        
        # 3. Right Panel (Player Area)
        self.setup_player_panel()
        
        # 4. Far Right Panel (EPG Schedule Panel)
        self.setup_epg_schedule_panel()
        
        self.splitter.addWidget(self.channel_panel)
        self.splitter.addWidget(self.player_panel)
        self.splitter.addWidget(self.epg_panel)
        
        self.epg_panel.hide() # Hidden by default
        self.splitter.setSizes([310, 840, 0])
        
        # Shortcuts overlay HUD
        self.hud = ShortcutsHUD(self.central_widget)
        
        self.apply_theme()

    def setup_sidebar(self):
        self.sidebar = QFrame(self)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(70)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignHCenter)
        
        logo_label = QLabel("K20", self.sidebar)
        logo_label.setObjectName("LogoLabel")
        logo_label.setFont(QFont("Outfit", 16, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        line = QFrame(self.sidebar)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("SidebarLine")
        layout.addWidget(line)
        
        self.btn_live = QPushButton("\uf26c", self.sidebar)
        self.btn_live.setToolTip(_t("live_tv_tooltip"))
        self.btn_live.setObjectName("SidebarBtnActive")
        self.btn_live.setFixedSize(50, 50)
        self.btn_live.clicked.connect(lambda: self.switch_view("live"))
        layout.addWidget(self.btn_live)
        
        self.btn_fav = QPushButton("\uf005", self.sidebar)
        self.btn_fav.setToolTip(_t("favorites_tooltip"))
        self.btn_fav.setObjectName("SidebarBtn")
        self.btn_fav.setFixedSize(50, 50)
        self.btn_fav.clicked.connect(lambda: self.switch_view("favorites"))
        layout.addWidget(self.btn_fav)
        
        self.btn_history = QPushButton("\uf1da", self.sidebar)
        self.btn_history.setToolTip(_t("history_tooltip"))
        self.btn_history.setObjectName("SidebarBtn")
        self.btn_history.setFixedSize(50, 50)
        self.btn_history.clicked.connect(lambda: self.switch_view("history"))
        layout.addWidget(self.btn_history)
        
        layout.addStretch()
        
        self.btn_open = QPushButton("\uf07c", self.sidebar)
        self.btn_open.setToolTip(_t("playlist_manager_tooltip"))
        self.btn_open.setObjectName("SidebarBtn")
        self.btn_open.setFixedSize(50, 50)
        self.btn_open.clicked.connect(self.open_playlist_manager)
        layout.addWidget(self.btn_open)
        
        self.btn_help = QPushButton("\uf059", self.sidebar)
        self.btn_help.setToolTip(_t("shortcuts_tooltip"))
        self.btn_help.setObjectName("SidebarBtn")
        self.btn_help.setFixedSize(50, 50)
        self.btn_help.clicked.connect(self.toggle_shortcuts_hud)
        layout.addWidget(self.btn_help)
        
        self.btn_settings = QPushButton("\uf013", self.sidebar)
        self.btn_settings.setToolTip(_t("settings_tooltip"))
        self.btn_settings.setObjectName("SidebarBtn")
        self.btn_settings.setFixedSize(50, 50)
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        layout.addWidget(self.btn_settings)
        
        self.main_layout.addWidget(self.sidebar)

    def setup_channel_panel(self):
        self.channel_panel = QFrame(self)
        self.channel_panel.setObjectName("ChannelPanel")
        
        layout = QVBoxLayout(self.channel_panel)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(12)
        
        self.lbl_view_title = QLabel(_t("live_tv_title"), self.channel_panel)
        self.lbl_view_title.setFont(QFont("Outfit", 12, QFont.Bold))
        self.lbl_view_title.setObjectName("ViewTitleLabel")
        layout.addWidget(self.lbl_view_title)
        
        self.search_bar = QLineEdit(self.channel_panel)
        self.search_bar.setPlaceholderText(_t("search_placeholder"))
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.textChanged.connect(self.filter_channels)
        layout.addWidget(self.search_bar)
        
        # Horizontal Layout for Category selector & Sort selector
        combo_layout = QHBoxLayout()
        combo_layout.setSpacing(8)
        
        self.cat_selector = QComboBox(self.channel_panel)
        self.cat_selector.setObjectName("CategorySelector")
        self.cat_selector.addItem(_t("all_categories"))
        self.cat_selector.currentTextChanged.connect(self.on_category_changed)
        combo_layout.addWidget(self.cat_selector)
        
        self.sort_selector = QComboBox(self.channel_panel)
        self.sort_selector.setObjectName("CategorySelector")
        self.sort_selector.addItems([_t("default_sort"), _t("az_sort"), _t("latency_sort")])
        self.sort_selector.currentTextChanged.connect(self.filter_channels)
        self.sort_selector.setFixedWidth(125)
        combo_layout.addWidget(self.sort_selector)
        
        # Manual status check button
        self.btn_check_status = QPushButton("⚡", self.channel_panel)
        self.btn_check_status.setToolTip(_t("check_status"))
        self.btn_check_status.setObjectName("GlassBtn")
        self.btn_check_status.setFixedSize(30, 30)
        self.btn_check_status.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_check_status.clicked.connect(self.start_channel_checker)
        combo_layout.addWidget(self.btn_check_status)
        
        layout.addLayout(combo_layout)
        
        # Resolution filter chips
        self.res_filter_layout = QHBoxLayout()
        self.res_filter_layout.setSpacing(6)
        
        self.res_filters = {
            "all": _t("all"),
            "4k": "4K",
            "fhd": "FHD",
            "hd": "HD"
        }
        self.active_res_filter = "all"
        self.res_buttons = {}
        
        for key, label in self.res_filters.items():
            btn = QPushButton(label, self.channel_panel)
            btn.setCheckable(True)
            btn.setChecked(key == "all")
            btn.setObjectName("FilterChipActive" if key == "all" else "FilterChip")
            btn.clicked.connect(lambda checked=False, k=key: self.set_resolution_filter(k))
            self.res_filter_layout.addWidget(btn)
            self.res_buttons[key] = btn
            
        layout.addLayout(self.res_filter_layout)
        
        self.channel_list = QListWidget(self.channel_panel)
        self.channel_list.setObjectName("ChannelList")
        self.channel_list.itemClicked.connect(self.on_channel_selected)
        self.channel_list.verticalScrollBar().valueChanged.connect(self.on_list_scroll)
        layout.addWidget(self.channel_list)

    def set_resolution_filter(self, key):
        self.active_res_filter = key
        for k, btn in self.res_buttons.items():
            btn.setChecked(k == key)
            btn.setObjectName("FilterChipActive" if k == key else "FilterChip")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.filter_channels()

    def setup_player_panel(self):
        self.player_panel = QFrame(self)
        self.player_panel.setObjectName("PlayerPanel")
        
        layout = QVBoxLayout(self.player_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Compact glass header bar
        self.header_bar = QFrame(self.player_panel)
        self.header_bar.setObjectName("HeaderBar")
        self.header_bar.setFixedHeight(54)
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(12)
        
        # Sidebar collapse toggle button
        self.btn_toggle_sidebar = QPushButton("☰", self.header_bar)
        self.btn_toggle_sidebar.setObjectName("HeaderToggleBtn")
        self.btn_toggle_sidebar.setFixedSize(34, 34)
        self.btn_toggle_sidebar.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_toggle_sidebar.setToolTip(_t("toggle_sidebar_tooltip"))
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar_panel)
        header_layout.addWidget(self.btn_toggle_sidebar)
        
        # Channel icon placeholder
        self.lbl_ch_dot = QLabel("●", self.header_bar)
        self.lbl_ch_dot.setStyleSheet("color: #00e5ff; font-size: 10px;")
        header_layout.addWidget(self.lbl_ch_dot)
        
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        self.lbl_channel_title = QLabel(_t("no_channel_playing"), self.header_bar)
        self.lbl_channel_title.setObjectName("ChannelTitle")
        self.lbl_channel_title.setFont(QFont("Outfit", 11, QFont.Bold))
        info_col.addWidget(self.lbl_channel_title)
        
        self.lbl_epg_now = QLabel("", self.header_bar)
        self.lbl_epg_now.setObjectName("EpgNowLabel")
        self.lbl_epg_now.setFont(QFont("Outfit", 9))
        self.lbl_epg_now.setStyleSheet("color: #00e5ff;")
        info_col.addWidget(self.lbl_epg_now)
        header_layout.addLayout(info_col)
        
        header_layout.addStretch()
        
        # EPG schedule toggle button
        self.btn_toggle_epg = QPushButton(_t("epg_schedule_btn"), self.header_bar)
        self.btn_toggle_epg.setObjectName("HeaderEpgBtn")
        self.btn_toggle_epg.setFixedHeight(34)
        self.btn_toggle_epg.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_toggle_epg.setToolTip(_t("toggle_epg_tooltip"))
        self.btn_toggle_epg.clicked.connect(self.toggle_epg_panel)
        header_layout.addWidget(self.btn_toggle_epg)
        
        # Sleep timer label in header
        self.lbl_sleep_status = QLabel("", self.header_bar)
        self.lbl_sleep_status.setStyleSheet(
            "color: #ffb300; font-weight: bold; font-size: 12px;"
            "background: rgba(0,0,0,120); border-radius: 6px; padding: 2px 8px;"
        )
        self.lbl_sleep_status.hide()
        header_layout.addWidget(self.lbl_sleep_status)
        
        layout.addWidget(self.header_bar)
        
        # Player Grid Container — fills remaining space, glass overlay inside
        self.player_container = QWidget(self.player_panel)
        self.player_container.setObjectName("PlayerContainer")
        self.player_container.setMouseTracking(True)
        self.grid_layout = QGridLayout(self.player_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(4)
        layout.addWidget(self.player_container)
        
        # ── SOLID CONTROLS BAR (Floating Overlay) ──────────────────────────
        self.controls_bar = QFrame(self.player_panel)
        self.controls_bar.setAttribute(Qt.WA_NativeWindow, True)
        self.controls_bar.setObjectName("GlassControls")
        self.controls_bar.setFixedHeight(90)
        # Removed layout.addWidget(self.controls_bar) to make it a floating overlay
        self._controls_visible = True
        self._hide_controls_timer = QTimer(self)
        self._hide_controls_timer.setSingleShot(True)
        self._hide_controls_timer.timeout.connect(self._slide_hide_controls)
        
        self.player_panel.setMouseTracking(True)
        self.player_panel.installEventFilter(self)
        self.player_container.setMouseTracking(True)
        self.player_container.installEventFilter(self)
        
        # We use a QVBoxLayout to stack the progress bar row above the buttons row
        controls_outer_layout = QVBoxLayout(self.controls_bar)
        controls_outer_layout.setContentsMargins(15, 6, 15, 6)
        controls_outer_layout.setSpacing(4)
        
        # Row 1: Progress bar layout
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(5, 0, 5, 0)
        progress_layout.setSpacing(10)
        
        self.lbl_time_current = QLabel("00:00", self.controls_bar)
        self.lbl_time_current.setObjectName("TimeLabel")
        self.lbl_time_current.setStyleSheet("color: #888896; font-size: 11px; font-weight: bold;")
        
        self.progress_slider = QSlider(Qt.Horizontal, self.controls_bar)
        self.progress_slider.setObjectName("GlassProgressSlider")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setFixedHeight(12)
        self.progress_slider.setCursor(QCursor(Qt.PointingHandCursor))
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        
        self.lbl_time_duration = QLabel("Live", self.controls_bar)
        self.lbl_time_duration.setObjectName("TimeLabel")
        self.lbl_time_duration.setStyleSheet("color: #888896; font-size: 11px; font-weight: bold;")
        
        progress_layout.addWidget(self.lbl_time_current)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.lbl_time_duration)
        controls_outer_layout.addLayout(progress_layout)
        
        # Row 2: Buttons layout
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        controls_outer_layout.addLayout(controls_layout)
        
        def _glass_btn(text, size=38, obj="GlassBtn"):
            b = QPushButton(text, self.controls_bar)
            b.setObjectName(obj)
            b.setFixedSize(size, size)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            return b
        
        # Play/Pause
        self.btn_play = _glass_btn("\uf04b", 40, "GlassBtnPrimary")
        self.btn_play.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.btn_play)
        
        # Seek Back 5s
        self.btn_seek_back = _glass_btn("\uf04a", 36)
        self.btn_seek_back.setToolTip(_t("seek_back_tooltip"))
        self.btn_seek_back.clicked.connect(self.seek_backward_5s)
        controls_layout.addWidget(self.btn_seek_back)
        
        # Seek Forward 5s
        self.btn_seek_forward = _glass_btn("\uf04e", 36)
        self.btn_seek_forward.setToolTip(_t("seek_forward_tooltip"))
        self.btn_seek_forward.clicked.connect(self.seek_forward_5s)
        controls_layout.addWidget(self.btn_seek_forward)
        
        # Stop
        self.btn_stop = _glass_btn("\uf04d", 36)
        self.btn_stop.clicked.connect(self.stop_play)
        controls_layout.addWidget(self.btn_stop)
        
        # Volume
        self.btn_volume = _glass_btn("\uf028", 34)
        self.btn_volume.clicked.connect(self.toggle_mute)
        controls_layout.addWidget(self.btn_volume)
        
        self.volume_slider = QSlider(Qt.Horizontal, self.controls_bar)
        self.volume_slider.setObjectName("GlassVolumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        controls_layout.addWidget(self.volume_slider)
        
        controls_layout.addStretch()
        
        # Multi-view
        self.view_combo = QComboBox(self.controls_bar)
        self.view_combo.setObjectName("GlassCombo")
        self.view_combo.addItems([_t("view_1_screen"), _t("view_2_screens"), _t("view_4_screens")])
        self.view_combo.currentIndexChanged.connect(self.on_multiview_changed)
        self.view_combo.setFixedWidth(150)
        controls_layout.addWidget(self.view_combo)
        
        # Audio tracks
        self.btn_audio = _glass_btn("\uf001", 34)
        self.btn_audio.setToolTip(_t("audio_tooltip"))
        self.audio_menu = QMenu(self)
        self.btn_audio.setMenu(self.audio_menu)
        self.audio_menu.aboutToShow.connect(self.populate_audio_tracks)
        controls_layout.addWidget(self.btn_audio)
        
        # Subtitles
        self.btn_subs = _glass_btn("\uf075", 34)
        self.btn_subs.setToolTip(_t("subs_tooltip"))
        self.subs_menu = QMenu(self)
        self.btn_subs.setMenu(self.subs_menu)
        self.subs_menu.aboutToShow.connect(self.populate_subtitle_tracks)
        controls_layout.addWidget(self.btn_subs)
        
        # Aspect Ratio
        self.aspect_combo = QComboBox(self.controls_bar)
        self.aspect_combo.setObjectName("GlassCombo")
        self.aspect_combo.addItems(["Auto", "16:9", "4:3", "2.35:1", "Fill"])
        self.aspect_combo.currentTextChanged.connect(self.on_aspect_changed)
        self.aspect_combo.setFixedWidth(75)
        controls_layout.addWidget(self.aspect_combo)
        
        # HW decode badge
        self.btn_hwdec = QPushButton("HW", self.controls_bar)
        self.btn_hwdec.setObjectName("GlassChip")
        self.btn_hwdec.setCheckable(True)
        hwdec_val = self.config.get("hwdec_enabled", True)
        self.btn_hwdec.setChecked(hwdec_val)
        self.btn_hwdec.setText("HW: On" if hwdec_val else "HW: Off")
        self.btn_hwdec.setFixedSize(56, 28)
        self.btn_hwdec.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_hwdec.clicked.connect(self.on_hwdec_toggled)
        controls_layout.addWidget(self.btn_hwdec)
        
        # Screenshot button
        self.btn_screenshot = _glass_btn("\uf030", 34)
        self.btn_screenshot.setToolTip(_t("screenshot_tooltip"))
        self.btn_screenshot.clicked.connect(self.take_active_player_screenshot)
        controls_layout.addWidget(self.btn_screenshot)
        
        # Stats info button
        self.btn_stats = _glass_btn("\uf080", 34)
        self.btn_stats.setToolTip(_t("stats_tooltip"))
        self.btn_stats.clicked.connect(self.toggle_active_player_stats)
        controls_layout.addWidget(self.btn_stats)
        
        # Fullscreen
        self.btn_fullscreen = _glass_btn("\uf065", 38, "GlassBtnPrimary")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        controls_layout.addWidget(self.btn_fullscreen)

    def setup_epg_schedule_panel(self):
        self.epg_panel = QFrame(self)
        self.epg_panel.setObjectName("ChannelPanel") # Reuses same design panel styling
        
        layout = QVBoxLayout(self.epg_panel)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(12)
        
        title_lbl = QLabel(_t("epg_panel_title"), self.epg_panel)
        title_lbl.setFont(QFont("Outfit", 12, QFont.Bold))
        title_lbl.setObjectName("ViewTitleLabel")
        layout.addWidget(title_lbl)
        
        self.epg_list = QListWidget(self.epg_panel)
        self.epg_list.setObjectName("EpgList")
        self.epg_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.epg_list)

    def setup_players(self):
        if not MPV_AVAILABLE:
            error_lbl = QLabel(
                _t("libmpv_error"),
                self.player_container
            )
            error_lbl.setAlignment(Qt.AlignCenter)
            error_lbl.setStyleSheet("color: #ff3366; font-size: 14px; font-weight: bold; background-color: #121214;")
            self.grid_layout.addWidget(error_lbl, 0, 0)
            self.btn_play.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.volume_slider.setEnabled(False)
            self.aspect_combo.setEnabled(False)
            self.btn_hwdec.setEnabled(False)
            self.btn_fullscreen.setEnabled(False)
            self.btn_audio.setEnabled(False)
            self.btn_subs.setEnabled(False)
            self.view_combo.setEnabled(False)
            return

        # Create 4 independent player frames for multi-view grid support
        self.overlays = []
        for i in range(4):
            frame = PlayerFrame(i, self.player_container)
            mpv_w = MpvWidget(frame)
            frame.set_player(mpv_w)
            
            self.overlays.append(frame.overlay)
            
            # Selection event handlers
            frame.clicked.connect(self.select_active_screen)
            frame.double_clicked.connect(self.on_player_double_clicked)
            mpv_w.signals.file_loaded.connect(self.on_player_file_loaded)
            
            # Install event filter to capture mouse movement over video area
            frame.installEventFilter(self)
            mpv_w.installEventFilter(self)
            frame.overlay.installEventFilter(self)
            
            # Signals are now dynamically bound to the active screen in select_active_screen()
                
            self.player_frames.append(frame)
            
        # Draw initial 1x1 layout (Screen 0 only)
        self.draw_layout()
        self.select_active_screen(0)

    def draw_layout(self):
        # Save visibility states and hide all overlays to avoid native window ghosting during layout changes
        was_visible = []
        if hasattr(self, 'player_frames'):
            for frame in self.player_frames:
                if hasattr(frame, 'overlay'):
                    was_visible.append(frame.overlay.isVisible())
                    frame.overlay.hide()
                else:
                    was_visible.append(False)

        # Reparent old layout to delete it and clear all row/column stretch/sizes
        if self.player_container.layout():
            old_layout = self.player_container.layout()
            while old_layout.count() > 0:
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.setParent(self.player_container)
            # Delete layout by assigning it to a temporary QWidget
            QWidget().setLayout(old_layout)
            
        # Create a fresh new grid layout
        self.grid_layout = QGridLayout(self.player_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(4)
                
        if self.num_screens == 1:
            frame = self.player_frames[0]
            self.grid_layout.addWidget(frame, 0, 0)
            frame.show()
            self.grid_layout.setColumnStretch(0, 1)
            self.grid_layout.setRowStretch(0, 1)
            # Hide other screens and stop their playbacks/overlays to prevent background traffic & ghost rendering
            for i in range(1, 4):
                self.player_frames[i].overlay.hide()
                if self.player_frames[i].mpv_widget:
                    self.player_frames[i].mpv_widget.stop()
                self.player_frames[i].hide()
        elif self.num_screens == 2:
            # 1x2 side-by-side layout
            for i in range(2):
                frame = self.player_frames[i]
                self.grid_layout.addWidget(frame, 0, i)
                frame.show()
            self.grid_layout.setColumnStretch(0, 1)
            self.grid_layout.setColumnStretch(1, 1)
            self.grid_layout.setRowStretch(0, 1)
            # Hide screens 2 & 3 and stop their streams
            for i in range(2, 4):
                self.player_frames[i].overlay.hide()
                if self.player_frames[i].mpv_widget:
                    self.player_frames[i].mpv_widget.stop()
                self.player_frames[i].hide()
        else:
            # 2x2 layout
            for i in range(4):
                row = i // 2
                col = i % 2
                frame = self.player_frames[i]
                self.grid_layout.addWidget(frame, row, col)
                frame.show()
            
            self.grid_layout.setColumnStretch(0, 1)
            self.grid_layout.setColumnStretch(1, 1)
            self.grid_layout.setRowStretch(0, 1)
            self.grid_layout.setRowStretch(1, 1)
                
        # Reposition all overlays and controls to match active frames
        self._reposition_overlays()
        self._reposition_glass_controls()
        self.update_active_frame_glow()

        # Keep Qt overlays hidden above native mpv windows; otherwise Windows can show clipped ghost cards.
        if hasattr(self, 'player_frames'):
            for i, frame in enumerate(self.player_frames):
                if hasattr(frame, 'overlay'):
                    frame.overlay.hide()

    def select_active_screen(self, idx):
        self.active_player_idx = idx
        
        # Disconnect previous widget signals
        if hasattr(self, 'connected_widget') and self.connected_widget:
            try:
                self.connected_widget.signals.pause_changed.disconnect(self.on_player_pause_changed)
                self.connected_widget.signals.volume_changed.disconnect(self.on_player_volume_changed)
                self.connected_widget.signals.time_changed.disconnect(self.on_player_time_changed)
                self.connected_widget.signals.duration_changed.disconnect(self.on_player_duration_changed)
            except Exception:
                pass
                
        for i, frame in enumerate(self.player_frames):
            frame.set_active(i == idx and self.num_screens > 1)
            # Route audio to the active screen, mute all other screens
            if MPV_AVAILABLE and frame.mpv_widget and frame.mpv_widget.player:
                try:
                    if i == idx and not self.is_app_muted:
                        frame.mpv_widget.player.mute = False
                        frame.mpv_widget.player.volume = self.volume_slider.value()
                    else:
                        frame.mpv_widget.player.mute = True
                except Exception as e:
                    print(f"[-] Error setting mute/volume for player {i}: {e}")
            
        # Connect new widget signals
        if idx < len(self.player_frames):
            frame = self.player_frames[idx]
            self.connected_widget = frame.mpv_widget
            if self.connected_widget:
                self.connected_widget.signals.pause_changed.connect(self.on_player_pause_changed)
                self.connected_widget.signals.volume_changed.connect(self.on_player_volume_changed)
                self.connected_widget.signals.time_changed.connect(self.on_player_time_changed)
                self.connected_widget.signals.duration_changed.connect(self.on_player_duration_changed)
                
                # Immediately update controls to reflect current state
                if MPV_AVAILABLE and self.connected_widget.player:
                    try:
                        self.on_player_pause_changed(self.connected_widget.player.pause)
                        self.on_player_volume_changed(self.connected_widget.player.volume or 80)
                        
                        time_pos = self.connected_widget.player.time_pos
                        self.on_player_time_changed(time_pos if time_pos is not None else 0)
                        
                        duration = self.connected_widget.player.duration
                        self.on_player_duration_changed(duration if duration is not None else 0)
                    except Exception:
                        pass
                        
        print(f"[*] Active Screen set to: {idx}")
        self.update_active_frame_glow()

    def on_player_double_clicked(self, idx):
        self.select_active_screen(idx)
        active_frame = self.player_frames[idx]
        if hasattr(active_frame, 'is_pip') and active_frame.is_pip:
            self.toggle_pip_mode()
        else:
            self.toggle_fullscreen()

    # Views & Playlists
    def switch_view(self, view_name):
        self.current_view = view_name
        
        self.btn_live.setObjectName("SidebarBtn")
        self.btn_fav.setObjectName("SidebarBtn")
        self.btn_history.setObjectName("SidebarBtn")
        
        if view_name == "live":
            self.btn_live.setObjectName("SidebarBtnActive")
            self.lbl_view_title.setText(_t("live_tv_title"))
            self.cat_selector.show()
        elif view_name == "favorites":
            self.btn_fav.setObjectName("SidebarBtnActive")
            self.lbl_view_title.setText(_t("favorites_title"))
            self.cat_selector.hide()
        elif view_name == "history":
            self.btn_history.setObjectName("SidebarBtnActive")
            self.lbl_view_title.setText(_t("recent_title"))
            self.cat_selector.hide()
            
        self.sidebar.setStyleSheet(self.sidebar.styleSheet())
        self.filter_channels()

    def start_epg_update(self, epg_url):
        if not epg_url:
            return
        self.epg_thread = EPGDownloadWorker(epg_url)
        self.epg_thread.finished.connect(self.on_epg_load_finished)
        self.epg_thread.start()

    def on_epg_load_finished(self, success):
        if success:
            print("[+] EPG loaded successfully, updating active channel info.")
            self.update_current_program_info()
            self.update_epg_schedule_list()
            self.filter_channels() # Refresh channel list items to show loaded EPG titles
        else:
            print("[-] EPG download or parse failed.")

    def load_playlist(self, path):
        # Cancel any active playlist load thread
        if getattr(self, 'playlist_worker', None) and self.playlist_worker.isRunning():
            self.playlist_worker.terminate()
            self.playlist_worker.wait()
            
        # Display a sleek loading state to the user
        self.channel_list.clear()
        self.channel_list.addItem(_t("loading_playlist"))
        self.search_bar.setPlaceholderText(_t("loading_playlist_placeholder"))
        
        self.playlist_worker = PlaylistDownloadWorker(path)
        self.playlist_worker.finished.connect(lambda channels, epg_url, p=path: self.on_playlist_loaded(channels, epg_url, p))
        self.playlist_worker.failed.connect(self.on_playlist_failed)
        self.playlist_worker.start()

    def on_playlist_loaded(self, channels, epg_url, path):
        self.search_bar.setPlaceholderText(_t("search_placeholder"))
        self.channels = channels
        self.current_playlist_path = path
        
        if not self.channels:
            print(f"[-] Could not load playlist: {path}")
            self.channel_list.clear()
            self.channel_list.addItem(_t("empty_playlist_error"))
            return
            
        # Automatic EPG Loading
        active_epg = epg_url or self.get_active_epg_url()
        if active_epg:
            print(f"[+] Found EPG URL: {active_epg}. Starting background update.")
            self.start_epg_update(active_epg)
            
        groups = sorted(list(set(c.get("group", "Default") for c in self.channels)))
        
        self.cat_selector.blockSignals(True)
        self.cat_selector.clear()
        self.cat_selector.addItem(_t("all_categories"))
        for g in groups:
            self.cat_selector.addItem(g)
        self.cat_selector.blockSignals(False)
        
        # Display channels
        self.filter_channels()
        print(f"[+] Loaded {len(self.channels)} channels from {path}")
        
        # Automatic checker startup removed

    def on_playlist_failed(self, error_msg):
        self.search_bar.setPlaceholderText(_t("search_placeholder"))
        self.channel_list.clear()
        self.channel_list.addItem(_t("load_playlist_error").format(error_msg))
        print(f"[-] Playlist load worker error: {error_msg}")

    def start_channel_checker(self):
        # Stop existing checker thread
        if self.checker_thread and self.checker_thread.isRunning():
            self.checker_thread.stop()
            self.checker_thread.wait()
            
        self.channel_statuses.clear()
        
        # Limit checking to first 300 channels of active view to avoid background lag
        check_list = []
        if hasattr(self, 'filtered_channels') and self.filtered_channels:
            check_list = self.filtered_channels[:300]
        else:
            check_list = self.channels[:300]
            
        self.checker_thread = ChannelChecker(check_list)
        self.checker_thread.status_updated.connect(self.on_channel_status_updated)
        self.checker_thread.start()

    def on_channel_status_updated(self, url, is_alive, latency_ms):
        self.channel_statuses[url] = is_alive
        self.channel_latencies[url] = latency_ms
        
        # Dynamically update the visual status and latency of items in the QListWidget
        for i in range(self.channel_list.count()):
            item = self.channel_list.item(i)
            widget = self.channel_list.itemWidget(item)
            if widget and hasattr(widget, 'url') and widget.url == url:
                widget.set_status(is_alive, latency_ms)
                break

    def filter_channels(self):
        query = self.search_bar.text().strip()
        query_clean = clean_search_string(query)
        selected_cat = self.cat_selector.currentText()
        
        self.channel_list.clear()
        self.filtered_channels = []
        
        raw_list = []
        if self.current_view == "live":
            raw_list = self.channels
        elif self.current_view == "favorites":
            self.config = config_manager.load_config()
            raw_list = self.config.get("favorites", [])
        elif self.current_view == "history":
            self.config = config_manager.load_config()
            raw_list = self.config.get("history", [])
            
        for c in raw_list:
            name = c.get("name", "")
            group = c.get("group", "Default")
            url = c.get("url", "")
            
            # Text search filter
            if query:
                name_clean = clean_search_string(name)
                if query_clean not in name_clean:
                    continue
                
            # Category filter
            # Category filter
            if self.current_view == "live" and selected_cat != _t("all_categories") and group != selected_cat:
                continue
                
            # Resolution tag filter
            if hasattr(self, 'active_res_filter') and self.active_res_filter != "all":
                name_upper = name.upper()
                if self.active_res_filter == "4k":
                    if "4K" not in name_upper and "UHD" not in name_upper:
                        continue
                elif self.active_res_filter == "fhd":
                    if "FHD" not in name_upper and "1080" not in name_upper:
                        continue
                elif self.active_res_filter == "hd":
                    if "HD" not in name_upper and "720" not in name_upper:
                        continue
                        
            self.filtered_channels.append(c)
            
        # Sorting logic
        if hasattr(self, 'sort_selector'):
            sort_idx = self.sort_selector.currentIndex()
            if sort_idx == 1:
                self.filtered_channels.sort(key=lambda c: c.get("name", "").lower())
            elif sort_idx == 2:
                def get_sort_key(c):
                    url = c.get("url", "")
                    is_alive = self.channel_statuses.get(url, True)
                    latency = self.channel_latencies.get(url, 999999)
                    
                    # 1. Alive & low latency
                    # 2. Alive & unknown/untested latency
                    # 3. Offline/dead channels
                    if not is_alive:
                        return (2, 999999, c.get("name", "").lower())
                    
                    lat_key = latency if latency > 0 else 99999
                    return (0 if is_alive else 1, lat_key, c.get("name", "").lower())
                    
                self.filtered_channels.sort(key=get_sort_key)
                
        # Clear and load the first batch of channels lazily
        self.channel_list.clear()
        self.loaded_item_count = 0
        self.load_more_channels()

    def load_more_channels(self):
        if not hasattr(self, 'filtered_channels') or not self.filtered_channels:
            return
            
        start_idx = getattr(self, 'loaded_item_count', 0)
        batch_size = 150
        end_idx = min(start_idx + batch_size, len(self.filtered_channels))
        
        if start_idx >= len(self.filtered_channels):
            return
            
        self.channel_list.blockSignals(True)
        for i in range(start_idx, end_idx):
            c = self.filtered_channels[i]
            name = c.get("name", "")
            url = c.get("url", "")
            tvg_id = c.get("tvg-id", "")
            logo_url = c.get("logo", "")
            
            is_alive = self.channel_statuses.get(url, None)
            latency_ms = self.channel_latencies.get(url, -1)
            
            # Fetch current EPG program if available
            current_prog = ""
            if tvg_id or name:
                prog = epg_manager.get_current_program(tvg_id, name)
                if prog:
                    current_prog = prog.get("title", "")
            
            widget = ChannelItemWidget(name, url, tvg_id, is_alive, latency_ms, logo_url, current_prog)
            
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 58))
            self.channel_list.addItem(item)
            self.channel_list.setItemWidget(item, widget)
            
        self.loaded_item_count = end_idx
        self.channel_list.blockSignals(False)
        print(f"[+] Lazy loaded channels: {start_idx} to {end_idx} of {len(self.filtered_channels)}")

    def on_list_scroll(self, value):
        scrollbar = self.channel_list.verticalScrollBar()
        if value > scrollbar.maximum() * 0.85:  # Scrolled past 85%
            self.load_more_channels()

    def on_category_changed(self):
        self.filter_channels()

    def on_channel_selected(self, item):
        row = self.channel_list.row(item)
        if 0 <= row < len(self.filtered_channels):
            channel = self.filtered_channels[row]
            name = channel.get("name", "")
            stream_url = channel.get("url", "")
            
            # Lookup full channel in playlist if user-agent is not present (e.g. from history/favorites)
            if self.current_view in ("favorites", "history") or not channel.get("user-agent"):
                matched_channel = next((c for c in self.channels if c.get("url") == stream_url), None)
                if matched_channel:
                    channel = matched_channel
                    
            # Set titles on player header
            self.lbl_channel_title.setText(f"[Màn {self.active_player_idx + 1}] - {name}")
            self.lbl_epg_now.setText("")
            
            # Play in active screen
            if MPV_AVAILABLE:
                active_frame = self.player_frames[self.active_player_idx]
                active_frame.mpv_widget.play(channel)
                self.btn_play.setText("\uf04c")
                
                # Show and raise glass controls above mpv native surface after play starts
                QTimer.singleShot(150, self._reposition_glass_controls)
                QTimer.singleShot(150, self._show_glass_controls)
                
                # Add to history
                config_manager.add_history(name, stream_url)
                
            # Update EPG info
            self.update_current_program_info()
            self.update_epg_schedule_list()

    def update_current_program_info(self):
        current_item = self.channel_list.currentItem()
        if not current_item:
            self.lbl_epg_now.setText("")
            return
            
        row = self.channel_list.row(current_item)
        if 0 <= row < len(self.filtered_channels):
            channel = self.filtered_channels[row]
            tvg_id = channel.get("tvg-id", "")
            name = channel.get("name", "")
            
            prog = epg_manager.get_current_program(tvg_id, name)
            if prog:
                start_str = prog['start'].strftime("%H:%M")
                stop_str = prog['stop'].strftime("%H:%M")
                title = prog['title']
                self.lbl_epg_now.setText(_t("epg_now_playing").format(start_str, stop_str, title))
            else:
                self.lbl_epg_now.setText(_t("epg_live_no_epg"))

    def update_epg_schedule_list(self):
        self.epg_list.clear()
        current_item = self.channel_list.currentItem()
        if not current_item:
            return
            
        row = self.channel_list.row(current_item)
        if 0 <= row < len(self.filtered_channels):
            channel = self.filtered_channels[row]
            tvg_id = channel.get("tvg-id", "")
            name = channel.get("name", "")
            
            schedule = epg_manager.get_schedule(tvg_id, name)
            if not schedule:
                self.epg_list.addItem(_t("epg_no_details"))
                return
                
            from datetime import datetime
            now = datetime.now().astimezone()
            
            for prog in schedule:
                start_str = prog['start'].strftime("%H:%M")
                stop_str = prog['stop'].strftime("%H:%M")
                title = prog['title']
                
                # Check if currently active program
                is_active = (prog['start'] <= now <= prog['stop'])
                prefix = "🔥 " if is_active else ""
                
                display_text = f"{prefix}{start_str} - {stop_str}\n{title}"
                
                item = QListWidgetItem(display_text)
                
                # Highlight active program with bold and accent colors
                if is_active:
                    item.setFont(QFont("Outfit", 10, QFont.Bold))
                    item.setForeground(QColor("#00e5ff"))
                self.epg_list.addItem(item)

    # Right-click Context Menu
    def show_channel_context_menu(self, position):
        item = self.channel_list.itemAt(position)
        if not item:
            return
            
        row = self.channel_list.row(item)
        channel = self.filtered_channels[row]
        name = channel.get("name", "")
        url = channel.get("url", "")
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #18181c;
                border: 1px solid #282830;
                color: #e0e0e6;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #7c4dff;
                color: #ffffff;
            }
        """)
        
        is_fav = config_manager.is_favorite(url)
        
        if is_fav:
            action_fav = QAction(_t("context_remove_fav"), self)
            action_fav.triggered.connect(lambda: self.remove_from_favorites(url))
        else:
            action_fav = QAction(_t("context_add_fav"), self)
            action_fav.triggered.connect(lambda: self.add_to_favorites(name, url))
            
        action_check = QAction(_t("context_check_channel"), self)
        action_check.triggered.connect(lambda: self.check_single_channel_status(url, item))
            
        action_copy = QAction(_t("context_copy_link"), self)
        action_copy.triggered.connect(lambda: self.copy_channel_url(url))
            
        menu.addAction(action_fav)
        menu.addAction(action_check)
        menu.addAction(action_copy)
        menu.exec(QCursor.pos())

    def copy_channel_url(self, url):
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        try:
            active_frame = self.player_frames[self.active_player_idx]
            if active_frame and active_frame.mpv_widget and active_frame.mpv_widget.player:
                active_frame.mpv_widget.player.show_message(_t("copied_link_msg"), 3000)
        except Exception:
            pass

    def check_single_channel_status(self, url, item):
        class SingleChecker(QThread):
            result = Signal(bool, int)
            def __init__(self, url):
                super().__init__()
                self.url = url
            def run(self):
                import time
                start_time = time.perf_counter()
                try:
                    r = requests.head(self.url, timeout=3.0, headers={"User-Agent": "VLC/3.0.18 LibVLC/3.0.18"}, allow_redirects=True)
                    latency = int((time.perf_counter() - start_time) * 1000)
                    self.result.emit(r.status_code < 400, latency)
                except Exception:
                    try:
                        start_time = time.perf_counter()
                        r = requests.get(self.url, timeout=3.0, headers={"User-Agent": "VLC/3.0.18 LibVLC/3.0.18"}, stream=True)
                        is_alive = (r.status_code < 400)
                        latency = int((time.perf_counter() - start_time) * 1000)
                        r.close()
                        self.result.emit(is_alive, latency)
                    except Exception:
                        self.result.emit(False, -1)
        
        # Keep a reference to prevent garbage collection
        self.active_single_checker = SingleChecker(url)
        
        # Update UI to show checking status
        widget = self.channel_list.itemWidget(item)
        if widget:
            widget.lbl_status.setText("⏳")
        
        def on_finished(is_alive, latency_ms):
            self.channel_statuses[url] = is_alive
            self.channel_latencies[url] = latency_ms
            if widget:
                widget.set_status(is_alive, latency_ms)
            
        self.active_single_checker.result.connect(on_finished)
        self.active_single_checker.start()

    def add_to_favorites(self, name, url):
        if config_manager.add_favorite(name, url):
            print(f"[+] Added {name} to favorites.")
            for i in range(self.channel_list.count()):
                item = self.channel_list.item(i)
                w = self.channel_list.itemWidget(item)
                if w and hasattr(w, 'url') and w.url == url:
                    w.is_fav = True
                    w._update_star_icon()
                    break
            if self.current_view == "favorites":
                self.filter_channels()

    def remove_from_favorites(self, url):
        if config_manager.remove_favorite(url):
            print(f"[-] Removed stream {url} from favorites.")
            for i in range(self.channel_list.count()):
                item = self.channel_list.item(i)
                w = self.channel_list.itemWidget(item)
                if w and hasattr(w, 'url') and w.url == url:
                    w.is_fav = False
                    w._update_star_icon()
                    break
            if self.current_view == "favorites":
                self.filter_channels()

    # Dynamic Audio & Subtitle track lists
    def populate_audio_tracks(self):
        self.audio_menu.clear()
        if not MPV_AVAILABLE:
            return
            
        active_player = self.player_frames[self.active_player_idx].mpv_widget.player
        if not active_player:
            return
            
        try:
            tracks = active_player.track_list
            audio_tracks = [t for t in tracks if t.get('type') == 'audio']
            
            if not audio_tracks:
                action = self.audio_menu.addAction(_t("no_audio_stream"))
                action.setEnabled(False)
                return
                
            for t in audio_tracks:
                lang = t.get('lang', 'unk')
                title = t.get('title', '')
                t_id = t.get('id', 1)
                
                display_name = f"Track {t_id}"
                if lang:
                    display_name += f" ({lang.upper()})"
                if title:
                    display_name += f" - {title}"
                if t.get('selected'):
                    display_name = "✓ " + display_name
                    
                action = QAction(display_name, self)
                action.setData(t_id)
                action.triggered.connect(lambda checked=False, tid=t_id: self.select_audio_track(tid))
                self.audio_menu.addAction(action)
        except Exception as e:
            print(f"Error reading audio tracks: {e}")

    def select_audio_track(self, track_id):
        active_player = self.player_frames[self.active_player_idx].mpv_widget.player
        if active_player:
            try:
                active_player['aid'] = track_id
                print(f"[+] Active Screen {self.active_player_idx} switched to Audio Track: {track_id}")
            except Exception as e:
                print(e)

    def populate_subtitle_tracks(self):
        self.subs_menu.clear()
        if not MPV_AVAILABLE:
            return
            
        active_player = self.player_frames[self.active_player_idx].mpv_widget.player
        if not active_player:
            return
            
        try:
            tracks = active_player.track_list
            sub_tracks = [t for t in tracks if t.get('type') == 'sub']
            
            # Turn Off Subtitles Action
            off_name = _t("turn_off_subs")
            is_off_selected = not any(t.get('selected') for t in sub_tracks)
            if is_off_selected:
                off_name = "✓ " + off_name
            action_off = QAction(off_name, self)
            action_off.triggered.connect(lambda: self.select_subtitle_track("no"))
            self.subs_menu.addAction(action_off)
            
            if not sub_tracks:
                return
                
            self.subs_menu.addSeparator()
            
            for t in sub_tracks:
                lang = t.get('lang', 'unk')
                title = t.get('title', '')
                t_id = t.get('id', 1)
                
                display_name = _t("subtitle_track").format(t_id)
                if lang:
                    display_name += f" ({lang.upper()})"
                if title:
                    display_name += f" - {title}"
                if t.get('selected'):
                    display_name = "✓ " + display_name
                    
                action = QAction(display_name, self)
                action.setData(t_id)
                action.triggered.connect(lambda checked=False, tid=t_id: self.select_subtitle_track(tid))
                self.subs_menu.addAction(action)
        except Exception as e:
            print(f"Error reading subtitle tracks: {e}")

    def select_subtitle_track(self, track_id):
        active_player = self.player_frames[self.active_player_idx].mpv_widget.player
        if active_player:
            try:
                active_player['sid'] = track_id
                print(f"[+] Active Screen {self.active_player_idx} switched to Subtitle Track: {track_id}")
            except Exception as e:
                print(e)

    # Dialog Windows
    def open_playlist_manager(self):
        dialog = PlaylistManagerDialog(self)
        dialog.playlist_changed.connect(self.on_active_playlist_changed)
        dialog.exec()

    def get_active_epg_url(self):
        active_url = self.config.get("active_playlist_url", "")
        for pl in self.config.get("playlists", []):
            if pl.get("url") == active_url:
                if pl.get("epg_url"):
                    return pl.get("epg_url")
        return self.config.get("epg_url", "https://iptv-org.github.io/epg/guides/fr/telerama.fr.xml")

    def on_active_playlist_changed(self):
        self.config = config_manager.load_config()
        active_url = self.config.get("active_playlist_url", "playlist.m3u")
        self.load_playlist(active_url)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    # Player callbacks
    def on_player_pause_changed(self, is_paused):
        # Reflect status of screen 0
        if self.active_player_idx == 0:
            self.btn_play.setText("\uf04b" if is_paused else "\uf04c")

    def on_player_volume_changed(self, volume):
        if self.active_player_idx == 0:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(volume)
            self.volume_slider.blockSignals(False)
            self.btn_volume.setText("\uf026" if volume == 0 else "\uf028")

    def on_player_file_loaded(self):
        # Reposition and show controls bar to ensure it is visible and on top of rendering video
        self._reposition_glass_controls()
        self._show_glass_controls()
        self._hide_controls_timer.start(2000)

    # Playback Controls
    def toggle_play(self):
        if MPV_AVAILABLE:
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            active_player.toggle_pause()
            
            # Update Play/Pause button symbol based on state
            if active_player.player:
                is_p = active_player.player.pause
                self.btn_play.setText("\uf04b" if not is_p else "\uf04c")

    def stop_play(self):
        if MPV_AVAILABLE:
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            active_player.stop()
            self.btn_play.setText("\uf04b")
            self.lbl_channel_title.setText(_t("player_stopped").format(self.active_player_idx + 1))
            self.lbl_epg_now.setText("")
            self.epg_list.clear()

    def toggle_mute(self):
        if MPV_AVAILABLE:
            self.is_app_muted = not self.is_app_muted
            self.btn_volume.setText("\uf026" if self.is_app_muted else "\uf028")
            
            # Apply mute state to all player frames
            for i, frame in enumerate(self.player_frames):
                if frame.mpv_widget and frame.mpv_widget.player:
                    try:
                        if i == self.active_player_idx and not self.is_app_muted:
                            frame.mpv_widget.player.mute = False
                        else:
                            frame.mpv_widget.player.mute = True
                    except Exception:
                        pass

    def on_volume_changed(self, value):
        if MPV_AVAILABLE:
            # Set volume for active screen player
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            active_player.set_volume(value)

    def on_aspect_changed(self, text):
        if MPV_AVAILABLE:
            ratio_map = {
                "Auto": "-1",
                "16:9": "16:9",
                "4:3": "4:3",
                "2.35:1": "2.35:1",
                "Stretch": "no"
            }
            ratio = ratio_map.get(text, "-1")
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            active_player.set_aspect_ratio(ratio)

    def on_hwdec_toggled(self, checked):
        if MPV_AVAILABLE:
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            active_player.toggle_hwdec(checked)
            self.btn_hwdec.setText("HW: On" if checked else "HW: Off")

    def on_multiview_changed(self, index):
        if index == 2:
            self.num_screens = 4
        elif index == 1:
            self.num_screens = 2
            if self.active_player_idx > 1:
                self.select_active_screen(0)
        else:
            self.num_screens = 1
            self.select_active_screen(0)

        self.draw_layout()

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.sidebar.show()
            self.channel_panel.show()
            self.header_bar.show()
            self.setWindowState(self.windowState() & ~Qt.WindowFullScreen)
            self.is_fullscreen = False
            
            # Restore spacing and margins for the grid layout
            self.grid_layout.setContentsMargins(4, 4, 4, 4)
            self.grid_layout.setSpacing(4)
            
            # Reshow glass overlay
            self._controls_visible = True
            self._reposition_glass_controls()
            self.controls_bar.show()
            self.controls_bar.raise_()
        else:
            self.sidebar.hide()
            self.channel_panel.hide()
            self.header_bar.hide()
            self.showFullScreen()
            self.is_fullscreen = True
            
            # Remove all spacing and margins for absolute borderless fullscreen
            self.grid_layout.setContentsMargins(0, 0, 0, 0)
            self.grid_layout.setSpacing(0)
            
            # Ensure controls bar is visible and on top of the native surface, then hide after 300ms
            QTimer.singleShot(80, self.controls_bar.show)
            QTimer.singleShot(80, self.controls_bar.raise_)
            QTimer.singleShot(300, self._slide_hide_controls)
            
        # Dynamically toggle fullscreen styling to hide active/inactive borders
        for frame in self.player_frames:
            frame.setProperty("fullscreen", "true" if self.is_fullscreen else "false")
            frame.style().unpolish(frame)
            frame.style().polish(frame)

    # Global Keyboard Shortcuts
    def keyPressEvent(self, event):
        # Ignore shortcuts if typing inside search bar or settings inputs
        focused = QApplication.focusWidget()
        if isinstance(focused, QLineEdit):
            super().keyPressEvent(event)
            return
            
        key = event.key()
        if key == Qt.Key_Space:
            self.toggle_play()
        elif key == Qt.Key_F:
            self.toggle_fullscreen()
        elif key == Qt.Key_M:
            self.toggle_mute()
        elif key == Qt.Key_I:
            self.toggle_active_player_stats()
        elif key == Qt.Key_F12:
            self.take_active_player_screenshot()
        elif key == Qt.Key_Up:
            val = min(self.volume_slider.value() + 5, 100)
            self.volume_slider.setValue(val)
        elif key == Qt.Key_Down:
            val = max(self.volume_slider.value() - 5, 0)
            self.volume_slider.setValue(val)
        elif key == Qt.Key_Left:
            self.seek_backward_5s()
        elif key == Qt.Key_Right:
            self.seek_forward_5s()
        else:
            super().keyPressEvent(event)

    def toggle_active_player_stats(self):
        if hasattr(self, 'player_frames') and len(self.player_frames) > self.active_player_idx:
            frame = self.player_frames[self.active_player_idx]
            if frame.mpv_widget:
                frame.mpv_widget.toggle_stats()

    def update_player_cache_settings(self):
        self.config = config_manager.load_config()
        buffer_bytes = self.config.get("buffer_size_bytes", 50 * 1024 * 1024)
        for frame in self.player_frames:
            if frame.mpv_widget:
                frame.mpv_widget.config = self.config
                if frame.mpv_widget.player:
                    try:
                        frame.mpv_widget.player['demuxer-max-bytes'] = buffer_bytes
                        print(f"[+] Updated active screen {frame.index} cache size to {buffer_bytes / (1024*1024):.0f} MB")
                    except Exception as e:
                        print(f"[-] Could not update demuxer-max-bytes for screen {frame.index}: {e}")

    def setup_shortcuts(self):
        # Register window-level keyboard shortcuts that bypass focus-stealing native controls
        shortcut_map = {
            "Space": self.toggle_play,
            "F": self.toggle_fullscreen,
            "M": self.toggle_mute,
            "I": self.toggle_active_player_stats,
            "S": self.take_active_player_screenshot,
            "P": self.toggle_pip_mode,
            "R": self.toggle_active_player_recording,
            "F5": self.reload_active_player,
            "Up": self.volume_up,
            "Down": self.volume_down,
            "Escape": self.exit_fullscreen,
            "Left": self.seek_backward_5s,
            "Right": self.seek_forward_5s
        }
        
        self.shortcuts = []
        for key_str, method in shortcut_map.items():
            shortcut = QShortcut(QKeySequence(key_str), self)
            shortcut.activated.connect(self._create_shortcut_handler(method))
            shortcut.setContext(Qt.WindowShortcut)
            self.shortcuts.append(shortcut)

    def _create_shortcut_handler(self, method):
        def handler():
            if not self.is_typing():
                method()
        return handler

    def is_typing(self):
        focused = QApplication.focusWidget()
        return isinstance(focused, QLineEdit)

    def exit_fullscreen(self):
        if self.is_fullscreen:
            self.toggle_fullscreen()

    # ── Glass controls overlay: position & auto-hide ─────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_glass_controls()
        self._reposition_overlays()
        if hasattr(self, 'hud') and self.hud and self.hud.isVisible():
            self.hud.setGeometry(self.rect())

    def _reposition_glass_controls(self):
        if not hasattr(self, 'controls_bar') or not self.controls_bar:
            return
        panel_w = self.player_panel.width()
        panel_h = self.player_panel.height()
        bar_h = 80
        
        # Center the controls bar and make it float with margin
        margin = 16
        if self.is_fullscreen:
            margin = 32
            
        bar_w = panel_w - (margin * 2)
        if bar_w < 500: # fallback for small screens
            bar_w = panel_w
            x = 0
            y = panel_h - bar_h
            self.controls_bar.setGeometry(x, y, bar_w, bar_h)
            self.controls_bar.setStyleSheet("""
                QFrame#GlassControls {
                    background: transparent;
                    border: none;
                    border-radius: 0px;
                }
            """)
        else:
            x = margin
            y = panel_h - bar_h - 16
            self.controls_bar.setGeometry(x, y, bar_w, bar_h)
            self.controls_bar.setStyleSheet("""
                QFrame#GlassControls {
                    background: transparent;
                    border: none;
                    border-radius: 16px;
                }
            """)

    def toggle_sidebar_panel(self):
        new_state = not self.sidebar.isVisible()
        self.sidebar.setVisible(new_state)
        self.channel_panel.setVisible(new_state)
        self.btn_toggle_sidebar.setText("☰" if new_state else "▶")
        
        QTimer.singleShot(50, self._reposition_glass_controls)
        QTimer.singleShot(50, self._reposition_overlays)

    def toggle_epg_panel(self):
        epg_visible = self.epg_panel.isVisible()
        if epg_visible:
            self.epg_panel.hide()
            self.btn_toggle_epg.setText(_t("epg_schedule_btn"))
            self.btn_toggle_epg.setProperty("active", "false")
        else:
            self.epg_panel.show()
            self.btn_toggle_epg.setText(_t("epg_hide_btn"))
            self.btn_toggle_epg.setProperty("active", "true")
            self.update_epg_schedule_list()
            w_total = self.splitter.width()
            self.splitter.setSizes([310, w_total - 310 - 260, 260])
            
        self.btn_toggle_epg.style().unpolish(self.btn_toggle_epg)
        self.btn_toggle_epg.style().polish(self.btn_toggle_epg)
        
        QTimer.singleShot(50, self._reposition_glass_controls)
        QTimer.singleShot(50, self._reposition_overlays)

    def toggle_shortcuts_hud(self):
        if hasattr(self, 'hud') and self.hud:
            if self.hud.isVisible():
                self.hud.hide()
            else:
                self.hud.show_hud()

    def update_active_frame_glow(self):
        for idx, frame in enumerate(self.player_frames):
            if idx == self.active_player_idx and self.num_screens > 1:
                shadow = QGraphicsDropShadowEffect(frame)
                shadow.setBlurRadius(20)
                shadow.setColor(QColor(0, 229, 255, 180))
                shadow.setOffset(0, 0)
                frame.setGraphicsEffect(shadow)
            else:
                frame.setGraphicsEffect(None)

    def _reposition_overlays(self):
        if not hasattr(self, 'overlays'):
            return
        for i, frame in enumerate(self.player_frames):
            if hasattr(frame, 'overlay'):
                overlay = frame.overlay
                if frame.isVisible():
                    overlay.sync_to_parent()
                    if overlay.isVisible():
                        overlay.raise_()
                else:
                    overlay.hide()

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if self.is_fullscreen:
            is_player_obj = (obj in (self.player_container, self.player_panel) or 
                             any(obj == f or obj == f.mpv_widget or obj == f.overlay for f in self.player_frames))
            if is_player_obj:
                etype = event.type()
                if etype == QEvent.MouseMove:
                    self._show_glass_controls()
                    self._hide_controls_timer.start(2000)
                elif etype == QEvent.Enter:
                    self._show_glass_controls()
                    self._hide_controls_timer.start(2000)
                elif etype == QEvent.Leave:
                    self._hide_controls_timer.start(800)
        return super().eventFilter(obj, event)

    def _show_glass_controls(self):
        self.controls_bar.show()
        self.controls_bar.raise_()

    def _slide_hide_controls(self):
        if self.is_fullscreen:
            self.controls_bar.hide()

    def volume_up(self):
        val = min(self.volume_slider.value() + 5, 100)
        self.volume_slider.setValue(val)

    def volume_down(self):
        val = max(self.volume_slider.value() - 5, 0)
        self.volume_slider.setValue(val)

    def take_active_player_screenshot(self):
        if hasattr(self, 'player_frames') and len(self.player_frames) > self.active_player_idx:
            active_frame = self.player_frames[self.active_player_idx]
            if active_frame.mpv_widget:
                import datetime
                now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{now_str}.png"
                if getattr(sys, 'frozen', False):
                    root_dir = os.path.dirname(sys.executable)
                else:
                    root_dir = os.path.dirname(os.path.abspath(__file__))
                snapshots_dir = os.path.join(root_dir, "snapshots")
                filepath = os.path.join(snapshots_dir, filename)
                
                success = active_frame.mpv_widget.take_screenshot(filepath)
                if success:
                    print(f"[+] Screenshot saved to: {filepath}")

    def reload_active_player(self):
        if hasattr(self, 'player_frames') and len(self.player_frames) > self.active_player_idx:
            active_frame = self.player_frames[self.active_player_idx]
            if active_frame.mpv_widget and active_frame.mpv_widget.current_url:
                url = active_frame.mpv_widget.current_url
                print(f"[*] Reloading active player {self.active_player_idx}: {url}")
                active_frame.mpv_widget.play(url)
                if active_frame.mpv_widget.player:
                    active_frame.mpv_widget.player.show_message(_t("reloading_stream"), 2000)

    def seek_backward_5s(self):
        if MPV_AVAILABLE:
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            if active_player and active_player.player:
                try:
                    active_player.player.seek(-5, reference='relative')
                except Exception as e:
                    print(f"Error seeking relative backward: {e}")

    def seek_forward_5s(self):
        if MPV_AVAILABLE:
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            if active_player and active_player.player:
                try:
                    active_player.player.seek(5, reference='relative')
                except Exception as e:
                    print(f"Error seeking relative forward: {e}")

    def on_player_time_changed(self, time_val):
        if not hasattr(self, '_user_seeking') or not self._user_seeking:
            self.lbl_time_current.setText(self.format_time(time_val))
            duration = getattr(self, 'current_player_duration', 0)
            if duration > 0:
                slider_val = int((time_val / duration) * 1000)
                self.progress_slider.blockSignals(True)
                self.progress_slider.setValue(slider_val)
                self.progress_slider.blockSignals(False)
            else:
                self.progress_slider.blockSignals(True)
                self.progress_slider.setValue(0)
                self.progress_slider.blockSignals(False)

    def on_player_duration_changed(self, duration_val):
        self.current_player_duration = duration_val
        if duration_val > 0:
            self.lbl_time_duration.setText(self.format_time(duration_val))
            self.progress_slider.setEnabled(True)
        else:
            self.lbl_time_duration.setText("Live")
            self.progress_slider.setValue(0)
            self.progress_slider.setEnabled(False)

    def format_time(self, seconds):
        if seconds is None or seconds < 0:
            return "00:00"
        s = int(seconds)
        hours = s // 3600
        mins = (s % 3600) // 60
        secs = s % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            return f"{mins:02d}:{secs:02d}"

    def on_slider_pressed(self):
        self._user_seeking = True

    def on_slider_moved(self, value):
        duration = getattr(self, 'current_player_duration', 0)
        if duration > 0:
            current_time = (value / 1000.0) * duration
            self.lbl_time_current.setText(self.format_time(current_time))

    def on_slider_released(self):
        self._user_seeking = False
        duration = getattr(self, 'current_player_duration', 0)
        if duration > 0:
            value = self.progress_slider.value()
            target_time = (value / 1000.0) * duration
            active_player = self.player_frames[self.active_player_idx].mpv_widget
            if active_player:
                active_player.seek(target_time)

    def set_sleep_timer(self, minutes):
        self.sleep_timer_remaining = minutes * 60
        self.sleep_countdown_timer.start()
        print(f"[*] Sleep timer set for {minutes} minutes.")
        active_frame = self.player_frames[self.active_player_idx]
        if active_frame and active_frame.mpv_widget and active_frame.mpv_widget.player:
            active_frame.mpv_widget.player.show_message(_t("timer_set_msg").format(minutes), 3000)

    def cancel_sleep_timer(self):
        self.sleep_timer_remaining = 0
        self.sleep_countdown_timer.stop()
        self.lbl_sleep_status.hide()
        print("[*] Sleep timer cancelled.")
        active_frame = self.player_frames[self.active_player_idx]
        if active_frame and active_frame.mpv_widget and active_frame.mpv_widget.player:
            active_frame.mpv_widget.player.show_message(_t("timer_cancelled"), 3000)

    def update_sleep_timer(self):
        if self.sleep_timer_remaining > 0:
            self.sleep_timer_remaining -= 1
            
            mins, secs = divmod(self.sleep_timer_remaining, 60)
            self.lbl_sleep_status.setText(f"🕒 {mins}:{secs:02d}")
            self.lbl_sleep_status.show()
            
            if self.sleep_timer_remaining <= 0:
                self.sleep_countdown_timer.stop()
                self.lbl_sleep_status.hide()
                print("[*] Sleep timer reached 0. Exiting application.")
                self.close()
        else:
            self.lbl_sleep_status.hide()

    def toggle_pip_mode(self):
        if not hasattr(self, 'player_frames') or len(self.player_frames) <= self.active_player_idx:
            return
            
        active_frame = self.player_frames[self.active_player_idx]
        
        # Check if already in PiP mode
        if hasattr(active_frame, 'is_pip') and active_frame.is_pip:
            # Return to grid layout
            active_frame.is_pip = False
            active_frame.setParent(self.player_container)
            active_frame.setWindowFlags(Qt.Widget)
            
            # Re-draw layout
            self.draw_layout()
            active_frame.show()
            
            # Refocus main window
            self.raise_()
            self.activateWindow()
            
            print("[*] Exited PiP mode")
        else:
            # Enter PiP mode
            active_frame.is_pip = True
            
            # Remove from grid layout
            self.grid_layout.removeWidget(active_frame)
            
            # Set window flags for borderless always-on-top window
            active_frame.setParent(None)
            active_frame.setWindowFlags(
                Qt.Window | 
                Qt.FramelessWindowHint | 
                Qt.WindowStaysOnTopHint | 
                Qt.CustomizeWindowHint
            )
            
            # Set default size (e.g., 480x270 for 16:9 ratio)
            active_frame.resize(480, 270)
            
            # Position at bottom-right of primary screen
            screen_geo = QApplication.primaryScreen().geometry()
            x = screen_geo.width() - 500
            y = screen_geo.height() - 320
            active_frame.move(x, y)
            
            # Show window
            active_frame.show()
            active_frame.raise_()
            active_frame.activateWindow()
            
            print("[*] Entered PiP mode")

    def toggle_active_player_recording(self):
        if hasattr(self, 'player_frames') and len(self.player_frames) > self.active_player_idx:
            active_frame = self.player_frames[self.active_player_idx]
            w = active_frame.mpv_widget
            if not w or not hasattr(w, 'current_url') or not w.current_url:
                print("[-] No stream playing on active player to record.")
                return
                
            url = w.current_url
            
            # Check if already recording
            if hasattr(w, 'recording_path') and w.recording_path:
                w.stop_recording(url)
                print(f"[*] Stopped recording active player.")
            else:
                # Find channel name
                chan_name = "Kênh"
                for c in self.channels:
                    if c.get("url") == url:
                        chan_name = c.get("name", "Kênh")
                        break
                        
                import datetime
                now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # Clean channel name
                clean_name = "".join(c for c in chan_name if c.isalnum() or c in (' ', '_', '-')).strip()
                clean_name = clean_name.replace(" ", "_")
                filename = f"{clean_name}_{now_str}.ts"
                
                if getattr(sys, 'frozen', False):
                    root_dir = os.path.dirname(sys.executable)
                else:
                    root_dir = os.path.dirname(os.path.abspath(__file__))
                recordings_dir = os.path.join(root_dir, "recordings")
                filepath = os.path.join(recordings_dir, filename)
                
                success = w.start_recording(filepath, url)
                if success:
                    print(f"[+] Recording started: {filepath}")

    def save_session_state(self):
        try:
            config = config_manager.load_config()
            
            # Gather playing channels on each screen
            active_channels = []
            for frame in self.player_frames:
                w = frame.mpv_widget
                if w and hasattr(w, 'current_url') and w.current_url:
                    # Find channel info
                    chan_name = "Kênh"
                    for c in self.channels:
                        if c.get("url") == w.current_url:
                            chan_name = c.get("name", "Kênh")
                            break
                    active_channels.append({
                        "index": frame.index,
                        "name": chan_name,
                        "url": w.current_url
                    })
            
            session = {
                "num_screens": self.num_screens,
                "active_player_idx": self.active_player_idx,
                "active_res_filter": getattr(self, 'active_res_filter', 'all'),
                "sort_mode": self.sort_selector.currentText() if hasattr(self, 'sort_selector') else "Tên A-Z",
                "volume": self.volume_slider.value(),
                "is_app_muted": getattr(self, 'is_app_muted', False),
                "active_channels": active_channels
            }
            
            config["last_session"] = session
            config_manager.save_config(config)
            print("[+] Saved session state successfully.")
        except Exception as e:
            print(f"[-] Error saving session state: {e}")

    def restore_session_state(self):
        try:
            config = config_manager.load_config()
            session = config.get("last_session")
            if not session:
                return
                
            # Restore filters & sorting
            res_filter = session.get("active_res_filter", "all")
            self.active_res_filter = res_filter
            # Highlight the filter chip button visually
            if hasattr(self, 'filter_chips'):
                for key, btn in self.filter_chips.items():
                    btn.setProperty("active", "true" if key == res_filter else "false")
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                    
            if hasattr(self, 'sort_selector') and "sort_mode" in session:
                idx = self.sort_selector.findText(session["sort_mode"])
                if idx >= 0:
                    self.sort_selector.setCurrentIndex(idx)
                    
            # Run channel filtering
            self.filter_channels()
                    
            # Restore volume & mute
            vol = session.get("volume", 80)
            self.volume_slider.setValue(vol)
            self.is_app_muted = session.get("is_app_muted", False)
            self.btn_volume.setText("\uf026" if self.is_app_muted else "\uf028")
            
            # Restore screen count layout
            num_screens = session.get("num_screens", 1)
            self.num_screens = num_screens
            if hasattr(self, 'view_combo'):
                self.view_combo.blockSignals(True)
                if num_screens == 4:
                    self.view_combo.setCurrentIndex(2)
                elif num_screens == 2:
                    self.view_combo.setCurrentIndex(1)
                else:
                    self.view_combo.setCurrentIndex(0)
                self.view_combo.blockSignals(False)
            self.draw_layout()
            
            # Restore active channel selection index
            active_player_idx = session.get("active_player_idx", 0)
            self.active_player_idx = active_player_idx
            self.select_active_screen(active_player_idx)
            
            # Set default title
            self.lbl_channel_title.setText(_t("player_no_channel").format(active_player_idx + 1))
            self.lbl_epg_now.setText("")
                                
            print("[+] Restored last session state successfully (without autoplaying channels).")
        except Exception as e:
            print(f"[-] Error restoring session: {e}")

    def closeEvent(self, event):
        # Save session state before closing
        self.save_session_state()
        
        # Stop status checker thread
        if self.checker_thread and self.checker_thread.isRunning():
            self.checker_thread.stop()
            self.checker_thread.wait()
            
        # Stop playlist worker thread
        if hasattr(self, 'playlist_worker') and self.playlist_worker and self.playlist_worker.isRunning():
            self.playlist_worker.terminate()
            self.playlist_worker.wait()

        # Stop EPG thread
        if hasattr(self, 'epg_thread') and self.epg_thread and self.epg_thread.isRunning():
            self.epg_thread.terminate()
            self.epg_thread.wait()
            
        # Ensure detached PiP frames are closed/destroyed
        for frame in self.player_frames:
            if hasattr(frame, 'is_pip') and frame.is_pip:
                frame.close()
                
        super().closeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                print("[*] Window minimized. Pausing all active players to save resources...")
                for frame in self.player_frames:
                    if frame.mpv_widget and frame.mpv_widget.player:
                        try:
                            if not frame.mpv_widget.player.pause:
                                frame.mpv_widget.player.pause = True
                                frame._auto_paused = True
                        except Exception:
                            pass
            else:
                print("[*] Window restored. Resuming players that were auto-paused...")
                for frame in self.player_frames:
                    if frame.mpv_widget and frame.mpv_widget.player:
                        try:
                            if getattr(frame, '_auto_paused', False):
                                frame.mpv_widget.player.pause = False
                                frame._auto_paused = False
                        except Exception:
                            pass
        super().changeEvent(event)

    # Stylesheet application (Premium Dark Glassmorphism)
    def apply_theme(self):
        style = """
            /* General Palette */
            QWidget {
                background-color: #0A0A0F;
                color: #e0e0e6;
                font-family: "Outfit", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            
            /* Sidebar Styling */
            QFrame#Sidebar {
                background-color: rgba(14, 14, 20, 0.95);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            QLabel#LogoLabel {
                color: #00e5ff;
                margin-bottom: 5px;
                font-weight: 800;
            }
            
            QFrame#SidebarLine {
                background-color: rgba(255, 255, 255, 0.05);
                max-height: 1px;
            }
            
            QPushButton#SidebarBtn {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                color: #888896;
                font-family: "Font Awesome 6 Free";
                font-weight: 900;
                font-size: 18px;
            }
            QPushButton#SidebarBtn:hover {
                background-color: rgba(0, 229, 255, 0.08);
                color: #00e5ff;
            }
            
            QPushButton#SidebarBtnActive {
                background-color: rgba(0, 229, 255, 0.1);
                border: 1px solid rgba(0, 229, 255, 0.4);
                border-radius: 12px;
                color: #00e5ff;
                font-family: "Font Awesome 6 Free";
                font-weight: 900;
                font-size: 18px;
            }
            
            /* Collapsible panel buttons styling */
            QPushButton#HeaderToggleBtn {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e0e0e6;
                font-size: 16px;
            }
            QPushButton#HeaderToggleBtn:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #00e5ff;
                border-color: rgba(0, 229, 255, 0.5);
            }
            
            QPushButton#HeaderEpgBtn {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e0e0e6;
                font-size: 12px;
                font-weight: 500;
                padding: 0px 12px;
            }
            QPushButton#HeaderEpgBtn:hover {
                background-color: rgba(255, 255, 255, 0.05);
                color: #00e5ff;
                border-color: rgba(0, 229, 255, 0.5);
            }
            QPushButton#HeaderEpgBtn[active="true"] {
                background-color: rgba(124, 77, 255, 0.15);
                border: 1px solid rgba(124, 77, 255, 0.5);
                color: #7c4dff;
            }
            
            /* Channel Panel & EPG Panel (Middle / Right) */
            QFrame#ChannelPanel {
                background-color: rgba(18, 18, 26, 0.95);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            QLabel#ViewTitleLabel {
                color: #ffffff;
                margin-bottom: 2px;
                font-weight: bold;
            }
            
            QLineEdit#SearchBar {
                background-color: rgba(10, 10, 15, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 10px 14px;
                color: #ffffff;
            }
            QLineEdit#SearchBar:focus {
                border: 1px solid #7c4dff;
            }
            
            QComboBox#CategorySelector {
                background-color: rgba(10, 10, 15, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                padding: 8px 12px;
                color: #e0e0e6;
            }
            QComboBox#CategorySelector::drop-down {
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
            }
            QComboBox#CategorySelector:focus {
                border: 1px solid #7c4dff;
            }
            
            /* Resolution filter chip buttons */
            QPushButton#FilterChip {
                background-color: rgba(30, 30, 38, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
                padding: 6px 14px;
                color: #888896;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton#FilterChip:hover {
                background-color: rgba(0, 229, 255, 0.08);
                border-color: rgba(0, 229, 255, 0.3);
                color: #00e5ff;
            }
            QPushButton#FilterChipActive {
                background-color: rgba(124, 77, 255, 0.15);
                border: 1px solid rgba(124, 77, 255, 0.6);
                border-radius: 14px;
                padding: 6px 14px;
                color: #7c4dff;
                font-size: 11px;
                font-weight: bold;
            }
            
            QListWidget#ChannelList {
                background-color: transparent;
                border: none;
                outline: 0;
            }
            QListWidget#ChannelList::item {
                background-color: rgba(30, 30, 38, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.03);
                border-radius: 10px;
                padding: 0px;
                margin-bottom: 8px;
                color: #e0e0e6;
            }
            QListWidget#ChannelList::item:hover {
                background-color: rgba(45, 45, 58, 0.7);
                border: 1px solid rgba(0, 229, 255, 0.25);
            }
            QListWidget#ChannelList::item:selected {
                background-color: rgba(124, 77, 255, 0.18);
                border: 1px solid rgba(124, 77, 255, 0.6);
                color: #ffffff;
            }
            
            QListWidget#EpgList {
                background-color: transparent;
                border: none;
                outline: 0;
            }
            QListWidget#EpgList::item {
                background-color: rgba(30, 30, 38, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.03);
                border-radius: 10px;
                padding: 8px 12px;
                margin-bottom: 8px;
                color: #e0e0e6;
            }
            
            /* Player Panel (Right) */
            QFrame#PlayerPanel {
                background-color: #050508;
            }
            
            QFrame#HeaderBar {
                background-color: rgba(14, 14, 20, 0.85);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            QLabel#ChannelTitle {
                color: #ffffff;
            }
            
            QWidget#PlayerContainer {
                background-color: #030305;
            }
            
            /* Player selection frame borders for multi-view */
            QFrame#PlayerFrame {
                border: none;
                border-radius: 12px;
                background-color: #030305;
            }
            QFrame#PlayerFrame[active="true"] {
                border: 2px solid #00e5ff;
            }
            QFrame#PlayerFrame[fullscreen="true"] {
                border: none;
                border-radius: 0;
            }
            
            /* Controls Bar — removed from flow, now a glass overlay */
            QFrame#GlassControls {
                background: transparent;
                border: none;
                border-radius: 16px;
            }
            
            /* Primary action buttons (Play, Fullscreen) */
            QPushButton#GlassBtnPrimary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #00e5ff);
                border: none;
                border-radius: 18px;
                color: #121214;
                font-family: "Font Awesome 6 Free";
                font-weight: 900;
                font-size: 15px;
            }
            QPushButton#GlassBtnPrimary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9575ff, stop:1 #33ecff);
            }
            QPushButton#GlassBtnPrimary:pressed {
                background: #5028b4;
            }
            
            /* Secondary action buttons */
            QPushButton#GlassBtn {
                background: rgba(30, 30, 40, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 17px;
                color: #e2e8f0;
                font-family: "Font Awesome 6 Free";
                font-weight: 900;
                font-size: 14px;
                padding-left: 0px;
                padding-right: 0px;
            }
            QPushButton#GlassBtn:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(0, 229, 255, 0.5);
                color: #00e5ff;
            }
            QPushButton#GlassBtn:pressed {
                background: rgba(0, 229, 255, 0.3);
            }
            QPushButton#GlassBtn:checked {
                background: rgba(0, 229, 255, 0.15);
                border-color: #00e5ff;
                color: #00e5ff;
            }
            QPushButton#GlassBtn::menu-indicator {
                image: none;
                width: 0px;
                height: 0px;
            }
            
            /* HW chip badge */
            QPushButton#GlassChip {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                color: rgba(180, 180, 200, 200);
                font-size: 10px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton#GlassChip:checked {
                background: rgba(0, 229, 255, 0.15);
                border-color: #00e5ff;
                color: #00e5ff;
            }
            QPushButton#GlassChip:hover {
                border-color: rgba(0, 229, 255, 0.5);
            }
            
            /* Glass combos */
            QComboBox#GlassCombo {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 4px 8px;
                color: rgba(220, 220, 240, 230);
                font-size: 11px;
            }
            QComboBox#GlassCombo:hover {
                border-color: rgba(124, 77, 255, 0.5);
            }
            QComboBox#GlassCombo::drop-down {
                border: none;
                width: 16px;
            }
            
            /* Glass volume slider */
            QSlider#GlassVolumeSlider::groove:horizontal {
                border: none;
                height: 3px;
                background: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
            }
            QSlider#GlassVolumeSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #00e5ff);
                border-radius: 2px;
            }
            QSlider#GlassVolumeSlider::handle:horizontal {
                background: #ffffff;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
                border: 1px solid rgba(124, 77, 255, 0.8);
            }
            QSlider#GlassVolumeSlider::handle:horizontal:hover {
                background: #00e5ff;
                border-color: #00e5ff;
            }
            
            /* Glass progress slider */
            QSlider#GlassProgressSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: rgba(255, 255, 255, 0.12);
                border-radius: 2px;
            }
            QSlider#GlassProgressSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #00e5ff);
                border-radius: 2px;
            }
            QSlider#GlassProgressSlider::handle:horizontal {
                background: #ffffff;
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
                border: 1px solid rgba(124, 77, 255, 0.8);
            }
            QSlider#GlassProgressSlider::handle:horizontal:hover {
                background: #00e5ff;
                border-color: #00e5ff;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            
            QComboBox#AspectCombo {
                background-color: #121214;
                border: 1px solid #282830;
                border-radius: 6px;
                padding: 4px 6px;
                color: #e0e0e6;
            }
            
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #282830;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #7c4dff;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                height: 12px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #00e5ff;
            }
            
            QLabel#TimeLabel {
                color: #888896;
                font-size: 12px;
            }
            
            /* Scrollbar customization */
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.1);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(124, 77, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        self.setStyleSheet(style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(18, 18, 20))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(24, 24, 28))
    dark_palette.setColor(QPalette.AlternateBase, QColor(18, 18, 20))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(24, 24, 28))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(124, 77, 255))
    dark_palette.setColor(QPalette.Highlight, QColor(124, 77, 255))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    
    window = K20IPTVPlayer()
    window.show()
    sys.exit(app.exec())
