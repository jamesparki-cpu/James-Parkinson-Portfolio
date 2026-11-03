-- Anime studio database: schema
-- Originally built on MariaDB (university server). Standard SQL, also runs in DuckDB/PostgreSQL.
-- For MariaDB/MySQL, create and select a database first:  CREATE DATABASE anime_db; USE anime_db;

CREATE TABLE Creator (
    crID        INT NOT NULL,
    crName      VARCHAR(255),
    age         INT,
    nationality VARCHAR(255),
    PRIMARY KEY (crID)
);

CREATE TABLE Studio (
    stID         INT NOT NULL,
    stName       VARCHAR(255),
    headquarters VARCHAR(255),
    PRIMARY KEY (stID)
);

CREATE TABLE Anime (
    anID    INT NOT NULL,
    title   VARCHAR(255),
    genre   VARCHAR(100),
    aFormat VARCHAR(50),
    PRIMARY KEY (anID)
);

-- Creator is under contract with Studio (many-to-many)
CREATE TABLE ContractsWith (
    crID  INT NOT NULL,
    stID  INT NOT NULL,
    since DATE,
    PRIMARY KEY (crID, stID),
    FOREIGN KEY (crID) REFERENCES Creator(crID),
    FOREIGN KEY (stID) REFERENCES Studio(stID)
);

-- Creator created Anime (many-to-many)
CREATE TABLE CreatedBy (
    crID INT NOT NULL,
    anID INT NOT NULL,
    PRIMARY KEY (crID, anID),
    FOREIGN KEY (crID) REFERENCES Creator(crID),
    FOREIGN KEY (anID) REFERENCES Anime(anID)
);

-- Studio releases Anime, with stock figures
CREATE TABLE Releases (
    stID            INT NOT NULL,
    anID            INT NOT NULL,
    copiesAvailable INT DEFAULT 0,
    copiesSold      INT DEFAULT 0,
    PRIMARY KEY (stID, anID),
    FOREIGN KEY (stID) REFERENCES Studio(stID),
    FOREIGN KEY (anID) REFERENCES Anime(anID)
);
