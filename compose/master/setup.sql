DROP DATABASE IF EXISTS TseMarket;
CREATE DATABASE TseMarket;
Use TseMarket;

GRANT ALL PRIVILEGES ON TseMarket.* TO 'master'@'%';

DROP TABLE IF EXISTS InstrumentIdentification;
DROP TABLE IF EXISTS InstrumentType;
DROP TABLE IF EXISTS ExchangeMarket;
DROP TABLE IF EXISTS IndustrySubSector;
DROP TABLE IF EXISTS IndustrySector;
DROP TABLE IF EXISTS RealtimeTsetmcNatlegContribution;
DROP TABLE IF EXISTS DailyTradeCandle;
DROP TABLE IF EXISTS DailyNatlegContribution;

CREATE TABLE IndustrySector(
	Id INT NOT NULL,
	Title NVARCHAR(64) NOT NULL,
	CONSTRAINT PK_IndustrySector PRIMARY KEY (Id)
);

CREATE TABLE IndustrySubSector(
	Id INT NOT NULL,
	Title NVARCHAR(64) NOT NULL,
	IndustrySectorId INT NOT NULL,
	CONSTRAINT PK_IndustrySubSector PRIMARY KEY (Id),
	CONSTRAINT FK_IndustrySector_IndustrySubSector FOREIGN KEY (IndustrySectorId) REFERENCES IndustrySector(Id)
);

CREATE TABLE ExchangeMarket(
	Id INT NOT NULL,
	Title NVARCHAR(64) NOT NULL,
	CONSTRAINT PK_ExchangeMarket PRIMARY KEY (Id)
);

CREATE TABLE InstrumentType(
	Id INT NOT NULL,
	Title NVARCHAR(128) NOT NULL,
	CONSTRAINT PK_InstrumentType PRIMARY KEY (Id)
);

CREATE TABLE InstrumentIdentification(
	Isin NCHAR(12) NOT NULL,
	TsetmcCode NVARCHAR(32) NOT NULL,
	Ticker NVARCHAR(32) NOT NULL,
	PersianName NVARCHAR(64) NULL,
	EnglishName NVARCHAR(64) NULL,
	InstrumentTypeId INT NOT NULL,
	ExchangeMarketId INT NULL,
	IndustrySubSectorId INT NULL,
	CONSTRAINT PK_InstrumentIdentification PRIMARY KEY (Isin),
	CONSTRAINT UQ_InstrumentIdentification_TsetmcCode UNIQUE (TsetmcCode),
	CONSTRAINT FK_Identification_Type FOREIGN KEY (InstrumentTypeId) REFERENCES InstrumentType(Id),
	CONSTRAINT FK_Identification_TsetmcExchangeMarket FOREIGN KEY (ExchangeMarketId) REFERENCES ExchangeMarket(Id),
	CONSTRAINT FK_Identification_TsetmcIndustrySubSector FOREIGN KEY (IndustrySubSectorId) REFERENCES IndustrySubSector(Id)
);

CREATE TABLE IndexIdentification(
	Isin NCHAR(12) NOT NULL,
	TsetmcCode NVARCHAR(32) NOT NULL,
	PersianName NVARCHAR(64) NULL,
	EnglishName NVARCHAR(64) NULL,
	CONSTRAINT PK_IndexIdentification PRIMARY KEY (Isin),
	CONSTRAINT UQ_IndexIdentification_TsetmcCode UNIQUE (TsetmcCode)
);

CREATE TABLE DailyTradeCandle(
	Isin NCHAR(12) NOT NULL,
	RecordDate DATE NOT NULL,
	PreviousPrice BIGINT,
	OpenPrice BIGINT,
	ClosePrice BIGINT,
	LastPrice BIGINT,
	MaxPrice BIGINT,
	MinPrice BIGINT,
	TradeNum INT,
	TradeVolume BIGINT,
	TradeValue BIGINT,
	CONSTRAINT PK_DailyTradeCandle PRIMARY KEY (Isin),
	CONSTRAINT FK_DailyTradeCandle_InstrumentIdentification FOREIGN KEY (Isin) REFERENCES InstrumentIdentification(Isin)	
);

CREATE TABLE DailyClientType(
	Isin NCHAR(12) NOT NULL,
	RecordDate DATE NOT NULL,
	NaturalBuyNum INT NOT NULL,
	LegalBuyNum INT NOT NULL,
	NaturalBuyVolume BIGINT NOT NULL,
	LegalBuyVolume BIGINT NOT NULL,
	NaturalSellNum INT NOT NULL,
	LegalSellNum INT NOT NULL,
	NaturalSellVolume BIGINT NOT NULL,
	LegalSellVolume BIGINT NOT NULL,
	CONSTRAINT PK_DailyClientType PRIMARY KEY (Isin),
	CONSTRAINT FK_DailyClientType_InstrumentIdentification FOREIGN KEY (Isin) REFERENCES InstrumentIdentification(Isin)
);

CREATE TABLE DailyInstrumentDetail(
	Isin NCHAR(12) NOT NULL,
	RecordDate DATE NOT NULL,
	TotalShareCount BIGINT,
	BaseVolume BIGINT,
	MaxPriceThreshold BIGINT,
	MinPriceThreshold BIGINT,
	CONSTRAINT PK_DailyInstrumentDetail PRIMARY KEY (Isin),
	CONSTRAINT FK_DailyInstrumentDetail_InstrumentIdentification FOREIGN KEY (Isin) REFERENCES InstrumentIdentification(Isin)
);

CREATE TABLE TickTrade(
	Isin NCHAR(12) NOT NULL,
	RecordDateTime DATETIME NOT NULL,
	Htn INT NOT NULL,
	Quantity BIGINT NOT NULL,
	Price BIGINT NOT NULL,
	Invalidated BIT NOT NULL DEFAULT 0,
	CONSTRAINT PK_TickTrade PRIMARY KEY (Isin),
	CONSTRAINT FK_TickTrade_InstrumentIdentification FOREIGN KEY (Isin) REFERENCES InstrumentIdentification(Isin)
);

CREATE TABLE DailyIndexValue(
	Isin NCHAR(12) NOT NULL,
	RecordDate DATE NOT NULL,
	CloseVal FLOAT NOT NULL, 
	MaxVal FLOAT NOT NULL,
	MinVal FLOAT NOT NULL,
	CONSTRAINT PK_DailyIndexValue PRIMARY KEY (Isin),
	CONSTRAINT FK_DailyIndexValue_IndexIdentification FOREIGN KEY (Isin) REFERENCES IndexIdentification(Isin)
);
