# ELK レンダリング テスト

mermaid の `%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%` ディレクティブで ELK レイアウトエンジンを有効化します。

---

## 1. ELK あり（複雑なフローチャート）

%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
graph LR
    subgraph Frontend["フロントエンド"]
        UI["Web UI"]
        Mobile["モバイルアプリ"]
    end

    subgraph API["API サーバー"]
        Router["ルーター"]
        Auth["認証ミドルウェア"]
        TaskCtrl["タスクコントローラ"]
        LabelCtrl["ラベルコントローラ"]
    end

    subgraph DB["データストア"]
        Postgres["PostgreSQL"]
        Redis["Redis（キャッシュ）"]
    end

    subgraph Worker["バックグラウンドワーカー"]
        Queue["ジョブキュー"]
        ReportJob["レポート生成"]
        ReminderJob["リマインダー送信"]
    end

    UI -->|"HTTP/REST"| Router
    Mobile -->|"HTTP/REST"| Router
    Router --> Auth
    Auth --> TaskCtrl
    Auth --> LabelCtrl
    TaskCtrl --> Postgres
    TaskCtrl --> Redis
    LabelCtrl --> Postgres
    TaskCtrl -->|"ジョブ登録"| Queue
    Queue --> ReportJob
    Queue --> ReminderJob
    ReportJob --> Postgres
    ReminderJob --> Redis
```

---

## 2. ELK なし（同じ構造、dagre デフォルト）

```mermaid
graph LR
    subgraph Frontend["フロントエンド"]
        UI["Web UI"]
        Mobile["モバイルアプリ"]
    end

    subgraph API["API サーバー"]
        Router["ルーター"]
        Auth["認証ミドルウェア"]
        TaskCtrl["タスクコントローラ"]
        LabelCtrl["ラベルコントローラ"]
    end

    subgraph DB["データストア"]
        Postgres["PostgreSQL"]
        Redis["Redis（キャッシュ）"]
    end

    subgraph Worker["バックグラウンドワーカー"]
        Queue["ジョブキュー"]
        ReportJob["レポート生成"]
        ReminderJob["リマインダー送信"]
    end

    UI -->|"HTTP/REST"| Router
    Mobile -->|"HTTP/REST"| Router
    Router --> Auth
    Auth --> TaskCtrl
    Auth --> LabelCtrl
    TaskCtrl --> Postgres
    TaskCtrl --> Redis
    LabelCtrl --> Postgres
    TaskCtrl -->|"ジョブ登録"| Queue
    Queue --> ReportJob
    Queue --> ReminderJob
    ReportJob --> Postgres
    ReminderJob --> Redis
```

---

## 3. ELK + TB（上から下、ポート割り当てが顕著）

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
graph TB
    A["入力データ"] --> B["バリデーション"]
    A --> C["サニタイズ"]
    B --> D{"検証OK?"}
    C --> D
    D -->|"Yes"| E["DBへ保存"]
    D -->|"No"| F["エラー返却"]
    E --> G["キャッシュ更新"]
    E --> H["イベント発行"]
    H --> I["ワーカー1"]
    H --> J["ワーカー2"]
    H --> K["ワーカー3"]
    I --> L["完了通知"]
    J --> L
    K --> L
```
