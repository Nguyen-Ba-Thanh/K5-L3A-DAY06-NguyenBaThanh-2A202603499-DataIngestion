# Báo cáo cá nhân — Day 6

Nguyễn Bá Thành · 2A202603499 · L3A.
Ngày chạy: 13/11/2026, khoảng 18:13–18:14 giờ Việt Nam (11:13–11:14 UTC).

## Dữ liệu và pipeline

Dữ liệu được chọn là bản tiếng Anh của Alice’s Adventures in Wonderland, do Lewis Carroll viết, lấy từ Project Gutenberg #11. Bản gốc được giữ kèm thông tin tác giả và điều khoản phân phối. Phần đưa vào truy xuất chỉ có văn bản, không gồm minh họa hay bản dịch. [Nguồn và quyền](../../data/README.md), [manifest](../../data/manifest.json).

Vì file text không có trang in, nội dung được chia thành 67 đơn vị nguồn, mỗi đơn vị có ít nhất 1.500 ký tự sau chuẩn hóa. Các đoạn được gom theo thứ tự trong cùng chương, nhắm tới khoảng 1.800 ký tự; phần cuối quá ngắn được gộp vào đơn vị trước. Bìa, mục lục và điều khoản phân phối không tham gia tìm kiếm. Không lặp nội dung để đạt số lượng. Trường page trong dữ liệu chỉ ID của đơn vị nguồn, không phải số trang PDF.

Văn bản được chuẩn hóa Unicode NFC và khoảng trắng, đồng thời giữ ranh giới giữa các đoạn. Nguồn đã có text nên không cần OCR. Code có hỗ trợ đọc PDF và ghi lỗi trang rỗng hoặc không trích xuất được; chức năng này không được sử dụng trong thí nghiệm hiện tại. Metadata: document_id, source URL, page=unit ID, chapter, chapter_title, language=en, chapter_start/end; chunk thêm start/end trong unit. Chapter lấy từ heading để lọc, source/page/offset để truy vết, không đoán ngày hiệu lực.

Embedding: sentence-transformers/all-MiniLM-L6-v2, revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf, 384 chiều, CPU, mean pooling/L2 normalization, batch 32; query/document cùng xử lý, giới hạn 256 token. Python 3.10.1, sentence-transformers 3.4.1, transformers 4.57.6, torch 2.11.0+cu128 (inference CPU). [Môi trường](../../results/baseline/environment.json).

Store: Qdrant client 1.13.3 local persistent, .qdrant/, day6_A/B/C, exact cosine top-3. Nạp lại thay toàn bộ snapshot để loại chunk cũ; count trước/sau reload và sau reopen đều 343/222/222. Thay snapshot không crash-atomic, cần ingest lại nếu gián đoạn. API cost 0 USD; chưa tính điện/phần cứng/mạng. [Lệnh setup/run](../../README.md).

## Cấu hình và benchmark

| Strategy | Chunking | Metadata filter |
|---|---|---|
| A | Fixed 500 ký tự, overlap 50, trong unit | Không |
| B | Gom đoạn tối đa 900 ký tự; đoạn dài tách whitespace | Không |
| C | Cùng chunks và vectors với B | Chapter khi câu hỏi cho sẵn |

So sánh A với B cho thấy tác động chung của cấu hình chia đoạn, vì kích thước và phần chồng lấn cũng thay đổi. So sánh B với C chỉ thay việc lọc theo chương. C dùng lại vector của B, do đó thời gian nạp thấp hơn không có nghĩa model tạo embedding nhanh hơn.

20 câu: q01–q15 dev ở chương I–IX; q16–q20 test ở X–XII. Có 8 filter: 5 dev, 3 test; chương viết trong câu hỏi trước retrieval. Không dùng gold source/page làm filter. Quote là nguyên đoạn được script kiểm tra tồn tại sau chuẩn hóa. [Benchmark](../../benchmark/questions.jsonl), [freeze](../../benchmark/freeze.json).

Tiêu chí chọn cố định: dev Hit@3 cao nhất, rồi Hit@1, rồi ít chunk, rồi tên. [Selection](../../results/baseline/selection.json) ghi chọn C sau dev trước truy xuất test. Không chỉnh cấu hình sau test; chạy lại chỉ kiểm chứng tái lập. Cùng sách/nhân vật và khả năng model đã thấy tác phẩm là nguy cơ rò rỉ.

## 1. Retrieval accuracy và tài nguyên

