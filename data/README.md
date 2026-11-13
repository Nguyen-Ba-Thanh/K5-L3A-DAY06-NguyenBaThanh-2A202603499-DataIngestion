# Corpus và quyền sử dụng

Nguồn: [Project Gutenberg #11](https://www.gutenberg.org/ebooks/11), Lewis Carroll (1832–1898), Alice’s Adventures in Wonderland. Catalog ghi public domain tại Hoa Kỳ. Giữ nguyên raw/alice.txt cùng credit và [điều khoản phân phối](https://www.gutenberg.org/policy/license.html). Chỉ dùng văn bản gốc, không minh họa hay bản dịch hiện đại. Tác giả mất năm 1898; cơ sở suy luận về hết thời hạn quyền tài sản văn học tại Việt Nam là đời tác giả cộng 50 năm, xem [WIPO, Điều 27](https://www.wipo.int/edocs/pubdocs/en/wipo-pub-1081-3-en-intellectual-property-adjudication-in-viet-nam.pdf). Vẫn giữ credit và tính toàn vẹn nguồn gốc.

manifest.json có URL, ngày tải UTC, phiên bản, hash gốc/từng đơn vị, ranh giới và số ký tự. Loại bìa, mục lục, license khỏi retrieval. Gom các đoạn liên tiếp trong cùng chương, mục tiêu 1.800 ký tự; phần cuối gộp vào đơn vị trước. Tất cả 67 đơn vị ≥1.500 ký tự sau chuẩn hóa NFC, không nhân bản. Đây không phải trang PDF.

pages.jsonl chứa document_id, source, page (integer unit ID), text, metadata. chapter=1–12 và chapter_title lấy từ heading; language=en từ nguồn; chapter_start/end trong chương chuẩn hóa. Chunk có thêm start/end trong unit. Không suy đoán ngày hiệu lực.

Repo có sẵn corpus, không cần tải lại. Để tái tạo trên bản sao chưa có benchmark/freeze.json: python -m starter.src.prepare; thêm --download nếu cần tải nguồn. Script từ chối ghi đè benchmark đã cố định. Nguồn online có thể thay đổi: đối chiếu raw_sha256. .gitattributes giữ nguyên byte các đầu vào được hash.
