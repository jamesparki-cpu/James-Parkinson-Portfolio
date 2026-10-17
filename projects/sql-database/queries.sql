-- Q1. Names of studios that have released at least one TV-format anime.
SELECT DISTINCT s.stName
FROM Studio s
JOIN Releases r ON s.stID = r.stID
JOIN Anime a    ON r.anID = a.anID
WHERE a.aFormat = 'TV';

-- Q2. Studios that have released both a mecha and a slice-of-life anime (self-join on Releases).
SELECT DISTINCT s.stName
FROM Studio s
JOIN Releases r1 ON s.stID = r1.stID
JOIN Anime a1    ON r1.anID = a1.anID
JOIN Releases r2 ON s.stID = r2.stID
JOIN Anime a2    ON r2.anID = a2.anID
WHERE a1.genre = 'mecha'
  AND a2.genre = 'slice of life';

-- Q3. Studios that release EVERY isekai anime with copies still available (relational division via COUNT).
SELECT s.stName
FROM Studio s
JOIN Releases r ON s.stID = r.stID
JOIN Anime a    ON r.anID = a.anID
WHERE a.genre = 'isekai' AND r.copiesAvailable > 0
GROUP BY s.stID, s.stName
HAVING COUNT(DISTINCT a.anID) = (SELECT COUNT(*) FROM Anime WHERE genre = 'isekai');

-- Q4. IDs of studios releasing slice-of-life anime that have no contracted creator older than 30.
SELECT DISTINCT s.stID
FROM Studio s
JOIN Releases r ON s.stID = r.stID
JOIN Anime a    ON r.anID = a.anID
WHERE a.genre = 'slice of life'
  AND s.stID NOT IN (
      SELECT c_link.stID
      FROM ContractsWith c_link
      JOIN Creator c ON c_link.crID = c.crID
      WHERE c.age > 30
  );

-- Q5. Age of the oldest contracted creator at each studio.
SELECT s.stID, MAX(c.age) AS OldestCreatorAge
FROM Studio s
JOIN ContractsWith cw ON s.stID = cw.stID
JOIN Creator c        ON cw.crID = c.crID
GROUP BY s.stID;

-- Q6. Creators older than at least one creator contracted with 'Mecha Forge' (> ANY).
SELECT DISTINCT c.crName
FROM Creator c
WHERE c.age > ANY (
    SELECT c2.age
    FROM Creator c2
    JOIN ContractsWith cw ON c2.crID = cw.crID
    JOIN Studio s         ON cw.stID = s.stID
    WHERE s.stName = 'Mecha Forge'
);

-- Q7. Creators contracted with a studio that has released anime in five or more genres.
SELECT DISTINCT c.crName
FROM Creator c
JOIN ContractsWith cw ON c.crID = cw.crID
WHERE cw.stID IN (
    SELECT r.stID
    FROM Releases r
    JOIN Anime a ON r.anID = a.anID
    GROUP BY r.stID
    HAVING COUNT(DISTINCT a.genre) >= 5
);