Hit yêu cầu một chunk đúng nguồn/unit và chứa đủ nguyên đoạn gold sau chuẩn hóa whitespace. Evidence bị chia qua nhiều chunk không đạt metric chính. Có hỗ trợ alternative_gold, nhưng bộ hiện tại chưa có nhãn thay thế được xác nhận. Không đánh giá độ chính xác câu trả lời LLM.

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunks | Ingest lần đầu | API cost |
|---|---|---|---|---|---|---|
| A | dev | 5/15 | 7/15 | 343 | 7,61 s | 0 USD |
| A | test | 1/5 | 2/5 | 343 | như trên | như trên |
| B | dev | 7/15 | 12/15 | 222 | 5,92 s | 0 USD |
| B | test | 2/5 | 4/5 | 222 | như trên | như trên |
| C | dev | 7/15 | 13/15 | 222 | 0,67 s, reuse B | 0 USD |
| C | test | 2/5 | 5/5 | 222 | như trên | như trên |

[Metrics](../../results/baseline/metrics.csv), [60 trace](../../results/baseline/traces.jsonl), [resources](../../results/baseline/resources.json).
Ingest gồm chunk/token thống kê, embedding, ghi store; không gồm model load 11,82 s hay lần ingest thứ hai. Chạy một lần, A chịu warm-up; không coi timing là hiệu năng ổn định.

| Strategy | Min/median/max ký tự | Tổng ký tự | Tổng token trước cắt | Chunk vượt 256 token |
|---|---|---|---|---|
| A | 51/500/500 | 156.650 | 41.303 | 0 |
| B | 49/708/899 | 142.548 | 37.211 | 3 |
| C | như B | 142.548 | 37.211 | 3 |

Nội dung lưu còn đầy đủ, nhưng embedding B/C có 3 chunk chỉ dùng 256 token đầu. A overlap nên tổng ký tự lớn hơn corpus.

## 2. Chunk coherence

Kết quả đọc mẫu với sự hỗ trợ của Codex là A đạt 1,0/2; B và C đạt 1,6/2. Các điểm này được lưu riêng, chưa có xác nhận thủ công của học viên. Mẫu cố định trước retrieval: unit 1–10, anchor giữa unit; A có 11 chunk do overlap ở unit 10, lấy trung bình trong vị trí rồi trung bình 10 vị trí. B/C có 10 chunk giống nhau.

Các đoạn của A thường bắt đầu hoặc kết thúc giữa câu nên chỉ giữ được một phần ý. B và C giữ được nhiều đoạn trọn vẹn hơn. Tuy vậy, mẫu ở đơn vị 7 vẫn bị cắt vì đoạn gốc quá dài; một số mẫu khác mở đầu bằng đại từ mà chưa nói rõ đang chỉ ai. [Nhãn/lý do AI](../../results/ai_review/coherence.csv); [bảng human](../../results/baseline/audit_coherence.csv).

## 3. Metadata usefulness

Code đối chiếu source, page, chapter/language và substring start/end: đúng 15/15 bản ghi test mỗi cấu hình, tổng 45. Đây là kiểm tra tự động, chưa thay audit thủ công nguồn gốc.

| Strategy | Tự động đúng nguồn | Top-3 tuân thủ filter dev | Top-3 tuân thủ filter test |
|---|---|---|---|
| A | 15/15 | 3/5 | 1/3 |
| B | 15/15 | 2/5 | 1/3 |
| C | 15/15 | 5/5 | 3/3 |

Đo tuân thủ theo phạm vi câu hỏi kể cả A/B không lọc. Chapter giúp loại distractor khác chương; source/page/offset giúp truy vết. Có metadata đúng chưa đảm bảo đúng top-1: C vẫn chỉ Hit@1=2/5 test. [Bảng human](../../results/baseline/audit_metadata.csv).

## 4. Grounding quality

Phần này xem ba kết quả đầu có đủ thông tin để trả lời câu hỏi hay không. Hệ thống chưa sinh câu trả lời bằng LLM nên không đo độ chính xác của câu trả lời. Bảng dưới là nhãn Codex đề xuất sau khi đọc năm câu test cho từng cấu hình; điểm được chấm theo nội dung, không quy đổi trực tiếp từ Hit@3:

| Strategy | Số mức 0/1/2 | Mean /2 |
|---|---|---|
| A | 2/1/2 | 1,0 |
| B | 0/1/4 | 1,8 |
| C | 0/0/5 | 2,0 |

A q16/q18 thiếu evidence; q19 có suppression nhưng thiếu phương thức, mức 1. B q20 có lời pack of cards ở thời điểm trước, nên mức 1 dù strict hit=0. C đủ evidence theo AI review.
[Nhãn/lý do](../../results/ai_review/grounding.csv), [phương pháp](../../results/ai_review/method.json), [bảng human](../../results/baseline/audit_grounding.csv).
AI cùng tác giả benchmark và đã thấy metric trước chấm: không độc lập, không chấm mù.

## 5. Data strategy impact và kết luận

