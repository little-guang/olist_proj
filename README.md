# Olist Data Pipeline

這個專案將 Olist 電商資料整理成適合 MariaDB 匯入的 CSV，並提供資料品質檢查、欄位字典與批次匯入工具。

## 專案內容

```text
olist/
├─ data/
│  ├─ raw/                  # 9 張 Olist 原始資料表
│  └─ clean/                # clean_olist.py 產生的 CSV
├─ db/                      # MariaDB 建表 SQL
├─ clean_olist.py           # 格式整理，不刪除列、不去除重複值
├─ check_olist.py           # clean CSV 品質檢查
├─ setup_mariadb.py         # 建立資料庫與資料表
├─ import_to_mariadb.py     # 分批匯入 MariaDB
├─ olist_columns_dictionary.html # 欄位中英對照
├─ .env.example             # MariaDB 設定範本
└─ README.md
```

## 1. 下載資料

從 [Kaggle Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 下載以下 9 個 CSV，放到 `data/raw/`，並保留原始檔名：

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

目前清理、檢查與 MariaDB 匯入流程處理的是這 9 張表。`data/raw/` 與 `data/clean/` 都已列入 `.gitignore`，不會因執行流程而提交大型資料檔。

## 資料集授權與使用規定

Kaggle 目前將資料集標示為 **CC BY-NC-SA 4.0**。公開分享或使用資料集與 `data/clean/` 衍生資料時，請保留來源標示：`Brazilian E-Commerce Public Dataset by Olist`，並附上 [Kaggle 資料集連結](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)。

- **BY**：保留資料來源與授權資訊。
- **NC**：不得將資料集或衍生資料用於商業目的。
- **SA**：公開分享改作或整理版本時，依相同或相容條件分享。
- 不要移除原始來源、授權或著作權聲明，也不要宣稱資料由本專案原創。
- 本專案的 Python、SQL、HTML 程式碼與資料集授權分開看待；程式碼若公開，請另外指定程式碼授權。

詳見 [Creative Commons CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 官方條款。Kaggle 條款可能更新，實際使用前請以來源頁面與官方條款為準；本 README 不構成法律意見。

## 2. 安裝環境

需要 Python 3.12 以上。使用 [uv](https://docs.astral.sh/uv/) 安裝依賴：

```powershell
uv sync
```

也可以啟用已建立的虛擬環境：

```powershell
& .\.venv\Scripts\Activate.ps1
```

主要依賴是 `pandas`、`PyMySQL` 與 `python-dotenv`。

## 3. 設定環境變數

複製 `.env.example` 為 `.env`，再填入 MariaDB 資訊：

```powershell
Copy-Item .env.example .env
```

```dotenv
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=請填入你的MariaDB密碼
MARIADB_DATABASE=olist_db
```

`.env` 已列入 `.gitignore`，請勿提交真實密碼或資料庫連線資訊。

## 4. 建立 MariaDB 資料庫與資料表

確認 MariaDB 服務已啟動，且 `.env` 已填好後執行：

```powershell
uv run python setup_mariadb.py
```

這個指令會依序：

1. 使用 `.env` 的設定建立 `olist_db` 資料庫。
2. 依照 `db/` 內的 SQL 建立 9 張資料表。

初始化程式不會刪除資料庫、資料表或資料列，也不會匯入 CSV。

若只想手動分開執行，也可以使用以下流程：

先建立資料庫：

```sql
CREATE DATABASE olist_db
	CHARACTER SET utf8mb4
	COLLATE utf8mb4_unicode_ci;
```

接著執行 `db/olist_db.sql`，或依照資料表相依順序執行 `db/` 內的 SQL 檔案。一般使用情境不需要手動執行這些 SQL，`setup_mariadb.py` 會自動處理。

`order_reviews` 必須使用複合主鍵 `PRIMARY KEY (review_id, order_id)`，因為原始資料中的 `review_id` 可能重複。`geolocation` 保留重複資料，不應設定限制每列唯一性的主鍵。

## 5. 整理與檢查資料

```powershell
& .\.venv\Scripts\python.exe .\clean_olist.py
```

清理程式會統一欄位名稱、修正 `lenght` 拼字、清除文字前後空白、將空字串轉為缺失值、整理日期為 `YYYY-MM-DD HH:MM:SS`、轉換數值欄位，以及將 ZIP Code 保留為 5 位字串。它不會刪除欄位、資料列或重複值。

清理完成後，建議執行品質檢查：

```powershell
& .\.venv\Scripts\python.exe .\check_olist.py
```

品質檢查會驗證欄位 schema、NULL、主鍵與複合鍵、外鍵、日期解析、數值格式與 ZIP Code 格式；發現錯誤時會以非零狀態結束。這一步不是建立資料庫的必要條件，但在匯入前執行可以提早發現資料問題。原始日期異常只會被報告，不會在清理時擅自修改。

## 6. 匯入 MariaDB

確認 MariaDB 已啟動、資料庫與資料表已建立，且 `.env` 已填好：

```powershell
& .\.venv\Scripts\python.exe .\import_to_mariadb.py
```

匯入程式會先驗證 `order_reviews` 複合主鍵，依父表到子表的順序匯入，每批 5,000 筆，將缺失值轉為 MariaDB `NULL`，並驗證 CSV 欄位名稱與預期 schema 一致。完整匯入的表會跳過；部分匯入的表會停止，避免重複追加。程式不會刪除資料或自動去除重複值。

## 7. 欄位字典與延伸資料

開啟 [olist_columns_dictionary.html](olist_columns_dictionary.html)，可查看目前 9 張 Olist 主資料表的欄位中英對照。行銷漏斗資料目前未納入清理、檢查或 MariaDB 匯入流程，不應誤當成可直接匯入的輸入。

## 快速開始（懶人包）

想直接開跑、不想在說明文件裡迷路？跟著下面四步走，資料就會乖乖進 MariaDB：

```text
🧰 準備工具  →  🔐 設定連線  →  📦 放入 CSV  →  🚀 啟動流程
	uv sync         .env          data/raw/       setup_mariadb.py
```

> 🎯 **小目標：** 看到最後的 `Import completed.`，就代表資料已經順利抵達 MariaDB。

### 🧰 1. 先把工具準備好

在專案根目錄執行：

```powershell
uv sync
```

### 🔐 2. 告訴程式 MariaDB 在哪裡

複製設定範本：

```powershell
Copy-Item .env.example .env
```

接著打開 `.env` 填入 MariaDB 密碼，並確認 MariaDB 服務已經啟動。

> 🔒 密碼請留在自己的電腦裡，不要讓它出門旅行。

### 📦 3. 把 Olist CSV 放到指定位置

將 9 張原始 CSV 放進 `data/raw/`，檔名保持不變。檔案到位，程式才知道要去哪裡找資料。

```text
data/raw/
├─ olist_customers_dataset.csv
├─ olist_orders_dataset.csv
├─ olist_products_dataset.csv
└─ ... 其餘 6 張 CSV
```

### 🚀 4. 按下自動化按鈕

```powershell
uv run python setup_mariadb.py
```

接下來請依序執行下面四個指令：先整理資料，再視需要檢查，接著建立資料庫與資料表，最後匯入資料。每一步都各司其職，出了問題也比較容易找到是哪一關卡住。這些指令都不會刪除既有資料。

```powershell
uv run python clean_olist.py
uv run python check_olist.py       # 可選，但建議執行
uv run python setup_mariadb.py
uv run python import_to_mariadb.py
```

✅ **完成！** 如果四個步驟都順利跑完，Olist 資料就已經在 MariaDB 裡排好隊了。

## 注意事項

- `data/` 中的原始與清理 CSV 不應提交到 Git；目前 `data/raw/` 與 `data/clean/` 都被 `.gitignore` 忽略。
- MariaDB 匯入前請確認資料表欄位型別、索引、主鍵與外鍵和 CSV 一致。
