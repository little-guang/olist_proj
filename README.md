# Olist 電商資料分析專案

本專案提供兩條彼此獨立、可單獨使用的分析流程：

1. **CSV → Python → GitHub Pages**：清理 Olist CSV，產生靜態商業分析網站。不需要 MariaDB、ODBC 或 Power BI。
2. **CSV → Python → MariaDB → ODBC → Power BI**：將清理後的資料匯入 MariaDB，建立分析資料模型，再由 Power BI 透過 MariaDB ODBC Driver 連線。

兩條流程共用原始 CSV 與 `clean_olist.py`。可以只選一條，也可以清理一次後，接著各自完成兩條流程。

## 互動式商業分析網站

[**查看完整互動式分析網站 →**](https://little-guang.github.io/olist_proj/)

## 專案結構

```text
olist_proj/
├─ data/
│  ├─ raw/                         # 本機 Olist 原始 CSV，不提交
│  └─ clean/                       # Python 清理後 CSV，不提交
├─ docs/                            # GitHub Pages 網站及彙總 JSON
├─ scripts/
│  └─ build_city_dashboard.py       # 產生網站 JSON
├─ tests/
│  └─ test_build_city_dashboard.py
├─ mariadb_powerbi/                 # MariaDB／ODBC／Power BI 專用檔案
│  ├─ db/                           # MariaDB 建表及 Power BI 分析模型 SQL
│  ├─ .env.example                  # MariaDB 連線設定範本
│  ├─ setup_mariadb.py              # 建資料庫及原始表格
│  └─ import_to_mariadb.py          # 匯入清理後 CSV
├─ clean_olist.py                   # 兩條流程共用的資料清理程式
├─ pyproject.toml
├─ uv.lock
└─ README.md
```

`.env`、原始／清理 CSV、虛擬環境和 Power BI `.pbix` 檔留在本機，不要提交到 GitHub。

## 共同準備：下載與清理 CSV

從 [Kaggle Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 下載 9 個 CSV，放在 `data/raw/`，並保留原始檔名：

- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

安裝 Python 專案依賴並清理資料：

```powershell
uv sync
uv run python .\clean_olist.py
```

清理結果會寫入 `data/clean/`。清理不只是格式轉換，也會篩選訂單、彙總地理資料，並為每筆訂單保留最新的一則評論；詳細口徑見下方「資料篩選與授權」。

完成共同準備後，選擇以下其中一條或兩條流程。

## 做法 A：CSV → Python → GitHub Pages

這條流程直接由清理後 CSV 產生靜態網站，不連線 MariaDB，不需要 ODBC 或 Power BI。

### 產生及預覽網站

```powershell
uv run python .\scripts\build_city_dashboard.py
uv run python -m http.server 8000 --directory docs
```

在瀏覽器開啟 `http://localhost:8000`。產生器會更新：

- `docs/data/business_summary.json`：月趨勢、下單時段、州別、品類、付款、顧客分群、配送時間與評價關聯及賣家風險。
- `docs/data/cities.json`：城市彙總明細；網站進入區域分析時才會載入。

若要公開網站，將專案推送到 GitHub，然後在 Repository 的 **Settings → Pages** 設定從 `main` 分支的 `/docs` 資料夾部署。部署完成後，GitHub Pages 設定頁會顯示網站網址。

## 做法 B：CSV → Python → MariaDB → ODBC → Power BI

這條流程使用 `mariadb_powerbi/` 內的資料庫檔案，與 GitHub Pages 的網站產生流程分開。

### 1. 安裝 MariaDB 專用 Python 套件

在專案根目錄執行：

```powershell
uv sync --extra mariadb
```

### 2. 設定 MariaDB 連線

複製範本，在 `mariadb_powerbi/` 資料夾內建立 `.env`，再填入自己的 MariaDB 資訊：

```powershell
Copy-Item .\mariadb_powerbi\.env.example .\mariadb_powerbi\.env
```

確認 MariaDB 服務已啟動。`.env` 含有資料庫密碼，只留在本機。

### 3. 建立資料庫和原始資料表

```powershell
uv run --extra mariadb python .\mariadb_powerbi\setup_mariadb.py
```

程式會讀取 `mariadb_powerbi/.env`，建立資料庫（預設 `olist_db`）和 9 張原始資料表。這一步只建結構，不會匯入 CSV。

### 4. 匯入清理後 CSV

```powershell
uv run --extra mariadb python .\mariadb_powerbi\import_to_mariadb.py
```

程式會從共用的 `data/clean/` 讀取 CSV。若清理檔更新且要完整重匯，才明確使用：

```powershell
uv run --extra mariadb python .\mariadb_powerbi\import_to_mariadb.py --replace
```

**注意：**`--replace` 會清空並重載 9 張原始匯入表，執行前確認目標資料庫正確。

### 5. 建立 Power BI 分析模型

原始 CSV 匯入成功後，從專案根目錄連線到 `.env` 指定的資料庫（以下假設資料庫名稱是 `olist_db`）：

```powershell
mariadb -h localhost -P 3306 -u root -p -D olist_db
```

進入 MariaDB 用戶端後執行：

```sql
SOURCE mariadb_powerbi/db/002_analytics_model.sql;
```

`002_analytics_model.sql` 會建立維度表、事實表及兩個 Power BI 檢視表，並同步事實表（包括移除來源 CSV 已不存在的列）。這一步必須在原始表建立並匯入資料後執行；`setup_mariadb.py` 不會自動執行它。

- `view_order_summary`：每筆訂單一列；商品、付款及評論先各自彙總，避免多對多 JOIN 重複計算。
- `view_order_item_summary`：每筆商品項目一列，適用商品類別、賣家及城市分析；不含會因商品項目重複加總的訂單層級付款／評論指標。

最後在 Power BI Desktop 安裝 MariaDB ODBC Driver，透過 ODBC 連線到 MariaDB，並選取上述 View。

## 更新資料時的順序

如果原始 CSV 有更新，兩條流程都先重新清理：

```powershell
uv run python .\clean_olist.py
```

接著依使用目的選擇：

- **更新 GitHub Pages 網站資料**：執行 `uv run python .\scripts\build_city_dashboard.py`，再提交更新後的 `docs/`。
- **更新 MariaDB／Power BI 資料**：執行 `uv run --extra mariadb python .\mariadb_powerbi\import_to_mariadb.py --replace`，然後重新執行 `SOURCE mariadb_powerbi/db/002_analytics_model.sql;` 同步分析表與 View。

## 資料篩選與授權

清理程式會統一欄位名稱、修正 `lenght` 拼字、清理文字與日期格式，並保留 ZIP Code 前導零。它也會改變資料列數與資料內容：

- 訂單只保留有效購買時間早於 2018-09-01，且交付時間不早於購買時間的資料；商品、付款和評論會排除不屬於保留訂單的列。
- 地理資料依郵遞區號前綴彙總，座標取平均，並記錄原始座標樣本數。
- 每筆訂單只保留回覆時間最新的評論；付款分期數 0 改成 1；缺少的商品類別補為 `unknown`。

Kaggle 來源頁將資料集標示為 **CC BY-NC-SA 4.0**。公開分享時，請標示 `Brazilian E-Commerce Public Dataset by Olist`、連結 [資料集來源](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 與 [CC BY-NC-SA 4.0 授權](https://creativecommons.org/licenses/by-nc-sa/4.0/)，並說明所做修改。資料集衍生內容須依相同授權分享，且不得用於商業目的；不要暗示 Olist 或 Kaggle 認可或背書本專案。本專案程式碼的授權與資料集授權分開處理。本 README 不構成法律意見。

網站中的商品金額是商品明細價格總和，不含運費、退款或利潤，不代表公司淨營收。網站不包含顧客 ID、訂單 ID、評論文字或 MariaDB 憑證。
