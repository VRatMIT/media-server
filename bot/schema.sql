CREATE TABLE IF NOT EXISTS videos (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL UNIQUE,
    filename    TEXT NOT NULL UNIQUE, -- relative to video root
    uploaded_by INTEGER NOT NULL,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
