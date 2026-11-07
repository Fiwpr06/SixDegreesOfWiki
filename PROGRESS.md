# Tiến độ SixDegreesOfWiki

Cập nhật: 07/11/2026 (giờ Việt Nam)

| Hạng mục | Trạng thái | Bằng chứng |
| --- | --- | --- |
| SQLite và cache MediaWiki | Hoàn thành | Schema, nâng cấp DB cũ, cache links/backlinks có TTL, phân trang và lọc namespace 0. |
| Standard IDS | Hoàn thành | Kiểm thử đường ngắn nhất, chu trình, độ sâu, timeout và giới hạn nút. |
| Bidirectional IDS | Hoàn thành | Duyệt xuôi/ngược theo cạnh có hướng; kiểm tra giao điểm ngay khi duyệt, đọc backlinks theo trang và dùng lại mức sâu phía xuôi. |
| Giao diện Streamlit | Hoàn thành | Form, gợi ý bài viết, thiết lập tìm kiếm, chỉ số, so sánh và đồ thị PyVis. |
| Lịch sử và báo cáo | Hoàn thành | Lưu các lượt tìm kiếm, lọc lịch sử, tải báo cáo JSON. |

## Xác minh

- Bộ kiểm thử tự động: 22/22 bài qua, gồm API, thuật toán, chế độ không giới hạn, nhận URL có dấu `_`, nâng cấp SQLite, lịch sử, JSON và Streamlit AppTest. Thuật toán còn được đối chiếu với BFS trên 30 đồ thị có hướng nhỏ.
- Đã gỡ bước kiểm tra nhanh đường 1–2 cạnh; Standard IDS và Bidirectional IDS tự duyệt từng mức độ sâu. Đã thêm tùy chọn không giới hạn ba ngưỡng tìm kiếm trong giao diện.
- Đã thêm khung tiến trình trực tiếp với sự kiện được lấy mẫu: mức sâu, phía xuôi/ngược, bài hiện tại, số nút thăm/mở rộng, cache hit/miss và thời gian. Việc ghi nhận không đổi thứ tự duyệt.
- Tìm đường bằng dữ liệu cache MediaWiki thật: `Python (programming language) → ADMB`, độ sâu 1, bằng cả hai thuật toán.
- Bidirectional IDS với giới hạn mặc định đã tìm thấy `World War II → Buddhist philosophy → Japan` trên Wikipedia thật: độ sâu 2, 1.866 nút thăm, khoảng 0,56 giây trong lần thử này. Các chỉ số có thể thay đổi theo dữ liệu và mạng.
- Streamlit chạy trên `127.0.0.1:8501`; health endpoint trả HTTP 200.
- Luồng tích hợp với Wikipedia thật đã xác thực tiêu đề, chạy cả hai thuật toán, lưu lịch sử SQLite, tạo báo cáo JSON và dựng đồ thị PyVis cho đường `Python (programming language) → ADMB`.
- Gợi ý tiêu đề đã được kiểm tra với tiền tố `Pyth` trên Wikipedia tiếng Anh.
- MediaWiki thật từng trả 710 liên kết xuôi cho `Python (programming language)` và 117 backlink cho `ADMB`. Các con số có thể đổi theo thời gian.

## Giới hạn vận hành

- Wikipedia có thể thay đổi; cache mặc định hết hạn sau 7 ngày.
- Độ sâu tối đa 6, thời gian và số trạng thái thăm có thể khiến truy vấn dừng sớm với trạng thái `timeout` hoặc `node_limit`.
- Truy vấn MediaWiki đang chạy có thể kéo dài tới timeout của một request trước khi giới hạn thời gian tìm kiếm được kiểm tra lại.
- Bảng so sánh dùng chung cache giữa hai thuật toán; thời gian đo không phải benchmark trên cache lạnh độc lập.
- Chế độ không giới hạn có thể chạy không dừng nếu không tồn tại đường đi hoặc không thể hoàn tất do giới hạn tài nguyên, API hay Python.
