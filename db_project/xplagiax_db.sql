
CREATE TABLE users_admin(
  id               INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
  name	           varchar(100)	NULL,
  lastname	       varchar(100)	NULL,
  email	           varchar(100) NULL,
  password	       varchar(255)	NULL,
  active_session   tinyint(1)	NULL,
  confirmado	     tinyint(1)	NULL,
  created_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE log_status(
  id            INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
  status	      varchar(10)	NULL,
  created_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO log_status (status) values
('Loguin'),
('logout');

CREATE TABLE ErrorLogAdmin(
    id               INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    error_text       VARCHAR(255) NOT NULL,
    error_line       VARCHAR(50) NOT NULL,
    user_id          INT NULL,
    created_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
);


CREATE TABLE Country(
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    country      VARCHAR(100)  NULL,
    user_id      INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
);


INSERT INTO Country (country) values
('Dominican Republic'),
('Canada'),
('United States');

CREATE TABLE Institution(
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    institution  VARCHAR(255) NULL,
    institution_type INT NULL,
    city_id         INT NULL,
    country_id       INT  NULL,
    user_id          INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (institution_type) REFERENCES Institution_type(id),
     FOREIGN KEY (city_id) REFERENCES City (id),
    FOREIGN KEY (country_id) REFERENCES Country(id),
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
);

INSERT INTO Institution(institution,institution_type,city_id,country_id) values
('College of the Rockies'

('ABM College of Health and Technology
('Academy of Applied Pharmaceutical Sciences
('Academy of Business and Professional Training
('Acadia University
Albert College
Alexander College
Algoma University
Algonquin College
Ambrose University
Appleby College
Athabasca University
BAC Training Centre Inc./BAC Masonry College
Bayview Secondary School
Bodwell Preparatory School
Bow Valley College'
Brandon University'
Branksome Hall'
Brentwood College'
British Columbia Institute of Technology'
Brock University')
Burman University')
Camosun College')
Canadian Mennonite University')
Cape Breton University')
Carleton University')
Cégep de Sainte-Foy')
Cégep de Sherbrooke')
Cégep du Vieux Montreal')
Centennial College')
College Ahuntsic')
Maisonneuve College')
College of Rosemont')
College Lionel-Groulx')
College Montmorency')
North Atlantic College')
Columbia International College
Concordia University
Concordia University of Edmonton
Conestoga College
Crandall University
Crescent School
Crestwood Preparatory College
Crofton House School
Dalhousie University
Douglas College
Elmwood School
Fanshawe College
George Brown College
Georgian College
Greystone College
Havergal College
Herzing College
Hua Xia Acupuncture, Massage, Herb College of Canada
Hudson College
Humber College
ILAC College
John Abbott College
Kingsway College School
Kwantlen Polytechnic University
Lakefield College School
Lakehead University
Langara College
LaSalle College
Laurentian University
LINKS Institute
Little Flower Academy
London Central Secondary School
Lower Canada College
M College of Canada
Maple Grove Elementary School
McGill University
McMaster University
Memorial University of Newfoundland
Mohawk College
Mount Allison University
Mount Royal University
Mount Saint Vincent University
New Brunswick Community College
Nipissing University
Northern Alberta Institute of Technology (NAIT)
Old Scona Academic High School
Owen Public School
Pickering College
Prestige School - Toronto Campus
Queen's University
Quest University Canada
Red River College
Redeemer University
Richard Robinson Academy of Fashion Design
Rose Avenue Junior Public School
Royal Roads University
Rundle College
Saint Mary's University
Seneca College
Simon Fraser University
Simon Fraser University (SFU)
Southern Alberta Institute of Technology
Southern Alberta Institute of Technology (SAIT)
Southridge School
St. Francis Xavier University
St. George's School
St. Mary's University
St. Michael's Choir School
St. Thomas University
The Bishop Strachan School
The King's University
The York School
Thompson Rivers University
Thompson Rivers University (TRU)
Toronto Metropolitan University (TMU)
Trebas Institute
Trent University
Trinity Western University
Tyee Elementary School
Unionville High School
Université de Acadia
Université de Cape Breton
Université de Dalhousie
Université de Hearst
Université de King's College
Université de l'Île-du-Prince-Édouard
Université de l'Ontario français
Université de Moncton
Université de Montréal
Université de Mount Allison
Université de Mount Saint Vincent
Université de NSCAD
Université de Saint Mary's
Université de Saint-Boniface
Université de Saint-Michel
Université de Saint-Paul
Université de Sherbrooke
Université de St. Thomas
Université de Sudbury
Université de Trinity College
Université du Québec
Université du Québec à Chicoutimi (UQAC)
Université du Québec à Montréal (UQAM)
Université du Québec à Rimouski (UQAR)
Université du Québec à Trois-Rivières (UQTR)
Université du Québec en Abitibi-Témiscamingue (UQAT)
Université du Québec en Outaouais (UQO)
Université Laval
Université Sainte-Anne
Université TÉLUQ
University Canada West
University of Alberta
University of British Columbia
University of British Columbia (UBC)
University of Calgary
University of Guelph
University of King's College
University of Lethbridge
University of Manitoba
University of New Brunswick
University of New Brunswick (UNB)
University of Ontario Institute of Technology
University of Ottawa
University of Prince Edward Island
University of Saskatchewan
University of Toronto
University of Victoria
University of Waterloo
University of Western Ontario (Western)
University of Windsor
University of Winnipeg
Upper Canada College
Vancouver Community College (VCC)
Vancouver Island University
Vanier College
W. Erskine Johnston Public School
West Point Grey Academy
Western University
Wilfrid Laurier University
York House School
York University
Yorkville University
Yukon University


CREATE TABLE Institution_type(    
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    institution_type  VARCHAR(255) NULL,
    user_id       INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
);


INSERT INTO Institution_type (institution_type) values

('University'),
('College'),
('Cégep'),
('Technical Institute'),
('High School'),
('Elementary School')

CREATE TABLE Sector (
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    sector_type  VARCHAR(255) NULL,
    user_id      INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
)

INSERT INTO Sector(sector_type) values
('Private'),
('Public')

CREATE TABLE Province_state (
    id               INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    province_state   VARCHAR(255) NULL,
    country_id       INT  NULL,
    user_id          INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES Country(id),
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
)

INSERT INTO Province_state (province_state,country_id)values

('Alberta',2),
('British Columbia',2),
('Prince Edward Island',2),
('Manitoba',2),
('Nova Scotia',2),
('New Brunswick',2),
('Ontario',2),
('Quebec',2)
('Saskatchewan',2),
('Newfoundland and Labrador',2),
('Yukon',2)

CREATE TABLE City (
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    city         VARCHAR(255) NULL,
    state_id       INT  NULL,
    user_id      INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (state_id) REFERENCES Province_state(id),
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
)

INSERT INTO City(city,state_id)
('Ancaster',7),
('Antigonish',5),
('Athabasca',1),
('Belleville',7),
('Brandon',4),
('Burnaby',2),
('Calgary',1),
('Charlottetown',3),
('Chicoutimi',8),
('Edmonton',1),
('Etobicoke',7),
('Fredericton',6),
('Gatineau',8),
('Guelph',7),
('Halifax',5),
('Hamilton',7),
('Hearst',7),
('Kamloops',2),
('Kanata',7),
('Kingston',7),
('Kitchener',7),
('Lacombe',1),
('Lakefield',7),
('Langley',2),
('Laval',8),
('Lethbridge',1),
('London',7),
('Mill Bay',2),
('Moncton',6),
('Montreal',8),
('Nanaimo',2),
('New Westminster',2),
('Newmarket',7),
('North Bay',7),
('North Vancouver',2),
('Oakville',7),
('Oshawa',7),
('Ottawa',7),
('Peterborough',7),
('Pointe-de-l Église',5),
('Quebec City',8),
('Richmond Hill',7),
('Rimouski',8),
('Rouyn-Noranda',8),
('Sackville',6),
('Sainte-Anne-de-Bellevue',8),
('Sainte-Thérèse',8),
('Saskatoon',9),
('Sault Ste. Marie',7),
('Sherbrooke',8),
('Squamish',2),
('St. Catharines',7),
('St. Johns',10),
('Sudbury',7),
('Surrey',2),
('Thunder Bay',7),
('Toronto',7),
('Trois-Rivières',8),
('Unionville',7),
('Vancouver',2),
('Victoria',2),
('Waterloo',7),
('Whitehorse',11),
('Windsor',7),
('Winnipeg',4),
('Wolfville'5)


CREATE TABLE Doctype(
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    doctype      VARCHAR(4) NULL,
    user_id       INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
);

INSERT INTO Doctype(doctype) values
('PDF'),
('DOC'),
('DOCX'),
('XPS'),
('EPUB'),
('MOBI'),
('FB2'),
('CBZ'),
('TXT');

CREATE TABLE Lenguage(
    id              INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    lenguage_name    VARCHAR(50)  NULL,
    lenguage        VARCHAR(2)  NULL,
    user_id         INT NULL,
    created_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users_admin(id)
);


INSERT INTO Lenguage(lenguage_name,lenguage) VALUES 
('English','en'),
('Spanish','es');

-- Tabla de servicios
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    endpoint VARCHAR(500),
    timeout INTEGER DEFAULT 5,
    icon VARCHAR(100) DEFAULT 'fas fa-server',
    username VARCHAR(100),
    password_encrypted TEXT,
    extra_config TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_monitored BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users (id)
);

-- Tabla de logs de servicios
CREATE TABLE IF NOT EXISTS service_logs (
    id INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    service_id INTEGER NOT NULL,
    status BOOLEAN NOT NULL,
    response_time REAL,
    error_message TEXT,
    additional_data TEXT,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

-- Tabla de estadísticas de servicios
CREATE TABLE IF NOT EXISTS service_stats (
    id INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    service_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_checks INTEGER DEFAULT 0,
    successful_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,
    avg_response_time REAL,
    min_response_time REAL,
    max_response_time REAL,
    total_downtime INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
    UNIQUE(service_id, date)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_service_active_monitored ON services (is_active, is_monitored);
CREATE INDEX IF NOT EXISTS idx_service_type ON services (service_type);
CREATE INDEX IF NOT EXISTS idx_service_host_port ON services (host, port);

CREATE INDEX IF NOT EXISTS idx_service_log_service_time ON service_logs (service_id, checked_at);
CREATE INDEX IF NOT EXISTS idx_service_log_status_time ON service_logs (status, checked_at);

CREATE INDEX IF NOT EXISTS idx_service_stats_date ON service_stats (date);

-- Insertar servicios por defecto
INSERT INTO services (name, display_name, host, port, service_type, endpoint, timeout, icon) VALUES 
('elasticsearch', 'Elasticsearch', 'localhost', 9200, 'http', '/_cluster/health', 5, 'fas fa-search'),
('clamav', 'ClamAV', 'localhost', 3310, 'socket', NULL, 5, 'fas fa-shield-virus'),
('redis', 'Redis', 'localhost', 6379, 'redis', NULL, 5, 'fas fa-database'),
('mysql', 'MySQL', 'localhost', 3306, 'mysql', NULL, 5, 'fas fa-server'),
('qdrant', 'Qdrant', 'localhost', 6333, 'http', '/health', 5, 'fas fa-vector-square'),
('minio', 'MinIO', 'localhost', 9000, 'http', '/minio/health/live', 5, 'fas fa-cloud'),
('rabbitmq', 'RabbitMQ', 'localhost', 5672, 'rabbitmq', NULL, 5, 'fas fa-exchange-alt');

-- Actualizar configuración extra para RabbitMQ
UPDATE services SET extra_config = '{"management_port": 15672}' WHERE name = 'rabbitmq';

-- Actualizar credenciales para MySQL (usuario por defecto)
UPDATE services SET username = 'root' WHERE name = 'mysql';


CREATE TABLE Documents (
    id             INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    title          VARCHAR(255)  NULL,
    author         VARCHAR(255) NULL,
    content        LONGTEXT    NULL,
    rena           VARCHAR(255) NULL,
    theme          VARCHAR(55)  NULL,
    doctype_id     INT  NULL,
    country_id     INT  NULL,
    institution_id INT  NULL,
    lenguage_id    INT  NULL,
    user_id        INT  NULL,
    created_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctype_id) REFERENCES Doctype(id),
    FOREIGN KEY (country_id) REFERENCES Country(id),
    FOREIGN KEY (institution_id) REFERENCES Institution(id),
    FOREIGN KEY (lenguage_id) REFERENCES Lenguage(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);


CREATE TABLE Docmodels (
  id  INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
  institution_id  int  NULL,
  user_id int NULL,
  lenguage_id int  NULL,
  accuracy varchar(50)  NULL,
  model varchar(255)  NULL,
  vectorizer varchar(255)  NULL,
  xtrain varchar(255)  NULL,
  update_date timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  created_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ;

CREATE TABLE Patents (
  id           INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
  WKU	         VARCHAR(25)  NULL,
  Title	       VARCHAR(255) NULL,
  App_Date   	 VARCHAR(14) NULL,
  Issue_Date	 VARCHAR(14) NULL,
  Inventor	   VARCHAR(255) NULL,
  Assignee	   VARCHAR(100) NULL,
  ICL_Class    VARCHAR(100) NULL,
  Reference    VARCHAR(100) NULL,
  Claims       LONGTEXT NULL,
  user_id  INT NULL,
  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users_admin(id)
);

CREATE TABLE Rehearsal(
  id           INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
  title        VARCHAR(255) NULL,
  content      LONGTEXT NULL,
  source       VARCHAR(50) NULL,
  user_id      INT NULL,
  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users_admin(id)
);

CREATE TABLE  array_shape(
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    arry         LONGTEXT NULL,
    doc_id       INT NULL,
    rena         VARCHAR(255),
    row_num      INT NULL,
    columns      INT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES Documents(id)
);


CREATE TABLE Citations(
    id          INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    regex       LONGTEXT NULL,
    descripcion VARCHAR(255)  NULL,
    formato     VARCHAR(10)  NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE Feedback(
    id           INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    recipient    VARCHAR(100) NULL,
    comment      VARCHAR(255) NULL,
    user_id      BIGINT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

CREATE TABLE History_db_analysis(
    id               INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    total_percent    DECIMAL NULL,
    aproved_percent  DECIMAL NULL,
    db_percent       DECIMAL NULL,
    ai_percent       DECIMAL NULL,
    web_percent      DECIMAL NULL,
    img_percent      DECIMAL NULL,
    paragraph        INT NULL,
    user_id          INT NULL,
    created_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE History_ai_analysis(
    id                 INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    total_percent      DECIMAL NULL,
    ai_percent         DECIMAL NULL,
    probablyai_percent DECIMAL NULL,
    paragraph          INT NULL,
    perplexity         DECIMAL NULL,
    burstiness         DECIMAL NULL,
    ai                 DECIMAL NULL,
    human              DECIMAL NULL,
    writen_by          VARCHAR(15) NULL,
    user_id            INT NULL,
    created_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE users(
  id              INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
  email	          varchar(100) NULL,
  _password_hash  varchar(255) NULL,
  hashcode	      varchar(255) NULL,
  name	          varchar(100) NULL,
  lastname	      varchar(100) NULL,
  avatar	      varchar(200) NULL,
  tokens	      text	       NULL,
  institute	      varchar(255) NULL,
  country	      varchar(100) NULL,
  is_active	      tinyint(1)   NULL,
  token	          varchar(32)	 NULL,
  totp_secret     varchar(16)	 NULL,
  active_session  tinyint(1)	 NULL,
  confirmado	  tinyint(1)	 NULL,
  user_id         INT NULL,
  storage_plan_id INT NULL,
  used_storage_bytes  BIGINT NULL,
  is_professor BOOLEAN NOT NULL DEFAULT FALSE,
  created_date    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,    
  INDEX idx_user_email (email),
  INDEX idx_user_role (is_professor)
  FOREIGN KEY (user_id) REFERENCES users_admin(id)
);

-- Tabla de sesiones de entrega
CREATE TABLE IF NOT EXISTS submission_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    professor_id INT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    analysis_started BOOLEAN NOT NULL DEFAULT FALSE,
    analysis_completed BOOLEAN NOT NULL DEFAULT FALSE,
    forced_analysis BOOLEAN NOT NULL DEFAULT FALSE,
    
    FOREIGN KEY (professor_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_session_dates (start_date, end_date),
    INDEX idx_session_professor (professor_id),
    INDEX idx_session_status (analysis_started, analysis_completed)
) ENGINE=InnoDB COMMENT='Sesiones de entrega creadas por profesores';

-- Tabla de participantes de sesiones
CREATE TABLE IF NOT EXISTS session_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    email VARCHAR(120) NOT NULL,
    access_token VARCHAR(64) NOT NULL UNIQUE,
    invitation_sent BOOLEAN NOT NULL DEFAULT FALSE,
    reminder_sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES submission_sessions(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_participant_per_session (session_id, email),
    INDEX idx_participant_token (access_token),
    INDEX idx_participant_email (email)
) ENGINE=InnoDB COMMENT='Participantes autorizados por sesión';

-- Tabla de entregas de documentos
CREATE TABLE IF NOT EXISTS student_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    student_id INT NULL,
    email VARCHAR(120) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_modified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    professor_comment TEXT NULL,
    
    FOREIGN KEY (session_id) REFERENCES submission_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE KEY unique_submission_per_session_email (session_id, email),
    INDEX idx_submission_email (email),
    INDEX idx_submission_date (uploaded_at)
) ENGINE=InnoDB COMMENT='Documentos entregados por estudiantes';

-- Tabla de versiones anteriores de documentos
CREATE TABLE IF NOT EXISTS document_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INT NOT NULL,
    uploaded_at DATETIME NOT NULL,
    
    FOREIGN KEY (submission_id) REFERENCES student_submissions(id) ON DELETE CASCADE,
    
    INDEX idx_version_submission (submission_id),
    INDEX idx_version_date (uploaded_at)
) ENGINE=InnoDB COMMENT='Versiones anteriores de documentos';

-- Tabla de registro de actividades
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    email VARCHAR(120) NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    details TEXT NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(255) NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_log_user (user_id),
    INDEX idx_log_action (action),
    INDEX idx_log_entity (entity_type, entity_id),
    INDEX idx_log_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='Registro de actividades y auditoría';

CREATE TABLE users_log(
    id               INT AUTO_INCREMENT PRIMARY KEY  NOT NULL,
    user_id          INT NULL,
    log_status_ID    INT NULL,
    created_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (log_status_id) REFERENCES log_status(id)
);

INSERT INTO users (email,_password_hash,name,lastname,is_active,active_session,confirmado) values
('novas@gmail.com','123456','Ruben','Gonzalez',1,1,1);

-- Crear tabla folders
CREATE TABLE IF NOT EXISTS folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    path VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    parent_id INT NULL,
    user_id INT NOT NULL,
    is_shared BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_folder_parent FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE SET NULL,
    CONSTRAINT fk_folder_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Crear tabla files
CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(100) NOT NULL,
    original_filename VARCHAR(100) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    folder_id INT NULL,
    user_id INT NOT NULL,
    minio_url VARCHAR(255) NOT NULL,
    CONSTRAINT fk_file_folder FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL,
    CONSTRAINT fk_file_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);



-- Tabla para planes de almacenamiento
CREATE TABLE IF NOT EXISTS storage_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    base_storage_mb INT NOT NULL, -- Almacenamiento base en MB
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para complementos de almacenamiento
CREATE TABLE IF NOT EXISTS storage_addons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    storage_mb INT NOT NULL, -- Almacenamiento adicional en MB
    price_monthly_usd DECIMAL(10,2) NOT NULL, -- Precio mensual en USD
    applicable_plan_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_addon_plan FOREIGN KEY (applicable_plan_id) REFERENCES storage_plans(id)
);

-- Tabla para suscripciones de usuarios a complementos
CREATE TABLE IF NOT EXISTS user_addon_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    addon_id INT NOT NULL,
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    auto_renew BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_subscription_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_subscription_addon FOREIGN KEY (addon_id) REFERENCES storage_addons(id)
);

-- Modificar la tabla users para agregar campos de almacenamiento
ALTER TABLE users
ADD COLUMN storage_plan_id INT NULL,
ADD COLUMN used_storage_bytes BIGINT DEFAULT 0,
ADD COLUMN user_type ENUM('Starter', 'Individual', 'Institutes') DEFAULT 'Starter',
ADD CONSTRAINT fk_user_storage_plan FOREIGN KEY (storage_plan_id) REFERENCES storage_plans(id);

-- Actualizar tabla files para incluir campo de tamaño en bytes
ALTER TABLE files
MODIFY COLUMN size BIGINT NOT NULL;

-- Insertar planes de almacenamiento por defecto
INSERT INTO storage_plans (name, base_storage_mb, description) VALUES
('Starter', 50, 'Free plan with 50 MB of storage'),
('Individual', 5120, 'Individual plan with 5 GB of storage'),
('Institutes', 51200, 'Plan for Institutes with 50 GB of storage');


-- Insertar complementos de almacenamiento
INSERT INTO storage_addons (name, storage_mb, price_monthly_usd, applicable_plan_id) VALUES
('Extra 10GB for Individual plan', 10240, 2.00, (SELECT id FROM storage_plans WHERE name = 'Individual')),
('Extra 10GB for Institutes plan', 10240, 3.00, (SELECT id FROM storage_plans WHERE name = 'Institutes'));


-- Procedimiento almacenado para limpiar logs antiguos (opcional)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_old_logs(IN days_to_keep INT)
BEGIN
    DELETE FROM activity_logs 
    WHERE timestamp < DATE_SUB(CURRENT_TIMESTAMP, INTERVAL days_to_keep DAY);
END //
DELIMITER ;

-- Procedimiento almacenado para obtener estadísticas de sesión (opcional)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS get_session_statistics(IN session_id_param INT)
BEGIN
    SELECT 
        s.id AS session_id,
        s.name AS session_name,
        COUNT(DISTINCT p.id) AS total_participants,
        COUNT(DISTINCT ss.id) AS total_submissions,
        CASE 
            WHEN COUNT(DISTINCT p.id) = 0 THEN 0
            ELSE (COUNT(DISTINCT ss.id) / COUNT(DISTINCT p.id)) * 100 
        END AS submission_rate,
        SUM(IFNULL(ss.file_size, 0)) AS total_file_size,
        s.analysis_completed
    FROM 
        submission_sessions s
    LEFT JOIN 
        session_participants p ON s.id = p.session_id
    LEFT JOIN 
        student_submissions ss ON s.id = ss.session_id
    WHERE 
        s.id = session_id_param
    GROUP BY 
        s.id;
END //
DELIMITER ;

-- Índices adicionales para optimizar consultas frecuentes

-- Para buscar sesiones activas
CREATE INDEX idx_active_sessions ON submission_sessions(professor_id, start_date, end_date);

-- Para verificar entregas pendientes
CREATE INDEX idx_pending_submissions ON session_participants(session_id, email, invitation_sent);

-- Para búsqueda de sesiones por nombre
CREATE INDEX idx_session_name ON submission_sessions(name(20));



-- ============================================
-- SQL para crear las tablas del sistema de modelos
-- ============================================

-- 1. Tabla principal de versiones de modelos
CREATE TABLE model_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    biological_name VARCHAR(100) DEFAULT NULL,
    icon VARCHAR(50) DEFAULT NULL,
    `order` INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_model_name (name),
    INDEX idx_model_order (`order`),
    INDEX idx_model_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabla de acceso de modelos por plan
CREATE TABLE model_plan_access (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_version_id INT NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    is_default TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE CASCADE,
    INDEX idx_plan_model (plan_name, model_version_id),
    INDEX idx_model_id (model_version_id),
    INDEX idx_plan_name (plan_name),
    UNIQUE KEY unique_plan_model (plan_name, model_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabla de preferencias de modelo por usuario
CREATE TABLE user_model_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    model_version_id INT NOT NULL,
    selected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_model_version_id (model_version_id),
    UNIQUE KEY unique_user_preference (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Insertar modelos
INSERT INTO model_versions (name, version, description, biological_name, icon, `order`, is_active) VALUES
('Solenodon Detector', 'v1.0', 'Del Solenodon paradoxus (mamífero venenoso endémico, "cazador nocturno" de presas; ideal para detectar textos "escondidos" generados por IA).', 'Solenodon paradoxus', '🦡', 1, 1),
('Hutia Sentinel', 'v2.1', 'Del Plagiodontia aedium (roedor hutía, guardián de cuevas; simboliza vigilancia constante contra contenido sintético).', 'Plagiodontia aedium', '🐭', 2, 1),
('Cyclura Guard', 'v3.0', 'Del Cyclura cornuta (iguana rinoceronte, robusta y defensiva; para un modelo "blindado" contra manipulaciones de IA).', 'Cyclura cornuta', '🦎', 3, 1),
('Dulus Vigil', 'v3.5', 'Del Dulus dominicus (palmchat, ave nacional que "vigila" palmeras; perfecto para monitoreo en tiempo real de textos).', 'Dulus dominicus', '🐦', 4, 1),
('Buteo Hunter', 'v4.2', 'Del Buteo ridgwayi (halcón de Ridgway, depredador aéreo endémico; evoca precisión quirúrgica en la caza de IA).', 'Buteo ridgwayi', '🦅', 5, 1),
('Todus Scout', 'v5.0', 'Del Todus subulatus (todí de pico ancho, pájaro sigiloso y rápido; para detección ligera y eficiente).', 'Todus subulatus', '🕊️', 6, 1),
('Coccyzus Probe', 'v5.7', 'Del Coccyzus rufigularis (cuco pechirufous, explorador vocal; enfocado en analizar "voces" o patrones lingüísticos de IA).', 'Coccyzus rufigularis', '🦜', 7, 1),
('Catharus Eagle', 'v6.1', 'Del Catharus bicknelli (zorzal de Bicknell, migrador alto; representa evolución y alcance global en detección).', 'Catharus bicknelli', '🦜', 8, 1);

-- ============================================
-- Asignar acceso por planes
-- ============================================

-- Plan Starter: Solo v1.0
INSERT INTO model_plan_access (model_version_id, plan_name, is_default) VALUES
((SELECT id FROM model_versions WHERE version = 'v1.0'), 'Starter', 1);

-- Plan Scholar Suite: v1.0, v2.1
INSERT INTO model_plan_access (model_version_id, plan_name, is_default) VALUES
((SELECT id FROM model_versions WHERE version = 'v1.0'), 'Scholar Suite', 0),
((SELECT id FROM model_versions WHERE version = 'v2.1'), 'Scholar Suite', 1);

-- Plan Individual: v1.0, v2.1, v3.0, v3.5
INSERT INTO model_plan_access (model_version_id, plan_name, is_default) VALUES
((SELECT id FROM model_versions WHERE version = 'v1.0'), 'Individual', 0),
((SELECT id FROM model_versions WHERE version = 'v2.1'), 'Individual', 0),
((SELECT id FROM model_versions WHERE version = 'v3.0'), 'Individual', 0),
((SELECT id FROM model_versions WHERE version = 'v3.5'), 'Individual', 1);

-- Plan Research Essentials: v1.0, v2.1, v3.0, v3.5, v4.2
INSERT INTO model_plan_access (model_version_id, plan_name, is_default) VALUES
((SELECT id FROM model_versions WHERE version = 'v1.0'), 'Research Essentials', 0),
((SELECT id FROM model_versions WHERE version = 'v2.1'), 'Research Essentials', 0),
((SELECT id FROM model_versions WHERE version = 'v3.0'), 'Research Essentials', 0),
((SELECT id FROM model_versions WHERE version = 'v3.5'), 'Research Essentials', 0),
((SELECT id FROM model_versions WHERE version = 'v4.2'), 'Research Essentials', 1);

-- Plan Institutes: Todos los modelos (v1.0 - v6.1)
INSERT INTO model_plan_access (model_version_id, plan_name, is_default) VALUES
((SELECT id FROM model_versions WHERE version = 'v1.0'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v2.1'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v3.0'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v3.5'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v4.2'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v5.0'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v5.7'), 'Institutes', 0),
((SELECT id FROM model_versions WHERE version = 'v6.1'), 'Institutes', 1);

-- ============================================
-- Queries útiles para verificación
-- ============================================

-- Ver todos los modelos
SELECT * FROM model_versions ORDER BY `order`;

-- Ver acceso por plan
SELECT 
    mv.name,
    mv.version,
    mpa.plan_name,
    mpa.is_default
FROM model_versions mv
JOIN model_plan_access mpa ON mv.id = mpa.model_version_id
ORDER BY mpa.plan_name, mv.`order`;

-- Ver modelos disponibles para un plan específico
SELECT 
    mv.id,
    mv.name,
    mv.version,
    mv.icon,
    mpa.is_default
FROM model_versions mv
JOIN model_plan_access mpa ON mv.id = mpa.model_version_id
WHERE mpa.plan_name = 'Individual'
ORDER BY mv.`order`;

-- Ver cuántos modelos tiene cada plan
SELECT 
    plan_name,
    COUNT(*) as total_models
FROM model_plan_access
GROUP BY plan_name
ORDER BY total_models;

-- Ver preferencias de usuarios
SELECT 
    u.email,
    u.user_type,
    mv.name,
    mv.version,
    ump.updated_at
FROM user_model_preferences ump
JOIN users u ON ump.user_id = u.id
JOIN model_versions mv ON ump.model_version_id = mv.id
ORDER BY ump.updated_at DESC;