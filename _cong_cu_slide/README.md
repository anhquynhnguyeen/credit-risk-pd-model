# Công cụ tạo file Bai1_Bai2_slides.pptx (không nộp)

Tạo lại file PowerPoint gộp Bài I + Bài II từ kết quả mới nhất:

```bash
cd "_cong_cu_slide"
npm install pptxgenjs@3.12.0                                   # chỉ cần lần đầu
../bai1/.venv/bin/python export_bai1.py ../bai1 bai1.json      # số liệu Bài I
../bai2/.venv/bin/python export_bai2.py ../bai2 bai2.json      # số liệu Bài II (~1 phút)
NODE_PATH=node_modules node build.js bai1.json bai2.json ../Bai1_Bai2_slides.pptx <thư mục skill pptx>
```

`build.js` dùng `scripts/apply_theme.js` của skill pptx (Claude Code) để ghi màu theme.
Lưu ý: chạy lại sẽ ghi đè `../Bai1_Bai2_slides.pptx`; nếu bạn đã sửa tay file đó, lưu bản sao trước.

## ⚠️ Từ 23/10/2026: KHÔNG chạy lại build.js để tạo slide

File `../Bai1_Bai2_slides.pptx` đã được sửa tay trong PowerPoint (tên, hình ảnh, bỏ cột Đèn, font Cambria...).
Chạy lại `build.js` sẽ tạo file mới từ đầu và **mất hết các sửa tay đó**. Từ giờ hãy sửa trực tiếp file .pptx.
Bản sao lưu trước khi đổi font: `Bai1_Bai2_slides_ban_sua_tay_truoc_khi_doi_font.pptx`.
