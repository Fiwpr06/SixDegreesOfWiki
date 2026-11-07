# Kịch bản tự demo SixDegreesOfWiki

## Chuẩn bị

Mở PowerShell:

```powershell
cd D:\AI_Seminar\SixDegreesOfWiki
& .\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Nếu chưa có `.venv`, tạo và cài thư viện theo [README.md](README.md). Mở [http://127.0.0.1:8501](http://127.0.0.1:8501). Cần Internet để xác thực bài viết và lấy liên kết chưa có trong cache. Nhấn `Ctrl+C` trong PowerShell để dừng ứng dụng.

## Demo 1: Tìm đường trực tiếp

1. Trong sidebar chọn **English**, **Bidirectional IDS**, độ sâu tối đa **1**.
2. Nhập bài bắt đầu `Python (programming language)` và bài đích `ADMB`. Bạn cũng có thể dán URL đầy đủ như `https://en.wikipedia.org/wiki/Python_(programming_language)`; ứng dụng sẽ hiển thị tiêu đề đã nhận bên dưới ô nhập.
3. Bấm **Bắt đầu phân tích liên kết**.
4. Quan sát khung **Tiến trình tìm kiếm trực tiếp** khi app chạy: mức sâu, phía duyệt, bài hiện tại, nút thăm/mở rộng, cache và thời gian. Sau đó xem kết quả: đường đi `Python (programming language) → ADMB`, độ sâu 1, số bài trung gian 0, đồ thị tương tác và link tới Wikipedia.

Số nút và thời gian có thể thay đổi theo Wikipedia và cache. Nếu mạng/API chậm, tăng giới hạn thời gian trong sidebar.

## Demo 2: So sánh thuật toán và cache

1. Đổi thuật toán thành **So sánh cả hai**, giữ cặp bài và độ sâu 1.
2. Chạy lại. Bảng đối chiếu cho thấy thời gian, số nút thăm, nút mở rộng và cache hit của từng thuật toán.
3. Chạy thêm lần nữa để thấy cache hit tăng. Thuật toán chạy thứ hai cũng có thể hưởng lợi từ cache do thuật toán thứ nhất tạo ra.

Để demo đường 2 bước, chọn riêng **Bidirectional IDS**, giữ giới hạn mặc định, rồi nhập `https://en.wikipedia.org/wiki/World_War_II` và `https://en.wikipedia.org/wiki/Japan`. Lần thử trên Wikipedia thật ngày 07/11/2026 tìm được `World War II → Buddhist philosophy → Japan` ở độ sâu 2, không cần chế độ không giới hạn. Đường đi, thời gian và số nút có thể đổi theo Wikipedia, cache và tốc độ mạng. Nếu tìm kiếm dừng với `timeout` hoặc `node_limit`, tăng giới hạn tương ứng rồi thử lại.

## Demo 3: Lịch sử và JSON

1. Mở tab **Lịch sử & báo cáo**. Các lần tìm kiếm đã được lưu trong `wiki_cache.db`.
2. Lọc ngôn ngữ, chọn một phiên, rồi bấm **Tải báo cáo của phiên này**.
3. Trong tab tìm kiếm, bấm **Tải báo cáo JSON** dưới kết quả hiện tại. File chứa đường đi, URL từng bài, chỉ số hiệu năng và trạng thái.

## Kiểm thử và demo terminal

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe .\demo_stage1.py
```

`demo_stage1.py` chỉ minh họa tầng API và cache trong terminal. Ứng dụng Streamlit là demo đầy đủ.
