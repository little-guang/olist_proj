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
├─ import_to_mariadb.py     # 分批匯入 MariaDB
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

先建立資料庫：

```sql
CREATE DATABASE olist_db
	CHARACTER SET utf8mb4
	COLLATE utf8mb4_unicode_ci;
```

接著執行 `db/olist_db.sql`，或依照資料表相依順序執行 `db/` 內的 SQL 檔案。

`order_reviews` 必須使用複合主鍵 `PRIMARY KEY (review_id, order_id)`，因為原始資料中的 `review_id` 可能重複。`geolocation` 保留重複資料，不應設定限制每列唯一性的主鍵。

## 5. 整理與檢查資料

```powershell
& .\.venv\Scripts\python.exe .\clean_olist.py
& .\.venv\Scripts\python.exe .\check_olist.py
```

清理程式會統一欄位名稱、修正 `lenght` 拼字、清除文字前後空白、將空字串轉為缺失值、整理日期為 `YYYY-MM-DD HH:MM:SS`、轉換數值欄位，以及將 ZIP Code 保留為 5 位字串。它不會刪除欄位、資料列或重複值。

品質檢查會驗證欄位 schema、NULL、主鍵與複合鍵、外鍵、日期解析、數值格式與 ZIP Code 格式；發現錯誤時會以非零狀態結束。原始日期異常只會被報告，不會在清理時擅自修改。

## 6. 匯入 MariaDB

確認 MariaDB 已啟動、資料庫與資料表已建立，且 `.env` 已填好：

```powershell
& .\.venv\Scripts\python.exe .\import_to_mariadb.py
```

匯入程式會先驗證 `order_reviews` 複合主鍵，依父表到子表的順序匯入，每批 5,000 筆，將缺失值轉為 MariaDB `NULL`，並驗證 CSV 欄位名稱與預期 schema 一致。完整匯入的表會跳過；部分匯入的表會停止，避免重複追加。程式不會刪除資料或自動去除重複值。

## 7. 欄位字典與延伸資料

目前版本的執行流程只涵蓋上述 9 張 Olist 主資料表。行銷漏斗資料與 HTML 欄位字典尚未放入此工作區；若日後加入，請將資料放在獨立目錄，並在此補上欄位中英對照與來源授權資訊。不要把未納入清理與匯入流程的資料誤當成可直接匯入 MariaDB 的輸入。

## 注意事項

- `data/` 中的原始與清理 CSV 不應提交到 Git；目前 `data/raw/` 與 `data/clean/` 都被 `.gitignore` 忽略。
- MariaDB 匯入前請確認資料表欄位型別、索引、主鍵與外鍵和 CSV 一致。
