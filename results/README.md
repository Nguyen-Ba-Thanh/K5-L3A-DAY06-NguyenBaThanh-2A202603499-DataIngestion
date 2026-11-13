# Kết quả thực nghiệm

baseline/ lưu lần chạy đầu 13/11/2026: 60 lượt truy vấn × top-3, metrics dev/test, chunks, tài nguyên, môi trường, lựa chọn trên dev và log. Model thật 384 chiều, Qdrant persistent, exact cosine, API cost 0 USD.

Các bảng baseline/audit_*.csv đã được điền điểm và nhận xét tiếng Việt bởi Codex, với reviewer=Codex (AI), status=ai_reviewed_pending_student. Cột human_correct vẫn để dành cho học viên xác nhận. Đây chưa phải nhãn do học viên chấm độc lập. AI đã thấy metric, nên không phải chấm mù; coherence và grounding được đánh giá theo nội dung, không suy từ exact hit.

Coherence: 10 unit đầu, anchor giữa unit; A có 11 chunk do overlap ở unit 10, lấy trung bình trong vị trí rồi trung bình 10 vị trí. B/C có 10 chunk giống nhau. Grounding: 5 test × 3 cấu hình. Metadata: code đối chiếu 45 bản ghi test với nguồn, tách khỏi xác nhận thủ công.

Chạy mới tạo results/runs/<UTC timestamp>/, không ghi đè baseline hay nhãn. latest.json mặc định trỏ baseline trong bản nộp; khi chạy sẽ trỏ run mới tại máy. runs không commit. Lỗi tạo errors.log/failure.json, không fallback vector giả.

test_output.txt lưu 6 tests đạt. verification.json ghi so sánh lần chạy lại: 6 dòng metric và ID top-3/evidence hit của cả 60 trace giống baseline.

Xem thêm [biên bản rà soát nguồn và đáp án](ai_review/REVIEW.md), gồm nhận xét đủ 20 câu và ảnh hưởng của độ dài gold đến cấu hình A.