Khi chuyển từ A sang B, dev Hit@3 tăng từ 7/15 lên 12/15, còn test tăng từ 2/5 lên 4/5. Số chunk giảm 121, tương đương 35,3%. Tuy nhiên, cách đặt gold ảnh hưởng đáng kể đến phép so sánh: q01, q02, q04 và q05 có đoạn evidence dài lần lượt 715, 701, 556 và 559 ký tự, đều lớn hơn cửa sổ 500 ký tự của A. Theo định nghĩa một chunk phải chứa đủ gold, A không thể đạt hit cho bốn câu dev này, dù truy xuất đúng một phần trả lời. Vì vậy, dev Hit@3 của A có trần 11/15 theo bộ gold hiện tại. Chênh lệch A–B không đủ để kết luận rằng cách gom đoạn luôn tốt hơn cửa sổ cố định.

Từ B sang C, dev Hit@3 tăng từ 12/15 lên 13/15 và test tăng từ 4/5 lên 5/5, trong khi Hit@1 không đổi. Đây là so sánh dễ diễn giải hơn vì hai cấu hình dùng cùng đoạn và vector. Việc lọc theo chương giảm kết quả ngoài phạm vi, nhưng chỉ có ích nếu chương được cung cấp đúng. Độ mạch lạc không đổi vì nội dung chunk giống nhau.

Hai lỗi thực tế:
1. A q19, gold unit 60/chương XI: rank 2 dừng ở “how it was done”, thiếu canvas bag/head first/sat upon it; các hits khác không bù được. B/C lấy trọn phương thức.
2. B q20, gold unit 66/chương XII: top-3 có câu pack of cards tại unit 40/chương VIII, sai thời điểm trước attack. C filter chapter=12 lấy unit 66 ở rank 2. A cũng lấy unit 66 rank 2 nhưng lẫn chương khác.

Chọn C theo dev đã cố định. Khi không có filter, C giống B. Test chỉ 5 câu, mỗi câu đổi tỷ lệ 20 điểm phần trăm; không kết luận tốt nhất tổng quát.

Giới hạn: một sách tiếng Anh, không chứng minh tiếng Việt; ít câu điều kiện/ngoại lệ; gold cả đoạn có thể quá rộng; q17 gold chưa chứa câu giải thích purpose dù source/trace có; thiếu human audit; 3 chunk vượt token budget; timing một lần; store local đơn tiến trình; thiên lệch cùng AI tạo câu hỏi và review.

Cải tiến: học viên xác nhận gold/nhãn; khi sửa cấu hình phải tạo test mới chưa xem; chia theo tokenizer; thêm nguồn/ngôn ngữ, điều kiện và multi-evidence; đo timing lặp/warm-up; thử hybrid trên dev rồi đánh giá holdout mới.

## Cách kiểm tra và công cụ hỗ trợ

Codex được sử dụng để hỗ trợ viết code, soạn benchmark trước khi chạy truy xuất và phân tích kết quả. Cách kiểm tra gồm đối chiếu hash, kiểm tra đoạn trích với nguồn, chạy sáu tests và kiểm tra dữ liệu sau khi nạp lại, đóng rồi mở kho. Lần chạy lại cho cùng sáu dòng chỉ số và cùng thứ tự ID top-3, nhãn evidence hit của 60 lượt truy vấn. Nhãn do công cụ đề xuất được nhận diện bằng reviewer và status trong từng bảng; xác nhận của học viên vẫn được giữ riêng. [Verification](../../results/verification.json).

Sau test chỉ bỏ định nghĩa code trùng, thêm tài liệu/tests/audit và sửa mã hóa UTF-8; không chỉnh model, corpus, cấu hình hay benchmark.

Học viên cần xác nhận thông tin, tự chấm các bảng human, chạy python -m starter.src.audit results/baseline, cập nhật kết quả human, commit bổ sung nhãn và nộp link theo lớp. Không coi việc push GitHub là đã nộp trên kênh giảng viên.

Kết quả rà soát bổ sung: 67 đơn vị đã được dựng lại từ bản gốc và đối chiếu đúng theo vị trí; 20 đoạn gold và 45 bản ghi metadata test đều khớp nguồn. Nhận xét từng câu và giới hạn của gold được ghi trong [biên bản rà soát](../../results/ai_review/REVIEW.md).

Ngày 14/11/2026, Codex đã đọc lại các mẫu và điền nhận xét tiếng Việt cho đủ 31 hàng coherence, 15 hàng grounding và 45 hàng metadata trong các bảng baseline. Điểm coherence và grounding giữ nguyên sau khi đọc lại. Metadata có lý do đối chiếu theo từng vị trí nguồn; cột human_correct chờ học viên xác nhận. [Tổng hợp nhãn đã điền](../../results/ai_review/annotated_audit_summary.json).
