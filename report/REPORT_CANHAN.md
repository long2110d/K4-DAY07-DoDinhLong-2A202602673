# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Đình Long
**Nhóm:** G16
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao có nghĩa là 2 câu có nghĩa gần giống trong trong không gian embeeding  2 vecto cùng hướng với nhau thì cosine càng tiến gần đến 1 

**Ví dụ có độ tương tự CAO:**
- Câu A:Tôi ăn cơm
- Câu B:Tôi ăn gạo nấu lên
- Tại sao tương đồng: cùng 1 ý nghĩa

**Ví dụ có độ tương tự THẤP:**
- Câu A:tôi đi bơi
- Câu B:chó
- Tại sao khác: 2 câu ý nghĩa khác nhau trong không gian sẽ huongs không cùng nhau 

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì các câu hay các đoạn đôi khi có độ dài khác nhau nhưng lại có ý nghĩa giống nhau hay nói là cùng 1 cách miêu tả nhưng ý nghĩa ghioongs nhau nên cùng hướng điêu này thích hợp cho dùng cosine thay vì euclide đo độ lớn khi đó euclide quan tâm đến độ dài của 2 vecto hơn không phải đo đô giống nhau

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> ((10000-500)/450) +1
> 23

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> số lượng chunking tăng lên

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận: chia thành 500  1 chunk over lap 50 
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo chia để trị khi chia không được pthanhf đoạn thì chia đến câu rồi chứ ưu tiên chia thành các đoạn lớn trước rồi đến các thành phần nhỏ fpfhwipfhwepifepfewfks;jvhghfhgfga

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Embedding store theo metadata và tài liệu doc xem tài chunk thuộc document nào seearch dựa trên embedding hoặc theo metaseach flter lọc nhãn ra rồi search 

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc các record theo toàn bộ cặp key-value trong metadata trước, sau đó mới tính điểm similarity và lấy top-k. `delete_document` dùng `metadata["doc_id"]`, nên các chunk có id dạng `file#0`, `file#1` vẫn được xóa cùng file gốc. Hàm tạo record copy metadata và luôn bổ sung `doc_id` từ phần trước dấu `#`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Constructor lưu tham chiếu đến `EmbeddingStore` và hàm gọi LLM. `answer` truy xuất top-k chunk, nối nội dung thành phần `Context`, rồi tạo prompt yêu cầu LLM chỉ dùng context để trả lời; nếu context không đủ thì phải nói rõ. Cuối cùng prompt được truyền vào `llm_fn` và trả về chuỗi câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
41 passed
```

**Số lượng bài test vượt qua (pass):** 41 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả | Thời gian đổi trả | cao | Chưa đo riêng | Chưa kết luận |
| 2 | Hủy giao dịch | Bảo hành sản phẩm | thấp | Chưa đo riêng | Chưa kết luận |
| 3 | Hoàn tiền | Đổi trả | cao | Chưa đo riêng | Chưa kết luận |
| 4 | Chính sách người mua | Quy chế ứng dụng | trung bình | Chưa đo riêng | Chưa kết luận |
| 5 | Chunk có cùng chủ đề | Chunk không liên quan | thấp | Chưa đo riêng | Chưa kết luận |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Benchmark dùng `MockEmbedder`, vốn băm MD5 nội dung và không biểu diễn ngữ nghĩa. Vì vậy score không thể dùng để kết luận hai câu gần nghĩa hay không; cần chạy lại bằng embedding thật như OpenAI hoặc local model trước khi điền điểm thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Khách hàng có thể hủy giao dịch trong khoảng thời gian nào? | `return-refund-guide#6` | 0.2972 | Không, không có evidence | Chưa trả lời được từ top-3 |
| 2 | Có những phương thức nào để hủy giao dịch? | `cellphones-app-regulation#62` | 0.3320 | Không, không có evidence | Chưa trả lời được từ top-3 |
| 3 | Thời gian hoàn tiền là bao lâu khi giao dịch có vấn đề? | `cellphones-app-regulation#20` | 0.3121 | Không, không có evidence | Chưa trả lời được từ top-3 |
| 4 | Với giao dịch từ 10.000.000 VNĐ trở lên, người mua cần cung cấp gì? | `cellphones-app-regulation#82` | 0.2848 | Không, không có evidence | Chưa trả lời được từ top-3 |
| 5 | Chính sách đổi mới miễn phí cho sản phẩm kéo dài bao nhiêu ngày? | `cellphones-app-regulation#35` | 0.3220 | Không, không có evidence | Chưa trả lời được từ top-3 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5

> Kết quả trên dùng `RecursiveChunker` với `MockEmbedder`. Chấm ở mức nội dung: chunk phải chứa evidence của gold answer, không chỉ cần cùng `doc_id`. Câu 4 đã chạy A/B; top-3 unfiltered và filtered giống nhau, nên corpus hiện tại chưa chứng minh được lợi ích của metadata filter vì tất cả tài liệu đều có `audience: buyer`.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chunking chỉ là một phần của retrieval. Với mock embedding, cosine score bị chi phối bởi hash nên top-1 có thể không chứa câu trả lời dù đúng tài liệu nằm trong corpus. Cần dùng embedding có ngữ nghĩa và kiểm tra evidence trong nội dung trước khi kết luận chiến lược tốt.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/ 5 |
| Hướng tiếp cận của tôi (My Approach) | 9/ 10 |
| Hoàn thiện code (Core Implementation — tests) | 29/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8/ 10 |
| **Tổng phần cá nhân** | **56/ 60** |
