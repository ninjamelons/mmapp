DROP TABLE IF EXISTS [Acquisition];

CREATE TABLE [Acquisition] (
    [Id] INTEGER PRIMARY KEY,
    [SeriesId] INTEGER NOT NULL,
    [CoordX] INTEGER NOT NULL,
    [CoordY] INTEGER NOT NULL,
    [Frequency] INTEGER NOT NULL,
    [Intensity] REAL NOT NULL
);

/*
SELECT * FROM Acquisition WHERE
        (CoordX > -1 AND CoordX < 1) AND
        (CoordY > -1 AND CoordY < 1) AND
        (Frequency > 100 AND Frequency < 1000)