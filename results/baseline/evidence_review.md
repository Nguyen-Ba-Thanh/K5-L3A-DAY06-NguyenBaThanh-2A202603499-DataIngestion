# Rà soát nguồn và đáp án

Lần rà soát này giữ nguyên corpus, bộ câu hỏi, cấu hình và kết quả ban đầu. Bản rà soát ban đầu được lập bằng công cụ hỗ trợ; Nguyễn Bá Thành đã kiểm tra và xác nhận nội dung ngày 14/11/2026.

## Đối chiếu dữ liệu

Đã dựng lại nội dung từng chương từ file gốc, sau đó đối chiếu 67 đơn vị theo offset. Cả 20 đoạn gold đều xuất hiện đúng nguồn. Với 45 kết quả truy xuất thuộc tập test, source, unit, chương, ngôn ngữ và vị trí cắt đều khớp dữ liệu nguồn.

[Chi tiết kiểm tra nguồn](source_verification.json), [nhận xét từng câu](evidence_review.json).

## Nhận xét từng câu

| Câu | Nhận xét |
|---|---|
| q01 | Lọ có nhãn mứt cam nhưng rỗng; đoạn trích nói trực tiếp điều này. |
| q02 | Alice kiểm tra chữ poison trước khi uống. Đoạn trích giữ cả quyết định và lý do. |
| q03 | Dòng EAT ME được xếp bằng quả lý chua khô trên bánh. |
| q04 | Đoạn trích nêu chiếc quạt làm Alice nhỏ lại; nguồn ở phần trước xác định đó là quạt của Rabbit. |
| q05 | Alice thử tiếng Anh rồi đoán Mouse là người Pháp và chuyển sang tiếng Pháp. Câu hỏi yêu cầu tổng hợp hai chi tiết. |
| q06 | Alice chia comfits làm giải thưởng, mỗi con vật một chiếc. |
| q07 | Dodo trao chiếc đê khâu; các đoạn liền trước xác định người nhận là Alice. |
| q08 | Rabbit yêu cầu lấy một đôi găng tay và một chiếc quạt. |
| q09 | Những viên sỏi biến thành bánh nhỏ khi nằm trên sàn. |
| q10 | Caterpillar nói một phía làm Alice cao hơn, phía kia làm thấp hơn. |
| q11 | Pigeon không tin vì chưa từng thấy bé gái có chiếc cổ như vậy. |
| q12 | Alice nói súp có quá nhiều tiêu trong lúc đang hắt hơi. |
| q13 | Hatter nói bơ không phù hợp với bộ máy đồng hồ. |
| q14 | Nhím sống làm bóng, hồng hạc sống làm gậy. |
| q15 | Đoạn trích có taught us, cơ sở của lối chơi chữ với Tortoise. Giải thích chơi chữ là diễn giải, không phải một câu giải thích nguyên văn. |
| q16 | Lời hát nêu porpoise đứng sau và giẫm lên đuôi whiting. |
| q17 | Gold nêu quy tắc đi cùng porpoise nhưng chưa chứa lời Alice nhắc purpose. Phần giải thích nằm tiếp theo trong cùng nguồn; không sửa gold sau khi đã xem test. |
| q18 | Nhân chứng đầu tiên là Hatter, mang tách trà và bánh mì phết bơ. |
| q19 | Đoạn trích mô tả đủ việc cho guinea-pig vào túi vải, đầu vào trước, rồi ngồi lên túi. |
| q20 | Gold có lời pack of cards của Alice. Đoạn liền sau mô tả cả bộ bài bay lên và lao vào Alice, xác nhận đúng thời điểm câu hỏi. |

## Điểm cần lưu ý khi đọc kết quả

Bốn gold của tập dev dài hơn cửa sổ 500 ký tự của A: q01 (715), q02 (701), q04 (556), q05 (559). A không thể chứa đủ bất kỳ gold nào trong bốn câu này trong một chunk. Vì vậy, so sánh A–B chịu ảnh hưởng của cách đặt gold và kích thước chunk, không chỉ cách giữ ranh giới đoạn.

q17 cần phần tiếp theo trong nguồn để giải thích đầy đủ lối chơi chữ. Gold được giữ nguyên sau khi xem test và hạn chế này được nêu trong báo cáo. Các nhãn chấm nội dung vẫn cần phân biệt bằng chứng trực tiếp với lời diễn giải.

Nếu thay gold hoặc chỉnh cấu hình, phải ghi rõ phiên bản và dùng bộ test mới chưa xem để đánh giá độc lập. Không dùng kết quả hiện tại như bằng chứng rằng bộ đã chỉnh đã được kiểm thử.
