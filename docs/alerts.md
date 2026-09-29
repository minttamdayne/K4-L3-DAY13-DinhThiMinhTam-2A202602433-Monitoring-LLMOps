# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High latency SLO breach
- Severity: warning
- Duration: 10 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: fast_successful_requests, latency P95 <= 3000 ms
- Điều kiện: `latency_p95_ms > 3000` trong 10 phút.
- Ảnh hưởng: người dùng thấy phản hồi chậm và có nguy cơ vượt error budget.
- Ba bước kiểm tra đầu tiên: xem panel latency; lọc response chậm trong log; mở trace theo correlation ID.
- Mitigation tạm thời: giảm concurrency, tắt workload nặng và bật incident practice để cô lập thành phần chậm.
- Owner: on-call-llmops

## Alert 2

- Tên: Elevated request errors
- Severity: critical
- Duration: 5 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: error rate guardrail <= 2%.
- Điều kiện: `error_rate_pct > 2` trong 5 phút.
- Ảnh hưởng: request thất bại hoặc người dùng không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên: xem breakdown lỗi; lấy correlation ID từ request_failed; kiểm tra trace và dependency.
- Mitigation tạm thời: giảm traffic, disable feature lỗi và rollback prompt nếu lỗi bắt đầu sau thay đổi.
- Owner: on-call-llmops

## Alert 3

- Tên: Low retrieval success
- Severity: warning
- Duration: 10 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: retrieval success rate >= 90%.
- Điều kiện: `retrieval_success_rate_pct < 90` trong 10 phút.
- Ảnh hưởng: câu trả lời dễ rơi vào fallback hoặc thiếu ngữ cảnh.
- Ba bước kiểm tra đầu tiên: xem panel errors; kiểm tra tool_success và error_type; mở trace để phân biệt retrieval với generation.
- Mitigation tạm thời: chuyển sang index/nguồn dự phòng, giảm phạm vi truy vấn và theo dõi quality proxy.
- Owner: on-call-llmops
