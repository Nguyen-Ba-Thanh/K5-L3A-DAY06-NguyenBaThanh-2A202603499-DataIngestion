# Benchmark đã cố định

20 câu với đáp án và evidence nguyên văn: 15 dev ở chương I–IX, 5 test ở X–XII. Có 8 câu filter chương: 5 dev, 3 test. Phạm vi chương được viết trong câu hỏi trước retrieval; không lấy gold source/page làm filter.

freeze.json ghi SHA-256 corpus, câu hỏi, cấu hình, thời điểm và tiêu chí chọn. run.py từ chối input thay đổi. selection.json ghi lựa chọn sau dev, trước truy xuất test. Không chỉnh cấu hình theo test. Chạy lại cùng bộ test để tái lập không tạo holdout mới.

page là ID đơn vị nguồn, không phải trang in. Evidence là cả đoạn đã kiểm tra tồn tại sau chuẩn hóa; metric nghiêm hơn câu trả lời tối thiểu. Bằng chứng tương đương cần người chấm xác nhận và ghi riêng.

Bộ câu hỏi và đáp án đã được học viên kiểm tra, xác nhận ngày 14/11/2026. Cách dùng công cụ hỗ trợ được ghi trong báo cáo. q17 giải thích chơi chữ trong đáp án; gold paragraph chỉ nêu quy tắc porpoise, còn câu purpose ở phần tiếp theo trong nguồn và trace A/B/C. Giữ nguyên giới hạn này sau test.

Nguy cơ rò rỉ: cùng sách/nhân vật/từ vựng; model pretrained có thể đã thấy tác phẩm. Bộ hiện tại chủ yếu paraphrase và metadata, chưa phủ đầy đủ điều kiện/ngoại lệ phức tạp.
