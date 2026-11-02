-- Enskilda händelser. Gallras efter 90 dagar. IP-adress och webbläsare sparas aldrig.
CREATE TABLE IF NOT EXISTS handelser (
  id INTEGER PRIMARY KEY,
  dag TEXT NOT NULL,
  typ TEXT NOT NULL,          -- 's' = sidvisning, 'e' = händelse
  namn TEXT,
  varde TEXT,
  sida TEXT NOT NULL,
  kalla TEXT,
  utm_kalla TEXT,
  utm_medium TEXT,
  utm_kampanj TEXT,
  enhet TEXT,
  land TEXT,
  besokare TEXT NOT NULL      -- engångsvärde för dygnet, se dagsnyckel
);
CREATE INDEX IF NOT EXISTS handelser_dag ON handelser (dag);

-- Slumpnyckel per dygn. Raderas när dygnet är slut, så att besökare inte kan följas mellan dagar.
CREATE TABLE IF NOT EXISTS dagsnyckel (
  dag TEXT PRIMARY KEY,
  nyckel TEXT NOT NULL
);

-- Summeringar som sparas efter att händelserna gallrats.
CREATE TABLE IF NOT EXISTS dagsumma (
  dag TEXT NOT NULL,
  dimension TEXT NOT NULL,
  nyckel TEXT NOT NULL,
  antal INTEGER NOT NULL,
  unika INTEGER NOT NULL,
  PRIMARY KEY (dag, dimension, nyckel)
);
