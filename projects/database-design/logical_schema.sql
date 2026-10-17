-- Logical schema for the digital-marketplace EER model (eer_diagram.png), as SQL DDL.
-- Superclass/subclass relationships ({Mandatory, Or}) are mapped to one table per
-- subclass sharing the superclass primary key. Many-to-many relationships with
-- attributes (Purchases, RunsOn) become their own tables.

CREATE TABLE Organisation (
    orgName VARCHAR(100) PRIMARY KEY,
    address VARCHAR(255)
);

CREATE TABLE UserAccount (
    accountId   INT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,   -- alternate key
    gender      VARCHAR(20),
    phoneNumber VARCHAR(30),
    DOB         DATE
);

CREATE TABLE DeveloperAccount (
    accountId     INT PRIMARY KEY REFERENCES UserAccount(accountId),
    officeAddress VARCHAR(255),
    orgName       VARCHAR(100) NOT NULL REFERENCES Organisation(orgName)   -- AffiliatedWith (1..1)
);

CREATE TABLE CustomerAccount (
    accountId        INT PRIMARY KEY REFERENCES UserAccount(accountId),
    creditCardNumber VARCHAR(19) NOT NULL UNIQUE,  -- alternate key
    homeAddress      VARCHAR(255)
);

CREATE TABLE VirtualMachine (
    iD             INT PRIMARY KEY,
    capability     VARCHAR(100),
    dateOwned      DATE,                                                     -- attribute of Owns
    orgName        VARCHAR(100) NOT NULL REFERENCES Organisation(orgName),   -- Maintains (1..1)
    ownerAccountId INT NOT NULL REFERENCES CustomerAccount(accountId)        -- Owns (1..1)
);

CREATE TABLE EProduct (
    productId          INT PRIMARY KEY,
    releaseDate        DATE,
    developerAccountId INT NOT NULL REFERENCES DeveloperAccount(accountId)  -- Develops (1..1)
);

CREATE TABLE Music (productId INT PRIMARY KEY REFERENCES EProduct(productId), type VARCHAR(50),   quality  VARCHAR(50));
CREATE TABLE Book  (productId INT PRIMARY KEY REFERENCES EProduct(productId), title VARCHAR(255), author   VARCHAR(255));
CREATE TABLE Movie (productId INT PRIMARY KEY REFERENCES EProduct(productId), title VARCHAR(255), rank     INT);
CREATE TABLE Image (productId INT PRIMARY KEY REFERENCES EProduct(productId), size  VARCHAR(50),  category VARCHAR(100));

CREATE TABLE Purchase (
    accountId INT REFERENCES CustomerAccount(accountId),
    productId INT REFERENCES EProduct(productId),
    price     DECIMAL(10, 2),
    discount  DECIMAL(5, 2),
    PRIMARY KEY (accountId, productId)
);

CREATE TABLE RunsOn (
    productId INT REFERENCES EProduct(productId),
    iD        INT REFERENCES VirtualMachine(iD),
    PRIMARY KEY (productId, iD)
);
