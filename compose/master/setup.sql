DROP DATABASE IF EXISTS tse_market;
CREATE DATABASE tse_market;
Use tse_market;

GRANT ALL PRIVILEGES ON tse_market.* TO 'master'@'%';

DROP TABLE IF EXISTS instrument_identification;
DROP TABLE IF EXISTS instrument_type;
DROP TABLE IF EXISTS exchange_market;
DROP TABLE IF EXISTS industry_sub_sector;
DROP TABLE IF EXISTS industry_sector;
DROP TABLE IF EXISTS realtime_tsetmc_natleg_contribution;
DROP TABLE IF EXISTS daily_trade_candle;
DROP TABLE IF EXISTS daily_natleg_contribution;

CREATE TABLE industry_sector(
	id INT NOT NULL,
	title NVARCHAR(64) NOT NULL,
	CONSTRAINT pk_industry_sector PRIMARY KEY (id)
);

CREATE TABLE industry_sub_sector(
	id INT NOT NULL,
	title NVARCHAR(64) NOT NULL,
	industry_sector_id INT NOT NULL,
	CONSTRAINT pk_industry_sub_sector PRIMARY KEY (id),
	CONSTRAINT fk_industry_sector_industry_sub_sector FOREIGN KEY (industry_sector_id) REFERENCES industry_sector(id)
);

CREATE TABLE exchange_market(
	id INT NOT NULL,
	title NVARCHAR(64) NOT NULL,
	CONSTRAINT pk_exchange_market PRIMARY KEY (id)
);

CREATE TABLE instrument_type(
	id INT NOT NULL,
	title NVARCHAR(128) NOT NULL,
	CONSTRAINT pk_instrument_type PRIMARY KEY (id)
);

CREATE TABLE instrument_identification(
	isin NCHAR(12) NOT NULL,
	tsetmc_code NVARCHAR(32) NOT NULL,
	ticker NVARCHAR(32) NOT NULL,
	persian_name NVARCHAR(64) NULL,
	english_name NVARCHAR(64) NULL,
	instrument_type_id INT NOT NULL,
	exchange_market_id INT NULL,
	industry_sub_sector_id INT NULL,
	CONSTRAINT pk_instrument_identification PRIMARY KEY (isin),
	CONSTRAINT uq_instrument_identification_tsetmc_code UNIQUE (tsetmc_code),
	CONSTRAINT fk_identification_type FOREIGN KEY (instrument_type_id) REFERENCES instrument_type(id),
	CONSTRAINT fk_identification_tsetmc_exchange_market FOREIGN KEY (exchange_market_id) REFERENCES exchange_market(id),
	CONSTRAINT fk_identification_tsetmc_industry_sub_sector FOREIGN KEY (industry_sub_sector_id) REFERENCES industry_sub_sector(id)
);

CREATE TABLE index_identification(
	isin NCHAR(12) NOT NULL,
	tsetmc_code NVARCHAR(32) NOT NULL,
	persian_name NVARCHAR(64) NULL,
	english_name NVARCHAR(64) NULL,
	CONSTRAINT pk_index_identification PRIMARY KEY (isin),
	CONSTRAINT uq_index_identification_tsetmc_code UNIQUE (tsetmc_code)
);

CREATE TABLE daily_trade_candle(
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	previous_price BIGINT,
	open_price BIGINT,
	close_price BIGINT,
	last_price BIGINT,
	max_price BIGINT,
	min_price BIGINT,
	trade_num INT,
	trade_volume BIGINT,
	trade_value BIGINT,
	CONSTRAINT pk_daily_trade_candle PRIMARY KEY (isin),
	CONSTRAINT fk_daily_trade_candle_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(Isin)	
);

CREATE TABLE daily_client_type(
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	natural_buy_num INT NOT NULL,
	legal_buy_num INT NOT NULL,
	natural_buy_volume BIGINT NOT NULL,
	legal_buy_volume BIGINT NOT NULL,
	natural_sell_num INT NOT NULL,
	legal_sell_num INT NOT NULL,
	natural_sell_volume BIGINT NOT NULL,
	legal_sell_volume BIGINT NOT NULL,
	CONSTRAINT pk_daily_client_type PRIMARY KEY (isin),
	CONSTRAINT fk_daily_client_type_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(isin)
);

CREATE TABLE daily_instrument_detail(
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	total_share_count BIGINT,
	base_volume BIGINT,
	max_price_threshold BIGINT,
	min_price_threshold BIGINT,
	CONSTRAINT pk_daily_instrument_detail PRIMARY KEY (isin),
	CONSTRAINT fk_daily_instrument_detail_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(isin)
);

CREATE TABLE tick_trade(
	isin NCHAR(12) NOT NULL,
	record_date_time DATETIME NOT NULL,
	htn INT NOT NULL,
	quantity BIGINT NOT NULL,
	price BIGINT NOT NULL,
	invalidated BIT NOT NULL DEFAULT 0,
	CONSTRAINT pk_tick_trade PRIMARY KEY (isin),
	CONSTRAINT fk_tick_trade_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(Isin)
);

CREATE TABLE daily_index_value(
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	close_value FLOAT NOT NULL, 
	max_value FLOAT NOT NULL,
	min_value FLOAT NOT NULL,
	CONSTRAINT pk_daily_index_value PRIMARY KEY (isin),
	CONSTRAINT fk_daily_index_value_index_identification FOREIGN KEY (isin) REFERENCES index_identification(isin)
);
