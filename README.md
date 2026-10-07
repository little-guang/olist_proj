# Olist Data Pipeline

這個專案將 Olist 電商資料整理成適合 MariaDB 匯入的 CSV，提供 MariaDB 批次匯入、Power BI 分析資料集，以及可部署至 GitHub Pages 的城市分析頁。

## 專案內容

```text
olist_proj/
├─ data/
│  ├─ raw/                  # 9 張 Olist 原始資料表
│  └─ clean/                # clean_olist.py 產生的 CSV
├─ db/                      # MariaDB 建表 SQL
├─ docs/
│  ├─ index.html            # GitHub Pages 商業分析報告
│  └─ data/
│     ├─ business_summary.json # 月趨勢、品類、付款、物流、顧客與賣家彙總
│     └─ cities.json        # 延遲載入的城市營運明細
├─ scripts/
│  └─ build_city_dashboard.py # 產生商業分析 JSON
├─ clean_olist.py           # 清理、篩選並彙總 Olist CSV
├─ setup_mariadb.py         # 建立資料庫與資料表
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

目前清理與 MariaDB 匯入流程處理的是這 9 張表。`data/raw/` 與 `data/clean/` 都已列入 `.gitignore`，不會因執行流程而提交大型資料檔。

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

1. 使用 `.env` 的 `MARIADB_DATABASE` 設定建立資料庫（預設為 `olist_db`）。
2. 依照 `db/` 內的 SQL 建立 9 張資料表。

初始化程式不會刪除資料庫、資料表或資料列，也不會匯入 CSV。

若只想手動分開執行，也可以使用以下流程：

先建立資料庫：

```sql
CREATE DATABASE olist_db
	CHARACTER SET utf8mb4
	COLLATE utf8mb4_unicode_ci;
```

接著依照 `setup_mariadb.py` 中列出的相依順序執行 `db/` 內的建表 SQL。一般使用情境不需要手動執行這些 SQL，`setup_mariadb.py` 會自動處理。

`order_reviews` 必須使用複合主鍵 `PRIMARY KEY (review_id, order_id)`，因為原始資料中的 `review_id` 可能重複。`clean_olist.py` 會把地理資料彙總為每個郵遞區號前綴一列，並保留原始座標的筆數，因此清理後的 `geolocation` 以郵遞區號作為主鍵。

若先前已建立沒有 `geolocation_sample_count` 欄位的 `geolocation` 表，`CREATE TABLE IF NOT EXISTS` 不會自動修改既有結構。匯入新版 CSV 前，先在 MariaDB 執行：

```sql
ALTER TABLE geolocation
    ADD COLUMN geolocation_sample_count INT NOT NULL DEFAULT 1;
