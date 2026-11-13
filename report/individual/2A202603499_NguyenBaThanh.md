# Báo cáo cá nhân — Day 6

Nguyễn Bá Thành · 2A202603499 · L3A. 
Ngày chạy: 13/11/2026, khoảng 18:13–18:14 giờ Việt Nam (11:13–11:14 UTC).

## Dữ liệu và pipeline

Corpus: Alice’s Adventures in Wonderland, Lewis Carroll, Project Gutenberg #11. Giữ bản gốc, credit và license; chỉ dùng văn bản, không minh họa/bản dịch. [Nguồn và quyền](../../data/README.md), [manifest](../../data/manifest.json).

67 đơn vị nguồn, tất cả ≥1.500 ký tự chuẩn hóa. Gom đoạn liên tiếp trong cùng chương, mục tiêu 1.800 ký tự, phần cuối gộp vào unit trước. Loại bìa/mục lục/license khỏi retrieval; không nhân bản. Đây là đơn vị tương đương cho text không phân trang, không phải 67 trang PDF.

Chuẩn hóa NFC/whitespace, giữ ranh giới đoạn. Nguồn text nên không OCR; hàm PDF có log trang lỗi/rỗng nhưng không dùng cho benchmark này. Metadata: document_id, source URL, page=unit ID, chapter, chapter_title, language=en, chapter_start/end; chunk thêm start/end trong unit. Chapter lấy từ heading để lọc, source/page/offset để truy vết, không đoán ngày hiệu lực.

Embedding: sentence-transformers/all-MiniLM-L6-v2, revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf, 384 chiều, CPU, mean pooling/L2 normalization, batch 32; query/document cùng xử lý, giới hạn 256 token. Python 3.10.1, sentence-transformers 3.4.1, transformers 4.57.6, torch 2.11.0+cu128 (inference CPU). [Môi trường](../../results/baseline/environment.json).

Store: Qdrant client 1.13.3 local persistent, .qdrant/, day6_A/B/C, exact cosine top-3. Nạp lại thay toàn bộ snapshot để loại chunk cũ; count trước/sau reload và sau reopen đều 343/222/222. Thay snapshot không crash-atomic, cần ingest lại nếu gián đoạn. API cost 0 USD; chưa tính điện/phần cứng/mạng. [Lệnh setup/run](../../README.md).

## Cấu hình và benchmark

| Strategy | Chunking | Metadata filter |
|---|---|---|
| A | Fixed 500 ký tự, overlap 50, trong unit | Không |
| B | Gom đoạn tối đa 900 ký tự; đoạn dài tách whitespace | Không |
| C | Cùng chunks và vectors với B | Chapter khi câu hỏi cho sẵn |

A–B thay cấu hình chunking gồm cả kích thước/overlap, nên không tách riêng hiệu ứng ranh giới đoạn. B–C chỉ thay filter. C reuse embedding B để tránh tính lại, không được xem thời gian thấp là embedding nhanh hơn.

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

Human audit chưa hoàn tất. AI đã đọc mẫu và đề xuất A=1,0/2; B=C=1,6/2. Đây không phải nhãn học viên chấm. Mẫu cố định trước retrieval: unit 1–10, anchor giữa unit; A có 11 chunk do overlap ở unit 10, lấy trung bình trong vị trí rồi trung bình 10 vị trí. B/C có 10 chunk giống nhau.

A thường cắt đầu/cuối, giữ được một phần ý. B/C giữ đoạn tốt hơn nhưng unit 7 có đoạn dài bị cắt; vài mẫu thiếu antecedent. [Nhãn/lý do AI](../../results/ai_review/coherence.csv); [bảng human](../../results/baseline/audit_coherence.csv).

## 3. Metadata usefulness

Code đối chiếu source, page, chapter/language và substring start/end: đúng 15/15 bản ghi test mỗi cấu hình, tổng 45. Đây là kiểm tra tự động, chưa thay audit thủ công nguồn gốc.

| Strategy | Tự động đúng nguồn | Top-3 tuân thủ filter dev | Top-3 tuân thủ filter test |
|---|---|---|---|
| A | 15/15 | 3/5 | 1/3 |
| B | 15/15 | 2/5 | 1/3 |
| C | 15/15 | 5/5 | 3/3 |

