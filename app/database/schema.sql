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

CREATE INDEX IF NOT EXISTS idx_posts_account_id ON posts(account_id);
CREATE INDEX IF NOT EXISTS idx_insights_post_id ON insights(post_id);
