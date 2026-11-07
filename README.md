# SixDegreesOfWiki

Ứng dụng tìm đường liên kết ngắn nhất giữa hai bài Wikipedia bằng **Standard IDS** và **Bidirectional IDS** trên đồ thị có hướng. Hỗ trợ Wikipedia tiếng Việt và tiếng Anh. Toàn bộ cache và lịch sử dùng **SQLite**; không cần MySQL.

## Chức năng

- Nhập tiêu đề hoặc dán URL bài viết (`https://en.wikipedia.org/wiki/World_War_II`), nhận gợi ý tiêu đề và xác thực bài viết thuộc namespace 0. Ngôn ngữ của URL được nhận diện tự động.
- Chạy từng thuật toán hoặc so sánh cả hai; chọn giới hạn độ sâu, thời gian, số trạng thái thăm hoặc bật chế độ không giới hạn.
- Xem đường đi, số bài trung gian, thời gian, nút đã thăm, nút mở rộng và tỷ lệ cache hit.
- Theo dõi trực tiếp mức sâu, chiều duyệt, bài đang xử lý, số nút và cache khi thuật toán chạy. Giao diện lấy mẫu sự kiện khoảng 4 lần/giây để tránh làm chậm tìm kiếm; đây không phải nhật ký của mọi nút. Thời gian dựng khung tiến trình được trừ khỏi thời gian tìm kiếm báo cáo.
- Xem đồ thị tương tác PyVis với đường đi được tô nổi bật.
- Xem lịch sử tìm kiếm trong SQLite và tải báo cáo JSON của kết quả hiện tại hoặc phiên cũ.

Khi hết thời gian hoặc đạt giới hạn nút, kết quả được ghi là **chưa xác định** (`timeout` hoặc `node_limit`), không bị báo nhầm thành không có đường. Khi tìm thấy, cả hai thuật toán trả về đường ngắn nhất trong các liên kết API đã cung cấp. Wikipedia thay đổi theo thời gian; cache mặc định có hạn 7 ngày.

Hai thuật toán chạy đúng vòng lặp độ sâu của mình, không dùng bước kiểm tra nhanh đường dài 1–2 cạnh hay ưu tiên tiêu đề liên quan. Bidirectional IDS cho phía xuất phát đi thêm bước ở độ sâu lẻ, dùng lại kết quả phía xuất phát khi mức sâu phía đó chưa đổi, và dừng ngay khi hai phía gặp nhau. Backlinks được đọc theo từng trang API; chỉ danh sách đã tải đầy đủ mới được ghi vào SQLite. Các thay đổi này giữ thứ tự thử độ sâu tăng dần và kết quả đường ngắn nhất. Cache SQLite giảm số lần tải lại cùng danh sách liên kết.

Chế độ **Không giới hạn** bỏ các ngưỡng do ứng dụng đặt cho độ sâu, thời gian tìm kiếm và số trạng thái thăm. Nó không bỏ timeout của từng HTTP request hay giới hạn vật lý của Python/máy tính. Nếu không có đường tới đích, truy vấn không giới hạn có thể chạy rất lâu; bạn có thể dừng phiên đang chạy trong Streamlit hoặc dừng máy chủ bằng `Ctrl+C`.

## Cài đặt và chạy

Yêu cầu Python 3.10 trở lên và Internet khi tra cứu bài chưa nằm trong cache.

```powershell
cd D:\AI_Seminar\SixDegreesOfWiki
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Mở [http://127.0.0.1:8501](http://127.0.0.1:8501). Trên máy đang dùng, nếu lệnh `python` trỏ tới Microsoft Store, có thể tạo môi trường bằng `C:\Users\ntbin\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv`. Môi trường `.venv` trong workspace đã được cài sẵn.

Sao chép `.env.example` thành `.env` nếu cần đổi đường dẫn SQLite hoặc giới hạn mặc định. Mặc định dữ liệu nằm trong `wiki_cache.db` tại thư mục dự án. File này và `.env` được `.gitignore` bỏ qua.

## Demo nhanh

Chọn `en`, nhập `Python (programming language)` và `ADMB`, chọn `Bidirectional IDS`, độ sâu `1`, rồi bấm **Bắt đầu phân tích liên kết**. Đường đi mong đợi là `Python (programming language) → ADMB`. Nếu thuật toán dừng trước khi đọc hết danh sách liên kết, danh sách chưa được ghi cache; dùng chế độ **So sánh cả hai** để quan sát tác dụng của cache khi Standard IDS đã tải đủ dữ liệu. Xem [DEMO.md](DEMO.md) để có kịch bản trình bày đầy đủ.

## Kiểm thử

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các bài kiểm thử thuật toán và API dùng đồ thị/response giả lập; kiểm thử giao diện dùng Streamlit AppTest. Một số kiểm thử giao diện trên máy này cần chạy ngoài sandbox của Codex vì sandbox chặn socket cục bộ.

## Cấu trúc

| Thành phần | Vai trò |
| --- | --- |
| `app.py` | Giao diện Streamlit, so sánh, lịch sử và tải JSON |
| `core/ids_search.py` | Standard IDS |
| `core/bidirectional_ids.py` | Bidirectional IDS qua backlinks |
| `core/wiki_api.py` | MediaWiki API, phân trang, namespace 0 và cache |
| `core/visualizer.py` | Đồ thị PyVis |
| `database/` | Schema, nâng cấp SQLite cũ và lịch sử |
| `utils/exporter.py` | Báo cáo JSON |

`PROJECT_PLAN.md` là kế hoạch ban đầu. Các tham chiếu MySQL trong kế hoạch đó đã được thay thế bằng SQLite trong mã nguồn và README này.
