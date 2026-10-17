-- Illustrative sample data (invented for demonstration).
-- Chosen so that every query in queries.sql has a non-trivial answer, including the
-- edge cases: a studio with an out-of-stock isekai title (excluded by Q3) and a studio
-- whose only contracted creator is 30 or under (returned by Q4).

INSERT INTO Creator VALUES
    (1, 'Aiko Tanaka',  28, 'Japanese'),
    (2, 'Kenji Mori',   41, 'Japanese'),
    (3, 'Lena Fischer', 35, 'German'),
    (4, 'Sam Okafor',   24, 'Nigerian'),
    (5, 'Mina Park',    31, 'Korean');

INSERT INTO Studio VALUES
    (1, 'Mecha Forge',   'Tokyo'),
    (2, 'Sunlit Frames', 'Osaka'),
    (3, 'Portal Works',  'Kyoto'),
    (4, 'Quiet Hours',   'Sapporo');

INSERT INTO Anime VALUES
    (1, 'Iron Tide',       'mecha',         'TV'),
    (2, 'Steel Bloom',     'mecha',         'Movie'),
    (3, 'Tea at Noon',     'slice of life', 'TV'),
    (4, 'Another Sky',     'isekai',        'TV'),
    (5, 'Reborn Merchant', 'isekai',        'OVA'),
    (6, 'Night Market',    'slice of life', 'Movie'),
    (7, 'Shadow Court',    'fantasy',       'TV'),
    (8, 'Last Inning',     'sports',        'TV'),
    (9, 'Quiet Signal',    'drama',         'Movie');

INSERT INTO ContractsWith VALUES
    (1, 1, DATE '2020-01-15'),
    (2, 1, DATE '2018-05-01'),
    (3, 2, DATE '2021-09-30'),
    (4, 4, DATE '2023-03-12'),
    (5, 3, DATE '2019-11-20'),
    (4, 3, DATE '2024-02-01');

INSERT INTO CreatedBy VALUES
    (1, 1), (2, 2), (2, 1), (3, 3), (3, 6), (5, 4), (5, 5), (4, 7), (4, 8), (3, 9);

INSERT INTO Releases VALUES
    (1, 1, 10, 50), (1, 2, 0, 30), (1, 3, 5, 12),
    (2, 3, 4, 20),  (2, 6, 2, 8),  (2, 9, 1, 3),
    (3, 4, 7, 40),  (3, 5, 3, 15), (3, 7, 6, 22), (3, 8, 2, 9), (3, 1, 0, 5), (3, 3, 1, 1),
    (4, 5, 0, 10),  (4, 6, 3, 7);