Đo tuân thủ theo phạm vi câu hỏi kể cả A/B không lọc. Chapter giúp loại distractor khác chương; source/page/offset giúp truy vết. Có metadata đúng chưa đảm bảo đúng top-1: C vẫn chỉ Hit@1=2/5 test. [Bảng human](../../results/baseline/audit_metadata.csv).

## 4. Grounding quality

Đánh giá độ đủ bằng chứng trong top-3, không phải answer accuracy của LLM. Nhãn sau là AI đề xuất sau khi đọc đủ 5 test mỗi cấu hình, không suy từ exact hit và chưa được human xác nhận:

| Strategy | Số mức 0/1/2 | Mean /2 |
|---|---|---|
| A | 2/1/2 | 1,0 |
| B | 0/1/4 | 1,8 |
| C | 0/0/5 | 2,0 |

A q16/q18 thiếu evidence; q19 có suppression nhưng thiếu phương thức, mức 1. B q20 có lời pack of cards ở thời điểm trước, nên mức 1 dù strict hit=0. C đủ evidence theo AI review.
[Nhãn/lý do](../../results/ai_review/grounding.csv), [phương pháp](../../results/ai_review/method.json), [bảng human](../../results/baseline/audit_grounding.csv).
AI cùng tác giả benchmark và đã thấy metric trước chấm: không độc lập, không chấm mù.

## 5. Data strategy impact và kết luận

A–B: dev Hit@3 tăng 7/15 → 12/15, test 2/5 → 4/5; giảm 121 chunks (35,3%). Gom đoạn giữ evidence tốt hơn, nhưng gold nguyên đoạn và chunk lớn hơn cũng góp phần, không quy toàn bộ cho ranh giới đoạn.

B–C: dev Hit@3 tăng 12/15 → 13/15; test 4/5 → 5/5; Hit@1 không tăng. Coherence không đổi vì chunks giống nhau. Filter có ích khi scope đáng tin; filter sai có thể loại gold.

Hai lỗi thực tế:
1. A q19, gold unit 60/chương XI: rank 2 dừng ở “how it was done”, thiếu canvas bag/head first/sat upon it; các hits khác không bù được. B/C lấy trọn phương thức.
2. B q20, gold unit 66/chương XII: top-3 có câu pack of cards tại unit 40/chương VIII, sai thời điểm trước attack. C filter chapter=12 lấy unit 66 ở rank 2. A cũng lấy unit 66 rank 2 nhưng lẫn chương khác.

Chọn C theo dev đã cố định. Khi không có filter, C giống B. Test chỉ 5 câu, mỗi câu đổi tỷ lệ 20 điểm phần trăm; không kết luận tốt nhất tổng quát.

Giới hạn: một sách tiếng Anh, không chứng minh tiếng Việt; ít câu điều kiện/ngoại lệ; gold cả đoạn có thể quá rộng; q17 gold chưa chứa câu giải thích purpose dù source/trace có; thiếu human audit; 3 chunk vượt token budget; timing một lần; store local đơn tiến trình; thiên lệch cùng AI tạo câu hỏi và review.

Cải tiến: học viên xác nhận gold/nhãn; khi sửa cấu hình phải tạo test mới chưa xem; chia theo tokenizer; thêm nguồn/ngôn ngữ, điều kiện và multi-evidence; đo timing lặp/warm-up; thử hybrid trên dev rồi đánh giá holdout mới.

## Tái lập, AI và việc còn lại

Codex đọc yêu cầu, viết pipeline/tests, soạn benchmark trước retrieval, chạy model/store thật và báo cáo từ artifact. Không bịa số liệu hay nhãn human. Kiểm chứng bằng hash, quote đối chiếu nguồn, 6 tests đạt, reload/reopen và lần chạy lại cho đúng 6 dòng metric cùng top-3/evidence hit của 60 trace. [Verification](../../results/verification.json).

Sau test chỉ bỏ định nghĩa code trùng, thêm tài liệu/tests/audit và sửa mã hóa UTF-8; không chỉnh model, corpus, cấu hình hay benchmark.

Học viên cần xác nhận thông tin, tự chấm các bảng human, chạy python -m starter.src.audit results/baseline, cập nhật kết quả human, commit bổ sung nhãn và nộp link theo lớp. Không coi việc push GitHub là đã nộp trên kênh giảng viên.
