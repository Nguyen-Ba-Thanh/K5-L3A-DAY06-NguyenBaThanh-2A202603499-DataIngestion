# Kết quả thực nghiệm

baseline/ lưu lần chạy đầu 13/11/2026: 60 lượt truy vấn × top-3, metrics dev/test, chunks, tài nguyên, môi trường, lựa chọn trên dev và log. Model thật 384 chiều, Qdrant persistent, exact cosine, API cost 0 USD.

Các bảng baseline/audit_*.csv đã được Nguyễn Bá Thành xác nhận ngày 14/11/2026. Cả 91 hàng có status=human_reviewed; 31 hàng coherence và 15 hàng grounding có điểm và lý do, 45 hàng metadata có human_correct=1. [Kết quả tổng hợp](baseline/human_audit_summary.json). Các bản đề xuất trước xác nhận được giữ trong ai_review/ để truy vết quá trình; không phải một lượt chấm độc lập khác.

Coherence: 10 unit đầu, anchor giữa unit; A có 11 chunk do overlap ở unit 10, lấy trung bình trong vị trí rồi trung bình 10 vị trí. B/C có 10 chunk giống nhau. Grounding: 5 test × 3 cấu hình. Metadata: code đối chiếu 45 bản ghi test với nguồn, tách khỏi xác nhận thủ công.

Chạy mới tạo results/runs/<UTC timestamp>/, không ghi đè baseline hay nhãn. latest.json mặc định trỏ baseline trong bản nộp; khi chạy sẽ trỏ run mới tại máy. runs không commit. Lỗi tạo errors.log/failure.json, không fallback vector giả.

test_output.txt lưu 6 tests đạt. verification.json ghi so sánh lần chạy lại: 6 dòng metric và ID top-3/evidence hit của cả 60 trace giống baseline.

Xem thêm [biên bản rà soát nguồn và đáp án](ai_review/REVIEW.md), gồm nhận xét đủ 20 câu và ảnh hưởng của độ dài gold đến cấu hình A.
