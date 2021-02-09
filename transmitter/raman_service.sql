DROP TABLE IF EXISTS [Series];
DROP TABLE IF EXISTS [SeriesEntry];

--SQLite INTEGER PRIMARY KEY is by default a reference to the rowid
--AUTOINCREMENT is unnecessary and adds overhead
CREATE TABLE [Series](
    [Id] INTEGER PRIMARY KEY,
    [Title] TEXT NOT NULL,
    [Radius] INTEGER NOT NULL,
    [Interval] INTEGER DEFAULT 10,
    [OriginX] REAL NOT NULL,
    [OriginY] REAL NOT NULL, 
    [StartDatetime] TEXT DEFAULT CURRENT_TIMESTAMP,
    [EndDatetime] TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE [SeriesEntry] (
    [SeriesId] INTEGER NOT NULL,
    [StageX] INTEGER NOT NULL,
    [StageY] INTEGER NOT NULL,
    [PointNo] INTEGER DEFAULT 0,
    [FileName] TEXT DEFAULT '',
    [InitDatetime] TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SeriesId)
        REFERENCES [Series](Id)
        ON DELETE CASCADE
);

--TEST DATA & SQL QUERIES
/*
    PRIMARY KEY (SeriesId, StageX, StageY),
INSERT INTO Series (Radius, Interval, OriginX, OriginY) VALUES
    (2, 1, 100.3, 10.4),
    (1,1, 1312.40, 120.47);

INSERT INTO SeriesEntry (SeriesId, StageX, StageY, InitDatetime) VALUES
    (1,0,0, '2020-01-01 12:30:30.500'),
    (1,1,0, '2020-01-01 12:30:35.000'),
    (1,1,-1, '2020-01-01 12:30:36.000'),
    (1,0,-1, '2020-01-01 12:30:37.000'),
    (1,-1,-1, '2020-01-01 12:30:40.523'),
    (1,-1,0, '2020-01-01 12:30:42.100'),
    (1,-1,1, '2020-01-01 12:30:43.000'),
    (1,0,1, '2020-01-01 12:30:43.500'),
    (1,1,1, '2020-01-01 12:30:43.501'),
    (2,0,0, '2020-01-01 12:30:45.000'),
    (2,1,0, '2020-01-01 12:30:45.500'),
    (2,1,-1, '2020-01-01 12:30:45.600'),
    (2,0,-1, '2020-01-01 12:30:50.100'),
    (2,-1,-1, '2020-01-01 12:30:55.169');

--TEST SQL QUERIES
SELECT Series.Id, Series.Radius, Series.Interval, SeriesEntry.StageX, SeriesEntry.StageY
FROM Series
INNER JOIN SeriesEntry
ON Series.Id = SeriesEntry.SeriesId
WHERE Series.Id = 1
ORDER BY SeriesEntry.InitDatetime DESC
LIMIT 1;