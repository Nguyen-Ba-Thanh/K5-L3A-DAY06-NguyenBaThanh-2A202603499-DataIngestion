# Kết quả thực nghiệm

baseline/ lưu lần chạy đầu 13/11/2026: 60 lượt truy vấn × top-3, metrics dev/test, chunks, tài nguyên, môi trường, lựa chọn trên dev và log. Model thật 384 chiều, Qdrant persistent, exact cosine, API cost 0 USD.

baseline/audit_*.csv chưa có nhãn thủ công. Học viên tự đọc nguồn và điền điểm/lý do/người chấm. ai_review/ chứa đề xuất Codex đã đọc nội dung; chưa được học viên xác nhận, không tính là human audit. AI đã thấy metric, nên không phải chấm mù; không suy coherence/grounding từ exact hit.

Coherence: 10 unit đầu, anchor giữa unit; A có 11 chunk do overlap ở unit 10, lấy trung bình trong vị trí rồi trung bình 10 vị trí. B/C có 10 chunk giống nhau. Grounding: 5 test × 3 cấu hình. Metadata: code đối chiếu 45 bản ghi test với nguồn, tách khỏi xác nhận thủ công.

Chạy mới tạo results/runs/<UTC timestamp>/, không ghi đè baseline hay nhãn. latest.json mặc định trỏ baseline trong bản nộp; khi chạy sẽ trỏ run mới tại máy. runs không commit. Lỗi tạo errors.log/failure.json, không fallback vector giả.

test_output.txt lưu 6 tests đạt. verification.json ghi so sánh lần chạy lại: 6 dòng metric và ID top-3/evidence hit của cả 60 trace giống baseline.

Xem th?m [bi?n b?n r? so?t ngu?n v? ??p ?n](ai_review/REVIEW.md), g?m nh?n x?t ?? 20 c?u v? ?nh h??ng c?a ?? d?i gold ??n c?u h?nh A.
