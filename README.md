# Day 06 · Data Ingestion Engineering — Nguyễn Bá Thành

Pipeline so sánh ba chiến lược truy xuất bằng chứng trên Alice’s Adventures in Wonderland. Corpus có 67 đơn vị nguồn ≥1.500 ký tự, benchmark 20 câu (15 dev / 5 test), embedding thật 384 chiều và Qdrant lưu bền vững. Không cần Docker hoặc API key.

## Cài đặt và chạy từ root repo

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r starter/requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m starter.src.run --validate-only
.\.venv\Scripts\python.exe -m starter.src.run
```

Lần đầu cần mạng tải thư viện/model. Sau khi có cache, chạy thêm --offline. Linux/macOS dùng python3 và .venv/bin/python. Đã kiểm chứng trên Windows, Python 3.10.1, CPU; môi trường đầy đủ ở results/baseline/environment.json. Model ghim revision trong configs/strategies.json, cache ở .cache/huggingface/. Không gửi corpus lên API.

## Kết quả thực tế

| Chiến lược | Dev Hit@1 | Dev Hit@3 | Test Hit@1 | Test Hit@3 | Chunks |
|---|---|---|---|---|---|
| A: fixed 500/overlap 50 | 5/15 | 7/15 | 1/5 | 2/5 | 343 |
| B: đoạn tối đa 900 | 7/15 | 12/15 | 2/5 | 4/5 | 222 |
| C: B + filter chương | 7/15 | 13/15 | 2/5 | 5/5 | 222 |

Cùng model all-MiniLM-L6-v2, cosine exact search và top-3. Chọn C theo dev trước truy xuất test. Không chỉnh cấu hình theo test. Chỉ 5 câu test nên không kết luận ưu thế tổng quát. API cost 0 USD; không tính điện/phần cứng.

## Tài liệu bài nộp

- [Thông tin học viên](STUDENT.md).
- [Dữ liệu và quyền sử dụng](data/README.md), [manifest](data/manifest.json).
- [Benchmark](benchmark/README.md), [cấu hình](configs/strategies.json).
- [Kết quả và audit](results/README.md), [nhật ký](artifacts/experiment_log.csv).
- [Báo cáo cá nhân](report/individual/2A202603499_NguyenBaThanh.md).
- [Hướng dẫn đề bài](GUIDE.md), [quy tắc](RULES.md), [benchmark bắt buộc](BENCHMARK.md), [rubric](RUBRIC.md), [checklist nộp](SUBMISSION.md).

Mỗi lần chạy tạo results/runs/<timestamp>/ và cập nhật results/latest.json; baseline/ lưu lần chạy đầu để nộp. Model cache, .venv và .qdrant không commit. Kho vector được dựng lại khi chạy pipeline. Nạp lại thay toàn bộ snapshot, loại chunk cũ; đã kiểm tra count và mở lại kho. Thay snapshot không crash-atomic: nếu gián đoạn, chạy lại ingest. Lỗi có errors.log/failure.json, không fallback vector giả.

## Trạng thái bài nộp

Code và thực nghiệm đã chạy; 6 tests đạt, kết quả tái lập đúng. Ngày 14/11/2026, Nguyễn Bá Thành xác nhận đã kiểm tra toàn bộ nhận xét. Ba bảng audit hiện có reviewer=Nguyễn Bá Thành, status=human_reviewed; 45 bản ghi metadata có human_correct=1.

[Tổng hợp đánh giá thủ công](results/baseline/human_audit_summary.json). Có thể tính lại bằng:

```powershell
.\.venv\Scripts\python.exe -m starter.src.audit results/baseline
```

Bài vẫn giữ phần khai báo công cụ hỗ trợ và giới hạn phương pháp trong báo cáo. Việc đẩy code lên GitHub không thay thế bước nộp link theo hướng dẫn lớp. Mỗi lần commit phải được người dùng xác nhận trước.
