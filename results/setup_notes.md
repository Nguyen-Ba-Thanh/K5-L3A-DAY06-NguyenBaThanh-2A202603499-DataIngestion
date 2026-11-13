# Ghi chú thiết lập thực tế — 13/11/2026

- Máy có Python 3.10.1, torch 2.11.0+cu128. Inference dùng CPU.
- Docker daemon chưa hoạt động; chọn Qdrant local trước benchmark.
- Sandbox chặn tải mạng; dependencies/corpus được tải qua phiên có quyền mạng.
- Tải model gặp WinError 1314 vì symlink Windows; đổi sang file thường, cùng model/revision.
- Needle q04/q08 được sửa theo bản gốc trước freeze và retrieval.
- Run đầu thành công. Có 3 chunk B/C vượt 256 token, được ghi resources; không đổi cấu hình sau test.
- Sau test bỏ định nghĩa code trùng hệt, không đổi thuật toán; tests và tái lập chỉ số đạt.
- Trước commit sửa tài liệu tiếng Việt về UTF-8 và giữ byte đầu vào bằng .gitattributes.
