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
	industry_sector_id INT NOT NULL,
	title NVARCHAR(64) NOT NULL,
	CONSTRAINT pk_industry_sector PRIMARY KEY (industry_sector_id)
);

CREATE TABLE industry_sub_sector(
	industry_sub_sector_id INT NOT NULL,
	title NVARCHAR(64) NOT NULL,
	industry_sector_id INT NOT NULL,
	CONSTRAINT pk_industry_sub_sector PRIMARY KEY (industry_sub_sector_id),
	CONSTRAINT fk_industry_sector_industry_sub_sector FOREIGN KEY (industry_sector_id) REFERENCES industry_sector(industry_sector_id)
);

CREATE TABLE exchange_market(
	exchange_market_id INT NOT NULL,
	title NVARCHAR(64) NOT NULL,
	CONSTRAINT pk_exchange_market PRIMARY KEY (exchange_market_id)
);

CREATE TABLE instrument_type(
	instrument_type_id INT NOT NULL,
	title NVARCHAR(128) NOT NULL,
	CONSTRAINT pk_instrument_type PRIMARY KEY (instrument_type_id)
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
	CONSTRAINT fk_identification_type FOREIGN KEY (instrument_type_id) REFERENCES instrument_type(instrument_type_id),
	CONSTRAINT fk_identification_tsetmc_exchange_market FOREIGN KEY (exchange_market_id) REFERENCES exchange_market(exchange_market_id),
	CONSTRAINT fk_identification_tsetmc_industry_sub_sector FOREIGN KEY (industry_sub_sector_id) REFERENCES industry_sub_sector(industry_sub_sector_id)
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
	daily_trade_candle_id INT NOT NULL AUTO_INCREMENT,
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	previous_price BIGINT NOT NULL,
	open_price BIGINT NOT NULL,
	close_price BIGINT NOT NULL,
	last_price BIGINT NOT NULL,
	max_price BIGINT NOT NULL,
	min_price BIGINT NOT NULL,
	trade_num INT NOT NULL,
	trade_volume BIGINT NOT NULL,
	trade_value BIGINT NOT NULL,
	CONSTRAINT pk_daily_trade_candle PRIMARY KEY (daily_trade_candle_id),
	CONSTRAINT fk_daily_trade_candle_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(Isin)
);

CREATE TABLE daily_client_type(
	daily_client_type_id INT NOT NULL AUTO_INCREMENT,
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	natural_buy_num INT NOT NULL,
	legal_buy_num INT NOT NULL,
	natural_buy_value BIGINT NOT NULL,
	legal_buy_value BIGINT NOT NULL,
	natural_buy_volume BIGINT NOT NULL,
	legal_buy_volume BIGINT NOT NULL,
	natural_sell_num INT NOT NULL,
	legal_sell_num INT NOT NULL,
	natural_sell_value BIGINT NOT NULL,
	legal_sell_value BIGINT NOT NULL,
	natural_sell_volume BIGINT NOT NULL,
	legal_sell_volume BIGINT NOT NULL,
	CONSTRAINT pk_daily_client_type PRIMARY KEY (daily_client_type_id),
	CONSTRAINT fk_daily_client_type_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(isin)
);

CREATE TABLE daily_instrument_detail(
	daily_instrument_detail_id INT NOT NULL AUTO_INCREMENT,
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	total_share_count BIGINT,
	base_volume BIGINT,
	max_price_threshold BIGINT,
	min_price_threshold BIGINT,
	CONSTRAINT pk_daily_instrument_detail PRIMARY KEY (daily_instrument_detail_id),
	CONSTRAINT fk_daily_instrument_detail_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(isin)
);

CREATE TABLE tick_trade(
	tick_trade_id BIGINT NOT NULL AUTO_INCREMENT,
	isin NCHAR(12) NOT NULL,
	record_date_time DATETIME NOT NULL,
	htn INT NOT NULL,
	quantity BIGINT NOT NULL,
	price BIGINT NOT NULL,
	invalidated BIT NOT NULL DEFAULT 0,
	CONSTRAINT pk_tick_trade PRIMARY KEY (tick_trade_id),
	CONSTRAINT fk_tick_trade_instrument_identification FOREIGN KEY (isin) REFERENCES instrument_identification(Isin)
);

CREATE TABLE daily_index_value(
	daily_index_value_id INT NOT NULL AUTO_INCREMENT,
	isin NCHAR(12) NOT NULL,
	record_date DATE NOT NULL,
	close_value FLOAT NOT NULL, 
	max_value FLOAT NOT NULL,
	min_value FLOAT NOT NULL,
	CONSTRAINT pk_daily_index_value PRIMARY KEY (daily_index_value_id),
	CONSTRAINT fk_daily_index_value_index_identification FOREIGN KEY (isin) REFERENCES index_identification(isin)
);