```

接著重新產生清理檔，再明確完整重匯；`--replace` 會清空並重載全部 9 張原始匯入表：

```powershell
uv run python .\clean_olist.py
uv run python .\import_to_mariadb.py --replace
```

## 5. 清理資料

```powershell
& .\.venv\Scripts\python.exe .\clean_olist.py
```

清理程式會統一欄位名稱、修正 `lenght` 拼字、清除文字前後空白、將空字串轉為缺失值、整理日期為 `YYYY-MM-DD HH:MM:SS`、轉換數值欄位，並將 ZIP Code 保留為 5 位字串。**此流程也會變更列數與資料內容，不是只有格式轉換：**

- 訂單僅保留有效購買時間早於 2018-09-01，且顧客交付時間不早於購買時間的資料；商品、付款與評論會排除不屬於保留訂單的列。
- 地理資料按郵遞區號前綴彙總，緯度與經度取平均、城市與州別取第一筆，另保留彙總前的座標筆數。
- 每個訂單只保留回覆時間最新的一則評論；付款分期數 0 會改成 1；缺少商品類別的值會補成 `unknown`。

原始 CSV 保留在 `data/raw/`，清理結果另寫到 `data/clean/`。匯入前請確認上述分析篩選符合需求；若要保留每筆原始地理座標或每則評論，需調整清理規則。

## 6. 匯入 MariaDB

確認 MariaDB 已啟動、資料庫與資料表已建立，且 `.env` 已填好：

```powershell
& .\.venv\Scripts\python.exe .\import_to_mariadb.py
```

匯入程式會依父表到子表的順序匯入，每批 5,000 筆，將缺失值轉為 MariaDB `NULL`，並驗證 CSV 欄位名稱與預期 schema 一致。目標表列數與 CSV 相同時會跳過；表內已有部分資料時會停止，不會默默刪除資料。若 CSV 內容更新但列數相同，也請使用 `uv run python .\import_to_mariadb.py --replace` 明確重新載入；這會先刪除所有 9 張匯入表的資料，再重新匯入。

## 7. 建立 Power BI 分析資料集

原始資料匯入完成後，執行 `db/002_analytics_model.sql` 建立維度表、事實表，以及適合 Power BI 使用的兩個檢視表：

先從專案根目錄連到 `.env` 指定的資料庫（以下以 `olist_db` 為例）：

```powershell
mariadb -h localhost -P 3306 -u root -p -D olist_db
```

在 client 提示符中執行：

```sql
SOURCE db/002_analytics_model.sql;
```

若自行設定了不同的 `MARIADB_DATABASE`，請將命令中的 `olist_db` 換成相同名稱。SQL 檔本身不切換資料庫，會在 client 目前選取的資料庫執行。可重複執行，既有維度與事實列會更新，不會清空原始表或分析表。

- `view_order_summary`：每筆訂單恰好一列，訂單商品、付款與評論分別先彙總，避免多對多 JOIN 導致金額重複；另提供郵遞區號彙總座標供地圖視覺化。
- `view_order_item_summary`：每筆訂單商品項目一列，適合商品類別、賣家與城市分析；不帶入訂單層級的付款或評論指標，避免被商品項目數重複加總。

Power BI Desktop 可安裝 MariaDB ODBC Driver，透過 ODBC 連線到 MariaDB，再選取上述 View。不要把資料庫密碼放進公開網頁；GitHub Pages 版本使用已彙總的靜態 JSON，不會連線到 MariaDB。

## 8. GitHub Pages 城市分析頁

清理 CSV 後，彙總月營運指標、品類、付款方式、物流州別、城市、顧客 RFM 與賣家風險，產生靜態網站資料：：

```powershell
uv run python .\scripts\build_city_dashboard.py
```

在專案根目錄啟動本機預覽：

```powershell
uv run python -m http.server 8000 --directory docs
```

開啟 `http://localhost:8000`。網站資料分為 `docs/data/business_summary.json`（月別、州別、品類、付款、顧客分群與賣家風險摘要）及 `docs/data/cities.json`（彙總城市資料）。城市明細會在瀏覽者開啟區域分析時才載入，縮短初始報告等待時間。資料不包含顧客 ID、訂單 ID、評論文字或 MariaDB 憑證。產生器會補齊資料期間內沒有訂單的月份，使趨勢圖不會跨越缺月；月彙總中的 `buyers` 是該月不重複顧客數，整段期間的唯一顧客數另由 RFM 快照計算，不能直接把每月顧客數相加。更新資料後重新產生兩份 JSON，再推送到 GitHub；接著在 Repository **Settings → Pages** 選擇從 `main` 分支的 `/docs` 資料夾部署，即可取得 `https://<帳號>.github.io/<專案>/` 網址。

網站指標來自 Olist 公開資料，依 CC BY-NC-SA 4.0 標示來源。商品金額是商品明細價格總和，不含運費或利潤，不應解讀為實際淨營收。

✦ ───────────────────────────── ✦

## 快速開始（懶人包）

> 🌟 想直接開跑？依序準備環境、設定連線、放入 CSV，再清理、建表及匯入：

```text
🧰 準備工具  →  🔐 設定連線  →  📦 放入 CSV  →  🧹 清理  →  🗄️ 建表  →  📥 匯入
	uv sync         .env          data/raw/       clean_olist.py  setup_mariadb.py  import_to_mariadb.py
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

### 🚀 4. 依序清理、建表與匯入

```powershell
uv run python clean_olist.py
uv run python setup_mariadb.py
uv run python import_to_mariadb.py
```

✅ **完成！** 如果以上三個步驟都順利跑完，Olist 資料就已經在 MariaDB 裡排好隊了。

## 注意事項

- `data/` 中的原始與清理 CSV 不應提交到 Git；目前 `data/raw/` 與 `data/clean/` 都被 `.gitignore` 忽略。
- MariaDB 匯入前請確認資料表欄位型別、索引、主鍵與外鍵和 CSV 一致。
