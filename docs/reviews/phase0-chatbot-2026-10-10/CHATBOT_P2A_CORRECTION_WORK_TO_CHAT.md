# LOTUS FIN — P2-A Correction Work → Chat

12/10/2026 · Asia/Saigon · **P2A_CORRECTION_LOCAL_PASS**, builder/self-verification, không independent PASS.

Đã trực tiếp sửa F01–F03 trên `develop@5f805ef34f788245a3ec0e9c2f44e224eb16c305`:

- F01: stable read-family scope; fresh capability và exact Company authorization riêng mỗi resolve. Fresh context→search→signed selection→fresh open đạt; scope/config/key change, tamper và replay/revoke vẫn deny.
- F02: ContextData có default_posting_from/to theo site timezone và90ngày inclusive; expires_at bằng actual signed token claim, tách khỏi request deadline. Missing/invalid timezone fail safely.
- F03: filters required/nonnullable; page_size omitted→20 nhưng null invalid; explicit-null dates reject, zero read-port calls. Omitted dates/default/NFC/range/type/extra-RPC controls giữ nguyên.

Fresh final regression **343/343 PASS =173P1+103P2existing+67new**. Oracle **84/84 PASS,12old FAIL→PASS**. Dedicated A16 **14/14**, B03 **8/8**, exits0. Không cộng overlapping runs. Runner adaptation/old exit-bookkeeping anomaly được ghi đầy đủ; historical evidence không overwrite, existing test assertions không weakened.

Exact delta:5production modules,5existing fixture timezone additions,3permanent regression modules; tất cả<200lines. P1 original codec, A16 sink, API/config, resolver và Open usecase nguyên SHA256. Panel/Drawer nguyên đầu phiên; một unrelated frontend file đổi concurrent đã ghi riêng, không sửa/hoàn nguyên. No frontend/Docker/package/ERP-permission edit của batch, no business read/write/network, no commit/deploy/enable.

GitNexus refreshed graph: filtersMEDIUM/6direct; authorizer/controllerUNKNOWN có source confirmation. Initial corrupt/CRITICAL graph cảnh báo được giữ, refresh thành công với FTS off. Final full detect_changes39symbols/8flows/HIGH gồm frontend có trước; không partial/truncated trong structured result, không clean release/commit claim.

Tài liệu bàn giao:

1. [Correction, hashes, RED→GREEN và commands](CHATBOT_P2A_F01_F03_CORRECTION.md).
2. [FROZEN P2-B wire contract từ implemented DTOs](CHATBOT_P2B_WIRE_CONTRACT.md).
3. [New evidence root / final audit](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/SOURCE_AFTER_AND_SELF_AUDIT.json), [commands/results](../evidence/chatbot-p2a-f01-f03-correction-2026-10-12/COMMANDS_AND_RESULTS.json).

**P2A_LIVE_INTEGRATION=BLOCKED / NOT_RUN; G10=BLOCKED độc lập.** Public APIs và search/open controller vẫn disabled; no HTTP/CSRF/permission/resource/deployed-source/no-write acceptance. P2-B contract chỉ đủ cho fixture/UI design handoff; chưa được nối live transport hoặc coi product end-to-end qualified.

Next gate: independent offline recheck trên exact current hashes; live qualification cần approved private immutable target/permission gold/ordinary-user fixtures/audit/HTTP/budgets/no-write/cleanup riêng. **Dừng sau correction+contract; không dispatch implementation, enable hoặc deploy.**
