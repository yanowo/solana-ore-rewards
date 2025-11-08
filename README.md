# ORE Mining Balance & Rewards Checker

`rewards.py` 是一個自動化工具，用於批量查詢 `ore.exe` 帳戶的 **ORE** 與 **SOL** 餘額，
同時支援單一帳號查詢與 JSON 格式輸出。

腳本會自動掃描專案根目錄下的 `./keypairs/*.json`，
透過 `ore.exe account --keypair` 執行查詢，並將結果格式化輸出。

---

## 功能特點

* 自動掃描 `keypairs` 資料夾中的所有帳號
* 支援單一 `keypair` 檔查詢
* 支援 JSON 輸出模式
* 自動過濾 `ore.exe` CLI 彩色輸出中的 ANSI 控制碼
* 自動偵測 `"account not found"` 狀態
* Windows 友好：避免 `cp950` 解碼錯誤，強制使用 UTF-8

---

## 系統需求

* Windows 10 / 11
* Python 3.9 以上
* `ore.exe` 放在根目錄中
  （可在命令提示字元中輸入 `ore.exe --version` 測試）

---

## 專案結構

```
E:\ORE-mining\
│
├─ ore.exe
├─ rewards.py
└─ keypairs\
   ├─ id-1.json
   ├─ id-2.json
   ├─ id-3.json
   └─ ...
```

---

## 使用方式

### 1. 批次查詢（自動掃描 keypairs 資料夾）

```bash
py rewards.py
```

輸出範例：

```
文件               ORE餘額          SOL餘額            備註
------------------------------------------------------------
id-20.json      0.000000000     0.011709899
id-21.json      0.000000000     0.000000000     account not found
合計            0.000000000     0.011709899
```

---

### 2. 查詢單一帳號

```bash
py rewards.py --keypair "E:\ORE-mining\keypairs\id-20.json"
```

---

### 3. 輸出 JSON 格式

```bash
py rewards.py --json
```

範例輸出：

```json
[
  {
    "keypair": "E:\\ORE-mining\\keypairs\\id-20.json",
    "address": "2XNm4kwe6E64PhMs1jNpZ9WhYL2QV3MRpYGT9DMYQvtR",
    "ore_balance": 0.0,
    "sol_balance": 0.011709899
  },
  {
    "keypair": "E:\\ORE-mining\\keypairs\\id-21.json",
    "address": "DhXH9TZwTqXXAq8RQaDcVDy3qSY2cm9mLXRkNkJswnCq",
    "ore_balance": 0.0,
    "sol_balance": 0.0,
    "note": "account not found"
  }
]
```

---

## 參數說明

| 參數          | 說明               | 預設值                 |
| ----------- | ---------------- | ------------------- |
| `--keypair` | 指定單一 keypair 檔路徑 | 自動掃描 `keypairs` 資料夾 |
| `--json`    | 輸出 JSON 格式結果     | 關閉                  |
| `--timeout` | 單次查詢逾時秒數         | 30                  |

---

## 執行流程

1. 掃描 `keypairs/*.json`
2. 執行：

   ```
   ore.exe account --keypair <path>
   ```
3. 解析輸出：

   * `Address`
   * `Balance ... ORE`
   * `SOL ... SOL`
4. 若偵測到 `"Not found"`，註記為 `"account not found"`
5. 計算總 ORE / SOL 餘額並輸出報表
