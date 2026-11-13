# Pipeline hoàn thiện — Qdrant local

Bài nộp chọn Qdrant theo GUIDE.md. Xem [README root](../README.md) để setup và chạy từ root.

- ingestion.py: NFC, whitespace, JSONL/PDF và log trang rỗng/lỗi.
- prepare.py: 67 đơn vị, 20 câu hỏi, hash cố định trước retrieval.
- chunking.py: fixed 500/50 và gom đoạn tối đa 900 ký tự.
- embeddings.py: MiniLM thật, CPU, 384 chiều; không fallback.
- store.py: Qdrant persistent, exact cosine, allowlist filter và thay snapshot.
- evaluation.py: single-chunk Evidence Hit@1/3, alternative gold.
- run.py: ingest, reload/reopen, chọn trên dev trước test, xuất trace/audit.
- audit.py: tổng hợp human chỉ khi tất cả hàng có reviewer/reason/status phù hợp.

Nếu đứng trong starter/, chạy python -m src.run --offline; đường dẫn resolve theo file.

docker-compose.yml, init.sql và scripts/check_setup.py giữ làm tham khảo pgvector gốc, không thuộc store thí nghiệm hiện tại. Muốn kiểm tra riêng pgvector phải cài psycopg/python-dotenv và khởi động Docker.
