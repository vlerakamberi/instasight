CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    followers_count INTEGER DEFAULT 0,
    media_count INTEGER DEFAULT 0,
    biography TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    caption TEXT,
    media_type TEXT,
    timestamp TIMESTAMP,
    permalink TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    followers_count INTEGER DEFAULT 0,
    avg_engagement_rate REAL DEFAULT 0.0,
    posts_count INTEGER DEFAULT 0,
    posts_this_week INTEGER DEFAULT 0,
    top_media_type TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    UNIQUE(account_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    metric_value REAL,
    metric_previous REAL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_sent INTEGER DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE INDEX IF NOT EXISTS idx_posts_account_id ON posts(account_id);
CREATE INDEX IF NOT EXISTS idx_insights_post_id ON insights(post_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_account_date
    ON performance_snapshots(account_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_alerts_account_id
    ON alerts(account_id);
